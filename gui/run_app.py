#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Точка входа графического интерфейса АСКАБР-Л."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from askabr.core.ssl import configure_ssl_certificates

configure_ssl_certificates()

from PyQt6.QtWidgets import QApplication

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from askabr.core.errors import E004_NO_MODELS, format_error
from gui.main_window import MainWindow
from gui.variants import available_variants, normalize_variant_id


def main() -> None:
    parser = argparse.ArgumentParser(description="Графический интерфейс АСКАБР-Л.")
    parser.add_argument(
        "--variant",
        default=None,
        help="Начальная культура в списке (необязательно).",
    )
    args = parser.parse_args()

    variants = available_variants()
    if not variants:
        raise SystemExit(format_error(E004_NO_MODELS))

    initial = normalize_variant_id(args.variant) if args.variant else None
    if initial is not None and initial not in variants:
        raise SystemExit(f"Модель {initial!r} недоступна. Доступны: {', '.join(variants)}")

    app = QApplication(sys.argv)
    win = MainWindow(initial_variant=initial)
    win.resize(780, 920)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
