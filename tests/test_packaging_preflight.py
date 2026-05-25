# -*- coding: utf-8 -*-
"""Проверки сценария сборки Windows .exe."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT = ROOT / "packaging" / "preflight.py"


def _load_preflight():
    spec = importlib.util.spec_from_file_location("packaging_preflight", PREFLIGHT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_release_models_present():
    preflight = _load_preflight()
    missing = preflight.missing_model_dirs(ROOT)
    if missing:
        pytest.skip(f"weights not in workspace: {missing}")
    preflight.assert_release_models(ROOT)


def test_python_version_supported():
    preflight = _load_preflight()
    preflight.assert_python_version()


def test_spec_declares_required_bundles():
    spec_text = (ROOT / "packaging" / "askabr_l_gui.spec").read_text(encoding="utf-8")
    assert "models/tomato" in spec_text
    assert "models/pear" in spec_text
    assert "rthook_ssl.py" in spec_text
    assert "upx=False" in spec_text
