# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Wallpaper Randomizer GUI (macOS).
This builds a standalone macOS .app bundle that includes all dependencies.
"""

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all customtkinter data files (themes, fonts, etc.)
customtkinter_datas = collect_data_files('customtkinter')

# Collect all hidden imports
hidden_imports = [
    'praw',
    'prawcore',
    'PIL',
    'PIL._tkinter_finder',
    'yaml',
    'requests',
    'customtkinter',
    'tkinter',
    'tkinter.ttk',
    '_cffi_backend',
]

# Add all customtkinter submodules
hidden_imports.extend(collect_submodules('customtkinter'))

a = Analysis(
    ['launch_gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config.yaml.template', '.'),  # Include config template
        *customtkinter_datas,  # Include customtkinter assets
    ],
    hiddenimports=hidden_imports,
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
    [],
    exclude_binaries=True,
    name='WallpaperRandomizer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window (GUI app)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='WallpaperRandomizer',
)

app = BUNDLE(
    coll,
    name='WallpaperRandomizer.app',
    icon=None,  # Add .icns file path here if you have one
    bundle_identifier='com.wallpaper-randomizer.app',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': 'True',
        'CFBundleName': 'Wallpaper Randomizer',
        'CFBundleDisplayName': 'Wallpaper Randomizer',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0',
        'NSHumanReadableCopyright': 'Copyright © 2025',
    },
)
