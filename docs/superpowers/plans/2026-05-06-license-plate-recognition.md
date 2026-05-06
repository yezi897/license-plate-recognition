# 车牌识别系统实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建基于 ESP32-CAM 的车牌识别系统，通过串口连接电脑，Python 服务器调用百度云 API 识别车牌，Web 界面展示结果。

**Architecture:** ESP32-CAM 通过 FTDI 串口连接电脑，Python Flask 服务器负责串口通信、百度云 API 调用、Web 服务和历史记录存储。

**Tech Stack:** Arduino (ESP32-CAM), Python Flask, pyserial, baidu-aip, SQLite, HTML/CSS/JS

---

## 文件结构

```
视觉/
├── firmware/
│   └── camera_capture/
│       └── camera_capture.ino        # ESP32-CAM 固件主文件
├── server/
│   ├── app.py                        # Flask 主程序
│   ├── serial_comm.py                # 串口通信模块
│   ├── plate_recognizer.py           # 百度云车牌识别模块
│   ├── database.py                   # SQLite 数据库模块
│   ├── config.json                   # 配置文件
│   └── requirements.txt              # Python 依赖
├── web/
│   ├── index.html                    # 主页面
│   ├── style.css                     # 样式
│   └── app.js                        # 前端逻辑
└── docs/
```

---

### Task 1: 创建 ESP32-CAM 固件

**Files:**
- Create: `firmware/camera_capture/camera_capture.ino`

- [ ] **Step 1: 创建固件目录和主文件**

```bash
mkdir -p firmware/camera_capture
```

- [ ] **Step 2: 编写 ESP32-CAM 固件代码**

创建 `firmware/camera_capture/camera_capture.ino`：

```cpp
#include "esp_camera.h"
#include "Arduino.h"

// ESP32-CAM (AI Thinker) 引脚定义
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

// 闪光灯
#define FLASH_GPIO_NUM     4

void setup() {
  Serial.begin(921600);
  Serial.setDebugOutput(true);

  // 初始化摄像头
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.grab_mode = CAMERA_GRAB_LATEST;
  config.fb_location = CAMERA_FB_IN_PSRAM;
  config.jpeg_quality = 12;
  config.fb_count = 1;

  // 根据 PSRAM 调整分辨率
  if (psramFound()) {
    config.frame_size = FRAMESIZE_VGA;  // 640x480
    config.jpeg_quality = 10;
    config.fb_count = 2;
  } else {
    config.frame_size = FRAMESIZE_QVGA;  // 320x240
    config.jpeg_quality = 12;
    config.fb_count = 1;
  }

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("摄像头初始化失败: 0x%x\n", err);
    return;
  }

  // 设置摄像头参数
  sensor_t *s = esp_camera_sensor_get();
  s->set_brightness(s, 1);
  s->set_contrast(s, 1);

  // 初始化闪光灯
  pinMode(FLASH_GPIO_NUM, OUTPUT);
  digitalWrite(FLASH_GPIO_NUM, LOW);

  Serial.println("READY");
}

void loop() {
  if (Serial.available()) {
    char cmd = Serial.read();
    if (cmd == 'C') {
      captureAndSend();
    } else if (cmd == 'F') {
      flashCapture();
    }
  }
}

void captureAndSend() {
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("CAPTURE_FAIL");
    return;
  }

  // 发送帧头标记
  Serial.write("IMG_START");
  // 发送图片长度（4字节）
  uint32_t len = fb->len;
  Serial.write((uint8_t)(len & 0xFF));
  Serial.write((uint8_t)((len >> 8) & 0xFF));
  Serial.write((uint8_t)((len >> 16) & 0xFF));
  Serial.write((uint8_t)((len >> 24) & 0xFF));
  // 发送图片数据
  Serial.write(fb->buf, fb->len);
  // 发送帧尾标记
  Serial.write("IMG_END");

  esp_camera_fb_return(fb);
}

void flashCapture() {
  digitalWrite(FLASH_GPIO_NUM, HIGH);
  delay(100);
  captureAndSend();
  digitalWrite(FLASH_GPIO_NUM, LOW);
}
```

- [ ] **Step 3: 验证固件能编译**

运行：
```bash
arduino-cli compile --fqbn esp32:esp32:ai-thinker-esp32-cam firmware/camera_capture/
```
预期：编译成功，无错误

- [ ] **Step 4: 烧录固件到 ESP32-CAM**

运行：
```bash
arduino-cli upload -p COM3 --fqbn esp32:esp32:ai-thinker-esp32-cam firmware/camera_capture/
```
预期：烧录成功，串口监视器输出 `READY`

- [ ] **Step 5: 提交固件代码**

```bash
git add firmware/
git commit -m "feat: add ESP32-CAM firmware for serial image capture"
```

---

### Task 2: 创建 Python 项目结构和依赖

**Files:**
- Create: `server/requirements.txt`
- Create: `server/config.json`

- [ ] **Step 1: 创建目录结构**

```bash
mkdir -p server web
```

- [ ] **Step 2: 创建 requirements.txt**

创建 `server/requirements.txt`：

```
flask==3.1.1
pyserial==3.5
baidu-aip==4.16.13
Pillow==11.2.1
```

- [ ] **Step 3: 创建默认配置文件**

创建 `server/config.json`：

```json
{
  "serial_port": "COM3",
  "baud_rate": 921600,
  "baidu_app_id": "",
  "baidu_api_key": "",
  "baidu_secret_key": "",
  "server_host": "0.0.0.0",
  "server_port": 5000
}
```

- [ ] **Step 4: 安装依赖**

运行：
```bash
cd server && pip install -r requirements.txt
```
预期：所有依赖安装成功

- [ ] **Step 5: 提交**

```bash
git add server/requirements.txt server/config.json
git commit -m "feat: add Python project structure and dependencies"
```

---

### Task 3: 实现串口通信模块（TDD）

**Files:**
- Create: `server/serial_comm.py`
- Create: `server/test_serial_comm.py`

- [ ] **Step 1: 编写串口通信测试**

创建 `server/test_serial_comm.py`：

```python
import pytest
from unittest.mock import MagicMock, patch
from serial_comm import SerialComm


class TestSerialComm:
    def test_init_with_valid_config(self):
        """测试用有效配置初始化"""
        comm = SerialComm("COM3", 921600)
        assert comm.port == "COM3"
        assert comm.baud_rate == 921600

    def test_init_default_baud_rate(self):
        """测试默认波特率"""
        comm = SerialComm("COM3")
        assert comm.baud_rate == 921600

    @patch('serial_comm.serial.Serial')
    def test_connect(self, mock_serial):
        """测试连接串口"""
        comm = SerialComm("COM3", 921600)
        comm.connect()
        mock_serial.assert_called_once_with("COM3", 921600, timeout=2)

    @patch('serial_comm.serial.Serial')
    def test_capture_image_returns_bytes(self, mock_serial):
        """测试拍照返回图片字节数据"""
        mock_conn = MagicMock()
        mock_serial.return_value = mock_conn

        # 模拟串口返回：IMG_START + 长度(4字节) + 数据 + IMG_END
        test_data = b'\x89PNG_test'
        img_start = b'IMG_START'
        img_end = b'IMG_END'
        length_bytes = len(test_data).to_bytes(4, 'little')

        mock_conn.read.side_effect = [
            img_start,
            length_bytes,
            test_data,
            img_end
        ]
        mock_conn.in_waiting = True

        comm = SerialComm("COM3")
        comm.connect()
        result = comm.capture_image()

        assert result is not None
        assert isinstance(result, bytes)
        assert result == test_data

    @patch('serial_comm.serial.Serial')
    def test_capture_image_returns_none_on_fail(self, mock_serial):
        """测试拍照失败返回 None"""
        mock_conn = MagicMock()
        mock_serial.return_value = mock_conn
        mock_conn.read.return_value = b'CAPTURE_FAIL'

        comm = SerialComm("COM3")
        comm.connect()
        result = comm.capture_image()

        assert result is None

    @patch('serial_comm.serial.Serial')
    def test_is_connected(self, mock_serial):
        """测试连接状态检查"""
        comm = SerialComm("COM3")
        assert comm.is_connected() is False

        comm.connect()
        assert comm.is_connected() is True

    @patch('serial_comm.serial.Serial')
    def test_disconnect(self, mock_serial):
        """测试断开连接"""
        mock_conn = MagicMock()
        mock_serial.return_value = mock_conn

        comm = SerialComm("COM3")
        comm.connect()
        comm.disconnect()

        mock_conn.close.assert_called_once()
        assert comm.is_connected() is False
```

- [ ] **Step 2: 运行测试确认失败**

运行：
```bash
cd server && python -m pytest test_serial_comm.py -v
```
预期：FAIL — `ModuleNotFoundError: No module named 'serial_comm'`

- [ ] **Step 3: 实现串口通信模块**

创建 `server/serial_comm.py`：

```python
import serial
import time


class SerialComm:
    def __init__(self, port, baud_rate=921600):
        self.port = port
        self.baud_rate = baud_rate
        self.serial_conn = None

    def connect(self):
        self.serial_conn = serial.Serial(
            self.port, self.baud_rate, timeout=2
        )
        time.sleep(0.5)

    def is_connected(self):
        return self.serial_conn is not None and self.serial_conn.is_open

    def disconnect(self):
        if self.serial_conn:
            self.serial_conn.close()
            self.serial_conn = None

    def capture_image(self):
        if not self.is_connected():
            return None

        self.serial_conn.reset_input_buffer()
        self.serial_conn.write(b'C')

        # 等待 IMG_START 标记
        header = self._read_until(b'IMG_START')
        if header is None:
            return None

        # 读取图片长度（4字节）
        length_bytes = self.serial_conn.read(4)
        if len(length_bytes) < 4:
            return None
        img_length = int.from_bytes(length_bytes, 'little')

        # 读取图片数据
        img_data = b''
        remaining = img_length
        while remaining > 0:
            chunk = self.serial_conn.read(min(remaining, 1024))
            if not chunk:
                break
            img_data += chunk
            remaining -= len(chunk)

        # 读取 IMG_END 标记
        self._read_until(b'IMG_END')

        if len(img_data) == img_length:
            return img_data
        return None

    def _read_until(self, marker, timeout=5):
        start = time.time()
        buffer = b''
        while time.time() - start < timeout:
            if self.serial_conn.in_waiting:
                buffer += self.serial_conn.read(self.serial_conn.in_waiting)
                if marker in buffer:
                    return marker
            time.sleep(0.01)
        return None
```

- [ ] **Step 4: 运行测试确认通过**

运行：
```bash
cd server && python -m pytest test_serial_comm.py -v
```
预期：全部 PASS

- [ ] **Step 5: 提交**

```bash
git add server/serial_comm.py server/test_serial_comm.py
git commit -m "feat: add serial communication module with tests"
```

---

### Task 4: 实现车牌识别模块（TDD）

**Files:**
- Create: `server/plate_recognizer.py`
- Create: `server/test_plate_recognizer.py`

- [ ] **Step 1: 编写车牌识别测试**

创建 `server/test_plate_recognizer.py`：

```python
import pytest
from unittest.mock import MagicMock, patch
from plate_recognizer import PlateRecognizer


class TestPlateRecognizer:
    def test_init_with_credentials(self):
        """测试用凭证初始化"""
        recognizer = PlateRecognizer("app_id", "api_key", "secret_key")
        assert recognizer.app_id == "app_id"
        assert recognizer.api_key == "api_key"
        assert recognizer.secret_key == "secret_key"

    def test_init_with_empty_credentials(self):
        """测试空凭证初始化"""
        recognizer = PlateRecognizer("", "", "")
        assert recognizer.is_configured() is False

    def test_is_configured_true(self):
        """测试已配置状态"""
        recognizer = PlateRecognizer("app_id", "api_key", "secret_key")
        assert recognizer.is_configured() is True

    @patch('plate_recognizer.AipOcr')
    def test_recognize_plate_success(self, mock_ocr_class):
        """测试成功识别车牌"""
        mock_ocr = MagicMock()
        mock_ocr_class.return_value = mock_ocr

        mock_ocr.licensePlate.return_value = {
            'words_result': [{
                'number': '京A12345',
                'color': '蓝色',
                'probability': [0.98, 0.97, 0.96]
            }]
        }

        recognizer = PlateRecognizer("app_id", "api_key", "secret_key")
        result = recognizer.recognize(b'fake_image_data')

        assert result is not None
        assert result['plate_number'] == '京A12345'
        assert result['color'] == '蓝色'
        assert result['confidence'] > 0

    @patch('plate_recognizer.AipOcr')
    def test_recognize_plate_no_result(self, mock_ocr_class):
        """测试未识别到车牌"""
        mock_ocr = MagicMock()
        mock_ocr_class.return_value = mock_ocr
        mock_ocr.licensePlate.return_value = {'words_result': []}

        recognizer = PlateRecognizer("app_id", "api_key", "secret_key")
        result = recognizer.recognize(b'fake_image_data')

        assert result is None

    def test_recognize_not_configured(self):
        """测试未配置时识别"""
        recognizer = PlateRecognizer("", "", "")
        result = recognizer.recognize(b'fake_image_data')
        assert result is None
```

- [ ] **Step 2: 运行测试确认失败**

运行：
```bash
cd server && python -m pytest test_plate_recognizer.py -v
```
预期：FAIL — `ModuleNotFoundError: No module named 'plate_recognizer'`

- [ ] **Step 3: 实现车牌识别模块**

创建 `server/plate_recognizer.py`：

```python
from aip import AipOcr


class PlateRecognizer:
    def __init__(self, app_id, api_key, secret_key):
        self.app_id = app_id
        self.api_key = api_key
        self.secret_key = secret_key
        self.client = None
        if self.is_configured():
            self.client = AipOcr(app_id, api_key, secret_key)

    def is_configured(self):
        return bool(self.app_id and self.api_key and self.secret_key)

    def update_credentials(self, app_id, api_key, secret_key):
        self.app_id = app_id
        self.api_key = api_key
        self.secret_key = secret_key
        if self.is_configured():
            self.client = AipOcr(app_id, api_key, secret_key)
        else:
            self.client = None

    def recognize(self, image_data):
        if not self.is_configured() or not self.client:
            return None

        result = self.client.licensePlate(image_data)

        if 'words_result' not in result or not result['words_result']:
            return None

        plate_info = result['words_result'][0]
        probabilities = plate_info.get('probability', [0])

        return {
            'plate_number': plate_info['number'],
            'color': plate_info['color'],
            'confidence': round(sum(probabilities) / len(probabilities) * 100, 2)
        }
```

- [ ] **Step 4: 运行测试确认通过**

运行：
```bash
cd server && python -m pytest test_plate_recognizer.py -v
```
预期：全部 PASS

- [ ] **Step 5: 提交**

```bash
git add server/plate_recognizer.py server/test_plate_recognizer.py
git commit -m "feat: add plate recognizer module with Baidu Cloud API integration"
```

---

### Task 5: 实现数据库模块（TDD）

**Files:**
- Create: `server/database.py`
- Create: `server/test_database.py`

- [ ] **Step 1: 编写数据库测试**

创建 `server/test_database.py`：

```python
import pytest
import os
import sqlite3
from database import Database


class TestDatabase:
    @pytest.fixture
    def db(self, tmp_path):
        """创建临时数据库"""
        db_path = str(tmp_path / "test.db")
        return Database(db_path)

    def test_init_creates_table(self, db):
        """测试初始化创建表"""
        conn = sqlite3.connect(db.db_path)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='records'"
        )
        assert cursor.fetchone() is not None
        conn.close()

    def test_add_record(self, db):
        """测试添加记录"""
        db.add_record("京A12345", "蓝色", 98.5, "test.jpg")
        records = db.get_records()
        assert len(records) == 1
        assert records[0]['plate_number'] == "京A12345"
        assert records[0]['color'] == "蓝色"
        assert records[0]['confidence'] == 98.5

    def test_get_records_empty(self, db):
        """测试空记录"""
        records = db.get_records()
        assert records == []

    def test_get_records_multiple(self, db):
        """测试多条记录"""
        db.add_record("京A12345", "蓝色", 98.5, "test1.jpg")
        db.add_record("沪B67890", "绿色", 95.0, "test2.jpg")
        records = db.get_records()
        assert len(records) == 2

    def test_get_records_with_pagination(self, db):
        """测试分页"""
        for i in range(15):
            db.add_record(f"京A{i:05d}", "蓝色", 95.0, f"test{i}.jpg")

        page1 = db.get_records(page=1, per_page=10)
        page2 = db.get_records(page=2, per_page=10)
        assert len(page1) == 10
        assert len(page2) == 5

    def test_get_records_order_desc(self, db):
        """测试按时间倒序"""
        db.add_record("京A11111", "蓝色", 95.0, "test1.jpg")
        db.add_record("沪B22222", "绿色", 90.0, "test2.jpg")
        records = db.get_records()
        assert records[0]['plate_number'] == "沪B22222"

    def test_get_total_count(self, db):
        """测试总数统计"""
        db.add_record("京A11111", "蓝色", 95.0, "test1.jpg")
        db.add_record("沪B22222", "绿色", 90.0, "test2.jpg")
        assert db.get_total_count() == 2
```

- [ ] **Step 2: 运行测试确认失败**

运行：
```bash
cd server && python -m pytest test_database.py -v
```
预期：FAIL — `ModuleNotFoundError: No module named 'database'`

- [ ] **Step 3: 实现数据库模块**

创建 `server/database.py`：

```python
import sqlite3
from datetime import datetime


class Database:
    def __init__(self, db_path="records.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plate_number TEXT NOT NULL,
                color TEXT,
                confidence REAL,
                image_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    def add_record(self, plate_number, color, confidence, image_path=None):
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO records (plate_number, color, confidence, image_path) VALUES (?, ?, ?, ?)",
            (plate_number, color, confidence, image_path)
        )
        conn.commit()
        conn.close()

    def get_records(self, page=1, per_page=20):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        offset = (page - 1) * per_page
        cursor = conn.execute(
            "SELECT * FROM records ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (per_page, offset)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_total_count(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("SELECT COUNT(*) FROM records")
        count = cursor.fetchone()[0]
        conn.close()
        return count
```

- [ ] **Step 4: 运行测试确认通过**

运行：
```bash
cd server && python -m pytest test_database.py -v
```
预期：全部 PASS

- [ ] **Step 5: 提交**

```bash
git add server/database.py server/test_database.py
git commit -m "feat: add database module for recognition history"
```

---

### Task 6: 实现 Flask 主服务器

**Files:**
- Create: `server/app.py`

- [ ] **Step 1: 编写 Flask 主程序**

创建 `server/app.py`：

```python
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
```

- [ ] **Step 2: 验证服务器能启动**

运行：
```bash
cd server && python app.py
```
预期：Flask 服务器启动，监听 5000 端口

- [ ] **Step 3: 提交**

```bash
git add server/app.py
git commit -m "feat: add Flask main server with all API endpoints"
```

---

### Task 7: 实现 Web 前端页面

**Files:**
- Create: `web/index.html`
- Create: `web/style.css`
- Create: `web/app.js`

- [ ] **Step 1: 创建主页面**

创建 `web/index.html`：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>车牌识别系统</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>车牌识别系统</h1>
            <div class="header-actions">
                <span id="status-indicator" class="status disconnected">未连接</span>
                <button id="btn-settings" class="btn btn-secondary">⚙️ 设置</button>
            </div>
        </header>

        <main>
            <div class="panel video-panel">
                <h2>实时预览</h2>
                <div class="video-container">
                    <img id="video-stream" src="" alt="视频流">
                    <div id="video-placeholder" class="placeholder">
                        <p>请先连接串口设备</p>
                    </div>
                </div>
                <div class="video-actions">
                    <button id="btn-connect" class="btn btn-primary">连接设备</button>
                    <button id="btn-capture" class="btn btn-success" disabled>📸 拍照识别</button>
                </div>
            </div>

            <div class="side-panels">
                <div class="panel result-panel">
                    <h2>识别结果</h2>
                    <div id="result-content" class="result-content">
                        <p class="placeholder">等待识别...</p>
                    </div>
                </div>

                <div class="panel history-panel">
                    <h2>识别历史</h2>
                    <div class="table-container">
                        <table id="history-table">
                            <thead>
                                <tr>
                                    <th>车牌号</th>
                                    <th>颜色</th>
                                    <th>置信度</th>
                                    <th>时间</th>
                                </tr>
                            </thead>
                            <tbody id="history-body">
                            </tbody>
                        </table>
                    </div>
                    <div class="pagination">
                        <button id="btn-prev" class="btn btn-small" disabled>上一页</button>
                        <span id="page-info">第 1 页</span>
                        <button id="btn-next" class="btn btn-small" disabled>下一页</button>
                    </div>
                </div>
            </div>
        </main>
    </div>

    <!-- 设置弹窗 -->
    <div id="settings-modal" class="modal hidden">
        <div class="modal-content">
            <div class="modal-header">
                <h2>系统设置</h2>
                <button id="btn-close-modal" class="btn-close">&times;</button>
            </div>
            <div class="modal-body">
                <div class="form-group">
                    <label>串口端口</label>
                    <input type="text" id="input-port" placeholder="COM3">
                </div>
                <div class="form-group">
                    <label>波特率</label>
                    <input type="number" id="input-baud" value="921600">
                </div>
                <hr>
                <h3>百度云 API 配置</h3>
                <div class="form-group">
                    <label>App ID</label>
                    <input type="text" id="input-app-id" placeholder="百度云 App ID">
                </div>
                <div class="form-group">
                    <label>API Key</label>
                    <input type="text" id="input-api-key" placeholder="百度云 API Key">
                </div>
                <div class="form-group">
                    <label>Secret Key</label>
                    <input type="password" id="input-secret-key" placeholder="百度云 Secret Key">
                </div>
            </div>
            <div class="modal-footer">
                <button id="btn-save-config" class="btn btn-primary">保存</button>
                <button id="btn-cancel-config" class="btn btn-secondary">取消</button>
            </div>
        </div>
    </div>

    <script src="app.js"></script>
</body>
</html>
```

- [ ] **Step 2: 创建样式文件**

创建 `web/style.css`：

```css
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #f0f2f5;
    color: #333;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding: 15px 20px;
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

header h1 {
    font-size: 24px;
    color: #1a1a1a;
}

.header-actions {
    display: flex;
    align-items: center;
    gap: 12px;
}

.status {
    padding: 6px 12px;
    border-radius: 20px;
    font-size: 14px;
    font-weight: 500;
}

.status.connected {
    background: #e6f7e6;
    color: #52c41a;
}

.status.disconnected {
    background: #fff2e8;
    color: #fa8c16;
}

main {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
}

.panel {
    background: #fff;
    border-radius: 8px;
    padding: 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.panel h2 {
    font-size: 18px;
    margin-bottom: 15px;
    color: #1a1a1a;
}

.video-container {
    width: 100%;
    aspect-ratio: 4/3;
    background: #000;
    border-radius: 8px;
    overflow: hidden;
    position: relative;
}

.video-container img {
    width: 100%;
    height: 100%;
    object-fit: contain;
}

.placeholder {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    color: #999;
}

.video-actions {
    display: flex;
    gap: 10px;
    margin-top: 15px;
}

.btn {
    padding: 10px 20px;
    border: none;
    border-radius: 6px;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.2s;
}

.btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.btn-primary {
    background: #1890ff;
    color: #fff;
}

.btn-primary:hover:not(:disabled) {
    background: #40a9ff;
}

.btn-success {
    background: #52c41a;
    color: #fff;
}

.btn-success:hover:not(:disabled) {
    background: #73d13d;
}

.btn-secondary {
    background: #f0f0f0;
    color: #333;
}

.btn-secondary:hover:not(:disabled) {
    background: #d9d9d9;
}

.btn-small {
    padding: 6px 12px;
    font-size: 12px;
}

.side-panels {
    display: flex;
    flex-direction: column;
    gap: 20px;
}

.result-content {
    min-height: 100px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.result-item {
    text-align: center;
}

.result-item .plate-number {
    font-size: 32px;
    font-weight: bold;
    color: #1890ff;
    margin-bottom: 10px;
}

.result-item .plate-info {
    color: #666;
}

.table-container {
    max-height: 300px;
    overflow-y: auto;
}

table {
    width: 100%;
    border-collapse: collapse;
}

th, td {
    padding: 10px;
    text-align: left;
    border-bottom: 1px solid #f0f0f0;
}

th {
    background: #fafafa;
    font-weight: 600;
}

.pagination {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 15px;
    margin-top: 15px;
}

/* 弹窗 */
.modal {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0,0,0,0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
}

.modal.hidden {
    display: none;
}

.modal-content {
    background: #fff;
    border-radius: 8px;
    width: 450px;
    max-width: 90%;
}

.modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px;
    border-bottom: 1px solid #f0f0f0;
}

.modal-header h2 {
    margin: 0;
}

.btn-close {
    background: none;
    border: none;
    font-size: 24px;
    cursor: pointer;
    color: #999;
}

.modal-body {
    padding: 20px;
}

.modal-body h3 {
    margin: 15px 0 10px;
    color: #666;
}

.form-group {
    margin-bottom: 15px;
}

.form-group label {
    display: block;
    margin-bottom: 5px;
    font-weight: 500;
}

.form-group input {
    width: 100%;
    padding: 10px;
    border: 1px solid #d9d9d9;
    border-radius: 6px;
    font-size: 14px;
}

.form-group input:focus {
    outline: none;
    border-color: #1890ff;
    box-shadow: 0 0 0 2px rgba(24,144,255,0.2);
}

.modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    padding: 20px;
    border-top: 1px solid #f0f0f0;
}
```

- [ ] **Step 3: 创建前端逻辑**

创建 `web/app.js`：

```javascript
const API_BASE = '';

// 状态
let currentPage = 1;
let isConnected = false;

// DOM 元素
const statusIndicator = document.getElementById('status-indicator');
const btnConnect = document.getElementById('btn-connect');
const btnCapture = document.getElementById('btn-capture');
const btnSettings = document.getElementById('btn-settings');
const videoStream = document.getElementById('video-stream');
const videoPlaceholder = document.getElementById('video-placeholder');
const resultContent = document.getElementById('result-content');
const historyBody = document.getElementById('history-body');
const btnPrev = document.getElementById('btn-prev');
const btnNext = document.getElementById('btn-next');
const pageInfo = document.getElementById('page-info');
const settingsModal = document.getElementById('settings-modal');
const btnCloseModal = document.getElementById('btn-close-modal');
const btnSaveConfig = document.getElementById('btn-save-config');
const btnCancelConfig = document.getElementById('btn-cancel-config');

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    checkStatus();
    loadHistory();
    loadConfig();
    bindEvents();
});

function bindEvents() {
    btnConnect.addEventListener('click', toggleConnection);
    btnCapture.addEventListener('click', captureAndRecognize);
    btnSettings.addEventListener('click', () => settingsModal.classList.remove('hidden'));
    btnCloseModal.addEventListener('click', () => settingsModal.classList.add('hidden'));
    btnCancelConfig.addEventListener('click', () => settingsModal.classList.add('hidden'));
    btnSaveConfig.addEventListener('click', saveConfig);
    btnPrev.addEventListener('click', () => changePage(-1));
    btnNext.addEventListener('click', () => changePage(1));
}

async function checkStatus() {
    try {
        const res = await fetch(`${API_BASE}/api/status`);
        const data = await res.json();
        isConnected = data.serial_connected;
        updateStatusUI();
    } catch (e) {
        console.error('获取状态失败:', e);
    }
}

function updateStatusUI() {
    if (isConnected) {
        statusIndicator.textContent = '已连接';
        statusIndicator.className = 'status connected';
        btnConnect.textContent = '断开连接';
        btnCapture.disabled = false;
        videoPlaceholder.style.display = 'none';
        videoStream.src = `${API_BASE}/api/stream`;
    } else {
        statusIndicator.textContent = '未连接';
        statusIndicator.className = 'status disconnected';
        btnConnect.textContent = '连接设备';
        btnCapture.disabled = true;
        videoStream.src = '';
        videoPlaceholder.style.display = 'block';
    }
}

async function toggleConnection() {
    if (isConnected) {
        await fetch(`${API_BASE}/api/disconnect`, { method: 'POST' });
        isConnected = false;
    } else {
        try {
            const res = await fetch(`${API_BASE}/api/connect`, { method: 'POST' });
            const data = await res.json();
            if (data.status === 'ok') {
                isConnected = true;
            } else {
                alert('连接失败: ' + data.message);
            }
        } catch (e) {
            alert('连接失败: ' + e.message);
        }
    }
    updateStatusUI();
}

async function captureAndRecognize() {
    btnCapture.disabled = true;
    btnCapture.textContent = '识别中...';
    resultContent.innerHTML = '<p class="placeholder">正在识别...</p>';

    try {
        const res = await fetch(`${API_BASE}/api/capture`, { method: 'POST' });
        const data = await res.json();

        if (data.status === 'ok' && data.result) {
            resultContent.innerHTML = `
                <div class="result-item">
                    <div class="plate-number">${data.result.plate_number}</div>
                    <div class="plate-info">
                        <p>颜色: ${data.result.color}</p>
                        <p>置信度: ${data.result.confidence}%</p>
                    </div>
                </div>
            `;
            loadHistory();
        } else if (data.image) {
            resultContent.innerHTML = `
                <div class="result-item">
                    <p class="placeholder">${data.message || '未识别到车牌'}</p>
                </div>
            `;
        } else {
            resultContent.innerHTML = `<p class="placeholder">${data.message || '识别失败'}</p>`;
        }
    } catch (e) {
        resultContent.innerHTML = `<p class="placeholder">识别出错: ${e.message}</p>`;
    }

    btnCapture.disabled = false;
    btnCapture.textContent = '📸 拍照识别';
}

async function loadHistory() {
    try {
        const res = await fetch(`${API_BASE}/api/history?page=${currentPage}&per_page=10`);
        const data = await res.json();

        historyBody.innerHTML = '';
        data.records.forEach(record => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${record.plate_number}</td>
                <td>${record.color}</td>
                <td>${record.confidence}%</td>
                <td>${new Date(record.created_at).toLocaleString('zh-CN')}</td>
            `;
            historyBody.appendChild(row);
        });

        const totalPages = Math.ceil(data.total / data.per_page);
        pageInfo.textContent = `第 ${currentPage} 页 / 共 ${totalPages} 页`;
        btnPrev.disabled = currentPage <= 1;
        btnNext.disabled = currentPage >= totalPages;
    } catch (e) {
        console.error('加载历史记录失败:', e);
    }
}

function changePage(delta) {
    currentPage += delta;
    loadHistory();
}

async function loadConfig() {
    try {
        const res = await fetch(`${API_BASE}/api/config`);
        const config = await res.json();
        document.getElementById('input-port').value = config.serial_port || '';
        document.getElementById('input-baud').value = config.baud_rate || 921600;
        document.getElementById('input-app-id').value = config.baidu_app_id || '';
        document.getElementById('input-api-key').value = config.baidu_api_key || '';
        document.getElementById('input-secret-key').value = config.baidu_secret_key || '';
    } catch (e) {
        console.error('加载配置失败:', e);
    }
}

async function saveConfig() {
    const config = {
        serial_port: document.getElementById('input-port').value,
        baud_rate: parseInt(document.getElementById('input-baud').value),
        baidu_app_id: document.getElementById('input-app-id').value,
        baidu_api_key: document.getElementById('input-api-key').value,
        baidu_secret_key: document.getElementById('input-secret-key').value
    };

    try {
        const res = await fetch(`${API_BASE}/api/config`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        const data = await res.json();
        if (data.status === 'ok') {
            settingsModal.classList.add('hidden');
            alert('配置已保存');
        }
    } catch (e) {
        alert('保存失败: ' + e.message);
    }
}
```

- [ ] **Step 4: 验证前端页面能访问**

启动服务器后访问 `http://localhost:5000`，确认页面正常显示。

- [ ] **Step 5: 提交**

```bash
git add web/
git commit -m "feat: add web frontend with real-time preview, capture, and history"
```

---

### Task 8: 集成测试和整体调试

- [ ] **Step 1: 确认 ESP32-CAM 已烧录固件并连接电脑**

检查串口是否识别到设备。

- [ ] **Step 2: 启动 Python 服务器**

```bash
cd server && python app.py
```

- [ ] **Step 3: 打开浏览器访问 http://localhost:5000**

- [ ] **Step 4: 在设置页面配置串口端口和百度云 API**

- [ ] **Step 5: 点击"连接设备"，确认状态变为"已连接"**

- [ ] **Step 6: 点击"拍照识别"，确认能看到图片和识别结果**

- [ ] **Step 7: 确认历史记录正常显示**

- [ ] **Step 8: 最终提交**

```bash
git add .
git commit -m "feat: complete license plate recognition system"
```
