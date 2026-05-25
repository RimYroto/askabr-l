# -*- coding: utf-8 -*-
"""Слой отображения технических идентификаторов классов в научные названия."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from askabr.core.paths import resource_path

# Дополнительные синонимы PlantVillage (разные соглашения об именовании)
_CLASS_ALIASES: dict[str, str] = {
    "Tomato___healthy": "Tomato_healthy",
    "Tomato___Bacterial_spot": "Tomato_Bacterial_spot",
    "Tomato___Early_blight": "Tomato_Early_blight",
    "Tomato___Late_blight": "Tomato_Late_blight",
    "Tomato___Leaf_Mold": "Tomato_Leaf_Mold",
    "Tomato___Septoria_leaf_spot": "Tomato_Septoria_leaf_spot",
    "Tomato___Spider_mites Two-spotted spider mite": "Tomato_Spider_mites_Two_spotted_spider_mite",
    "Tomato___Target_Spot": "Tomato__Target_Spot",
    "Tomato___Tomato_YellowLeaf_Curl_Virus": "Tomato__Tomato_YellowLeaf__Curl_Virus",
    "Tomato___Tomato_mosaic_virus": "Tomato__Tomato_mosaic_virus",
    "Pepper__bell___Bacterial_spot": "Pepper__bell___Bacterial_spot",
    "Pepper__bell___healthy": "Pepper__bell___healthy",
}


@lru_cache(maxsize=1)
def _load_display_names() -> dict[str, str]:
    candidates = (
        resource_path("gui", "class_labels_ru.json"),
        Path(__file__).resolve().parents[2] / "gui" / "class_labels_ru.json",
    )
    for path in candidates:
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))
    return {}


def normalize_class_id(model_class_id: str) -> str:
    """Приводит идентификатор класса к ключу словаря отображения."""
    if model_class_id in _load_display_names():
        return model_class_id
    return _CLASS_ALIASES.get(model_class_id, model_class_id)


def display_name_ru(model_class_id: str) -> str:
    """Научное отображаемое имя класса на русском языке."""
    labels = _load_display_names()
    key = normalize_class_id(model_class_id)
    return labels.get(key, labels.get(model_class_id, model_class_id))


def all_known_class_ids() -> list[str]:
    return sorted(_load_display_names().keys())
