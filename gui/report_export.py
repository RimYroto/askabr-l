# -*- coding: utf-8 -*-
"""Экспорт результатов анализа в текстовый отчёт."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from askabr.assessment.phytosanitary_index import PhytosanitaryAssessment
from askabr.core.terminology import display_name_ru
from askabr.core.version import IFS_DISCLAIMER, PRODUCT_NAME_SHORT, __version__


def export_report_txt(
    path: Path,
    *,
    variant_label: str,
    single_results: list[dict],
    batch_assessment: PhytosanitaryAssessment | None,
) -> None:
    lines = [
        f"Отчёт {PRODUCT_NAME_SHORT} v{__version__}",
        f"Дата и время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Модель: {variant_label}",
        "",
    ]
    for i, item in enumerate(single_results, start=1):
        lines.append(f"--- Изображение {i}: {item.get('path', '—')} ---")
        lines.append(f"Класс: {item['class_ru']} ({item['class_id']})")
        lines.append(f"Уверенность модели: {item['confidence_pct']:.1f} %")
        lines.append(f"ИНК: {item['ink_pct']:.1f} %")
        if item.get("topk"):
            lines.append("Топ-5 классов:")
            for name_ru, name_id, prob in item["topk"]:
                lines.append(f"  - {name_ru} ({name_id}): {prob:.2f} %")
        lines.append("")

    if batch_assessment is not None:
        lines.extend(
            [
                "--- Сводка по серии изображений ---",
                f"ИФС: {batch_assessment.phytosanitary_index:.1f} / 100",
                f"Доля поражённых/неоднозначных кадров: {batch_assessment.infection_rate:.2f}",
                f"Средний риск: {batch_assessment.mean_risk:.3f}",
                batch_assessment.summary,
                "",
            ]
        )

    lines.append(IFS_DISCLAIMER)
    path.write_text("\n".join(lines), encoding="utf-8")


def format_single_result(pred: dict, path: str | None = None) -> dict:
    top_class = str(pred["top_class"])
    ink = float(pred.get("ink", 0.0))
    topk = []
    for name, p in pred.get("topk", []):
        topk.append((display_name_ru(name), name, 100.0 * float(p)))
    return {
        "path": path or pred.get("path"),
        "class_id": top_class,
        "class_ru": display_name_ru(top_class),
        "confidence_pct": 100.0 * float(pred["top1_prob"]),
        "ink_pct": 100.0 * ink,
        "topk": topk,
    }
