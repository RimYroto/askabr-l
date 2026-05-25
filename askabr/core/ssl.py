# -*- coding: utf-8 -*-
"""Настройка доверенных CA для HTTPS (типичная проблема на Windows)."""

from __future__ import annotations

import os
import ssl


def configure_ssl_certificates() -> None:
    """Подключает пакет certifi, если он установлен.

    На Windows «голый» Python часто не видит корневые сертификаты ОС, из‑за чего
    падают uv/pip, torchvision и другие HTTPS-загрузки.
    """
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
