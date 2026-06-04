# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for signal-light-tray single-file EXE."""

from pathlib import Path

_PROJECT = Path(SPECPATH)

_icons = list((_PROJECT / "signal_light_tray" / "icons").glob("*.png"))
_sounds = list((_PROJECT / "sounds").glob("*.wav"))

a = Analysis(
    [_PROJECT / "signal_light_tray" / "__main__.py"],
    pathex=[],
    binaries=[],
    datas=[
        *[(str(p), "signal_light_tray/icons") for p in _icons],
        *[(str(p), "sounds") for p in _sounds],
    ],
    hiddenimports=["PIL._tkinter_finder"],
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "numpy", "pandas"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="signal-light-tray",
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
    icon=str(_PROJECT / "signal-light-tray.ico"),
)
