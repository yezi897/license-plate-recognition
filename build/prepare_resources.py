"""
资源准备脚本 - 为 PyInstaller 打包收集所有依赖项。

收集内容：
- esptool (从 Arduino15 packages 目录提取)
- 固件二进制文件 (arduino-cli 编译)
- Python 3.10.11 embeddable
- pip 离线 wheels
- server/ 和 web/ 源码
"""

import os
import shutil
import subprocess
import urllib.request
import zipfile
from pathlib import Path

# 路径常量
PROJECT_ROOT = Path(__file__).parent.parent
BUILD_DIR = Path(__file__).parent
RESOURCES_DIR = BUILD_DIR / "resources"
ARDUINO_CLI = PROJECT_ROOT / "arduino-cli.exe"
ARDUINO15 = Path(os.environ.get("LOCALAPPDATA", "")) / "Arduino15"

# 目录
FIRMWARE_DIR = PROJECT_ROOT / "firmware" / "camera_capture"
SERVER_DIR = PROJECT_ROOT / "server"
WEB_DIR = PROJECT_ROOT / "web"
REQUIREMENTS_FILE = SERVER_DIR / "requirements.txt"

# 固件编译
BOARD_FQBN = "esp32:esp32:esp32s3"

# Python embeddable (仅 amd64)
PYTHON_VERSION = "3.10.11"
PYTHON_URL = f"https://www.python.org/ftp/python/{PYTHON_VERSION}/python-{PYTHON_VERSION}-embed-amd64.zip"


def clean_resources():
    """清理并重建 build/resources/ 目录。"""
    print("[1/6] 清理资源目录...")
    if RESOURCES_DIR.exists():
        shutil.rmtree(RESOURCES_DIR)
    RESOURCES_DIR.mkdir(parents=True)
    print("  完成: build/resources/ 已重建")


def extract_esptool():
    """从 Arduino15 packages 目录提取 esptool。"""
    print("[2/6] 提取 esptool...")
    esptool_dir = ARDUINO15 / "packages" / "esp32" / "tools" / "esptool_py"

    if not esptool_dir.exists():
        raise FileNotFoundError(f"esptool 目录不存在: {esptool_dir}")

    # 按语义版本号排序查找最新版本
    def version_key(p):
        try:
            return [int(x) for x in p.name.split('.')]
        except (ValueError, AttributeError):
            return [0]

    versions = sorted(esptool_dir.iterdir(), key=version_key)
    if not versions:
        raise FileNotFoundError(f"在 {esptool_dir} 中未找到 esptool 版本")

    latest_version = versions[-1]
    print(f"  使用 esptool 版本: {latest_version.name}")

    dest = RESOURCES_DIR / "esptool"
    dest.mkdir(exist_ok=True)

    # 复制 .exe 和 .py 文件
    copied = 0
    for f in latest_version.iterdir():
        if f.suffix in (".exe", ".py"):
            shutil.copy2(f, dest)
            copied += 1

    print(f"  完成: 已复制 {copied} 个文件到 {dest}")


def compile_firmware():
    """使用 arduino-cli 编译固件，复制 .bin 到 resources。"""
    print("[3/6] 编译固件...")

    if not ARDUINO_CLI.exists():
        raise FileNotFoundError(f"arduino-cli 不存在: {ARDUINO_CLI}")

    if not FIRMWARE_DIR.exists():
        raise FileNotFoundError(f"固件目录不存在: {FIRMWARE_DIR}")

    output_dir = BUILD_DIR / "firmware_output"
    output_dir.mkdir(exist_ok=True)

    cmd = [
        str(ARDUINO_CLI),
        "compile",
        "--fqbn", BOARD_FQBN,
        "--output-dir", str(output_dir),
        str(FIRMWARE_DIR),
    ]

    print(f"  执行: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

    if result.returncode != 0:
        print(f"  编译输出:\n{result.stdout}")
        print(f"  编译错误:\n{result.stderr}")
        raise RuntimeError("固件编译失败")

    # 查找 .bin 文件
    bin_files = list(output_dir.glob("*.bin"))
    if not bin_files:
        raise FileNotFoundError(f"在 {output_dir} 中未找到 .bin 文件")

    bin_file = bin_files[0]
    dest = RESOURCES_DIR / "firmware.bin"
    shutil.copy2(bin_file, dest)
    print(f"  完成: {bin_file.name} -> {dest}")

    # 清理编译输出
    shutil.rmtree(output_dir)


def download_python():
    """下载 Python 3.10.11 embeddable 并启用 site-packages。"""
    print("[4/6] 下载 Python embeddable...")

    python_dir = RESOURCES_DIR / "python"
    python_dir.mkdir(exist_ok=True)

    zip_path = BUILD_DIR / "python-embed.zip"

    # 下载 (30秒超时)
    print(f"  下载: {PYTHON_URL}")
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    urllib.request.install_opener(opener)
    urllib.request.urlretrieve(PYTHON_URL, zip_path)

    # 解压
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(python_dir)

    zip_path.unlink()

    # 修改 ._pth 文件以启用 site-packages
    pth_files = list(python_dir.glob("*._pth"))
    for pth_file in pth_files:
        content = pth_file.read_text(encoding="utf-8")
        # 取消注释 "import site"
        content = content.replace("#import site", "import site")
        pth_file.write_text(content, encoding="utf-8")
        print(f"  已启用 site-packages: {pth_file.name}")

    # 使用 ensurepip 引导安装 pip
    python_exe = python_dir / "python.exe"
    print("  安装 pip...")
    subprocess.run(
        [str(python_exe), "-m", "ensurepip", "--upgrade"],
        capture_output=True, text=True,
    )

    # 验证 pip 安装
    result = subprocess.run(
        [str(python_exe), "-m", "pip", "--version"],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print(f"  pip 已安装: {result.stdout.strip()}")
    else:
        print("  警告: pip 安装失败，服务器启动时可能无法安装依赖")

    print(f"  完成: Python {PYTHON_VERSION} 已解压到 {python_dir}")


def download_wheels():
    """使用 pip download 获取离线 wheels 并安装到嵌入式 Python。"""
    print("[5/6] 下载并安装 pip wheels...")

    if not REQUIREMENTS_FILE.exists():
        raise FileNotFoundError(f"requirements.txt 不存在: {REQUIREMENTS_FILE}")

    wheels_dir = RESOURCES_DIR / "wheels"
    wheels_dir.mkdir(exist_ok=True)

    # 1. 下载 wheels
    cmd = [
        sys.executable,
        "-m", "pip",
        "download",
        "--dest", str(wheels_dir),
        "--prefer-binary",
        "-r", str(REQUIREMENTS_FILE),
    ]

    print(f"  下载: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

    if result.returncode != 0:
        print(f"  pip 输出:\n{result.stdout}")
        print(f"  pip 错误:\n{result.stderr}")
        raise RuntimeError("pip download 失败")

    wheel_count = len(list(wheels_dir.glob("*.whl")))
    print(f"  已下载 {wheel_count} 个 wheel")

    # 2. 安装 wheels 到嵌入式 Python
    python_exe = RESOURCES_DIR / "python" / "python.exe"
    if python_exe.exists():
        cmd = [
            str(python_exe),
            "-m", "pip", "install",
            "--no-index",
            f"--find-links={wheels_dir}",
            "-r", str(REQUIREMENTS_FILE),
        ]
        print(f"  安装到嵌入式 Python: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            print(f"  安装警告:\n{result.stderr}")
        else:
            print("  依赖已安装到嵌入式 Python")

    print(f"  完成: {wheel_count} 个 wheel 已处理")


def copy_server_files():
    """复制 server/ 和 web/ 到 resources。"""
    print("[6/6] 复制 server 和 web 文件...")

    # 复制 server/，忽略不需要的文件
    server_dest = RESOURCES_DIR / "server"
    shutil.copytree(
        SERVER_DIR,
        server_dest,
        ignore=shutil.ignore_patterns(
            "__pycache__",
            "*.pyc",
            "*.db",
            "images",
            "config.json",
            "test_*.py",
        ),
    )
    print(f"  已复制: server/ -> {server_dest}")

    # 复制 web/
    web_dest = RESOURCES_DIR / "web"
    shutil.copytree(WEB_DIR, web_dest)
    print(f"  已复制: web/ -> {web_dest}")

    # 单独复制 config.json
    config_src = SERVER_DIR / "config.json"
    if config_src.exists():
        shutil.copy2(config_src, RESOURCES_DIR / "server" / "config.json")
        print(f"  已复制: config.json")


def get_dir_size(path: Path) -> int:
    """递归计算目录大小。"""
    total = 0
    for f in path.rglob("*"):
        if f.is_file():
            total += f.stat().st_size
    return total


def main():
    """按顺序运行所有步骤，最后打印总大小。"""
    print("=" * 50)
    print("资源准备脚本 - 开始")
    print("=" * 50)
    print()

    clean_resources()
    extract_esptool()
    compile_firmware()
    download_python()
    download_wheels()
    copy_server_files()

    # 计算并打印总大小
    total_size = get_dir_size(RESOURCES_DIR)
    size_mb = total_size / (1024 * 1024)

    print()
    print("=" * 50)
    print(f"完成! 资源总大小: {size_mb:.1f} MB")
    print(f"资源目录: {RESOURCES_DIR}")
    print("=" * 50)


if __name__ == "__main__":
    main()
