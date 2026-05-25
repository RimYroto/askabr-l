from __future__ import annotations

"""Загрузка модели и инференс по изображениям."""

import os
from pathlib import Path
from typing import Any

import numpy as np
import torch
import yaml
from PIL import Image

from askabr.classification.augment import build_transforms
from askabr.classification.model import build_model
from askabr.core.paths import torch_cache_dir
from askabr.training.data import load_label_map


def pick_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def _forward_for_inference(model: torch.nn.Module, x: torch.Tensor, device: torch.device) -> torch.Tensor:
    if device.type == "cuda":
        with torch.amp.autocast("cuda", enabled=True):
            return model(x)
    if device.type == "mps":
        try:
            with torch.autocast(device_type="mps", dtype=torch.float16):
                return model(x)
        except Exception:
            return model(x)
    return model(x)


def load_artifacts(
    config_path: Path,
    checkpoint_path: Path,
    device: torch.device | None = None,
) -> tuple[torch.nn.Module, list[str], dict[str, Any], torch.device]:
    """Загружает конфигурацию, веса и возвращает готовую модель."""
    torch_home = torch_cache_dir()
    os.environ.setdefault("TORCH_HOME", str(torch_home))

    device = device or pick_device()
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    resolved_ckpt_cfg = checkpoint_path.parent / "config_resolved.yaml"
    if resolved_ckpt_cfg.is_file():
        cfg = yaml.safe_load(resolved_ckpt_cfg.read_text(encoding="utf-8"))

    classes, _ = load_label_map(checkpoint_path.parent / "labels.json")
    num_classes = len(classes)
    model = build_model(
        cfg["model"]["backbone"],
        bool(cfg["model"]["pretrained"]),
        num_classes,
    ).to(device)
    state = torch.load(checkpoint_path, map_location=device, weights_only=True)
    model.load_state_dict(state)
    model.eval()
    return model, classes, cfg, device


def preprocess_eval(image_size: int, strong_augment: bool):
    """Пайплайн предобработки, совпадающий с валидацией при обучении."""
    _, val_tf = build_transforms(image_size, strong_augment)
    return val_tf


@torch.no_grad()
def predict_image(
    model: torch.nn.Module,
    classes: list[str],
    image: Image.Image,
    tf,
    device: torch.device,
    topk: int = 5,
) -> dict[str, Any]:
    """Классификация одного изображения."""
    x = tf(image.convert("RGB")).unsqueeze(0).to(device)
    logits = _forward_for_inference(model, x, device)[0].float()
    probs = torch.softmax(logits, dim=0).detach().cpu().numpy()
    topk = min(topk, len(classes))
    idx = np.argsort(-probs)[:topk]
    return {
        "top_class": classes[int(idx[0])],
        "top1_prob": float(probs[idx[0]]),
        "topk": [(classes[int(i)], float(probs[i])) for i in idx],
        "probs": probs,
    }


def predict_paths(
    model: torch.nn.Module,
    classes: list[str],
    paths: list[Path],
    tf,
    device: torch.device,
    topk: int = 5,
) -> list[dict[str, Any]]:
    """Пакетная классификация по списку путей."""
    out = []
    for p in paths:
        img = Image.open(p)
        pred = predict_image(model, classes, img, tf, device, topk=topk)
        pred["path"] = str(p)
        out.append(pred)
    return out
