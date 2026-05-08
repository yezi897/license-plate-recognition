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
