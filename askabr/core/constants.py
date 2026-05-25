# -*- coding: utf-8 -*-
"""Именованные константы алгоритмов и конфигурации."""

from __future__ import annotations

# Индекс неопределённости классификации (ИНК)
INK_ENTROPY_WEIGHT = 0.5
INK_CONFIDENCE_WEIGHT = 0.5

# Индекс фитосанитарного состояния (ИФС)
IFS_INFECTION_RATE_WEIGHT = 0.55
IFS_MEAN_RISK_WEIGHT = 0.45
IFS_HIGH_THRESHOLD = 80.0
IFS_MODERATE_THRESHOLD = 55.0

# Обучение
EARLY_STOP_PLATEAU_EPOCHS = 8
EARLY_STOP_MIN_MACRO_F1 = 0.93
MODEL_SELECTION_ACC_WEIGHT = 0.01
PLATEAU_F1_DELTA = 0.002

# Модели
DEFAULT_MODEL_FILENAME = "model_v1.0.0.pt"
LEGACY_MODEL_FILENAME = "best.pt"
SUPPORTED_IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp")

# Устаревшие идентификаторы вариантов моделей (обратная совместимость)
LEGACY_VARIANT_ALIASES: dict[str, str] = {
    "full": "multicrop",
}
