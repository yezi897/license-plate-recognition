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

            # 3.1 创建启动包装脚本，确保 sys.path 包含服务器目录
            wrapper_py = self.work_dir / "_start_server.py"
            wrapper_py.write_text(
                f'import sys\n'
                f'sys.path.insert(0, r"{self.server_dir}")\n'
                f'import os\n'
                f'os.chdir(r"{self.server_dir}")\n'
                f'exec(open(r"{self.server_dir / "app.py"}").read())\n',
                encoding="utf-8",
            )

            # 4. 验证依赖是否可用
            self.log.emit("验证依赖...")
            check = subprocess.run(
                [str(python_exe), "-c", "import flask; import serial; import PIL; print('依赖检查通过')"],
                capture_output=True, text=True, env=env,
            )
            if check.returncode != 0:
                self.log.emit(f"依赖检查失败: {check.stderr}")
                # 尝试离线安装
                self.log.emit("尝试离线安装依赖...")
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
            else:
                self.log.emit(check.stdout.strip())

            # 5. 启动 Flask 服务器
            self.log.emit("启动服务器...")
            self.status.emit("running")

            self._process = subprocess.Popen(
                [str(python_exe), str(wrapper_py)],
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
