import os
import json
import base64
import logging
import threading
from datetime import datetime
from flask import Flask, request, jsonify, Response, send_from_directory

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
from serial_comm import SerialComm
from tcp_comm import TcpComm
from plate_recognizer import PlateRecognizer
from database import Database

app = Flask(__name__, static_folder='../web')

# 加载配置
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')


def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_config(config):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def create_comm(cfg):
    """根据配置创建通信实例"""
    if cfg.get('comm_mode') == 'wifi':
        return TcpComm(cfg['esp32_ip'], cfg.get('esp32_port', 8080))
    else:
        return SerialComm(cfg['serial_port'], cfg['baud_rate'])


# 初始化模块
config = load_config()
comm = create_comm(config)
recognizer = PlateRecognizer(
    config['baidu_app_id'],
    config['baidu_api_key'],
    config['baidu_secret_key']
)
db = Database(os.path.join(os.path.dirname(__file__), 'records.db'))
comm_lock = threading.Lock()

# 图片保存目录
IMAGES_DIR = os.path.join(os.path.dirname(__file__), 'images')
os.makedirs(IMAGES_DIR, exist_ok=True)


@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory(app.static_folder, filename)


@app.route('/api/connect', methods=['POST'])
def connect_device():
    try:
        if comm.is_connected():
            comm.disconnect()
        comm.connect()
        mode = 'WiFi' if isinstance(comm, TcpComm) else '串口'
        return jsonify({'status': 'ok', 'message': f'{mode}连接成功'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400


@app.route('/api/disconnect', methods=['POST'])
def disconnect_device():
    comm.disconnect()
    return jsonify({'status': 'ok', 'message': '已断开连接'})


@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({
        'serial_connected': comm.is_connected(),
        'comm_mode': 'wifi' if isinstance(comm, TcpComm) else 'serial',
        'baidu_configured': recognizer.is_configured()
    })


@app.route('/api/debug/serial', methods=['POST'])
def debug_serial():
    """调试串口通信"""
    if not isinstance(comm, SerialComm) or not comm.is_connected():
        return jsonify({'status': 'error', 'message': '串口未连接'}), 400

    try:
        comm.serial_conn.reset_input_buffer()
        comm.serial_conn.write(b'C')
        import time
        time.sleep(2)
        available = comm.serial_conn.in_waiting
        raw_data = comm.serial_conn.read(available) if available else b''
        return jsonify({
            'status': 'ok',
            'available_bytes': available,
            'raw_data_hex': raw_data[:200].hex() if raw_data else '',
            'raw_data_ascii': raw_data[:200].decode('ascii', errors='replace') if raw_data else ''
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400


@app.route('/api/capture', methods=['POST'])
def capture_and_recognize():
    if not comm.is_connected():
        return jsonify({'status': 'error', 'message': '设备未连接'}), 400

    app.logger.info("开始拍照...")
    import time
    image_data = None
    for attempt in range(3):
        try:
            with comm_lock:
                image_data = comm.capture_image(cmd=b'C', timeout=10)
        except Exception as e:
            app.logger.error("拍照异常: %s", e)
            return jsonify({'status': 'error', 'message': f'拍照异常: {e}'}), 500
        if image_data:
            break
        if attempt < 2:
            app.logger.warning(f"拍照失败，重试 {attempt + 2}/3...")
            time.sleep(0.5)

    if image_data is None:
        app.logger.warning("拍照失败: 3 次重试后仍失败")
        return jsonify({'status': 'error', 'message': '拍照失败'}), 400
    app.logger.info(f"拍照成功, 图片大小: {len(image_data)} bytes")

    # 保存图片
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    image_filename = f"capture_{timestamp}.jpg"
    image_path = os.path.join(IMAGES_DIR, image_filename)
    with open(image_path, 'wb') as f:
        f.write(image_data)

    # 识别车牌
    try:
        result = recognizer.recognize(image_data)
    except Exception as e:
        app.logger.error("识别异常: %s", e)
        return jsonify({
            'status': 'ok',
            'result': None,
            'image': base64.b64encode(image_data).decode('utf-8'),
            'message': f'识别异常: {e}'
        })

    if result:
        db.add_record(
            result['plate_number'],
            result['color'],
            result['confidence'],
            image_filename
        )
        return jsonify({
            'status': 'ok',
            'result': result,
            'image': base64.b64encode(image_data).decode('utf-8')
        })
    else:
        return jsonify({
            'status': 'ok',
            'result': None,
            'image': base64.b64encode(image_data).decode('utf-8'),
            'message': '未识别到车牌'
        })


@app.route('/api/stream')
def video_stream():
    if not comm.is_connected():
        return jsonify({'status': 'error', 'message': '设备未连接'}), 400

    def generate():
        while comm.is_connected():
            try:
                image_data = comm.capture_image(cmd=b'S', timeout=10)
                if image_data:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' +
                           image_data + b'\r\n')
            except Exception:
                break

    return Response(generate(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/api/stream/frame')
def stream_frame():
    """单帧接口，供 JS 轮询使用，带重试机制"""
    if not comm.is_connected():
        app.logger.warning("stream_frame: 设备未连接")
        return jsonify({'status': 'error', 'message': '设备未连接'}), 400

    try:
        for attempt in range(3):
            with comm_lock:
                image_data = comm.capture_image(cmd=b'S', timeout=10)
            if image_data:
                return Response(image_data, mimetype='image/jpeg')
            app.logger.warning("stream_frame: 第 %d 次尝试失败", attempt + 1)
            if attempt < 2:
                import time
                time.sleep(0.1)
        app.logger.error("stream_frame: 3 次重试全部失败")
        return jsonify({'status': 'error', 'message': '获取帧失败'}), 400
    except Exception as e:
        app.logger.error("stream_frame 异常: %s", e)
        return jsonify({'status': 'error', 'message': str(e)}), 400


@app.route('/api/stream/recognize')
def stream_recognize():
    """从视频流抓一帧并识别，用于自动识别模式"""
    if not comm.is_connected():
        return jsonify({'status': 'error', 'message': '设备未连接'}), 400

    try:
        with comm_lock:
            image_data = comm.capture_image(cmd=b'C', timeout=10)
    except Exception as e:
        app.logger.error("自动识别拍照异常: %s", e)
        return jsonify({'status': 'error', 'message': str(e)}), 500

    if image_data is None:
        return jsonify({'status': 'error', 'message': '拍照失败'}), 400

    # 保存图片
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    image_filename = f"auto_{timestamp}.jpg"
    image_path = os.path.join(IMAGES_DIR, image_filename)
    with open(image_path, 'wb') as f:
        f.write(image_data)

    try:
        result = recognizer.recognize(image_data)
    except Exception as e:
        app.logger.error("自动识别异常: %s", e)
        return jsonify({'status': 'error', 'message': str(e)}), 500

    if result:
        db.add_record(
            result['plate_number'],
            result['color'],
            result['confidence'],
            image_filename
        )
        return jsonify({
            'status': 'ok',
            'result': result,
            'image': base64.b64encode(image_data).decode('utf-8')
        })
    else:
        return jsonify({
            'status': 'ok',
            'result': None,
            'image': base64.b64encode(image_data).decode('utf-8')
        })


@app.route('/api/history', methods=['GET'])
def get_history():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    records = db.get_records(page, per_page)
    total = db.get_total_count()
    return jsonify({
        'records': records,
        'total': total,
        'page': page,
        'per_page': per_page
    })


@app.route('/api/history/clear', methods=['POST'])
def clear_history():
    if os.path.exists(IMAGES_DIR):
        for f in os.listdir(IMAGES_DIR):
            file_path = os.path.join(IMAGES_DIR, f)
            if os.path.isfile(file_path):
                os.remove(file_path)
    db.clear_records()
    return jsonify({'status': 'ok', 'message': '历史记录已清空'})


@app.route('/api/config', methods=['GET'])
def get_config():
    config = load_config()
    return jsonify({
        'comm_mode': config.get('comm_mode', 'serial'),
        'serial_port': config['serial_port'],
        'baud_rate': config['baud_rate'],
        'esp32_ip': config.get('esp32_ip', ''),
        'esp32_port': config.get('esp32_port', 8080),
        'wifi_ssid': config.get('wifi_ssid', ''),
        'wifi_password': config.get('wifi_password', ''),
        'baidu_app_id': config['baidu_app_id'],
        'baidu_api_key': config['baidu_api_key'],
        'baidu_secret_key': config['baidu_secret_key']
    })


@app.route('/api/config', methods=['POST'])
def update_config():
    global comm
    data = request.get_json()
    config = load_config()

    old_mode = config.get('comm_mode', 'serial')
    need_mode_switch = False

    # 更新通信模式
    if 'comm_mode' in data:
        new_mode = data['comm_mode']
        if new_mode in ('serial', 'wifi'):
            config['comm_mode'] = new_mode
            if new_mode != old_mode:
                need_mode_switch = True

    # 串口配置
    need_reconnect = False
    if 'serial_port' in data:
        config['serial_port'] = data['serial_port']
        if isinstance(comm, SerialComm):
            comm.port = data['serial_port']
            need_reconnect = True
    if 'baud_rate' in data:
        config['baud_rate'] = data['baud_rate']
        if isinstance(comm, SerialComm):
            comm.baud_rate = data['baud_rate']
            need_reconnect = True

    # WiFi/TCP 配置
    if 'esp32_ip' in data:
        config['esp32_ip'] = data['esp32_ip']
        if isinstance(comm, TcpComm):
            comm.host = data['esp32_ip']
    if 'esp32_port' in data:
        config['esp32_port'] = data['esp32_port']
        if isinstance(comm, TcpComm):
            comm.port = data['esp32_port']

    # WiFi 凭据 — 通过串口发送给 ESP32
    wifi_cred_changed = False
    if 'wifi_ssid' in data:
        config['wifi_ssid'] = data['wifi_ssid']
        wifi_cred_changed = True
    if 'wifi_password' in data:
        config['wifi_password'] = data['wifi_password']
        wifi_cred_changed = True

    # 百度云配置
    if 'baidu_app_id' in data:
        config['baidu_app_id'] = data['baidu_app_id']
    if 'baidu_api_key' in data:
        config['baidu_api_key'] = data['baidu_api_key']
    if 'baidu_secret_key' in data:
        config['baidu_secret_key'] = data['baidu_secret_key']

    recognizer.update_credentials(
        config['baidu_app_id'],
        config['baidu_api_key'],
        config['baidu_secret_key']
    )

    # 如果 WiFi 凭据变更，通过串口发送给 ESP32
    if wifi_cred_changed and config['wifi_ssid']:
        if isinstance(comm, SerialComm) and comm.is_connected():
            try:
                cmd = f"W:{config['wifi_ssid']}\n{config['wifi_password']}\n"
                comm.serial_conn.write(cmd.encode('utf-8'))
                comm.serial_conn.flush()
                app.logger.info("已发送 WiFi 凭据给 ESP32: %s", config['wifi_ssid'])
            except Exception as e:
                app.logger.warning("发送 WiFi 凭据失败: %s", e)
        else:
            app.logger.info("WiFi 凭据已保存，需在串口模式下连接设备后才能发送给 ESP32")

    # 切换通信模式
    if need_mode_switch:
        comm.disconnect()
        comm = create_comm(config)
        app.logger.info("通信模式已切换为: %s", config['comm_mode'])
    elif need_reconnect and comm.is_connected():
        # 串口配置变更，自动重连
        comm.disconnect()
        try:
            comm.connect()
        except Exception as e:
            app.logger.warning("重连失败: %s", e)

    save_config(config)
    return jsonify({'status': 'ok', 'message': '配置已保存'})


if __name__ == '__main__':
    config = load_config()
    app.run(
        host=config['server_host'],
        port=config['server_port'],
        debug=True
    )
