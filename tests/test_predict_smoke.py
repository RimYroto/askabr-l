# -*- coding: utf-8 -*-
"""Дымовой тест инференса."""

from __future__ import annotations

from pathlib import Path

import pytest
import torch
import yaml
from PIL import Image

from askabr.classification.predict import load_artifacts, predict_image, preprocess_eval, pick_device
from askabr.core.paths import resolve_checkpoint_path, model_variant_dir


@pytest.fixture(scope="module")
def tomato_artifacts():
    variant_dir = model_variant_dir("tomato")
    ckpt = resolve_checkpoint_path(variant_dir)
    if ckpt is None:
        pytest.skip("tomato model not deployed")
    cfg_path = variant_dir / "config_resolved.yaml"
    if not cfg_path.is_file():
        pytest.skip("tomato config missing")
    return load_artifacts(cfg_path, ckpt, pick_device())


def test_predict_smoke(tomato_artifacts):
    model, classes, cfg, device = tomato_artifacts
    tcfg = cfg["train"]
    tf = preprocess_eval(int(tcfg["image_size"]), bool(tcfg["strong_augment"]))
    img = Image.new("RGB", (64, 64), color=(40, 120, 40))
    result = predict_image(model, classes, img, tf, device, topk=3)
    assert result["top_class"] in classes
    assert 0.0 <= result["top1_prob"] <= 1.0
    assert len(result["topk"]) <= 3
