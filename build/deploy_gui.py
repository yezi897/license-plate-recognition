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
