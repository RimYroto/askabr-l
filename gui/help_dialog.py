# -*- coding: utf-8 -*-
"""Окно с инструкцией пользователя."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QTextBrowser, QVBoxLayout

from askabr.core.paths import resource_path
from askabr.core.version import PRODUCT_NAME_SHORT


def _instruction_text() -> str:
    candidates = (
        resource_path("docs", "INSTRUKCIYA.txt"),
        Path(__file__).resolve().parents[1] / "docs" / "INSTRUKCIYA.txt",
    )
    for path in candidates:
        if path.is_file():
            return path.read_text(encoding="utf-8")
    return "Файл инструкции не найден. См. docs/INSTRUKCIYA.txt в каталоге программы."


def show_instruction_dialog(parent=None) -> None:
    dialog = QDialog(parent)
    dialog.setWindowTitle(f"Инструкция — {PRODUCT_NAME_SHORT}")
    dialog.resize(720, 560)

    browser = QTextBrowser()
    browser.setReadOnly(True)
    browser.setPlainText(_instruction_text())
    browser.setFont(QFont("Consolas", 10))

    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
    buttons.rejected.connect(dialog.reject)
    buttons.accepted.connect(dialog.accept)

    layout = QVBoxLayout(dialog)
    layout.addWidget(browser)
    layout.addWidget(buttons)
    dialog.exec()
