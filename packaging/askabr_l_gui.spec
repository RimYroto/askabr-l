# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec для автономной сборки АСКАБР-Л (Windows, CPU)."""

import sys
from pathlib import Path

block_cipher = None
ROOT = Path(SPECPATH).resolve().parent.parent

a = Analysis(
    [str(ROOT / "gui" / "run_app.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(ROOT / "models" / "tomato"), "models/tomato"),
        (str(ROOT / "models" / "pear"), "models/pear"),
        (str(ROOT / "docs" / "INSTRUKCIYA.txt"), "docs"),
        (str(ROOT / "gui" / "class_labels_ru.json"), "gui"),
        (str(ROOT / "gui" / "plant_variants.json"), "gui"),
    ],
    hiddenimports=[
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
        "askabr",
        "askabr.classification.augment",
        "askabr.classification.model",
        "askabr.classification.predict",
        "askabr.assessment.phytosanitary_index",
        "askabr.core.paths",
        "askabr.core.ssl",
        "askabr.core.terminology",
        "askabr.core.version",
        "certifi",
        "gui.main_window",
        "gui.variants",
        "gui.about_dialog",
        "gui.help_dialog",
        "gui.report_export",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "gradio",
        "kagglehub",
        "pytest",
        "sklearn",
        "matplotlib",
        "tensorboard",
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
