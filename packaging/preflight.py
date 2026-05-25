# -*- coding: utf-8 -*-
"""Проверки перед сборкой Windows .exe."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

WEIGHT_FILENAMES = ("model_v1.0.0.pt", "best.pt")
REQUIRED_VARIANTS = ("tomato", "pear")
REQUIRED_PYTHON = (3, 14)
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


def assert_python_version(*, build: bool = False) -> None:
    version = sys.version_info[:2]
    if build:
        if version != REQUIRED_PYTHON:
            raise SystemExit(
                f"Windows build requires Python {REQUIRED_PYTHON[0]}.{REQUIRED_PYTHON[1]}, "
                f"but got {version[0]}.{version[1]}.\n"
                "Install Python 3.14 and run: py -3.14 packaging\\build_windows.py"
            )
        return

    if version < REQUIRED_PYTHON or version >= MAX_PYTHON_EXCLUSIVE:
        raise SystemExit(
            f"Unsupported Python {version[0]}.{version[1]}. "
            f"This project requires Python {REQUIRED_PYTHON[0]}.{REQUIRED_PYTHON[1]}."
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="ASKABR-L build preflight checks.")
    parser.add_argument(
        "--build",
        action="store_true",
        help="Strict checks for Windows .exe build (Python 3.14 only).",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    assert_python_version(build=args.build)
    assert_release_models(root)
    label = "Build preflight" if args.build else "Preflight"
    print(f"{label} OK ({sys.version_info.major}.{sys.version_info.minor}):", root)


if __name__ == "__main__":
    main()
