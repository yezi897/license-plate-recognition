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
