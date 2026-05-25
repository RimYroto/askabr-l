# -*- coding: utf-8 -*-

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_frozen_torch_cache_uses_programdata_on_windows(monkeypatch):
    paths_mod = importlib.import_module("askabr.core.paths")
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "platform", "win32", raising=False)
    monkeypatch.setenv("ProgramData", str(ROOT / "fake-programdata"))

    cache = paths_mod.torch_cache_dir()
    assert "ASKABR-L" in str(cache)
    assert "torch" in str(cache)
    assert cache.as_posix().isascii()


def test_project_root_frozen_meipass(monkeypatch, tmp_path):
    paths_mod = importlib.import_module("askabr.core.paths")
    meipass = tmp_path / "bundle"
    meipass.mkdir()
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(meipass), raising=False)

    assert paths_mod.project_root() == meipass
