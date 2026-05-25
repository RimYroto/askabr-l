# -*- coding: utf-8 -*-
"""Тесты модуля расчёта ИФС."""

from __future__ import annotations

import numpy as np

from askabr.assessment.phytosanitary_index import (
    classification_uncertainty_index,
    disease_severity_weight,
    score_trial,
)


def test_disease_severity_weight_healthy():
    rules = [{"pattern": "healthy", "weight": 0.0}, {"pattern": "___", "weight": 0.6}]
    assert disease_severity_weight("Tomato___healthy", rules, 0.65) == 0.0


def test_disease_severity_weight_spot():
    rules = [{"pattern": "spot", "weight": 0.55}]
    assert disease_severity_weight("Pepper___Bacterial_spot", rules, 0.65) == 0.55


def test_ink_bounds():
    p = np.ones(5) / 5
    ink = classification_uncertainty_index(p, top1_prob=0.2)
    assert 0.0 <= ink <= 1.0


def test_score_trial_all_healthy():
    cfg = {
        "severity_rules": [{"pattern": "healthy", "weight": 0.0}],
        "default_severity_weight": 0.65,
    }
    preds = [
        {
            "top_class": "Tomato___healthy",
            "top1_prob": 0.95,
            "probs": np.array([0.95, 0.03, 0.02]),
        }
        for _ in range(5)
    ]
    out = score_trial(preds, cfg)
    assert out.phytosanitary_index >= 90.0
    assert out.resistance_index >= 90.0


def test_score_trial_disease_lowers_index():
    cfg = {
        "severity_rules": [
            {"pattern": "healthy", "weight": 0.0},
            {"pattern": "mosaic", "weight": 0.8},
        ],
        "default_severity_weight": 0.65,
    }
    k = 10
    probs = np.array([0.05] * (k - 1) + [0.55])
    preds = [
        {
            "top_class": "Tomato___Tomato_mosaic_virus",
            "top1_prob": 0.55,
            "probs": probs,
        }
        for _ in range(8)
    ]
    out = score_trial(preds, cfg)
    assert out.phytosanitary_index < 80.0
    assert out.infection_rate >= 0.5
