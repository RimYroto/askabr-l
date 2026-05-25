# -*- coding: utf-8 -*-

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_has_non_ascii():
    wp = _load("windows_paths", ROOT / "packaging" / "windows_paths.py")
    assert wp.has_non_ascii("C:\\Users\\Иван")
    assert not wp.has_non_ascii("C:\\Users\\Ivan")


def test_ascii_build_cache_root_is_ascii():
    wp = _load("windows_paths", ROOT / "packaging" / "windows_paths.py")
    cache = wp.ascii_build_cache_root(ROOT / "C:\\Users\\Иван\\askabr-l")
    assert not wp.has_non_ascii(cache)
    assert "ASKABR-L" in str(cache)


def test_prepare_build_paths_on_windows(monkeypatch, tmp_path):
    if sys.platform != "win32":
        return
    wp = _load("windows_paths", ROOT / "packaging" / "windows_paths.py")
    monkeypatch.setenv("ProgramData", str(tmp_path / "ProgramData"))
    paths = wp.prepare_build_paths(tmp_path / "proj")
    assert paths["venv"].parent == paths["cache"]
    assert not wp.has_non_ascii(paths["temp"])
