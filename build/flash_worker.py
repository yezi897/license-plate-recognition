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
