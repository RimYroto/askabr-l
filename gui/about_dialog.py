# -*- coding: utf-8 -*-
"""Диалог «О программе»."""

from __future__ import annotations

from PyQt6.QtWidgets import QMessageBox, QWidget

from askabr.core.version import (
    COPYRIGHT_NOTICE,
    IFS_DISCLAIMER,
    PRODUCT_NAME_FULL,
    PRODUCT_NAME_SHORT,
    __version__,
)


def show_about_dialog(parent: QWidget | None) -> None:
    text = (
        f"<h3>{PRODUCT_NAME_SHORT}</h3>"
        f"<p>{PRODUCT_NAME_FULL}</p>"
        f"<p>Версия {__version__}</p>"
        f"<p>{COPYRIGHT_NOTICE}</p>"
        f"<p><small>{IFS_DISCLAIMER}</small></p>"
    )
    QMessageBox.about(parent, f"О программе — {PRODUCT_NAME_SHORT}", text)
