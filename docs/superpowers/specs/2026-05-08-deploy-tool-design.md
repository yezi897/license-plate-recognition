# 一键部署工具设计文档

## 概述

构建一个带 GUI 的单文件部署工具（deploy.exe），将预编译固件、esptool 烧录工具、嵌入式 Python、pip wheels、服务器代码全部打包，实现从一台无环境的 Windows 机器一键烧录固件 + 启动服务器。

## 技术选型

- **GUI 框架：** PySide6（Qt for Python）
- **打包工具：** PyInstaller（单文件模式）
- **目标平台：** Windows 10/11 x64
- **目标板卡：** ESP32-S3 Dev Module（FQBN: `esp32:esp32:esp32s3`）

## 架构设计

### 整体结构

```
deploy.exe (单文件，~100-150MB)
├── PySide6 GUI 主界面
├── esptool.exe (~59MB，烧录工具)
├── firmware.bin (预编译固件 ~1MB)
├── python-3.10-embeddable/ (~15MB)
├── pip wheels (flask, pyserial 等 ~20MB)
├── server/ + web/ (服务器代码)
└── config.json (默认配置)
```

### 模块划分

```
build/
├── deploy_gui.py          # PySide6 主界面
├── flash_worker.py        # 烧录工作线程 (QThread)
├── server_worker.py       # 服务器工作线程 (QThread)
├── resources/             # 打包资源目录
│   ├── esptool/           # esptool 烧录工具
│   ├── firmware.bin       # 预编译固件
│   ├── python/            # 嵌入式 Python
│   ├── wheels/            # pip 离线包
│   ├── server/            # 服务器代码
│   └── web/               # 前端代码
└── deploy.spec            # PyInstaller 打包配置
```

## GUI 界面设计

### 窗口布局

```
┌──────────────────────────────────────────┐
│  ESP32-S3 车牌识别系统 - 一键部署工具     │
├──────────────────────────────────────────┤
│                                          │
│  [步骤1: 烧录固件]                        │
│  ┌────────────────────────────────────┐  │
│  │ 串口: [COM4 ▼]  芯片: ESP32-S3    │  │
│  │ [烧录固件]    进度: ████████░░ 80% │  │
│  │ 状态: 正在烧录...                   │  │
│  └────────────────────────────────────┘  │
│                                          │
│  [步骤2: 启动服务器]                      │
│  ┌────────────────────────────────────┐  │
│  │ Python环境: ✅ 已就绪               │  │
│  │ 依赖安装:   ✅ 已完成               │  │
│  │ [启动服务器]  状态: 运行中 ●        │  │
│  │ 服务器地址: http://localhost:5000   │  │
│  └────────────────────────────────────┘  │
│                                          │
│  [一键全流程]                             │
│  ┌────────────────────────────────────┐  │
│  │  [一键部署: 烧录固件 + 启动服务器]   │  │
│  └────────────────────────────────────┘  │
│                                          │
│  日志输出:                               │
│  ┌────────────────────────────────────┐  │
│  │ [12:00:01] 开始烧录固件...          │  │
│  │ [12:00:15] 正在写入 flash...        │  │
│  │ [12:00:25] 烧录成功!               │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
```

### 界面组件

1. **串口选择区**
   - COM 口下拉列表（自动检测可用串口，带刷新按钮）
   - 波特率显示（固定 115200）

2. **烧录区**
   - "烧录固件" 按钮
   - 进度条
   - 状态文字（空闲/烧录中/成功/失败）

3. **服务器区**
   - 环境状态指示（Python/依赖是否就绪）
   - "启动服务器" / "停止服务器" 按钮（切换）
   - 服务器运行状态指示灯
   - 服务器地址显示

4. **一键全流程区**
   - 单个按钮，依次执行烧录 + 启动服务器

5. **日志区**
   - 滚动文本框，显示所有操作日志
   - 带时间戳

## 核心流程

### 烧录流程

1. 解压内嵌的 esptool 和预编译 firmware.bin 到临时目录
2. 执行 `esptool.exe --chip esp32s3 --port COMx --baud 460800 write_flash 0x0 firmware.bin`
3. 通过 QThread + subprocess 实时捕获 stdout/stderr，发送信号更新 GUI
4. 烧录完成，清理临时文件

### 服务器部署流程

1. 首次运行时，将嵌入式 Python 解压到 `~/.deploy_tools/python/`
2. 创建 venv：`python -m venv <work_dir>/.venv`
3. 离线安装依赖：`pip install --no-index --find-links=wheels/ -r requirements.txt`
4. 启动 Flask 服务器：`python server/app.py`
5. 通过 QThread + subprocess 管理服务器进程
6. 退出工具时自动终止服务器进程

### 一键全流程

1. 串口检测 → 选择第一个可用串口
2. 烧录预编译固件
3. 部署 Python 环境 → 安装依赖 → 启动服务器
4. 自动打开浏览器 `http://localhost:5000`

## 资源打包

### 需要打包的文件

| 资源 | 来源 | 大小 |
|------|------|------|
| esptool.exe | 从 Arduino15 提取 | ~59MB |
| firmware.bin | arduino-cli 编译产出 | ~1MB |
| python-3.10-embeddable | 下载 | ~15MB |
| pip wheels | pip download | ~20MB |
| server/ | 项目服务器目录 | ~50KB |
| web/ | 项目前端目录 | ~20KB |
| **合计** | | **~100-150MB** |

### PyInstaller 配置

```python
# deploy.spec
a = Analysis(
    ['deploy_gui.py'],
    datas=[
        ('resources/esptool', 'resources/esptool'),
        ('resources/firmware.bin', 'resources'),
        ('resources/python', 'resources/python'),
        ('resources/wheels', 'resources/wheels'),
        ('resources/server', 'resources/server'),
        ('resources/web', 'resources/web'),
    ],
    ...
)
```

### 资源准备脚本

创建 `prepare_resources.py` 脚本，自动收集所有依赖：

1. 使用 arduino-cli 编译固件，产出 firmware.bin
2. 从 Arduino15 提取 esptool 工具
3. 下载 Python embeddable 版本
4. 使用 `pip download` 下载所有 wheels
5. 复制 server/、web/ 目录

## 错误处理

- **串口不可用：** 提示用户检查连接
- **烧录失败：** 提示检查板卡连接、串口、USB 驱动
- **服务器启动失败：** 显示错误信息，检查端口占用
- **资源解压失败：** 提示磁盘空间不足

## 关键技术点

- **子线程执行：** 烧录和服务器启动在 QThread 中执行，通过信号更新 GUI
- **实时日志：** subprocess 的 stdout/stderr 实时发送到 GUI 日志区
- **串口自动检测：** 使用 pyserial 的 `list_ports` 列出可用 COM 口
- **进程管理：** 服务器进程可启动/停止，退出时自动清理临时文件
- **首次解压缓存：** 解压到用户目录，后续运行直接使用缓存
