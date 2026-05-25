# -*- coding: utf-8 -*-
"""PyInstaller runtime hooks: SSL, PyQt6 plugins, ASCII-safe temp dirs."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _has_non_ascii(text: str) -> bool:
    return any(ord(ch) > 127 for ch in text)


def _configure_ssl() -> None:
    try:
        import certifi
    except ImportError:
        return

    cafile = certifi.where()
    os.environ.setdefault("SSL_CERT_FILE", cafile)
    os.environ.setdefault("REQUESTS_CA_BUNDLE", cafile)

    import ssl

    def _default_context() -> ssl.SSLContext:
        return ssl.create_default_context(cafile=cafile)

    ssl._create_default_https_context = _default_context  # type: ignore[attr-defined]


def _configure_qt_plugins() -> None:
    if not getattr(sys, "frozen", False):
        return
    base = Path(getattr(sys, "_MEIPASS", ""))
    if not base.is_dir():
        return

    for rel in (
        "PyQt6/Qt6/plugins",
        "PyQt6/Qt/plugins",
        "qt6/plugins",
    ):
        plugin_dir = base / rel
        if plugin_dir.is_dir():
            os.environ["QT_PLUGIN_PATH"] = str(plugin_dir)
            platforms = plugin_dir / "platforms"
            if platforms.is_dir():
                os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", str(platforms))
            break


def _configure_ascii_temp() -> None:
    if not getattr(sys, "frozen", False):
        return

    profile = os.environ.get("USERPROFILE", "")
    local_app = os.environ.get("LOCALAPPDATA", "")
    needs_ascii = _has_non_ascii(profile) or _has_non_ascii(local_app)

    program_data = os.environ.get("ProgramData", r"C:\ProgramData")
    runtime_root = Path(program_data) / "ASKABR-L" / "runtime"
    runtime_root.mkdir(parents=True, exist_ok=True)

    if needs_ascii or _has_non_ascii(os.environ.get("TEMP", "")):
        extract_dir = runtime_root / "onefile-extract"
        extract_dir.mkdir(parents=True, exist_ok=True)
        os.environ["TEMP"] = str(extract_dir)
        os.environ["TMP"] = str(extract_dir)
        os.environ.setdefault("ASKABR_RUNTIME_DIR", str(extract_dir))


_configure_ssl()
_configure_qt_plugins()
_configure_ascii_temp()
