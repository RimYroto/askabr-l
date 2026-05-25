from __future__ import annotations

import torch.nn as nn
from torchvision import models


def build_model(backbone: str, pretrained: bool, num_classes: int) -> nn.Module:
    """Сборка свёрточной нейронной сети с заменой выходного слоя."""
    if backbone == "resnet18":
        weights = models.ResNet18_Weights.IMAGENET1K_V1 if pretrained else None
        m = models.resnet18(weights=weights)
        in_f = m.fc.in_features
        m.fc = nn.Linear(in_f, num_classes)
        return m
    if backbone == "resnet50":
        weights = models.ResNet50_Weights.IMAGENET1K_V2 if pretrained else None
        m = models.resnet50(weights=weights)
        in_f = m.fc.in_features
        m.fc = nn.Linear(in_f, num_classes)
        return m
    if backbone == "efficientnet_b0":
        w = models.EfficientNet_B0_Weights.IMAGENET1K_V1 if pretrained else None
        m = models.efficientnet_b0(weights=w)
        head = m.classifier[1]
        in_f = head.in_features
        m.classifier[1] = nn.Linear(in_f, num_classes)
        return m
    if backbone == "mobilenet_v3_small":
        w = models.MobileNet_V3_Small_Weights.IMAGENET1K_V1 if pretrained else None
        m = models.mobilenet_v3_small(weights=w)
        in_f = m.classifier[3].in_features
        m.classifier[3] = nn.Linear(in_f, num_classes)
        return m
    raise ValueError(f"Неизвестная архитектура backbone: {backbone}")
