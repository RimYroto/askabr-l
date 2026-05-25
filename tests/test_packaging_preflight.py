# -*- coding: utf-8 -*-
"""Проверки сценария сборки Windows .exe."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PACKAGING = ROOT / "packaging"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_release_models_present():
    preflight = _load_module("preflight", PACKAGING / "preflight.py")
    missing = preflight.missing_model_dirs(ROOT)
    if missing:
        pytest.skip(f"weights not in workspace: {missing}")
    preflight.assert_release_models(ROOT)


@pytest.mark.skipif(
    sys.version_info[:2] != (3, 14),
    reason="project requires Python 3.14",
)
def test_python_version_is_314():
    preflight = _load_module("preflight", PACKAGING / "preflight.py")
    preflight.assert_python_version()
    preflight.assert_python_version(build=True)


def test_resolve_python314_on_current_interpreter():
    resolve = _load_module("resolve_python314", PACKAGING / "resolve_python314.py")
    if sys.version_info[:2] != (3, 14):
        pytest.skip("not running on Python 3.14")
    exe = resolve.resolve_python314_executable()
    assert exe
    assert Path(exe).is_file()


def test_spec_declares_required_bundles():
    spec_text = (PACKAGING / "askabr_l_gui.spec").read_text(encoding="utf-8")
    assert "rthook_runtime.py" in spec_text
    assert "pyinstaller_hooks_contrib" in spec_text
    assert "get_hook_dirs" in spec_text
    assert "upx=False" in spec_text
    assert "_collect_model_datas" in spec_text
    assert "Warning: PyInstaller hook collection skipped" not in spec_text


def test_windows_build_entrypoints_exist():
    for name in (
        "build_windows.py",
        "build_windows.cmd",
        "build_windows.ps1",
        "build_windows.bat",
        "resolve_python314.py",
        "constraints-build.txt",
        "rthook_runtime.py",
    ):
        assert (PACKAGING / name).is_file()


def test_staging_populates_required_files(tmp_path):
    wp = _load_module("windows_paths", PACKAGING / "windows_paths.py")
    staging = tmp_path / "staging"
    wp.populate_staging(ROOT, staging)
    assert (staging / "pyproject.toml").is_file()
    assert (staging / "askabr").is_dir()
    assert (staging / "gui").is_dir()
    assert (staging / "packaging" / "askabr_l_gui.spec").is_file()
    for variant in ("tomato", "pear"):
        variant_dir = staging / "models" / variant
        if not (ROOT / "models" / variant).is_dir():
            continue
        has_src = (
            (ROOT / "models" / variant / "model_v1.0.0.pt").is_file()
            or (ROOT / "models" / variant / "best.pt").is_file()
        )
        if not has_src:
            continue
        assert list(variant_dir.glob("*.pt")), f"no checkpoint in staging for {variant}"
