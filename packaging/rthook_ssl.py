# -*- coding: utf-8 -*-
"""PyInstaller runtime hook: CA bundle for HTTPS on Windows."""

from __future__ import annotations

import os
import ssl


def _configure() -> None:
    try:
        import certifi
    except ImportError:
        return

    cafile = certifi.where()
    os.environ.setdefault("SSL_CERT_FILE", cafile)
    os.environ.setdefault("REQUESTS_CA_BUNDLE", cafile)

    def _default_context() -> ssl.SSLContext:
        return ssl.create_default_context(cafile=cafile)

    ssl._create_default_https_context = _default_context  # type: ignore[attr-defined]


_configure()
