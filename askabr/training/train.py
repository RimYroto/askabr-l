from __future__ import annotations

import argparse
import copy
import os
from pathlib import Path

import torch
import torch.nn as nn
import yaml
from sklearn.metrics import f1_score
from tqdm import tqdm

from askabr.classification.model import build_model
from askabr.core.constants import (
    EARLY_STOP_MIN_MACRO_F1,
    EARLY_STOP_PLATEAU_EPOCHS,
    LEGACY_MODEL_FILENAME,
    MODEL_SELECTION_ACC_WEIGHT,
    PLATEAU_F1_DELTA,
)
from askabr.core.paths import project_root, torch_cache_dir
from askabr.training.data import DataConfig, build_disjoint_dataloaders, build_dataloaders, save_label_map


def pick_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def host_tensor_to_device(t: torch.Tensor, device: torch.device) -> torch.Tensor:
    nb = device.type == "cuda" and t.is_pinned()
    return t.to(device, non_blocking=nb)


def _mps_autocast_enabled(device: torch.device, cfg_flag: bool) -> bool:
    if device.type != "mps" or not cfg_flag:
        return False
    try:
        with torch.autocast(device_type="mps", dtype=torch.float16):
            _ = torch.zeros(2, 2, device="mps")
        return True
    except Exception:
        return False


def _class_weights_from_folder(train_root: Path, num_classes: int) -> torch.Tensor:
    from torchvision import datasets

    ds = datasets.ImageFolder(str(train_root), transform=None)
    counts = torch.zeros(num_classes, dtype=torch.float64)
    for _, y in ds.samples:
        counts[y] += 1.0
    counts = torch.clamp(counts, min=1.0)
    w = counts.sum() / (counts * float(num_classes))
    w = w / w.mean()
    return w.float()


@torch.no_grad()
def evaluate(
    model: nn.Module,
    loader,
    device: torch.device,
    crit: nn.Module,
    use_amp_cuda: bool,
    use_autocast_mps: bool,
) -> tuple[float, float, float]:
    del use_autocast_mps
    model.eval()
    correct = 0
    total = 0
    loss_sum = 0.0
    ys: list[int] = []
    preds: list[int] = []
    for x, y in loader:
        x = host_tensor_to_device(x, device)
        y = host_tensor_to_device(y, device)
        if use_amp_cuda:
            with torch.amp.autocast("cuda", enabled=True):
                logits = model(x)
        else:
            logits = model(x)
        logits = logits.float()
        loss_sum += crit(logits, y).item() * x.size(0)
        pred = logits.argmax(dim=1)
        correct += (pred == y).sum().item()
        total += x.size(0)
        ys.extend(y.detach().cpu().tolist())
        preds.extend(pred.detach().cpu().tolist())
    acc = correct / max(total, 1)
    f1 = float(f1_score(ys, preds, average="macro", zero_division=0))
    return loss_sum / max(total, 1), acc, f1


def main() -> None:
    parser = argparse.ArgumentParser(description="Обучение классификатора болезней растений (АСКАБР-Л).")
    parser.add_argument("--config", type=Path, default=project_root() / "configs" / "default.yaml")
    args = parser.parse_args()

    root = project_root()
    torch_home = torch_cache_dir()
    os.environ.setdefault("TORCH_HOME", str(torch_home))

    raw_cfg = yaml.safe_load(args.config.read_text(encoding="utf-8"))

    artifacts_dir = root / Path(raw_cfg["artifacts_dir"])
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    tcfg = raw_cfg["train"]
    mcfg = raw_cfg["model"]
    paths = raw_cfg.get("paths") or {}
    train_root_cfg = paths.get("train_root")
    val_root_cfg = paths.get("val_root")

    if train_root_cfg and val_root_cfg:
        train_root = root / Path(train_root_cfg)
        val_root = root / Path(val_root_cfg)
        train_loader, val_loader, classes = build_disjoint_dataloaders(
            train_root,
            val_root,
            int(tcfg["image_size"]),
            int(tcfg["batch_size"]),
            int(tcfg["num_workers"]),
            bool(tcfg["strong_augment"]),
            prefetch_factor=int(tcfg.get("prefetch_factor", 4)),
        )
    else:
        data_root = root / Path(raw_cfg["data_root"])
        dcfg = DataConfig(
            data_root=data_root,
            image_size=int(tcfg["image_size"]),
            batch_size=int(tcfg["batch_size"]),
            num_workers=int(tcfg["num_workers"]),
            train_ratio=float(raw_cfg["train_ratio"]),
            seed=int(raw_cfg["seed"]),
            strong_augment=bool(tcfg["strong_augment"]),
            prefetch_factor=int(tcfg.get("prefetch_factor", 4)),
        )
        train_loader, val_loader, classes = build_dataloaders(dcfg)

    num_classes = len(classes)
    resolved = copy.deepcopy(raw_cfg)
    resolved["model"]["num_classes"] = num_classes
    (artifacts_dir / "config_resolved.yaml").write_text(
        yaml.safe_dump(resolved, sort_keys=False), encoding="utf-8"
    )
    save_label_map(classes, artifacts_dir / "labels.json")

    device = pick_device()
    print(f"Устройство: {device}")

    model = build_model(
        mcfg["backbone"],
        bool(mcfg["pretrained"]),
        num_classes,
    ).to(device)

    if bool(tcfg.get("torch_compile", False)) and hasattr(torch, "compile"):
        try:
            model = torch.compile(model)  # type: ignore[assignment]
            print("Включён torch.compile.")
        except Exception as exc:  # noqa: BLE001
            print(f"torch.compile пропущен: {exc}")

    ls = float(tcfg.get("label_smoothing", 0.0))
    weight = None
    if bool(tcfg.get("use_class_weights", False)) and train_root_cfg:
        tr = root / Path(train_root_cfg)
        weight = _class_weights_from_folder(tr, num_classes).to(device)
    crit = nn.CrossEntropyLoss(weight=weight, label_smoothing=ls)

    optim = torch.optim.AdamW(
        model.parameters(),
        lr=float(tcfg["lr"]),
        weight_decay=float(tcfg["weight_decay"]),
    )

    epochs = int(tcfg["epochs"])
    sched_kind = str(tcfg.get("scheduler", "none")).lower()
    scheduler = None
    if sched_kind == "cosine":
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optim, T_max=epochs)

    use_amp_cuda = bool(tcfg.get("amp", False)) and device.type == "cuda"
    scaler = torch.amp.GradScaler("cuda", enabled=use_amp_cuda)
    amp_mps_cfg = bool(tcfg.get("amp_mps", True))
    use_autocast_mps = _mps_autocast_enabled(device, amp_mps_cfg)
    if device.type == "mps":
        print(f"MPS autocast (float16): {'да' if use_autocast_mps else 'нет'}")

    best_score = -1.0
    best_state = None
    best_epoch = 0
    plateau = 0
    last_f1 = -1.0

    no_tqdm = bool(tcfg.get("no_tqdm", False))
    total_batches = len(train_loader)

    for epoch in range(1, epochs + 1):
        model.train()
        batch_iter = train_loader if no_tqdm else tqdm(train_loader, desc=f"эпоха {epoch}/{epochs}")

        for bi, (x, y) in enumerate(batch_iter, start=1):
            x = host_tensor_to_device(x, device)
            y = host_tensor_to_device(y, device)
            optim.zero_grad(set_to_none=True)
            if use_amp_cuda:
                with torch.amp.autocast("cuda", enabled=True):
                    logits = model(x)
                    loss = crit(logits, y)
                scaler.scale(loss).backward()
                scaler.step(optim)
                scaler.update()
            elif use_autocast_mps:
                with torch.autocast(device_type="mps", dtype=torch.float16):
                    logits = model(x)
                loss = crit(logits.float(), y)
                loss.backward()
                optim.step()
            else:
                logits = model(x)
                loss = crit(logits, y)
                loss.backward()
                optim.step()
            if no_tqdm:
                step = max(1, total_batches // 12)
                if bi == 1 or bi % step == 0 or bi == total_batches:
                    print(f"  батч {bi}/{total_batches} loss={float(loss.item()):.4f}", flush=True)
            else:
                batch_iter.set_postfix(loss=float(loss.item()))

        val_loss, val_acc, val_f1 = evaluate(
            model, val_loader, device, crit, use_amp_cuda, use_autocast_mps
        )
        if scheduler is not None:
            scheduler.step()

        score = val_f1 + MODEL_SELECTION_ACC_WEIGHT * val_acc
        print(f"эпоха {epoch}: val_loss={val_loss:.4f} val_acc={val_acc:.4f} macro_f1={val_f1:.4f}")

        if val_f1 > last_f1 + PLATEAU_F1_DELTA:
            plateau = 0
        else:
            plateau += 1
        last_f1 = val_f1

        if score > best_score:
            best_score = score
            best_state = copy.deepcopy(model.state_dict())
            best_epoch = epoch
            (artifacts_dir / "val_metrics.txt").write_text(
                f"лучшая_эпоха={best_epoch}\nval_acc={val_acc:.6f}\nmacro_f1={val_f1:.6f}\nval_loss={val_loss:.6f}\n",
                encoding="utf-8",
            )

        if plateau >= EARLY_STOP_PLATEAU_EPOCHS and val_f1 >= EARLY_STOP_MIN_MACRO_F1:
            print("Ранняя остановка: плато macro-F1 при высоком качестве на валидации.")
            break

    if best_state is None:
        best_state = model.state_dict()
    ckpt_path = artifacts_dir / LEGACY_MODEL_FILENAME
    torch.save(best_state, ckpt_path)
    print(f"Сохранено: {ckpt_path} (лучший балл≈{best_score:.4f}, эпоха {best_epoch})")


if __name__ == "__main__":
    main()
