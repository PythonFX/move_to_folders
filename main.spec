# -*- mode: python ; coding: utf-8 -*-

import sys

# Define platform-specific data tuples
if sys.platform.startswith('win'):
    tkdnd_path = 'C:/Projects/PyCharm/move_to_folders/.venv/Lib/site-packages/tkdnd/tkdnd/win64/'
    datas = [(tkdnd_path, 'tkdnd')]
elif sys.platform.startswith('darwin'):
    tkdnd_path = 'C:/Projects/PyCharm/move_to_folders/.venv/Lib/site-packages/tkdnd/tkdnd/osx64/'
    datas = [(tkdnd_path, 'tkdnd')]
elif sys.platform.startswith('linux'):
    tkdnd_path = 'C:/Projects/PyCharm/move_to_folders/.venv/Lib/site-packages/tkdnd/tkdnd/linux64/'
    datas = [(tkdnd_path, 'tkdnd')]
else:
    datas = []

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
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
