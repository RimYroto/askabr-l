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
    assert "models/tomato" in spec_text
    assert "models/pear" in spec_text
    assert "rthook_ssl.py" in spec_text
    assert "upx=False" in spec_text


def test_windows_build_entrypoints_exist():
    for name in (
        "build_windows.py",
        "build_windows.cmd",
        "build_windows.ps1",
        "build_windows.bat",
        "resolve_python314.py",
    ):
        assert (PACKAGING / name).is_file()
