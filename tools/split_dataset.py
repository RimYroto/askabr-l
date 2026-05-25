#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Стратифицированное копирование ImageFolder в train / val / holdout."""

from __future__ import annotations

import argparse
import json
import random
import shutil
import sys
from pathlib import Path

from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from askabr.core.paths import plantvillage_root


def _list_images(folder: Path) -> list[Path]:
    out: list[Path] = []
    for pat in ("*.jpg", "*.JPG", "*.jpeg", "*.JPEG", "*.png", "*.PNG"):
        out.extend(folder.glob(pat))
    return sorted(out)


def _sizes_per_class(n: int, r_train: float, r_val: float, r_hold: float) -> tuple[int, int, int]:
    """Возвращает (n_train, n_val, n_holdout) с суммой n и минимумом 1 в val и holdout при n>=3."""
    if n < 3:
        raise ValueError(f"Слишком мало изображений в классе: {n}")
    nt = int(round(n * r_train))
    nv = int(round(n * r_val))
    nh = n - nt - nv
    nv = max(1, nv)
    nh = max(1, nh)
    nt = n - nv - nh
    if nt < 1:
        nt = 1
        rem = n - 1
        nv = max(1, rem // 2)
        nh = rem - nv
    assert nt + nv + nh == n
    return nt, nv, nh


def split_and_copy(
    source_root: Path,
    output_root: Path,
    seed: int,
    r_train: float,
    r_val: float,
    r_hold: float,
    clean: bool,
    max_per_class: int | None = None,
) -> None:
    if not source_root.is_dir():
        raise FileNotFoundError(f"Нет каталога с данными: {source_root}")

    train_root = output_root / "train"
    val_root = output_root / "val"
    hold_root = output_root / "holdout"
    if clean and output_root.exists():
        shutil.rmtree(output_root)
    train_root.mkdir(parents=True, exist_ok=True)
    val_root.mkdir(parents=True, exist_ok=True)
    hold_root.mkdir(parents=True, exist_ok=True)

    rng = random.Random(seed)
    manifest: list[dict[str, str]] = []

    class_dirs = sorted([p for p in source_root.iterdir() if p.is_dir()])
    if len(class_dirs) < 2:
        raise RuntimeError("Ожидалось несколько подкаталогов-классов в корне датасета.")

    for cls_dir in tqdm(class_dirs, desc="Классы"):
        label = cls_dir.name
        files = _list_images(cls_dir)
        if not files:
            continue
        rng.shuffle(files)
        if max_per_class is not None and len(files) > max_per_class:
            files = files[:max_per_class]
        nt, nv, nh = _sizes_per_class(len(files), r_train, r_val, r_hold)
        parts = {
            "train": files[:nt],
            "val": files[nt : nt + nv],
            "holdout": files[nt + nv :],
        }
        for split_name, subset in parts.items():
            dest_dir = {"train": train_root, "val": val_root, "holdout": hold_root}[split_name] / label
            dest_dir.mkdir(parents=True, exist_ok=True)
            for src in subset:
                dst = dest_dir / src.name
                shutil.copy2(src, dst)
                manifest.append(
                    {
                        "split": split_name,
                        "class": label,
                        "src": str(src.resolve()),
                        "dst": str(dst.resolve()),
                    }
                )

    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "manifest.json").write_text(
        json.dumps(
            {
                "seed": seed,
                "max_per_class": max_per_class,
                "ratios": {"train": r_train, "val": r_val, "holdout": r_hold},
                "items": manifest,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Готово. Скопировано записей в manifest: {len(manifest)}. Корень: {output_root}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Разбиение PlantVillage на train/val/holdout.")
    default_src = plantvillage_root() / "PlantVillage"
    parser.add_argument(
        "--source",
        type=Path,
        default=default_src,
        help="Корень ImageFolder (подкаталоги = классы). По умолчанию: $PLANTVILLAGE_ROOT/PlantVillage.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=PROJECT_ROOT / "data" / "split",
        help="Куда копировать train, val, holdout.",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--train-ratio", type=float, default=0.74)
    parser.add_argument("--val-ratio", type=float, default=0.13)
    parser.add_argument(
        "--holdout-ratio",
        type=float,
        default=0.13,
        help="Остаток после train и val; сумма трёх долей должна быть 1.0.",
    )
    parser.add_argument("--clean", action="store_true", help="Удалить output-root перед копированием.")
    parser.add_argument(
        "--max-per-class",
        type=int,
        default=None,
        help="Случайно ограничить число изображений на класс перед разбиением (seed-controlled).",
    )
    args = parser.parse_args()

    rt, rv, rh = args.train_ratio, args.val_ratio, args.holdout_ratio
    if abs(rt + rv + rh - 1.0) > 1e-6:
        raise SystemExit("Сумма train+val+holdout должна быть равна 1.0")

    split_and_copy(
        args.source.resolve(),
        args.output_root.resolve(),
        args.seed,
        rt,
        rv,
        rh,
        args.clean,
        args.max_per_class,
    )


if __name__ == "__main__":
    main()
