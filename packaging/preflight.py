# -*- coding: utf-8 -*-
"""Проверки перед сборкой Windows .exe."""

from __future__ import annotations

import sys
from pathlib import Path

WEIGHT_FILENAMES = ("model_v1.0.0.pt", "best.pt")
REQUIRED_VARIANTS = ("tomato", "pear")
MIN_PYTHON = (3, 10)
MAX_PYTHON_EXCLUSIVE = (3, 15)


def resolve_checkpoint(variant_dir: Path) -> Path | None:
    for name in WEIGHT_FILENAMES:
        path = variant_dir / name
        if path.is_file():
            return path
    return None


def missing_model_dirs(root: Path) -> list[Path]:
    missing: list[Path] = []
    for variant in REQUIRED_VARIANTS:
        variant_dir = root / "models" / variant
        if resolve_checkpoint(variant_dir) is None:
            missing.append(variant_dir)
    return missing


def assert_release_models(root: Path) -> None:
    missing = missing_model_dirs(root)
    if not missing:
        return
    lines = "\n  ".join(str(path) for path in missing)
    raise SystemExit(
        "Cannot build ASKABR-L.exe: missing model weights.\n"
        f"  {lines}\n"
        "Add model_v1.0.0.pt or best.pt to each folder (see docs/INSTRUKCIYA.txt)."
    )


def assert_python_version() -> None:
    version = sys.version_info[:3]
    if version[:2] < MIN_PYTHON or version >= MAX_PYTHON_EXCLUSIVE:
        max_supported = f"{MAX_PYTHON_EXCLUSIVE[0]}.{MAX_PYTHON_EXCLUSIVE[1] - 1}"
        raise SystemExit(
            f"Unsupported Python {version[0]}.{version[1]} for this project. "
            f"Use Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}–{max_supported}."
        )


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    assert_python_version()
    assert_release_models(root)
    print("Build preflight OK:", root)


if __name__ == "__main__":
    main()
