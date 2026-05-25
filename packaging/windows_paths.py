# -*- coding: utf-8 -*-
"""Пути сборки на Windows: обход кириллицы и не-ASCII в профиле пользователя."""

from __future__ import annotations

import hashlib
import os
import shutil
import sys
from pathlib import Path

REQUIRED_VARIANTS = ("tomato", "pear")


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


def frozen_torch_cache_dir() -> Path:
    """ASCII-safe torch hub cache for frozen Windows builds."""
    program_data = os.environ.get("ProgramData", r"C:\ProgramData")
    cache = Path(program_data) / "ASKABR-L" / "torch"
    cache.mkdir(parents=True, exist_ok=True)
    return cache


def _resolve_checkpoint(variant_dir: Path) -> Path | None:
    for name in ("model_v1.0.0.pt", "best.pt"):
        path = variant_dir / name
        if path.is_file():
            return path
    return None


def populate_staging(project_root: Path, staging_root: Path) -> None:
    """Копирует исходники и модели в ASCII staging для pip install ."""
    if staging_root.exists():
        shutil.rmtree(staging_root)
    staging_root.mkdir(parents=True, exist_ok=True)

    for package in ("askabr", "gui", "packaging"):
        src = project_root / package
        if src.is_dir():
            shutil.copytree(src, staging_root / package)

    shutil.copy2(project_root / "pyproject.toml", staging_root / "pyproject.toml")

    docs_src = project_root / "docs" / "INSTRUKCIYA.txt"
    if docs_src.is_file():
        (staging_root / "docs").mkdir(parents=True, exist_ok=True)
        shutil.copy2(docs_src, staging_root / "docs" / "INSTRUKCIYA.txt")

    for variant in REQUIRED_VARIANTS:
        src_dir = project_root / "models" / variant
        ckpt = _resolve_checkpoint(src_dir)
        if ckpt is None:
            continue
        dest_dir = staging_root / "models" / variant
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ckpt, dest_dir / ckpt.name)
        for meta in ("labels.json", "config_resolved.yaml"):
            meta_src = src_dir / meta
            if meta_src.is_file():
                shutil.copy2(meta_src, dest_dir / meta)


def prepare_build_paths(project_root: Path) -> dict[str, Path]:
    """Готовит ASCII-пути для сборки; dist остаётся в проекте."""
    configure_unicode_env()
    project_root = project_root.resolve()

    cache = ascii_build_cache_root(project_root)
    staging = cache / "staging"
    paths = {
        "project": project_root,
        "cache": cache,
        "staging": staging,
        "venv": cache / "venv-build",
        "temp": cache / "temp",
        "pyi_work": cache / "pyi-work",
        "pyi_dist": cache / "pyi-dist",
        "dist": project_root / "dist",
        "build_log": cache / "build.log",
        "pyinstaller_log": cache / "pyinstaller.log",
        "smoke_log": cache / "smoke.log",
        "dist_build_log": project_root / "dist" / "build.log",
        "dist_smoke_log": project_root / "dist" / "smoke.log",
        "dist_pyinstaller_log": project_root / "dist" / "pyinstaller.log",
    }

    for key in ("cache", "venv", "temp", "pyi_work", "pyi_dist", "dist"):
        paths[key].mkdir(parents=True, exist_ok=True)

    os.environ["TEMP"] = str(paths["temp"])
    os.environ["TMP"] = str(paths["temp"])
    os.environ["PIP_CACHE_DIR"] = str(cache / "pip-cache")

    populate_staging(project_root, staging)
    paths["build_cwd"] = staging

    if has_non_ascii(project_root):
        print(
            "Note: project path contains non-ASCII characters "
            f"({project_root})."
        )
        print(
            "Using ASCII staging for pip/PyInstaller:\n"
            f"  {staging}\n"
            "Final ASKABR-L.exe will be copied to dist\\ in your project."
        )

    return paths


def publish_build_logs(paths: dict[str, Path]) -> None:
    """Копирует логи из ASCII cache в dist проекта (удобно найти после сборки)."""
    paths["dist"].mkdir(parents=True, exist_ok=True)
    for cache_key, dist_key in (
        ("build_log", "dist_build_log"),
        ("pyinstaller_log", "dist_pyinstaller_log"),
        ("smoke_log", "dist_smoke_log"),
    ):
        src = paths[cache_key]
        if src.is_file():
            shutil.copy2(src, paths[dist_key])


def copy_built_exe(pyi_dist: Path, target: Path) -> Path:
    source = pyi_dist / "ASKABR-L.exe"
    if not source.is_file():
        raise FileNotFoundError(f"PyInstaller did not create {source}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return target
