# -*- coding: utf-8 -*-
"""Пути сборки на Windows: обход кириллицы и не-ASCII в профиле пользователя."""

from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path


def has_non_ascii(path: Path | str) -> bool:
    return any(ord(ch) > 127 for ch in str(path))


def configure_unicode_env() -> None:
    """Включает UTF-8 для дочерних процессов Python/pip/PyInstaller."""
    if sys.platform != "win32":
        return
    os.environ.setdefault("PYTHONUTF8", "1")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")


def subprocess_text_kwargs() -> dict:
    if sys.platform == "win32":
        return {"encoding": "utf-8", "errors": "replace"}
    return {}


def windows_short_path(path: Path) -> Path | None:
    """8.3 short path (ASCII), если включён на томе Windows."""
    if sys.platform != "win32":
        return None
    try:
        import ctypes

        buffer = ctypes.create_unicode_buffer(32768)
        result = ctypes.windll.kernel32.GetShortPathNameW(str(path), buffer, len(buffer))
        if result == 0:
            return None
        return Path(buffer.value)
    except OSError:
        return None


def ascii_build_cache_root(project_root: Path) -> Path:
    """Каталог только с ASCII-символами для venv, TEMP и PyInstaller."""
    program_data = os.environ.get("ProgramData", r"C:\ProgramData")
    digest = hashlib.sha256(str(project_root.resolve()).encode("utf-8")).hexdigest()[:12]
    return Path(program_data) / "ASKABR-L" / digest


def prepare_build_paths(project_root: Path) -> dict[str, Path]:
    """Готовит ASCII-пути для сборки; dist остаётся в проекте."""
    configure_unicode_env()
    project_root = project_root.resolve()

    cache = ascii_build_cache_root(project_root)
    paths = {
        "project": project_root,
        "cache": cache,
        "venv": cache / "venv-build",
        "temp": cache / "temp",
        "pyi_work": cache / "pyi-work",
        "pyi_dist": cache / "pyi-dist",
        "dist": project_root / "dist",
    }

    for key in ("cache", "venv", "temp", "pyi_work", "pyi_dist", "dist"):
        paths[key].mkdir(parents=True, exist_ok=True)

    os.environ["TEMP"] = str(paths["temp"])
    os.environ["TMP"] = str(paths["temp"])
    os.environ["PIP_CACHE_DIR"] = str(cache / "pip-cache")

    if has_non_ascii(project_root):
        short = windows_short_path(project_root)
        print(
            "Note: project path contains non-ASCII characters "
            f"({project_root})."
        )
        if short and not has_non_ascii(short):
            print(f"Using short path where possible: {short}")
            paths["project_short"] = short
        else:
            print(
                "Build caches were moved to ASCII path:\n"
                f"  {cache}\n"
                "Final ASKABR-L.exe will be copied to dist\\ in your project."
            )

    return paths


def copy_built_exe(pyi_dist: Path, target: Path) -> Path:
    source = pyi_dist / "ASKABR-L.exe"
    if not source.is_file():
        raise FileNotFoundError(f"PyInstaller did not create {source}")
    target.parent.mkdir(parents=True, exist_ok=True)
    import shutil

    shutil.copy2(source, target)
    return target
