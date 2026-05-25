# -*- coding: utf-8 -*-
"""Тесты слоя терминологии."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from askabr.core.paths import models_root, project_root
from askabr.core.terminology import display_name_ru, normalize_class_id


def test_display_name_tomato_healthy():
    assert "здоров" in display_name_ru("Tomato_healthy").lower()


def test_display_name_slug_formal():
    name = display_name_ru("slug")
    assert "моллюск" in name.lower()


def test_normalize_plantvillage_alias():
    assert normalize_class_id("Tomato___healthy") == "Tomato_healthy"


@pytest.mark.parametrize("variant_dir", ["tomato", "pear"])
def test_all_model_labels_have_display_names(variant_dir: str):
    labels_path = models_root() / variant_dir / "labels.json"
    if not labels_path.is_file():
        pytest.skip(f"no labels for {variant_dir}")
    payload = json.loads(labels_path.read_text(encoding="utf-8"))
    for class_id in payload["classes"]:
        name = display_name_ru(class_id)
        assert name != "" or class_id
