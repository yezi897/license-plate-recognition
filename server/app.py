import os
import json
import base64
from datetime import datetime
from flask import Flask, request, jsonify, Response, send_from_directory
from serial_comm import SerialComm
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


# 初始化模块
config = load_config()
serial_comm = SerialComm(config['serial_port'], config['baud_rate'])
recognizer = PlateRecognizer(
    config['baidu_app_id'],
    config['baidu_api_key'],
    config['baidu_secret_key']
)
db = Database(os.path.join(os.path.dirname(__file__), 'records.db'))

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
def connect_serial():
    try:
        if serial_comm.is_connected():
            serial_comm.disconnect()
        serial_comm.connect()
        return jsonify({'status': 'ok', 'message': '串口连接成功'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400


@app.route('/api/disconnect', methods=['POST'])
def disconnect_serial():
    serial_comm.disconnect()
    return jsonify({'status': 'ok', 'message': '已断开连接'})


@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({
        'serial_connected': serial_comm.is_connected(),
        'baidu_configured': recognizer.is_configured()
    })


@app.route('/api/capture', methods=['POST'])
def capture_and_recognize():
    if not serial_comm.is_connected():
        return jsonify({'status': 'error', 'message': '串口未连接'}), 400

    image_data = serial_comm.capture_image()
    if image_data is None:
        return jsonify({'status': 'error', 'message': '拍照失败'}), 400

    # 保存图片
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    image_filename = f"capture_{timestamp}.jpg"
    image_path = os.path.join(IMAGES_DIR, image_filename)
    with open(image_path, 'wb') as f:
        f.write(image_data)

    # 识别车牌
    result = recognizer.recognize(image_data)

    if result:
        # 保存到数据库
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
    if not serial_comm.is_connected():
        return jsonify({'status': 'error', 'message': '串口未连接'}), 400

    def generate():
        while True:
            image_data = serial_comm.capture_image()
            if image_data:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' +
                       image_data + b'\r\n')

    return Response(generate(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


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


@app.route('/api/config', methods=['GET'])
def get_config():
    config = load_config()
    return jsonify({
        'serial_port': config['serial_port'],
        'baud_rate': config['baud_rate'],
        'baidu_app_id': config['baidu_app_id'],
        'baidu_api_key': config['baidu_api_key'],
        'baidu_secret_key': config['baidu_secret_key']
    })


@app.route('/api/config', methods=['POST'])
def update_config():
    data = request.get_json()
    config = load_config()

    if 'serial_port' in data:
        config['serial_port'] = data['serial_port']
        serial_comm.port = data['serial_port']
    if 'baud_rate' in data:
        config['baud_rate'] = data['baud_rate']
        serial_comm.baud_rate = data['baud_rate']
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

    save_config(config)
    return jsonify({'status': 'ok', 'message': '配置已保存'})


if __name__ == '__main__':
    config = load_config()
    app.run(
        host=config['server_host'],
        port=config['server_port'],
        debug=True
    )
