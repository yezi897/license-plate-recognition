# 一键部署工具实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建带 GUI 的单文件部署工具，将预编译固件、esptool、嵌入式 Python、pip wheels 打包，实现一键烧录 + 启动服务器。

**Architecture:** PySide6 GUI + QThread 工作线程，PyInstaller 单文件打包。烧录使用 esptool 直接写入预编译 .bin，服务器使用嵌入式 Python + 离线 wheels。

**Tech Stack:** PySide6, PyInstaller, esptool_py, Python embeddable, pip wheels, subprocess

---

## 文件结构

```
build/
├── deploy_gui.py          # PySide6 主界面
├── flash_worker.py        # 烧录工作线程 (QThread)
├── server_worker.py       # 服务器工作线程 (QThread)
├── prepare_resources.py   # 资源准备脚本
├── deploy.spec            # PyInstaller 打包配置
├── requirements_build.txt # 构建环境依赖
└── resources/             # 打包资源目录 (由 prepare_resources.py 生成)
    ├── esptool/
    │   └── esptool.exe
    ├── firmware.bin
    ├── python/
    │   └── python310.zip + python.exe
    ├── wheels/
    │   └── *.whl
    ├── server/
    │   └── *.py
    └── web/
        └── *.html, *.css, *.js
```

---

### Task 1: 创建构建目录结构和资源准备脚本

**Files:**
- Create: `build/prepare_resources.py`
- Create: `build/requirements_build.txt`

- [ ] **Step 1: 创建 build 目录**

```bash
mkdir -p build/resources
```

- [ ] **Step 2: 创建 requirements_build.txt**

```
PySide6>=6.6.0
pyinstaller>=6.0.0
pyserial>=3.5
```

- [ ] **Step 3: 创建 prepare_resources.py - esptool 提取部分**

创建 `build/prepare_resources.py`：

```python
"""资源准备脚本：收集所有打包依赖到 build/resources/ 目录"""
import shutil
import subprocess
import urllib.request
import zipfile
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
BUILD_DIR = Path(__file__).parent
RESOURCES_DIR = BUILD_DIR / "resources"

ARDUINO_CLI = PROJECT_ROOT / "arduino-cli.exe"
ARDUINO15 = Path(os.environ.get("LOCALAPPDATA", "")) / "Arduino15"


def clean_resources():
    """清理资源目录"""
    if RESOURCES_DIR.exists():
        shutil.rmtree(RESOURCES_DIR)
    RESOURCES_DIR.mkdir(parents=True)


def extract_esptool():
    """从 Arduino15 提取 esptool"""
    print("[1/5] 提取 esptool...")
    esptool_src = ARDUINO15 / "packages" / "esp32" / "tools" / "esptool_py"
    if not esptool_src.exists():
        print(f"错误: 找不到 esptool: {esptool_src}")
        sys.exit(1)

    # 找到最新版本
    versions = sorted(esptool_src.iterdir())
    if not versions:
        print("错误: esptool 目录为空")
        sys.exit(1)

    esptool_dir = versions[-1]
    esptool_exe = esptool_dir / "esptool.exe"
    if not esptool_exe.exists():
        # 尝试在子目录找
        for f in esptool_dir.rglob("esptool.exe"):
            esptool_exe = f
            break

    dest = RESOURCES_DIR / "esptool"
    dest.mkdir(parents=True)
    shutil.copy2(esptool_exe, dest / "esptool.exe")

    # 复制 esptool 依赖 (serial 等)
    for f in esptool_dir.glob("*.exe"):
        if f.name != "esptool.exe":
            shutil.copy2(f, dest / f.name)
    for f in esptool_dir.glob("*.py"):
        shutil.copy2(f, dest / f.name)

    print(f"  -> {dest}")


def compile_firmware():
    """使用 arduino-cli 编译固件"""
    print("[2/5] 编译固件...")
    firmware_dir = PROJECT_ROOT / "firmware" / "camera_capture"
    output_dir = BUILD_DIR / "firmware_build"

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    cmd = [
        str(ARDUINO_CLI),
        "compile",
        "--fqbn", "esp32:esp32:esp32s3",
        "--output-dir", str(output_dir),
        str(firmware_dir),
    ]
    print(f"  执行: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"编译失败:\n{result.stderr}")
        sys.exit(1)

    # 找到 .bin 文件
    bin_files = list(output_dir.glob("*.bin"))
    if not bin_files:
        print("错误: 编译未产出 .bin 文件")
        sys.exit(1)

    # 复制到 resources
    dest = RESOURCES_DIR / "firmware.bin"
    shutil.copy2(bin_files[0], dest)
    print(f"  -> {dest} ({dest.stat().st_size / 1024:.0f} KB)")


def download_python():
    """下载 Python embeddable 版本"""
    print("[3/5] 下载 Python embeddable...")
    url = "https://www.python.org/ftp/python/3.10.11/python-3.10.11-embed-amd64.zip"
    zip_path = BUILD_DIR / "python-embed.zip"
    dest = RESOURCES_DIR / "python"

    if not zip_path.exists():
        print(f"  下载: {url}")
        urllib.request.urlretrieve(url, zip_path)

    dest.mkdir(parents=True)
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(dest)

    # 修改 ._pth 文件以启用 site-packages
    pth_file = dest / "python310._pth"
    content = pth_file.read_text()
    content = content.replace("#import site", "import site")
    pth_file.write_text(content)

    print(f"  -> {dest}")
```

- [ ] **Step 4: 添加 download_wheels 和 copy_server_files 函数**

在 `prepare_resources.py` 末尾追加：

```python
def download_wheels():
    """下载 pip wheels 离线包"""
    print("[4/5] 下载 pip wheels...")
    wheels_dir = RESOURCES_DIR / "wheels"
    wheels_dir.mkdir(parents=True)

    req_file = PROJECT_ROOT / "server" / "requirements.txt"
    cmd = [
        sys.executable, "-m", "pip", "download",
        "--dest", str(wheels_dir),
        "--only-binary=:all:",
        "-r", str(req_file),
    ]
    print(f"  执行: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"下载失败:\n{result.stderr}")
        sys.exit(1)

    whl_count = len(list(wheels_dir.glob("*.whl")))
    print(f"  -> {wheels_dir} ({whl_count} 个包)")


def copy_server_files():
    """复制服务器和前端代码"""
    print("[5/5] 复制服务器和前端代码...")

    # 复制 server/
    server_src = PROJECT_ROOT / "server"
    server_dest = RESOURCES_DIR / "server"
    shutil.copytree(server_src, server_dest, ignore=shutil.ignore_patterns(
        "__pycache__", "*.pyc", "*.db", "images", "config.json"
    ))

    # 复制 web/
    web_src = PROJECT_ROOT / "web"
    web_dest = RESOURCES_DIR / "web"
    shutil.copytree(web_src, web_dest)

    # 复制默认 config.json
    config_src = PROJECT_ROOT / "server" / "config.json"
    if config_src.exists():
        shutil.copy2(config_src, server_dest / "config.json")

    print(f"  -> {server_dest}")
    print(f"  -> {web_dest}")


if __name__ == "__main__":
    print("=== 准备打包资源 ===\n")
    clean_resources()
    extract_esptool()
    compile_firmware()
    download_python()
    download_wheels()
    copy_server_files()
    print("\n=== 资源准备完成 ===")
    total = sum(f.stat().st_size for f in RESOURCES_DIR.rglob("*") if f.is_file())
    print(f"总大小: {total / 1024 / 1024:.1f} MB")
```

- [ ] **Step 5: 测试资源准备脚本**

```bash
cd build && python prepare_resources.py
```

Expected: 所有 5 个步骤成功完成，resources/ 目录包含所有资源。

- [ ] **Step 6: 提交**

```bash
git add build/prepare_resources.py build/requirements_build.txt
git commit -m "feat(deploy): add resource preparation script"
```

---

### Task 2: 创建烧录工作线程

**Files:**
- Create: `build/flash_worker.py`

- [ ] **Step 1: 创建 flash_worker.py**

```python
"""烧录工作线程：使用 esptool 烧录预编译固件"""
import subprocess
import sys
from pathlib import Path
from PySide6.QtCore import QThread, Signal


class FlashWorker(QThread):
    """esptool 烧录工作线程"""

    log = Signal(str)       # 日志输出信号
    progress = Signal(int)  # 进度信号 (0-100)
    finished = Signal(bool) # 完成信号 (True=成功)

    def __init__(self, port: str, firmware_path: str, esptool_path: str):
        super().__init__()
        self.port = port
        self.firmware_path = firmware_path
        self.esptool_path = esptool_path
        self._process = None

    def run(self):
        try:
            self.log.emit(f"开始烧录固件到 {self.port}...")
            self.log.emit(f"固件: {self.firmware_path}")
            self.log.emit(f"工具: {self.esptool_path}")
            self.progress.emit(10)

            cmd = [
                self.esptool_path,
                "--chip", "esp32s3",
                "--port", self.port,
                "--baud", "460800",
                "write_flash",
                "0x0",
                self.firmware_path,
            ]
            self.log.emit(f"命令: {' '.join(cmd)}")
            self.progress.emit(20)

            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            for line in self._process.stdout:
                line = line.rstrip()
                if line:
                    self.log.emit(line)
                    # 解析进度
                    if "Writing at" in line:
                        self.progress.emit(50)
                    elif "Hash of data verified" in line:
                        self.progress.emit(90)
                    elif "Wrote" in line:
                        self.progress.emit(95)

            self._process.wait()
            self.progress.emit(100)

            if self._process.returncode == 0:
                self.log.emit("烧录成功!")
                self.finished.emit(True)
            else:
                self.log.emit(f"烧录失败，返回码: {self._process.returncode}")
                self.finished.emit(False)

        except Exception as e:
            self.log.emit(f"烧录异常: {e}")
            self.finished.emit(False)

    def stop(self):
        """终止烧录进程"""
        if self._process and self._process.poll() is None:
            self._process.terminate()
```

- [ ] **Step 2: 提交**

```bash
git add build/flash_worker.py
git commit -m "feat(deploy): add flash worker thread"
```

---

### Task 3: 创建服务器工作线程

**Files:**
- Create: `build/server_worker.py`

- [ ] **Step 1: 创建 server_worker.py**

```python
"""服务器工作线程：管理 Python 环境和 Flask 服务器"""
import subprocess
import sys
import os
from pathlib import Path
from PySide6.QtCore import QThread, Signal


class ServerWorker(QThread):
    """Flask 服务器管理工作线程"""

    log = Signal(str)
    status = Signal(str)  # "installing" / "running" / "stopped" / "error"
    finished = Signal(bool)

    def __init__(self, python_dir: Path, wheels_dir: Path, server_dir: Path, web_dir: Path, work_dir: Path):
        super().__init__()
        self.python_dir = python_dir
        self.wheels_dir = wheels_dir
        self.server_dir = server_dir
        self.web_dir = web_dir
        self.work_dir = work_dir
        self._process = None
        self._stop_flag = False

    def run(self):
        try:
            self.log.emit("正在部署 Python 环境...")
            self.status.emit("installing")

            # 1. 设置 Python 路径
            python_exe = self.python_dir / "python.exe"
            if not python_exe.exists():
                self.log.emit(f"错误: 找不到 Python: {python_exe}")
                self.finished.emit(False)
                return

            # 2. 创建工作目录
            self.work_dir.mkdir(parents=True, exist_ok=True)

            # 3. 设置环境变量
            env = os.environ.copy()
            env["PYTHONPATH"] = str(self.server_dir)
            env["PYTHONHOME"] = str(self.python_dir)

            # 4. 安装 pip (如果需要)
            pip_check = subprocess.run(
                [str(python_exe), "-m", "pip", "--version"],
                capture_output=True, text=True, env=env,
            )
            if pip_check.returncode != 0:
                self.log.emit("安装 pip...")
                get_pip = self.work_dir / "get-pip.py"
                import urllib.request
                urllib.request.urlretrieve(
                    "https://bootstrap.pypa.io/get-pip.py", str(get_pip)
                )
                subprocess.run([str(python_exe), str(get_pip)], env=env)

            # 5. 离线安装依赖
            self.log.emit("安装依赖 (离线模式)...")
            req_file = self.server_dir / "requirements.txt"
            cmd = [
                str(python_exe), "-m", "pip", "install",
                "--no-index",
                f"--find-links={self.wheels_dir}",
                "-r", str(req_file),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, env=env)
            if result.returncode != 0:
                self.log.emit(f"依赖安装失败:\n{result.stderr}")
                self.finished.emit(False)
                return

            self.log.emit("依赖安装完成")

            # 6. 启动 Flask 服务器
            self.log.emit("启动服务器...")
            self.status.emit("running")

            app_py = self.server_dir / "app.py"
            self._process = subprocess.Popen(
                [str(python_exe), str(app_py)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=str(self.server_dir),
                env=env,
            )

            for line in self._process.stdout:
                if self._stop_flag:
                    break
                line = line.rstrip()
                if line:
                    self.log.emit(f"[服务器] {line}")

            self._process.wait()
            self.status.emit("stopped")
            self.finished.emit(True)

        except Exception as e:
            self.log.emit(f"服务器异常: {e}")
            self.status.emit("error")
            self.finished.emit(False)

    def stop(self):
        """停止服务器"""
        self._stop_flag = True
        if self._process and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
```

- [ ] **Step 2: 提交**

```bash
git add build/server_worker.py
git commit -m "feat(deploy): add server worker thread"
```

---

### Task 4: 创建 PySide6 主界面

**Files:**
- Create: `build/deploy_gui.py`

- [ ] **Step 1: 创建 deploy_gui.py - 导入和主窗口框架**

```python
"""ESP32-S3 车牌识别系统 - 一键部署工具"""
import sys
import os
import webbrowser
from pathlib import Path
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QLabel, QComboBox, QPushButton, QTextEdit,
    QProgressBar, QMessageBox,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor

from flash_worker import FlashWorker
from server_worker import ServerWorker


def get_resource_path():
    """获取资源路径（支持 PyInstaller 打包）"""
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS) / "resources"
    return Path(__file__).parent / "resources"


def get_work_dir():
    """获取工作目录（用户目录下）"""
    work_dir = Path.home() / ".plate_deploy"
    work_dir.mkdir(exist_ok=True)
    return work_dir


class DeployWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ESP32-S3 车牌识别系统 - 一键部署工具")
        self.setMinimumSize(600, 700)
        self.resize(650, 750)

        self.resources = get_resource_path()
        self.work_dir = get_work_dir()

        self.flash_worker = None
        self.server_worker = None

        self._init_ui()
        self._refresh_ports()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(12)

        # === 烧录区 ===
        flash_group = QGroupBox("步骤 1: 烧录固件")
        flash_layout = QVBoxLayout(flash_group)

        port_row = QHBoxLayout()
        port_row.addWidget(QLabel("串口:"))
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(120)
        port_row.addWidget(self.port_combo)
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.setFixedWidth(60)
        self.refresh_btn.clicked.connect(self._refresh_ports)
        port_row.addWidget(self.refresh_btn)
        port_row.addWidget(QLabel("  芯片: ESP32-S3"))
        port_row.addStretch()
        flash_layout.addLayout(port_row)

        flash_btn_row = QHBoxLayout()
        self.flash_btn = QPushButton("烧录固件")
        self.flash_btn.setFixedHeight(36)
        self.flash_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                padding: 0 24px;
            }
            QPushButton:hover { background-color: #1d4ed8; }
            QPushButton:disabled { background-color: #94a3b8; }
        """)
        self.flash_btn.clicked.connect(self._start_flash)
        flash_btn_row.addWidget(self.flash_btn)

        self.flash_progress = QProgressBar()
        self.flash_progress.setFixedHeight(20)
        flash_btn_row.addWidget(self.flash_progress)

        self.flash_status = QLabel("就绪")
        self.flash_status.setFixedWidth(80)
        flash_btn_row.addWidget(self.flash_status)
        flash_layout.addLayout(flash_btn_row)

        layout.addWidget(flash_group)

        # === 服务器区 ===
        server_group = QGroupBox("步骤 2: 启动服务器")
        server_layout = QVBoxLayout(server_group)

        status_row = QHBoxLayout()
        self.python_status = QLabel("Python: 检查中...")
        status_row.addWidget(self.python_status)
        status_row.addWidget(QLabel("  "))
        self.deps_status = QLabel("依赖: 检查中...")
        status_row.addWidget(self.deps_status)
        status_row.addStretch()
        server_layout.addLayout(status_row)

        server_btn_row = QHBoxLayout()
        self.server_btn = QPushButton("启动服务器")
        self.server_btn.setFixedHeight(36)
        self.server_btn.setStyleSheet("""
            QPushButton {
                background-color: #16a34a;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                padding: 0 24px;
            }
            QPushButton:hover { background-color: #15803d; }
            QPushButton:disabled { background-color: #94a3b8; }
        """)
        self.server_btn.clicked.connect(self._toggle_server)
        server_btn_row.addWidget(self.server_btn)

        self.server_indicator = QLabel("  停止  ")
        self.server_indicator.setStyleSheet(
            "background-color: #e5e7eb; border-radius: 4px; padding: 4px 8px;"
        )
        server_btn_row.addWidget(self.server_indicator)

        self.open_browser_btn = QPushButton("打开浏览器")
        self.open_browser_btn.setEnabled(False)
        self.open_browser_btn.clicked.connect(
            lambda: webbrowser.open("http://localhost:5000")
        )
        server_btn_row.addWidget(self.open_browser_btn)
        server_btn_row.addStretch()
        server_layout.addLayout(server_btn_row)

        layout.addWidget(server_group)

        # === 一键全流程 ===
        oneclick_group = QGroupBox("一键全流程")
        oneclick_layout = QVBoxLayout(oneclick_group)

        self.oneclick_btn = QPushButton("  一键部署: 烧录固件 + 启动服务器  ")
        self.oneclick_btn.setFixedHeight(44)
        self.oneclick_btn.setStyleSheet("""
            QPushButton {
                background-color: #7c3aed;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #6d28d9; }
            QPushButton:disabled { background-color: #94a3b8; }
        """)
        self.oneclick_btn.clicked.connect(self._start_oneclick)
        oneclick_layout.addWidget(self.oneclick_btn)

        layout.addWidget(oneclick_group)

        # === 日志区 ===
        log_group = QGroupBox("日志输出")
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setStyleSheet(
            "background-color: #1e293b; color: #e2e8f0; border-radius: 6px; padding: 8px;"
        )
        log_layout.addWidget(self.log_text)

        layout.addWidget(log_group, stretch=1)

        # 检查环境状态
        QTimer.singleShot(500, self._check_env_status)

    def _log(self, msg: str):
        """添加日志"""
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{ts}] {msg}")

    def _refresh_ports(self):
        """刷新串口列表"""
        import serial.tools.list_ports
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        for p in ports:
            self.port_combo.addItem(f"{p.device} - {p.description}", p.device)
        if not ports:
            self.port_combo.addItem("未检测到串口", "")

    def _check_env_status(self):
        """检查环境状态"""
        python_dir = self.resources / "python"
        wheels_dir = self.resources / "wheels"

        if (python_dir / "python.exe").exists():
            self.python_status.setText("Python: 已就绪")
            self.python_status.setStyleSheet("color: #16a34a;")
        else:
            self.python_status.setText("Python: 未找到")
            self.python_status.setStyleSheet("color: #dc2626;")

        if wheels_dir.exists() and list(wheels_dir.glob("*.whl")):
            count = len(list(wheels_dir.glob("*.whl")))
            self.deps_status.setText(f"依赖: {count} 个包")
            self.deps_status.setStyleSheet("color: #16a34a;")
        else:
            self.deps_status.setText("依赖: 未找到")
            self.deps_status.setStyleSheet("color: #dc2626;")

    def _start_flash(self):
        """开始烧录"""
        port = self.port_combo.currentData()
        if not port:
            QMessageBox.warning(self, "提示", "请先选择串口")
            return

        esptool = self.resources / "esptool" / "esptool.exe"
        firmware = self.resources / "firmware.bin"

        if not esptool.exists():
            QMessageBox.critical(self, "错误", f"找不到 esptool: {esptool}")
            return
        if not firmware.exists():
            QMessageBox.critical(self, "错误", f"找不到固件: {firmware}")
            return

        self.flash_btn.setEnabled(False)
        self.oneclick_btn.setEnabled(False)
        self.flash_progress.setValue(0)
        self.flash_status.setText("烧录中...")

        self.flash_worker = FlashWorker(
            port=port,
            firmware_path=str(firmware),
            esptool_path=str(esptool),
        )
        self.flash_worker.log.connect(self._log)
        self.flash_worker.progress.connect(self.flash_progress.setValue)
        self.flash_worker.finished.connect(self._on_flash_done)
        self.flash_worker.start()

    def _on_flash_done(self, success: bool):
        """烧录完成回调"""
        self.flash_btn.setEnabled(True)
        self.oneclick_btn.setEnabled(True)
        if success:
            self.flash_status.setText("成功")
            self.flash_status.setStyleSheet("color: #16a34a; font-weight: bold;")
        else:
            self.flash_status.setText("失败")
            self.flash_status.setStyleSheet("color: #dc2626; font-weight: bold;")

        # 如果是一键模式，继续启动服务器
        if hasattr(self, '_oneclick_mode') and self._oneclick_mode:
            self._oneclick_mode = False
            if success:
                QTimer.singleShot(1000, self._start_server)
            else:
                self.oneclick_btn.setEnabled(True)

    def _toggle_server(self):
        """切换服务器状态"""
        if self.server_worker and self.server_worker.isRunning():
            self._stop_server()
        else:
            self._start_server()

    def _start_server(self):
        """启动服务器"""
        self.server_btn.setEnabled(False)
        self.oneclick_btn.setEnabled(False)
        self.server_btn.setText("启动中...")
        self.server_indicator.setText("  启动中  ")
        self.server_indicator.setStyleSheet(
            "background-color: #fbbf24; border-radius: 4px; padding: 4px 8px;"
        )

        self.server_worker = ServerWorker(
            python_dir=self.resources / "python",
            wheels_dir=self.resources / "wheels",
            server_dir=self.work_dir / "server",
            web_dir=self.resources / "web",
            work_dir=self.work_dir,
        )

        # 复制 server 和 web 到工作目录
        import shutil
        server_src = self.resources / "server"
        server_dst = self.work_dir / "server"
        if server_dst.exists():
            shutil.rmtree(server_dst)
        shutil.copytree(server_src, server_dst)

        web_src = self.resources / "web"
        web_dst = self.work_dir / "web"
        if web_dst.exists():
            shutil.rmtree(web_dst)
        shutil.copytree(web_src, web_dst)

        self.server_worker.log.connect(self._log)
        self.server_worker.status.connect(self._on_server_status)
        self.server_worker.finished.connect(self._on_server_done)
        self.server_worker.start()

    def _stop_server(self):
        """停止服务器"""
        if self.server_worker:
            self.server_worker.stop()
            self._log("正在停止服务器...")

    def _on_server_status(self, status: str):
        """服务器状态变化"""
        if status == "running":
            self.server_btn.setText("停止服务器")
            self.server_btn.setStyleSheet("""
                QPushButton {
                    background-color: #dc2626;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-weight: bold;
                    padding: 0 24px;
                }
                QPushButton:hover { background-color: #b91c1c; }
            """)
            self.server_indicator.setText("  运行中  ")
            self.server_indicator.setStyleSheet(
                "background-color: #22c55e; border-radius: 4px; padding: 4px 8px; color: white;"
            )
            self.open_browser_btn.setEnabled(True)
            self.oneclick_btn.setEnabled(True)
        elif status == "stopped":
            self.server_btn.setText("启动服务器")
            self.server_btn.setStyleSheet("""
                QPushButton {
                    background-color: #16a34a;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-weight: bold;
                    padding: 0 24px;
                }
                QPushButton:hover { background-color: #15803d; }
            """)
            self.server_indicator.setText("  停止  ")
            self.server_indicator.setStyleSheet(
                "background-color: #e5e7eb; border-radius: 4px; padding: 4px 8px;"
            )
            self.open_browser_btn.setEnabled(False)
        self.server_btn.setEnabled(True)

    def _on_server_done(self, success: bool):
        """服务器完成回调"""
        if not success:
            self._log("服务器异常退出")
        self.oneclick_btn.setEnabled(True)

    def _start_oneclick(self):
        """一键全流程"""
        self._oneclick_mode = True
        self.oneclick_btn.setEnabled(False)
        self._log("=== 开始一键部署 ===")
        self._start_flash()

    def closeEvent(self, event):
        """关闭窗口时清理"""
        if self.server_worker and self.server_worker.isRunning():
            self.server_worker.stop()
            self.server_worker.wait(3000)
        if self.flash_worker and self.flash_worker.isRunning():
            self.flash_worker.stop()
            self.flash_worker.wait(3000)
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = DeployWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 测试 GUI 启动**

```bash
cd build && python deploy_gui.py
```

Expected: 窗口正常显示，串口列表可刷新。

- [ ] **Step 3: 提交**

```bash
git add build/deploy_gui.py
git commit -m "feat(deploy): add PySide6 main GUI"
```

---

### Task 5: 创建 PyInstaller 打包配置

**Files:**
- Create: `build/deploy.spec`

- [ ] **Step 1: 创建 deploy.spec**

```python
# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置 - 一键部署工具"""

import os
from pathlib import Path

block_cipher = None
build_dir = os.path.dirname(os.path.abspath(SPEC))

a = Analysis(
    [os.path.join(build_dir, 'deploy_gui.py')],
    pathex=[build_dir],
    binaries=[],
    datas=[
        (os.path.join(build_dir, 'resources', 'esptool'), 'resources/esptool'),
        (os.path.join(build_dir, 'resources', 'firmware.bin'), 'resources'),
        (os.path.join(build_dir, 'resources', 'python'), 'resources/python'),
        (os.path.join(build_dir, 'resources', 'wheels'), 'resources/wheels'),
        (os.path.join(build_dir, 'resources', 'server'), 'resources/server'),
        (os.path.join(build_dir, 'resources', 'web'), 'resources/web'),
    ],
    hiddenimports=['serial', 'serial.tools', 'serial.tools.list_ports'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'scipy', 'pandas'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='deploy',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 无控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可选: 添加图标
)
```

- [ ] **Step 2: 提交**

```bash
git add build/deploy.spec
git commit -m "feat(deploy): add PyInstaller spec"
```

---

### Task 6: 创建构建脚本

**Files:**
- Create: `build/build.py`

- [ ] **Step 1: 创建 build.py 一键构建脚本**

```python
"""一键构建 deploy.exe"""
import subprocess
import sys
import os
from pathlib import Path

BUILD_DIR = Path(__file__).parent


def main():
    print("=== 构建 deploy.exe ===\n")

    # 1. 准备资源
    print("[1/2] 准备资源...")
    result = subprocess.run(
        [sys.executable, str(BUILD_DIR / "prepare_resources.py")],
        cwd=str(BUILD_DIR),
    )
    if result.returncode != 0:
        print("资源准备失败!")
        sys.exit(1)

    # 2. PyInstaller 打包
    print("\n[2/2] PyInstaller 打包...")
    result = subprocess.run(
        [sys.executable, "-m", "PyInstaller",
         "--clean", "--noconfirm",
         str(BUILD_DIR / "deploy.spec")],
        cwd=str(BUILD_DIR),
    )
    if result.returncode != 0:
        print("打包失败!")
        sys.exit(1)

    exe_path = BUILD_DIR / "dist" / "deploy.exe"
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / 1024 / 1024
        print(f"\n=== 构建完成 ===")
        print(f"输出: {exe_path}")
        print(f"大小: {size_mb:.1f} MB")
    else:
        print("错误: 未找到 deploy.exe")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 提交**

```bash
git add build/build.py
git commit -m "feat(deploy): add one-click build script"
```

---

### Task 7: 集成测试

**Files:**
- Test: `build/dist/deploy.exe`

- [ ] **Step 1: 安装构建依赖**

```bash
pip install PySide6 pyinstaller pyserial
```

- [ ] **Step 2: 运行完整构建**

```bash
cd build && python build.py
```

Expected: 产出 `build/dist/deploy.exe`，大小 ~100-150MB。

- [ ] **Step 3: 测试 deploy.exe 基本功能**

```bash
./build/dist/deploy.exe
```

Expected:
- GUI 窗口正常显示
- 串口列表可刷新
- 日志区可正常输出

- [ ] **Step 4: 测试烧录功能（需要连接 ESP32-S3）**

在 deploy.exe 中：
1. 选择正确的 COM 口
2. 点击"烧录固件"
3. 观察日志输出和进度条

Expected: 烧录成功，进度条到 100%。

- [ ] **Step 5: 测试服务器启动**

在 deploy.exe 中：
1. 点击"启动服务器"
2. 等待状态变为"运行中"
3. 点击"打开浏览器"

Expected: 浏览器打开 http://localhost:5000，页面正常显示。

- [ ] **Step 6: 测试一键全流程**

1. 重启 deploy.exe
2. 选择串口
3. 点击"一键部署"
4. 观察完整流程

Expected: 烧录成功 → 服务器启动 → 浏览器自动打开。

- [ ] **Step 7: 最终提交**

```bash
git add -A
git commit -m "feat(deploy): complete one-click deployment tool"
```
