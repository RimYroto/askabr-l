# -*- coding: utf-8 -*-
"""Валидация YAML-конфигураций."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from askabr.core.config import validate_config


CONFIG_DIR = Path(__file__).resolve().parents[1] / "configs"


@pytest.mark.parametrize(
    "name",
    ["default.yaml", "plantvillage_local.yaml", "tomato_only.yaml", "pear_only.yaml", "smoke.yaml"],
)
def test_config_schema(name: str):
    path = CONFIG_DIR / name
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    errors = validate_config(cfg)
    assert errors == [], f"{name}: {errors}"


def test_no_warmup_epochs_in_configs():
    for path in CONFIG_DIR.glob("*.yaml"):
        text = path.read_text(encoding="utf-8")
        assert "warmup_epochs" not in text, f"warmup_epochs found in {path.name}"
