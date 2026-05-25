# -*- coding: utf-8 -*-
"""
Расчёт индекса неопределённости классификации (ИНК) и
индекса фитосанитарного состояния (ИФС).

Реализация: askabr/assessment/phytosanitary_index.py, askabr/core/constants.py
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from askabr.core.constants import (
    IFS_HIGH_THRESHOLD,
    IFS_INFECTION_RATE_WEIGHT,
    IFS_MEAN_RISK_WEIGHT,
    IFS_MODERATE_THRESHOLD,
    INK_CONFIDENCE_WEIGHT,
    INK_ENTROPY_WEIGHT,
)
from askabr.core.version import IFS_DISCLAIMER


def disease_severity_weight(class_name: str, rules: list[dict[str, Any]], default: float) -> float:
    """Вес тяжести поражения по имени класса и правилам подстрок."""
    lower = class_name.lower()
    for r in rules:
        pat = str(r["pattern"]).lower()
        if pat in lower:
            return float(r["weight"])
    return float(default)


def classification_uncertainty_index(probs: np.ndarray, top1_prob: float) -> float:
    """Индекс неопределённости классификации (ИНК), диапазон 0..1."""
    eps = 1e-8
    p = np.clip(probs, eps, 1.0)
    p = p / p.sum()
    h = float(-(p * np.log(p)).sum())
    h_norm = h / np.log(len(p)) if len(p) > 1 else 0.0
    return float(
        INK_CONFIDENCE_WEIGHT * (1.0 - top1_prob) + INK_ENTROPY_WEIGHT * h_norm
    )


# Обратная совместимость
severity_proxy = classification_uncertainty_index


def is_healthy(class_name: str) -> bool:
    return "healthy" in class_name.lower()


@dataclass
class PhytosanitaryAssessment:
    phytosanitary_index: float
    infection_rate: float
    mean_risk: float
    summary: str

    @property
    def resistance_index(self) -> float:
        return self.phytosanitary_index


TrialScore = PhytosanitaryAssessment


def score_trial(predictions: list[dict[str, Any]], resistance_cfg: dict[str, Any]) -> PhytosanitaryAssessment:
    """
    Агрегирует результаты серии классификаций в индекс фитосанитарного состояния (ИФС).

    predictions: список словарей с ключами top_class, top1_prob, probs (np.ndarray).
    resistance_cfg: ключи severity_rules, default_severity_weight.
    """
    rules = list(resistance_cfg["severity_rules"])
    default_w = float(resistance_cfg["default_severity_weight"])
    if not predictions:
        return PhytosanitaryAssessment(
            phytosanitary_index=100.0,
            infection_rate=0.0,
            mean_risk=0.0,
            summary=(
                "Изображения не переданы; ИФС условно максимален. "
                f"{IFS_DISCLAIMER}"
            ),
        )

    risks: list[float] = []
    diseased = 0
    for pr in predictions:
        cls = str(pr["top_class"])
        p1 = float(pr["top1_prob"])
        probs = pr.get("probs")
        if probs is None:
            proxy = float(1.0 - p1)
        else:
            proxy = classification_uncertainty_index(np.asarray(probs, dtype=np.float64), p1)
        w = disease_severity_weight(cls, rules, default_w)
        risk = w * (0.5 + 0.5 * proxy)
        risks.append(risk)
        if not is_healthy(cls):
            diseased += 1
        elif p1 < 0.6:
            diseased += 1

    infection_rate = diseased / len(predictions)
    mean_risk = float(np.mean(risks)) if risks else 0.0
    burden = IFS_INFECTION_RATE_WEIGHT * infection_rate + IFS_MEAN_RISK_WEIGHT * mean_risk
    ifs = float(max(0.0, min(100.0, 100.0 * (1.0 - min(burden, 1.0)))))

    if ifs >= IFS_HIGH_THRESHOLD:
        label = "высокое фитосанитарное состояние (по результатам классификации)"
    elif ifs >= IFS_MODERATE_THRESHOLD:
        label = "умеренное фитосанитарное состояние (по результатам классификации)"
    else:
        label = "низкое фитосанитарное состояние (по результатам классификации)"

    summary = (
        f"{label}. ИФС={ifs:.1f}/100. "
        f"Доля поражённых или неоднозначных кадров={infection_rate:.2f}, "
        f"средний риск={mean_risk:.3f}. {IFS_DISCLAIMER}"
    )
    return PhytosanitaryAssessment(
        phytosanitary_index=ifs,
        infection_rate=float(infection_rate),
        mean_risk=mean_risk,
        summary=summary,
    )
