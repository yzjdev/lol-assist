# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],   # 文件路径 当前文件
    binaries=[],
    datas=[],   # 图片资源  ('1.png','.')
    hiddenimports=['config','entries', 'lcu','utils'], # 剩余模块
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['lcu-driver','willump'],   # 用不到的模块
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
