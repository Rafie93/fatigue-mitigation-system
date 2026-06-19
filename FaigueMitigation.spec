# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the Fatigue Mitigation System (Windows, --onedir).

models/, assets/, config/ and storage/ are shipped *next to* the executable by
the CI workflow (not embedded) so the AI model can be updated without rebuild.
This spec focuses on collecting the Python runtime + heavy libraries."""
from PyInstaller.utils.hooks import collect_all, collect_submodules

APP_NAME = "FaigueMitigation"

datas = []
binaries = []
hiddenimports = []


def _add(pkg: str) -> None:
    global datas, binaries, hiddenimports
    try:
        d, b, h = collect_all(pkg)
        datas += d
        binaries += b
        hiddenimports += h
        print(f"[spec] collected {pkg}: {len(d)} data, {len(b)} bin, {len(h)} hidden")
    except Exception as exc:  # pragma: no cover
        print(f"[spec] skip {pkg}: {exc}")


for _pkg in ("tensorflow", "keras", "cv2", "h5py", "google.protobuf", "psutil"):
    _add(_pkg)

hiddenimports += collect_submodules("tensorflow")

a = Analysis(
    ["app.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["PyQt5", "PyQt6", "tkinter", "matplotlib", "notebook", "IPython"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    icon="assets/icon.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name=APP_NAME,
)
