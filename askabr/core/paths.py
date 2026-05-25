# -*- coding: utf-8 -*-
"""Пути проекта, моделей и внешних датасетов."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from askabr.core.constants import DEFAULT_MODEL_FILENAME, LEGACY_MODEL_FILENAME
from askabr.core.errors import E006_DATASET_ROOT_MISSING, format_error


def project_root() -> Path:
    """Корень репозитория в разработке; корень bundle PyInstaller в frozen-сборке."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[2]


def torch_cache_dir() -> Path:
    """Записываемый кэш весов torch hub."""
    if getattr(sys, "frozen", False):
        if sys.platform == "win32":
            program_data = os.environ.get("ProgramData", r"C:\ProgramData")
            cache = Path(program_data) / "ASKABR-L" / "torch"
        else:
            base = os.environ.get("LOCALAPPDATA") or os.environ.get("XDG_CACHE_HOME") or str(Path.home())
            cache = Path(base) / "ASKABR-L" / "torch"
    else:
        cache = project_root() / ".cache" / "torch"
    cache.mkdir(parents=True, exist_ok=True)
    return cache


def models_root() -> Path:
    return project_root() / "models"


def model_variant_dir(variant: str) -> Path:
    """Каталог развёрнутой модели для культуры или набора культур."""
    return models_root() / variant


def resolve_checkpoint_path(variant_dir: Path) -> Path | None:
    """Возвращает путь к файлу весов: versioned имя или legacy best.pt."""
    versioned = variant_dir / DEFAULT_MODEL_FILENAME
    if versioned.is_file():
        return versioned
    legacy = variant_dir / LEGACY_MODEL_FILENAME
    if legacy.is_file():
        return legacy
    return None


def resource_path(*parts: str) -> Path:
    return project_root().joinpath(*parts)


def _require_env_root(env_name: str) -> Path:
    env = os.environ.get(env_name)
    if not env:
        raise FileNotFoundError(format_error(E006_DATASET_ROOT_MISSING, f"({env_name})"))
    path = Path(env).expanduser().resolve()
    if not path.is_dir():
        raise FileNotFoundError(
            format_error(E006_DATASET_ROOT_MISSING, f"Каталог не найден: {path}")
        )
    return path


def plantvillage_root() -> Path:
    """Корень внешнего датасета PlantVillage (ImageFolder parent)."""
    return _require_env_root("PLANTVILLAGE_ROOT")


def pear_leaves_root() -> Path:
    """Корень внешнего датасета Pear leaves."""
    return _require_env_root("PEAR_LEAVES_ROOT")
