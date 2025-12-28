# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['competitor_interface.py'],
    pathex=[],
    binaries=[('C:\\Users\\VOIS\\AppData\\Local\\Python\\pythoncore-3.14-64\\python314.dll', '.')],
    datas=[('problems', 'problems'), ('firebase_credentials.json', '.')],
    hiddenimports=['firebase_admin', 'firebase_admin.credentials', 'firebase_admin.firestore', 'firebase_admin.db', 'firebase_admin._sseclient', 'firebase_admin._http_client', 'google.cloud', 'google.cloud.firestore', 'google.cloud.firestore_v1', 'google.auth', 'google.auth.transport', 'grpc', 'google.api_core'],
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
    name='CompetitorInterface',
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
    icon='NONE',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='CompetitorInterface',
)
