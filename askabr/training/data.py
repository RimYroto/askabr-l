from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

import torch
from torch.utils.data import DataLoader, Dataset, Subset, random_split
from torchvision import datasets

from askabr.classification.augment import build_transforms


@dataclass
class DataConfig:
    """Один корень ImageFolder и случайное разбиение train/val."""

    data_root: Path
    image_size: int
    batch_size: int
    num_workers: int
    train_ratio: float
    seed: int
    strong_augment: bool
    prefetch_factor: int = 4


def save_label_map(classes: list[str], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    idx_to_class = {i: c for i, c in enumerate(classes)}
    path.write_text(json.dumps({"classes": classes, "idx_to_class": idx_to_class}, indent=2), encoding="utf-8")


def load_label_map(path: Path) -> tuple[list[str], dict[int, str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    classes = list(payload["classes"])
    idx_to_class = {int(k): v for k, v in payload["idx_to_class"].items()}
    return classes, idx_to_class


class _MapTransform(Dataset):
    def __init__(self, subset: Subset, transform) -> None:
        self.subset = subset
        self.transform = transform

    def __len__(self) -> int:
        return len(self.subset)

    def __getitem__(self, idx: int):
        x, y = self.subset[idx]
        return self.transform(x), y


def build_dataloaders(cfg: DataConfig) -> Tuple[DataLoader, DataLoader, list[str]]:
    root = cfg.data_root
    if not root.is_dir():
        raise FileNotFoundError(
            f"Корень датасета не найден: {root}. Укажите путь к данным или выполните подготовку."
        )

    train_tf, val_tf = build_transforms(cfg.image_size, cfg.strong_augment)

    full = datasets.ImageFolder(str(root), transform=None)
    if len(full.classes) < 2:
        raise ValueError(f"Ожидалось не меньше 2 классов в {root}, найдено {len(full.classes)}.")

    n_total = len(full)
    n_train = int(n_total * cfg.train_ratio)
    n_val = n_total - n_train
    if n_train < 1 or n_val < 1:
        raise ValueError(
            f"Недостаточно образцов для разбиения (всего {n_total}). "
            "Увеличьте объём данных или измените train_ratio."
        )
    generator = torch.Generator().manual_seed(cfg.seed)
    train_subset, val_subset = random_split(full, [n_train, n_val], generator=generator)

    train_ds = _MapTransform(train_subset, train_tf)
    val_ds = _MapTransform(val_subset, val_tf)

    pin = torch.cuda.is_available()
    dl_kw: dict = {"pin_memory": pin}
    if cfg.num_workers > 0:
        dl_kw["persistent_workers"] = True
        dl_kw["prefetch_factor"] = max(2, int(cfg.prefetch_factor))

    train_loader = DataLoader(
        train_ds,
        batch_size=cfg.batch_size,
        shuffle=True,
        num_workers=cfg.num_workers,
        **dl_kw,
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=cfg.batch_size,
        shuffle=False,
        num_workers=cfg.num_workers,
        **dl_kw,
    )
    return train_loader, val_loader, full.classes


def build_disjoint_dataloaders(
    train_root: Path,
    val_root: Path,
    image_size: int,
    batch_size: int,
    num_workers: int,
    strong_augment: bool,
    prefetch_factor: int = 4,
) -> Tuple[DataLoader, DataLoader, list[str]]:
    if not train_root.is_dir() or not val_root.is_dir():
        raise FileNotFoundError(f"Нет train или val: {train_root} / {val_root}")

    train_tf, val_tf = build_transforms(image_size, strong_augment)
    train_ds = datasets.ImageFolder(str(train_root), transform=train_tf)
    val_ds = datasets.ImageFolder(str(val_root), transform=val_tf)
    if train_ds.classes != val_ds.classes:
        raise ValueError("Имена классов в train и val не совпадают. Проверьте разбиение датасета.")

    pin = torch.cuda.is_available()
    dl_kw: dict = {"pin_memory": pin}
    if num_workers > 0:
        dl_kw["persistent_workers"] = True
        dl_kw["prefetch_factor"] = max(2, int(prefetch_factor))

    train_loader = DataLoader(
        train_ds,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        **dl_kw,
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        **dl_kw,
    )
    return train_loader, val_loader, train_ds.classes
