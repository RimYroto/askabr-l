# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec для автономной сборки АСКАБР-Л (Windows, CPU, onefile)."""

from __future__ import annotations

import importlib.util
import os
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


def _collect_model_datas() -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    for variant in ("tomato", "pear"):
        variant_dir = ROOT / "models" / variant
        if not variant_dir.is_dir():
            continue
        dest = f"models/{variant}"
        for ckpt_name in ("model_v1.0.0.pt", "best.pt"):
            ckpt = variant_dir / ckpt_name
            if ckpt.is_file():
                entries.append((str(ckpt), dest))
                break
        for meta in ("labels.json", "config_resolved.yaml"):
            meta_path = variant_dir / meta
            if meta_path.is_file():
                entries.append((str(meta_path), dest))
    return entries


def _merge_collect(package: str, datas: list, binaries: list, hiddenimports: list) -> None:
    from PyInstaller.utils.hooks import collect_all

    pkg_datas, pkg_binaries, pkg_hidden = collect_all(package)
    if not pkg_datas and not pkg_binaries and package in ("torch", "PyQt6"):
        raise RuntimeError(f"collect_all({package!r}) returned no binaries or datas")
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hidden


_binaries: list = []
_datas = [
    (str(ROOT / "docs" / "INSTRUKCIYA.txt"), "docs"),
    (str(ROOT / "gui" / "class_labels_ru.json"), "gui"),
    (str(ROOT / "gui" / "plant_variants.json"), "gui"),
]
_datas += _collect_model_datas()

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

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

import pyinstaller_hooks_contrib

_hookspath = pyinstaller_hooks_contrib.get_hook_dirs()

_merge_collect("certifi", _datas, _binaries, _hiddenimports)
_binaries += collect_dynamic_libs("torch")
_binaries += collect_dynamic_libs("PyQt6")
_merge_collect("PyQt6", _datas, _binaries, _hiddenimports)
_merge_collect("torch", _datas, _binaries, _hiddenimports)

for _pkg in ("yaml",):
    _datas += collect_data_files(_pkg)

_console = bool(os.environ.get("ASKABR_BUILD_DEBUG"))

a = Analysis(
    [str(ROOT / "gui" / "run_app.py")],
    pathex=[str(ROOT)],
    binaries=_binaries,
    datas=_datas,
    hiddenimports=_hiddenimports,
    hookspath=_hookspath,
    hooksconfig={},
    runtime_hooks=[str(ROOT / "packaging" / "rthook_runtime.py")],
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
    console=_console,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
