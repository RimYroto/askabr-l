#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Оценка macro-F1 и точности на holdout (не участвовал в обучении)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch
import yaml
from sklearn.metrics import classification_report, f1_score
from torch.utils.data import DataLoader
from torchvision import datasets

from askabr.core.paths import project_root

from askabr.classification.augment import build_transforms
from askabr.classification.model import build_model
from askabr.training.train import host_tensor_to_device


def pick_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


@torch.no_grad()
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=project_root() / "configs" / "plantvillage_local.yaml")
    parser.add_argument("--checkpoint", type=Path, default=project_root() / "artifacts" / "best.pt")
    args = parser.parse_args()

    cfg = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    resolved = args.checkpoint.parent / "config_resolved.yaml"
    if resolved.is_file():
        cfg = yaml.safe_load(resolved.read_text(encoding="utf-8"))

    hold = project_root() / Path(cfg["paths"]["holdout_root"])
    _, val_tf = build_transforms(int(cfg["train"]["image_size"]), bool(cfg["train"]["strong_augment"]))
    ds = datasets.ImageFolder(str(hold), transform=val_tf)
    nw = int(cfg["train"].get("num_workers", 2))
    pin = torch.cuda.is_available()
    dl_kw: dict = {"pin_memory": pin}
    if nw > 0:
        dl_kw["persistent_workers"] = True
        dl_kw["prefetch_factor"] = max(2, int(cfg["train"].get("prefetch_factor", 4)))
    loader = DataLoader(
        ds,
        batch_size=int(cfg["train"]["batch_size"]),
        shuffle=False,
        num_workers=nw,
        **dl_kw,
    )

    device = pick_device()
    num_classes = len(ds.classes)
    model = build_model(cfg["model"]["backbone"], bool(cfg["model"]["pretrained"]), num_classes).to(device)
    model.load_state_dict(torch.load(args.checkpoint, map_location=device))
    model.eval()

    ys: list[int] = []
    ps: list[int] = []
    for x, y in loader:
        x = host_tensor_to_device(x, device)
        if device.type == "cuda":
            with torch.amp.autocast("cuda", enabled=True):
                logits = model(x)
        elif device.type == "mps":
            try:
                with torch.autocast(device_type="mps", dtype=torch.float16):
                    logits = model(x)
            except Exception:
                logits = model(x)
        else:
            logits = model(x)
        pred = logits.float().argmax(dim=1).cpu().tolist()
        ys.extend(y.tolist())
        ps.extend(pred)

    acc = sum(int(a == b) for a, b in zip(ys, ps)) / max(len(ys), 1)
    f1m = float(f1_score(ys, ps, average="macro", zero_division=0))
    rep = classification_report(ys, ps, target_names=ds.classes, digits=4, zero_division=0)
    out = args.checkpoint.parent / "holdout_report.txt"
    out.write_text(f"accuracy={acc:.6f}\nmacro_f1={f1m:.6f}\n\n{rep}", encoding="utf-8")
    print(out.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
