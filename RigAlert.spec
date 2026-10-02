# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Bundle IANA timezone database so ZoneInfo works on any Windows machine
_tzdata_datas = collect_data_files('tzdata')
_tzdata_hidden = collect_submodules('tzdata')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('rigalert.ico', '.'), ('rigalert_preview.png', '.')] + _tzdata_datas,
    hiddenimports=['PyQt6.QtSvg', 'PyQt6.QtPrintSupport', 'zoneinfo', '_zoneinfo'] + _tzdata_hidden,
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
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['rigalert.ico'],
    upx_exclude=[],
    # None = unpack under the RUNNING user's %TEMP%. A path computed here is evaluated on the
    # build machine and baked in, so it pointed every other PC at the builder's profile.
    runtime_tmpdir=None,
)
