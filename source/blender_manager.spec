# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build definition for Blender Manager.

Produces a single self-contained blender_manager.exe. Requires PyInstaller 6.x.
Build with:  python -m PyInstaller --noconfirm --clean blender_manager.spec
"""

import os

from PyInstaller.utils.hooks import collect_all

# SPECPATH is injected by PyInstaller and points at this file's folder.
SOURCE_DIR = SPECPATH

# A windowed build shows nothing at all when startup fails. Set BM_DEBUG_CONSOLE=1
# (see build_debug.bat) to get blender_manager_debug.exe, which keeps a console
# attached so tracebacks and print output are visible.
DEBUG_CONSOLE = os.environ.get('BM_DEBUG_CONSOLE') == '1'

datas = [
    (os.path.join(SOURCE_DIR, 'Assets'), 'Assets'),
    (os.path.join(SOURCE_DIR, 'tkdnd2.8'), 'tkdnd2.8'),
]
binaries = []
hiddenimports = []

# ttkbootstrap keeps its themes as importable modules and tkinterdnd2 ships the tkdnd
# Tcl package as data, so both need collecting whole rather than by import analysis.
for package in ('ttkbootstrap', 'tkinterdnd2'):
    package_datas, package_binaries, package_hiddenimports = collect_all(package)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hiddenimports

# Imported lazily inside functions, where static analysis alone is not enough.
hiddenimports += [
    'pystray._win32',
    'PIL._tkinter_finder',
    'win32com.client',
    'win32timezone',
    'winshell',
    'psutil',
    'bs4',
    'certifi',
    'aiohttp',
    'packaging.version',
    'webview.platforms.edgechromium',
    'webview.platforms.mshtml',
    'webview.platforms.winforms',
]

a = Analysis(
    ['blender_manager.py'],
    pathex=[SOURCE_DIR],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # macOS-only imports, guarded by platform checks at runtime.
        'AppKit',
        'Foundation',
        'objc',
        # Not used by the app; excluded so they never get pulled in transitively.
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'IPython',
        'pytest',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='blender_manager_debug' if DEBUG_CONSOLE else 'blender_manager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    # UPX corrupts some pywin32 and Tcl/Tk binaries, so it stays off.
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=DEBUG_CONSOLE,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(SOURCE_DIR, 'blendermanager.ico'),
)
