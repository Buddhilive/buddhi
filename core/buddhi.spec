# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Collect all modules from the routers package
routers_hiddenimports = collect_submodules('routers')

# PLATFORM-SPECIFIC VARIABLE SETTINGS
if sys.platform.startswith('win'):
    # Windows
    final_name = 'buddhi-x86_64-pc-windows-msvc'
elif sys.platform.startswith('darwin'):
    # macOS
    final_name = 'buddhi-aarch64-apple-darwin'
else:
    # Linux (starts with 'linux')
    final_name = 'buddhi-x86_64-unknown-linux-gnu'

# Additional hidden imports
hiddenimports = [
    'routers',
    'routers.completions',
    'routers.embeddings',
    'sentence_transformers',
    'uvicorn',
    'numpy',
    'transformers',
    'torch',
    'fastapi',
    'pydantic',
    'typing',
    'uuid',
    'threading',
    'asyncio',
    'signal',
] + routers_hiddenimports

# Additional data files (static directory and entire routers directory)
datas = [
    ('static', 'static'),
    ('routers', 'routers'),  # Include the entire routers directory as a package
]

binaries = []

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name=final_name,
    distpath='src-tauri/bin/api',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)