# -*- coding: utf-8 -*-
"""Коды ошибок прикладного уровня."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AppError:
    code: str
    message: str


E001_MODEL_NOT_FOUND = AppError("E001", "Файл весов модели не найден.")
E002_UNSUPPORTED_FORMAT = AppError("E002", "Неподдерживаемый формат изображения.")
E003_IMAGE_READ_FAILED = AppError("E003", "Не удалось прочитать файл изображения.")
E004_NO_MODELS = AppError("E004", "Нет развёрнутых моделей в каталоге models/.")
E005_INFERENCE_FAILED = AppError("E005", "Ошибка выполнения классификации.")
E006_DATASET_ROOT_MISSING = AppError(
    "E006",
    "Не задан корень датасета. Укажите переменную окружения PLANTVILLAGE_ROOT или PEAR_LEAVES_ROOT.",
)
E007_EXPORT_FAILED = AppError("E007", "Не удалось сохранить отчёт.")


def format_error(err: AppError, detail: str = "") -> str:
    if detail:
        return f"[{err.code}] {err.message} {detail}".strip()
    return f"[{err.code}] {err.message}"
