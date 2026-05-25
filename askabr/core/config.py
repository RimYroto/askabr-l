# -*- coding: utf-8 -*-
"""Загрузка и проверка YAML-конфигураций."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

REQUIRED_TOP_LEVEL = {"artifacts_dir", "seed", "model", "train", "resistance"}
REQUIRED_TRAIN_KEYS = {
    "image_size",
    "batch_size",
    "epochs",
    "lr",
    "weight_decay",
    "num_workers",
    "strong_augment",
}
REQUIRED_MODEL_KEYS = {"backbone", "pretrained", "num_classes"}
REQUIRED_RESISTANCE_KEYS = {"severity_rules", "default_severity_weight"}


def load_yaml_config(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def validate_config(cfg: dict[str, Any]) -> list[str]:
    """Возвращает список нарушений схемы конфигурации."""
    errors: list[str] = []
    missing = REQUIRED_TOP_LEVEL - set(cfg.keys())
    if missing:
        errors.append(f"Отсутствуют ключи верхнего уровня: {sorted(missing)}")

    model = cfg.get("model") or {}
    missing_model = REQUIRED_MODEL_KEYS - set(model.keys())
    if missing_model:
        errors.append(f"model: отсутствуют ключи {sorted(missing_model)}")

    train = cfg.get("train") or {}
    missing_train = REQUIRED_TRAIN_KEYS - set(train.keys())
    if missing_train:
        errors.append(f"train: отсутствуют ключи {sorted(missing_train)}")

    resistance = cfg.get("resistance") or {}
    missing_res = REQUIRED_RESISTANCE_KEYS - set(resistance.keys())
    if missing_res:
        errors.append(f"resistance: отсутствуют ключи {sorted(missing_res)}")

    paths = cfg.get("paths")
    if paths is not None:
        for key in ("train_root", "val_root", "holdout_root"):
            if key not in paths:
                errors.append(f"paths: отсутствует ключ {key}")
    elif "data_root" not in cfg:
        errors.append("Не заданы paths или data_root для загрузки данных.")

    return errors
