#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Скачивание PlantVillage с Kaggle или создание крошечного синтетического датасета для проверки."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


def _find_imagefolder_root(start: Path) -> Path:
    """Ищет подкаталог, где прямые потомки — классы с изображениями."""
    best: Path | None = None
    best_score = 0
    for p in [start, *start.iterdir()]:
        if not p.is_dir():
            continue
        subdirs = [c for c in p.iterdir() if c.is_dir()]
        if len(subdirs) < 3:
            continue
        score = 0
        for c in subdirs[:50]:
            imgs = list(c.glob("*.jpg")) + list(c.glob("*.JPG")) + list(c.glob("*.png"))
            if imgs:
                score += 1
        if score > best_score:
            best_score = score
            best = p
    if best is None:
        raise RuntimeError(f"Не удалось найти корень ImageFolder внутри {start}")
    return best


def download_kaggle_plantvillage(cfg: dict, dest: Path) -> None:
    import kagglehub

    slug = cfg["download"]["kaggle_dataset"]
    cache_path = Path(kagglehub.dataset_download(slug))
    root = _find_imagefolder_root(cache_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(root, dest)
    print(f"Датасет скопирован в {dest} (из {root})")


def write_tiny_dataset(dest: Path, seed: int = 42) -> None:
    import random

    from PIL import Image
    import numpy as np

    random.seed(seed)
    rng = np.random.default_rng(seed)
    classes = [
        "Tomato___healthy",
        "Tomato___Tomato_mosaic_virus",
        "Pepper___Bacterial_spot",
    ]
    if dest.exists():
        shutil.rmtree(dest)
    for c in classes:
        d = dest / c
        d.mkdir(parents=True)
        for i in range(24):
            arr = rng.integers(0, 255, size=(128, 128, 3), dtype=np.uint8)
            Image.fromarray(arr).save(d / f"img_{i:03d}.jpg")
    print(f"Синтетический датасет записан в {dest} ({len(classes)} класса × 24 изображения)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Загрузка данных PlantVillage или режим --tiny.")
    parser.add_argument("--config", type=Path, default=PROJECT_ROOT / "configs" / "default.yaml")
    parser.add_argument(
        "--tiny",
        action="store_true",
        help="Создать маленький синтетический набор в data/tiny_plant.",
    )
    args = parser.parse_args()

    cfg = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    if args.tiny:
        dest = PROJECT_ROOT / "data" / "tiny_plant"
        write_tiny_dataset(dest, seed=int(cfg.get("seed", 42)))
        print("Для быстрых тестов укажите в конфиге data_root: data/tiny_plant или используйте configs/tiny.yaml.")
        return

    dest = PROJECT_ROOT / Path(cfg["data_root"])
    download_kaggle_plantvillage(cfg, dest)


if __name__ == "__main__":
    main()
