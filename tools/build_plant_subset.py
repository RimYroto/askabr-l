#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Симлинки train/val/holdout только для классов с заданным префиксом имени (одно растение)."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main() -> None:
    p = argparse.ArgumentParser(description="Подмножество ImageFolder по префиксу (например Tomato).")
    p.add_argument("--source", type=Path, default=PROJECT_ROOT / "data" / "split", help="Корень с train,val,holdout")
    p.add_argument("--output", type=Path, default=PROJECT_ROOT / "data" / "split_tomato", help="Куда положить симлинки")
    p.add_argument("--prefix", type=str, default="Tomato", help="Имя класса начинается с этого (PlantVillage)")
    p.add_argument("--clean", action="store_true", help="Удалить output перед созданием")
    args = p.parse_args()

    src = args.source.resolve()
    out = args.output.resolve()
    prefix = args.prefix
    if not src.is_dir():
        raise SystemExit(f"Нет каталога: {src}")

    if args.clean and out.exists():
        shutil.rmtree(out)

    for split in ("train", "val", "holdout"):
        sdir = src / split
        if not sdir.is_dir():
            raise SystemExit(f"Нет split-каталога: {sdir}")
        ddir = out / split
        ddir.mkdir(parents=True, exist_ok=True)
        matched = 0
        for cls_dir in sorted(sdir.iterdir()):
            if not cls_dir.is_dir() or not cls_dir.name.startswith(prefix):
                continue
            link = ddir / cls_dir.name
            if link.exists() or link.is_symlink():
                link.unlink()
            rel = os.path.relpath(cls_dir, ddir)
            link.symlink_to(rel, target_is_directory=True)
            matched += 1
        if matched < 2:
            raise SystemExit(f"В {split} найдено классов с префиксом {prefix!r}: {matched} (нужно >= 2).")
        print(f"{split}: {matched} классов -> {ddir}")

    print(f"Готово: {out} (симлинки на {src})")


if __name__ == "__main__":
    main()
