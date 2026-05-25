# -*- coding: utf-8 -*-

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_smoke_test_cli_exits_zero():
    missing = []
    for variant in ("tomato", "pear"):
        variant_dir = ROOT / "models" / variant
        has_pt = (variant_dir / "model_v1.0.0.pt").is_file() or (variant_dir / "best.pt").is_file()
        if not has_pt:
            missing.append(variant)
    if missing:
        pytest.skip(f"model weights missing: {missing}")

    result = subprocess.run(
        [sys.executable, str(ROOT / "gui" / "run_app.py"), "--smoke-test"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert "ASKABR-L smoke OK" in result.stdout
