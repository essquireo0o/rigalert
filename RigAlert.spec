# -*- mode: python ; coding: utf-8 -*-
import os
_runtime_cache = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')),
                              'RigAlert', 'runtime')


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('rigalert.ico', '.'), ('rigalert_preview.png', '.')],
    hiddenimports=['PyQt6.QtSvg', 'PyQt6.QtPrintSupport'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    name='RigAlert',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['rigalert.ico'],
    upx_exclude=[],
    runtime_tmpdir=_runtime_cache,  # reuse extracted files → fast restart after first launch
)
