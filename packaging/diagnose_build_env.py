# -*- coding: utf-8 -*-
"""Диагностика путей сборки на Windows (кириллица в имени пользователя и т.п.)."""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def main() -> None:
    if sys.platform != "win32":
        print("Run this script on Windows.")
        raise SystemExit(0)

    mod = _load(ROOT / "packaging" / "windows_paths.py", "windows_paths")

    print("=== ASKABR-L build environment ===")
    print(f"Python: {sys.version}")
    print(f"Executable: {sys.executable}")
    print(f"Project: {ROOT}")
    print(f"Non-ASCII in project path: {mod.has_non_ascii(ROOT)}")
    print(f"USERPROFILE: {os.environ.get('USERPROFILE', '')}")
    print(f"Non-ASCII in USERPROFILE: {mod.has_non_ascii(os.environ.get('USERPROFILE', ''))}")
    print(f"TEMP: {os.environ.get('TEMP', '')}")
    print(f"TMP: {os.environ.get('TMP', '')}")

    paths = mod.prepare_build_paths(ROOT)
    print(f"ASCII build cache: {paths['cache']}")
    print(f"Venv will be created at: {paths['venv']}")
    print(f"PyInstaller work: {paths['pyi_work']}")
    print(f"Final exe target: {paths['dist'] / 'ASKABR-L.exe'}")

    resolve = _load(ROOT / "packaging" / "resolve_python314.py", "resolve_python314")
    py314 = resolve.resolve_python314_executable()
    print(f"Python 3.14 resolved: {py314 or 'NOT FOUND'}")
    if not py314:
        raise SystemExit(1)
    print("Diagnostics OK.")


if __name__ == "__main__":
    main()
