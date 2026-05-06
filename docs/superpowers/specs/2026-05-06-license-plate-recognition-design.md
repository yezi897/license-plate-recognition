# 车牌识别系统设计文档

## 概述

基于 ESP32-CAM 的车牌识别系统，通过 USB 串口连接电脑，Python 服务器处理图片并调用百度云 OCR API 识别车牌，Web 界面展示实时预览、识别结果和历史记录。

## 架构

```
ESP32-CAM ──USB串口(FTDI)──▶ Python服务器(电脑)
                                │
                           ├─ 调百度云API识别车牌
                           ├─ Web界面(localhost)
                           └─ 历史记录(SQLite)
```

## 组件

### 1. ESP32-CAM 固件

- 开发板：`esp32:esp32:ai-thinker-esp32-cam`
- 库：`esp32-camera`
- 串口波特率：921600
- 功能：接收拍照指令，通过串口返回 JPEG 图片数据
- 编译烧录：`arduino-cli`

### 2. Python Flask 服务器

| 模块 | 功能 |
|------|------|
| `app.py` | Flask 主程序，提供 Web 页面和 REST API |
| `serial_comm.py` | 串口通信，发送拍照指令，接收 JPEG 数据 |
| `plate_recognizer.py` | 调用百度云车牌识别 API |
| `config.json` | 存储百度云 API Key/Secret Key 等配置 |

**API 接口：**

| 接口 | 方法 | 说明 |
|------|------|------|
| `/` | GET | Web 主页面 |
| `/api/capture` | POST | 拍照并识别车牌 |
| `/api/stream` | GET | 实时视频流（从串口读取） |
| `/api/history` | GET | 获取历史记录列表 |
| `/api/config` | POST | 保存百度云 API 配置 |

**依赖：**
- Flask
- pyserial
- baidu-aip
- Pillow
- sqlite3（内置）

### 3. Web 前端

纯 HTML + CSS + JavaScript，无框架。

**功能：**
- 实时视频预览（从串口持续读取画面）
- 手动拍照识别按钮
- 识别结果显示（车牌号、颜色、置信度）
- 历史记录表格（支持翻页）
- 设置页面（配置百度云 API Key/Secret Key）

**页面布局：**

```
┌────────────────────────────────────────────┐
│  车牌识别系统                    [⚙️ 设置]  │
├────────────────────────┬───────────────────┤
│                        │                   │
│   实时视频预览          │   识别结果         │
│                        │   车牌号: 京A12345 │
│                        │   颜色: 蓝色       │
│                        │   置信度: 98%      │
│                        │                   │
│  [📸 手动拍照识别]       │   [识别历史记录]   │
│                        │   ├─ 京A12345 14:30│
│                        │   ├─ 沪B67890 14:25│
│                        │   └─ ...          │
└────────────────────────┴───────────────────┘
```

## 项目目录结构

```
视觉/
├── firmware/              # ESP32-CAM 固件
│   ├── camera_capture.ino
│   └── platform.txt
├── server/                # Python 服务器
│   ├── app.py
│   ├── serial_comm.py
│   ├── plate_recognizer.py
│   ├── config.json
│   └── requirements.txt
├── web/                   # 前端页面
│   ├── index.html
│   ├── style.css
│   └── app.js
└── docs/                  # 文档
```

## 数据流

1. 浏览器请求实时预览 → Python 从串口读取 ESP32-CAM 画面 → 推送到浏览器
2. 用户点击拍照 → Python 发送拍照指令给 ESP32-CAM → 接收 JPEG → 调用百度云 API → 返回识别结果
3. 识别结果自动保存到 SQLite 数据库
4. 浏览器请求历史记录 → Python 从 SQLite 查询 → 返回 JSON

## 硬件连接

ESP32-CAM 通过 FTDI USB转TTL模块连接电脑：
- ESP32-CAM U0R → FTDI TX
- ESP32-CAM U0T → FTDI RX
- ESP32-CAM GND → FTDI GND
- ESP32-CAM 5V → FTDI 5V
