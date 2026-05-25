from __future__ import annotations

"""Преобразования изображений для обучения и валидации."""

import torchvision.transforms as T


def build_transforms(image_size: int, strong_augment: bool):
    """Возвращает (train_transform, val_transform) для RGB-изображений."""
    normalize = T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])

    val = T.Compose(
        [
            T.Resize(int(image_size * 1.15)),
            T.CenterCrop(image_size),
            T.ToTensor(),
            normalize,
        ]
    )

    base = [
        T.RandomResizedCrop(image_size, scale=(0.65, 1.0)),
        T.RandomHorizontalFlip(),
        T.ColorJitter(brightness=0.35, contrast=0.35, saturation=0.25, hue=0.04),
        T.RandomAffine(degrees=25, translate=(0.08, 0.08), scale=(0.85, 1.15)),
    ]
    if strong_augment:
        base.extend(
            [
                T.RandomPerspective(distortion_scale=0.25, p=0.35),
                T.GaussianBlur(kernel_size=3, sigma=(0.1, 1.2)),
            ]
        )
    base.extend([T.ToTensor(), normalize])
    train = T.Compose(base)
    return train, val
