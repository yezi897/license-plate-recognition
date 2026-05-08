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
