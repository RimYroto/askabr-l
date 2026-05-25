#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Вспомогательный веб-интерфейс демонстрации (Gradio). Не входит в основной дистрибутив GUI."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import gradio as gr
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from askabr.assessment.phytosanitary_index import score_trial
from askabr.classification.predict import load_artifacts, predict_image, preprocess_eval


def build_ui(config_path: Path, checkpoint_path: Path) -> gr.Blocks:
    model, classes, cfg, device = load_artifacts(config_path, checkpoint_path)
    tcfg = cfg["train"]
    tf = preprocess_eval(int(tcfg["image_size"]), bool(tcfg["strong_augment"]))

    def run(files: list | str | None):
        if not files:
            return "Загрузите одно или несколько изображений.", ""
        if not isinstance(files, list):
            files = [files]
        preds = []
        lines = []
        for f in files:
            path = Path(f if isinstance(f, (str, Path)) else getattr(f, "name", f))
            img = Image.open(path)
            pr = predict_image(model, classes, img, tf, device, topk=5)
            preds.append(pr)
            top = ", ".join(f"{n}: {p:.3f}" for n, p in pr["topk"])
            lines.append(f"{path.name}: **{pr['top_class']}** (top-1={pr['top1_prob']:.3f})  \n{top}")
        trial = score_trial(preds, cfg["resistance"])
        summary = trial.summary
        return "\n\n".join(lines), summary

    with gr.Blocks(title="АСКАБР-Л — демонстрация") as demo:
        gr.Markdown(
            "### Классификация и расчёт ИФС по серии снимков\n"
            "Вспомогательный модуль демонстрации. Основной продукт — десктопное приложение."
        )
        files = gr.File(label="Изображения", file_count="multiple", type="filepath")
        btn = gr.Button("Выполнить классификацию")
        preds_md = gr.Markdown()
        trial_md = gr.Markdown()
        btn.click(run, inputs=[files], outputs=[preds_md, trial_md])
    return demo


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=PROJECT_ROOT / "configs" / "default.yaml")
    parser.add_argument("--checkpoint", type=Path, default=PROJECT_ROOT / "artifacts" / "best.pt")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=7860)
    args = parser.parse_args()

    if not args.checkpoint.is_file():
        raise SystemExit(
            f"Нет чекпоинта: {args.checkpoint}. Сначала обучите модель "
            f"(askabr-train --config configs/smoke.yaml)."
        )
    demo = build_ui(args.config, args.checkpoint)
    demo.launch(server_name=args.host, server_port=args.port)


if __name__ == "__main__":
    main()
