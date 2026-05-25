from __future__ import annotations

import json
from pathlib import Path

from askabr.core.constants import LEGACY_VARIANT_ALIASES
from askabr.core.paths import model_variant_dir, models_root, project_root, resolve_checkpoint_path, resource_path


_FALLBACK_CONFIG = {
    "tomato": "tomato_only.yaml",
    "pear": "pear_only.yaml",
    "multicrop": "plantvillage_local.yaml",
    "full": "plantvillage_local.yaml",
}


def _manifest_path() -> Path:
    path = resource_path("gui", "plant_variants.json")
    if path.is_file():
        return path
    return Path(__file__).resolve().parent / "plant_variants.json"


def load_variant_manifest() -> dict[str, dict]:
    path = _manifest_path()
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_variant_id(variant: str) -> str:
    return LEGACY_VARIANT_ALIASES.get(variant, variant)


def variant_display_name(variant: str) -> str:
    variant = normalize_variant_id(variant)
    manifest = load_variant_manifest()
    entry = manifest.get(variant)
    if entry and entry.get("label_ru"):
        return str(entry["label_ru"])
    return variant


def resolve_variant_paths(variant: str) -> tuple[Path, Path | None]:
    variant = normalize_variant_id(variant)
    variant_dir = model_variant_dir(variant)
    config = variant_dir / "config_resolved.yaml"
    checkpoint = resolve_checkpoint_path(variant_dir)
    if not config.is_file():
        fallback_name = _FALLBACK_CONFIG.get(variant, "default.yaml")
        fallback = project_root() / "configs" / fallback_name
        if fallback.is_file():
            config = fallback
    return config, checkpoint


def available_variants() -> list[str]:
    """Варианты моделей с развёрнутым файлом весов в models/<variant>/."""
    manifest = load_variant_manifest()
    root = models_root()
    if not root.is_dir():
        return []

    ordered_ids = sorted(
        manifest.keys(),
        key=lambda key: int(manifest[key].get("order", 999)),
    )
    seen: set[str] = set()
    out: list[str] = []
    for variant in ordered_ids:
        if variant in seen:
            continue
        if resolve_checkpoint_path(model_variant_dir(variant)) is not None:
            out.append(variant)
            seen.add(variant)

    for path in sorted(root.iterdir()):
        if not path.is_dir():
            continue
        variant = path.name
        if variant in seen:
            continue
        if resolve_checkpoint_path(path) is not None:
            out.append(variant)
            seen.add(variant)
    return out
