# -*- coding: utf-8 -*-
"""Главное окно пользовательского интерфейса АСКАБР-Л."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QPixmap
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from PIL import Image

from askabr.assessment.phytosanitary_index import classification_uncertainty_index, score_trial
from askabr.classification.predict import load_artifacts, pick_device, predict_image, preprocess_eval
from askabr.core.constants import SUPPORTED_IMAGE_EXTENSIONS
from askabr.core.errors import (
    E002_UNSUPPORTED_FORMAT,
    E003_IMAGE_READ_FAILED,
    E005_INFERENCE_FAILED,
    E007_EXPORT_FAILED,
    format_error,
)
from askabr.core.terminology import display_name_ru
from askabr.core.version import IFS_DISCLAIMER, PRODUCT_NAME_SHORT, __version__
from gui.about_dialog import show_about_dialog
from gui.help_dialog import show_instruction_dialog
from gui.report_export import export_report_txt, format_single_result
from gui.variants import available_variants, resolve_variant_paths, variant_display_name


class MainWindow(QMainWindow):
    def __init__(self, initial_variant: str | None = None) -> None:
        super().__init__()
        self.setWindowTitle(f"{PRODUCT_NAME_SHORT} v{__version__}")
        self._image_paths: list[Path] = []
        self._last_predictions: list[dict] = []
        self._variants = available_variants()
        if not self._variants:
            raise RuntimeError(
                "Нет развёрнутых моделей в models/. "
                "Обучите модель и разместите веса в models/<культура>/."
            )

        self._device = pick_device()
        self._model_cache: dict[str, tuple] = {}
        self._current_variant: str | None = None
        self._model = None
        self._classes: list[str] = []
        self._cfg: dict = {}
        self._tf = None

        self._build_menu()
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        plant_row = QHBoxLayout()
        plant_row.addWidget(QLabel("Культура:"))
        self._combo = QComboBox()
        for variant in self._variants:
            self._combo.addItem(variant_display_name(variant), variant)
        plant_row.addWidget(self._combo, stretch=1)
        layout.addLayout(plant_row)

        self._status_label = QLabel("")
        self._status_label.setWordWrap(True)
        layout.addWidget(self._status_label)

        btn_row = QHBoxLayout()
        self._btn_open = QPushButton("Открыть изображение")
        self._btn_open_batch = QPushButton("Открыть серию изображений")
        self._btn_run = QPushButton("Выполнить классификацию")
        self._btn_export = QPushButton("Экспорт отчёта")
        self._btn_open.clicked.connect(self._on_open_single)
        self._btn_open_batch.clicked.connect(self._on_open_batch)
        self._btn_run.clicked.connect(self._on_analyze)
        self._btn_export.clicked.connect(self._on_export)
        btn_row.addWidget(self._btn_open)
        btn_row.addWidget(self._btn_open_batch)
        btn_row.addWidget(self._btn_run)
        btn_row.addWidget(self._btn_export)
        layout.addLayout(btn_row)

        self._preview = QLabel("Предпросмотр изображения")
        self._preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._preview.setMinimumHeight(240)
        layout.addWidget(self._preview)

        res_box = QGroupBox("Результат классификации (активное изображение)")
        grid = QGridLayout(res_box)
        self._lbl_class = QLabel("—")
        self._lbl_conf = QLabel("—")
        self._lbl_ink = QLabel("—")
        grid.addWidget(QLabel("Предполагаемый класс:"), 0, 0)
        grid.addWidget(self._lbl_class, 0, 1)
        grid.addWidget(QLabel("Уверенность модели, %:"), 1, 0)
        grid.addWidget(self._lbl_conf, 1, 1)
        grid.addWidget(QLabel("Индекс неопределённости классификации (ИНК), %:"), 2, 0)
        grid.addWidget(self._lbl_ink, 2, 1)
        layout.addWidget(res_box)

        batch_box = QGroupBox("Сводка по серии изображений")
        batch_layout = QVBoxLayout(batch_box)
        self._lbl_ifs = QLabel("—")
        self._lbl_ifs.setWordWrap(True)
        batch_layout.addWidget(self._lbl_ifs)
        layout.addWidget(batch_box)

        top_box = QGroupBox("Топ-5 классов")
        self._table = QTableWidget(0, 3)
        self._table.setHorizontalHeaderLabels(["Класс (RU)", "Идентификатор", "Вероятность, %"])
        top_layout = QVBoxLayout(top_box)
        top_layout.addWidget(self._table)
        layout.addWidget(top_box)

        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)

        self._combo.currentIndexChanged.connect(self._on_variant_changed)

        start_variant = initial_variant if initial_variant in self._variants else self._variants[0]
        self._combo.blockSignals(True)
        self._combo.setCurrentIndex(self._variants.index(start_variant))
        self._combo.blockSignals(False)
        self._load_variant(start_variant)

    def _build_menu(self) -> None:
        menu_file = self.menuBar().addMenu("Файл")
        act_open = QAction("Открыть изображение", self)
        act_open.triggered.connect(self._on_open_single)
        menu_file.addAction(act_open)
        act_batch = QAction("Открыть серию изображений", self)
        act_batch.triggered.connect(self._on_open_batch)
        menu_file.addAction(act_batch)
        act_export = QAction("Экспорт отчёта", self)
        act_export.triggered.connect(self._on_export)
        menu_file.addAction(act_export)
        menu_file.addSeparator()
        act_exit = QAction("Выход", self)
        act_exit.triggered.connect(self.close)
        menu_file.addAction(act_exit)

        menu_analysis = self.menuBar().addMenu("Анализ")
        act_run = QAction("Выполнить классификацию", self)
        act_run.triggered.connect(self._on_analyze)
        menu_analysis.addAction(act_run)

        menu_help = self.menuBar().addMenu("Справка")
        act_instruction = QAction("Инструкция", self)
        act_instruction.triggered.connect(lambda: show_instruction_dialog(self))
        menu_help.addAction(act_instruction)
        act_about = QAction("О программе", self)
        act_about.triggered.connect(lambda: show_about_dialog(self))
        menu_help.addAction(act_about)
        act_disclaimer = QAction("Ограничения ИФС", self)
        act_disclaimer.triggered.connect(self._show_ifs_disclaimer)
        menu_help.addAction(act_disclaimer)

    def _show_ifs_disclaimer(self) -> None:
        QMessageBox.information(self, "Ограничения применения", IFS_DISCLAIMER)

    def _set_status(self, text: str) -> None:
        self._status_label.setText(text)
        self._status_bar.showMessage(text)

    def _clear_results(self) -> None:
        self._lbl_class.setText("—")
        self._lbl_conf.setText("—")
        self._lbl_ink.setText("—")
        self._lbl_ifs.setText("—")
        self._table.setRowCount(0)
        self._last_predictions.clear()

    def _set_busy(self, busy: bool) -> None:
        self._combo.setEnabled(not busy)
        self._btn_open.setEnabled(not busy)
        self._btn_open_batch.setEnabled(not busy)
        self._btn_run.setEnabled(not busy)
        self._btn_export.setEnabled(not busy)

    def _load_variant(self, variant: str) -> None:
        if variant == self._current_variant and self._model is not None:
            return

        config_path, checkpoint_path = resolve_variant_paths(variant)
        if checkpoint_path is None or not checkpoint_path.is_file():
            QMessageBox.warning(
                self,
                "Модель недоступна",
                format_error(
                    E005_INFERENCE_FAILED,
                    f"Нет весов для «{variant_display_name(variant)}».",
                ),
            )
            return

        self._set_busy(True)
        self._set_status(f"Загрузка модели: {variant_display_name(variant)}")
        try:
            if variant not in self._model_cache:
                model, classes, cfg, device = load_artifacts(config_path, checkpoint_path, self._device)
                tcfg = cfg["train"]
                tf = preprocess_eval(int(tcfg["image_size"]), bool(tcfg["strong_augment"]))
                self._model_cache[variant] = (model, classes, cfg, tf)
            self._model, self._classes, self._cfg, self._tf = self._model_cache[variant]
            self._current_variant = variant
            self._clear_results()
            self._set_status(f"Активная модель: {variant_display_name(variant)}")
        except Exception as exc:
            self._set_status("")
            QMessageBox.critical(
                self,
                "Ошибка загрузки",
                format_error(E005_INFERENCE_FAILED, str(exc)),
            )
        finally:
            self._set_busy(False)

    def _on_variant_changed(self, _index: int) -> None:
        variant = self._combo.currentData()
        if not variant or variant == self._current_variant:
            return
        self._load_variant(str(variant))

    def _validate_extension(self, path: Path) -> bool:
        if path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
            QMessageBox.warning(self, "Формат файла", format_error(E002_UNSUPPORTED_FORMAT, path.name))
            return False
        return True

    def _show_preview(self, path: Path) -> None:
        pix = QPixmap(str(path))
        if pix.isNull():
            QMessageBox.warning(self, "Ошибка", format_error(E003_IMAGE_READ_FAILED, path.name))
            return
        self._preview.setPixmap(
            pix.scaled(480, 360, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        )

    def _on_open_single(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите изображение",
            "",
            "Изображения (*.png *.jpg *.jpeg *.bmp)",
        )
        if not path:
            return
        p = Path(path)
        if not self._validate_extension(p):
            return
        self._image_paths = [p]
        self._show_preview(p)
        self._set_status(f"Загружено изображений: 1")

    def _on_open_batch(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Выберите серию изображений",
            "",
            "Изображения (*.png *.jpg *.jpeg *.bmp)",
        )
        if not paths:
            return
        valid = []
        for raw in paths:
            p = Path(raw)
            if self._validate_extension(p):
                valid.append(p)
        if not valid:
            return
        self._image_paths = valid
        self._show_preview(valid[0])
        self._set_status(f"Загружено изображений: {len(valid)}")

    def _on_analyze(self) -> None:
        if self._model is None or self._tf is None:
            QMessageBox.information(self, "Подсказка", "Выберите доступную культуру.")
            return
        if not self._image_paths:
            QMessageBox.information(self, "Подсказка", "Сначала загрузите изображение или серию.")
            return

        self._set_busy(True)
        try:
            preds: list[dict] = []
            formatted: list[dict] = []
            for path in self._image_paths:
                img = Image.open(path)
                pr = predict_image(self._model, self._classes, img, self._tf, self._device, topk=5)
                ink = classification_uncertainty_index(
                    np.asarray(pr["probs"], dtype=np.float64), float(pr["top1_prob"])
                )
                pr["ink"] = ink
                pr["path"] = str(path)
                preds.append(pr)
                formatted.append(format_single_result(pr, str(path)))

            self._last_predictions = formatted
            active = formatted[0]
            self._lbl_class.setText(active["class_ru"])
            self._lbl_conf.setText(f"{active['confidence_pct']:.1f}")
            self._lbl_ink.setText(f"{active['ink_pct']:.1f}")

            self._table.setRowCount(0)
            for i, (name_ru, name_id, prob) in enumerate(active["topk"]):
                self._table.insertRow(i)
                self._table.setItem(i, 0, QTableWidgetItem(name_ru))
                self._table.setItem(i, 1, QTableWidgetItem(name_id))
                self._table.setItem(i, 2, QTableWidgetItem(f"{prob:.2f}"))
            self._table.resizeColumnsToContents()

            assessment = score_trial(preds, self._cfg["resistance"])
            self._lbl_ifs.setText(
                f"ИФС: {assessment.phytosanitary_index:.1f} / 100\n{assessment.summary}"
            )
            self._set_status(f"Классификация выполнена для {len(self._image_paths)} изображений.")
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", format_error(E005_INFERENCE_FAILED, str(exc)))
        finally:
            self._set_busy(False)

    def _on_export(self) -> None:
        if not self._last_predictions:
            QMessageBox.information(self, "Подсказка", "Сначала выполните классификацию.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить отчёт",
            "askabr_report.txt",
            "Текстовый отчёт (*.txt)",
        )
        if not path:
            return
        try:
            assessment = None
            if len(self._image_paths) > 0 and self._cfg:
                preds = []
                for item in self._last_predictions:
                    preds.append(
                        {
                            "top_class": item["class_id"],
                            "top1_prob": item["confidence_pct"] / 100.0,
                            "probs": None,
                        }
                    )
                assessment = score_trial(preds, self._cfg["resistance"])
            export_report_txt(
                Path(path),
                variant_label=variant_display_name(self._current_variant or ""),
                single_results=self._last_predictions,
                batch_assessment=assessment,
            )
            self._set_status(f"Отчёт сохранён: {path}")
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", format_error(E007_EXPORT_FAILED, str(exc)))
