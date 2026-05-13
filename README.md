# 车牌识别系统 (License Plate Recognition System)

基于 ESP32-S3 和百度云 OCR 的智能车牌识别系统，支持实时视频流、自动识别、历史记录等功能。

## 系统架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Browser Frontend                             │
│                    (HTML / CSS / JavaScript)                        │
│                                                                     │
│  ┌──────────┐ ┌──────────────┐ ┌──────────┐ ┌──────────────────┐   │
│  │ 实时预览 │ │ 手动/自动识别 │ │ 历史记录 │ │  设备配置管理    │   │
│  └──────────┘ └──────────────┘ └──────────┘ └──────────────────┘   │
└────────────────────────────┬────────────────────────────────────────┘
                             │ HTTP REST API
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Flask Server (Python)                           │
│                        server/app.py                                │
│                                                                     │
│  ┌──────────────┐  ┌──────────────────┐  ┌──────────────────────┐   │
│  │  视频流服务   │  │  拍照识别服务     │  │  设备连接管理        │   │
│  │  /api/stream  │  │  /api/capture    │  │  /api/connect        │   │
│  └──────┬───────┘  └────────┬─────────┘  └──────────┬───────────┘   │
│         │                   │                       │               │
│  ┌──────┴───────────────────┴───────────────────────┴───────────┐   │
│  │              Communication Layer                             │   │
│  │  ┌────────────────┐          ┌────────────────────┐          │   │
│  │  │  SerialComm    │          │  TcpComm           │          │   │
│  │  │  (USB Serial)  │          │  (WiFi TCP:8080)   │          │   │
│  │  └────────────────┘          └────────────────────┘          │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌──────────────────────┐        ┌─────────────────────────────┐    │
│  │  PlateRecognizer     │        │  Database (SQLite)          │    │
│  │  (百度云 OCR API)    │        │  records.db                 │    │
│  └──────────────────────┘        └─────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
         │
         │ Binary Protocol
         │ (IMG_START + len + JPEG + IMG_END)
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   ESP32-S3 Camera Module                            │
│                    firmware/                                        │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐   │
│  │  OV2640 摄像头│  │  串口/TCP 通信│  │  闪光灯控制             │   │
│  │  (JPEG 捕获)  │  │  (921600 baud│  │  (GPIO)                 │   │
│  │              │  │   / port 8080)│  │                         │   │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

## 数据流

```
用户点击"拍照识别"
       │
       ▼
浏览器 ──POST /api/capture──▶ Flask Server
                                    │
                              发送命令 'C'
                                    │
                                    ▼
                            ESP32-S3 捕获 JPEG
                                    │
                            IMG_START + len + JPEG
                                    │
                                    ▼
                            Server 接收 & 校验
                                    │
                            调用百度云 OCR API
                                    │
                                    ▼
                            返回车牌号/颜色/置信度
                                    │
                            保存到 SQLite DB
                                    │
                                    ▼
浏览器 ◀──JSON 响应──◀──── 返回识别结果
```

## 技术栈

| 层级 | 技术 |
|------|------|
| 硬件 | ESP32-S3 + OV2640 摄像头 |
| 固件 | Arduino (C++), esp_camera |
| 后端 | Python 3.10+, Flask |
| OCR | 百度云 AIP SDK (车牌识别) |
| 数据库 | SQLite |
| 前端 | HTML5 / CSS3 / JavaScript |
| 部署 | PySide6 GUI + PyInstaller |

## 项目结构

```
├── firmware/                   # ESP32-S3 固件
│   ├── camera_capture/         # USB 串口模式固件
│   └── camera_capture_wifi/    # WiFi/TCP 模式固件
├── server/                     # Python 后端
│   ├── app.py                  # Flask 主程序 & REST API
│   ├── serial_comm.py          # USB 串口通信
│   ├── tcp_comm.py             # WiFi/TCP 通信
│   ├── plate_recognizer.py     # 百度云车牌识别
│   ├── database.py             # SQLite 数据存储
│   ├── config.json             # 运行时配置
│   └── requirements.txt        # Python 依赖
├── web/                        # 前端页面
│   ├── index.html              # 单页应用
│   ├── style.css               # 样式
│   └── app.js                  # 客户端逻辑
├── build/                      # 部署工具
│   ├── deploy_gui.py           # PySide6 部署 GUI
│   ├── flash_worker.py         # 固件烧录线程
│   ├── server_worker.py        # 服务器管理线程
│   ├── prepare_resources.py    # 资源打包脚本
│   ├── deploy.spec             # PyInstaller 配置
│   └── build.py                # 一键构建脚本
└── docs/                       # 设计文档
```

## 快速开始

### 1. 环境准备

- Python 3.10+
- Arduino CLI（用于编译固件）
- ESP32-S3 开发板 + OV2640 摄像头

### 2. 烧录固件

```bash
# 使用 arduino-cli 编译并烧录
arduino-cli compile --fqbn esp32:esp32:esp32s3:PSRAM=opi firmware/camera_capture/
arduino-cli upload --fqbn esp32:esp32:esp32s3:PSRAM=opi -p COM4 firmware/camera_capture/
```

### 3. 启动服务器

```bash
cd server
pip install -r requirements.txt
python app.py
```

### 4. 访问前端

浏览器打开 `http://localhost:5000`

### 5. 配置百度云 OCR

在前端设置页面填入百度云 API 的 `app_id`、`api_key`、`secret_key`。

## 一键部署

项目提供了图形化部署工具，可打包为单个 `deploy.exe`：

```bash
cd build
pip install -r requirements_build.txt
python build.py
```

生成的 `deploy.exe` 包含固件、Python 运行时、所有依赖，可在裸机 Windows 上一键运行。

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/connect` | 连接设备 |
| POST | `/api/disconnect` | 断开连接 |
| GET | `/api/status` | 获取连接状态 |
| POST | `/api/capture` | 拍照并识别 |
| GET | `/api/stream/frame` | 获取单帧（视频流） |
| GET | `/api/stream/recognize` | 自动识别（定时调用） |
| GET | `/api/history` | 查询历史记录 |
| POST | `/api/history/clear` | 清空历史 |
| GET | `/api/config` | 读取配置 |
| POST | `/api/config` | 更新配置 |

## License

MIT
