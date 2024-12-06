# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['compareText.py'],
    pathex=[],
    binaries=[],
    datas=[('.\\Lang\\en.txt', '.\\Lang\\.'), ('.\\Lang\\it.txt', '.\\Lang\\.'), ('.\\Inc\\satispay-logo.png', '.\\Inc\\.'), ('.\\Inc\\paypal-logo.png', '.\\Inc\\.'), ('..\\Lib/site-packages/tkinterdnd2', 'tkinterdnd2/')],
    hiddenimports=[],
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
    [],
    exclude_binaries=True,
    name='compareText',
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
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='compareText',
)
