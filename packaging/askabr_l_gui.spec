# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec для автономной сборки АСКАБР-Л (Windows, CPU)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

block_cipher = None
ROOT = Path(SPECPATH).resolve().parent.parent

_preflight_path = ROOT / "packaging" / "preflight.py"
_spec = importlib.util.spec_from_file_location("packaging_preflight", _preflight_path)
_preflight = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_preflight)
_preflight.assert_release_models(ROOT)

_binaries: list = []
_datas = [
    (str(ROOT / "models" / "tomato"), "models/tomato"),
    (str(ROOT / "models" / "pear"), "models/pear"),
    (str(ROOT / "docs" / "INSTRUKCIYA.txt"), "docs"),
    (str(ROOT / "gui" / "class_labels_ru.json"), "gui"),
    (str(ROOT / "gui" / "plant_variants.json"), "gui"),
]
_hiddenimports = [
    "torch",
    "torchvision",
    "torchvision.models",
    "torchvision.models.resnet",
    "torchvision.models.efficientnet",
    "torchvision.models.mobilenet",
    "yaml",
    "PIL",
    "PIL.Image",
    "numpy",
    "certifi",
    "PyQt6",
    "PyQt6.QtCore",
    "PyQt6.QtGui",
    "PyQt6.QtWidgets",
    "PyQt6.sip",
    "askabr",
    "askabr.classification.augment",
    "askabr.classification.model",
    "askabr.classification.predict",
    "askabr.assessment.phytosanitary_index",
    "askabr.core.paths",
    "askabr.core.ssl",
    "askabr.core.terminology",
    "askabr.core.version",
    "gui.main_window",
    "gui.variants",
    "gui.about_dialog",
    "gui.help_dialog",
    "gui.report_export",
]

try:
    from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_dynamic_libs

    for _pkg in ("certifi",):
        _d, _b, _h = collect_all(_pkg)
        _datas += _d
        _binaries += _b
        _hiddenimports += _h

    _binaries += collect_dynamic_libs("torch")
    _binaries += collect_dynamic_libs("PyQt6")

    _qt_datas, _qt_binaries, _qt_hiddenimports = collect_all("PyQt6")
    _datas += _qt_datas
    _binaries += _qt_binaries
    _hiddenimports += _qt_hiddenimports

    for _pkg in ("yaml",):
        _datas += collect_data_files(_pkg)
except Exception as exc:  # pragma: no cover - only when PyInstaller missing locally
    print(f"Warning: PyInstaller hook collection skipped: {exc}", file=sys.stderr)

a = Analysis(
    [str(ROOT / "gui" / "run_app.py")],
    pathex=[str(ROOT)],
    binaries=_binaries,
    datas=_datas,
    hiddenimports=_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(ROOT / "packaging" / "rthook_ssl.py")],
    excludes=[
        "gradio",
        "kagglehub",
        "pytest",
        "sklearn",
        "matplotlib",
        "tensorboard",
        "torch.distributed",
        "torch.testing",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="ASKABR-L",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
