"""Shared checks for production-facing configuration values."""

from __future__ import annotations

from urllib.parse import urlparse


_PLACEHOLDER_MARKERS = ("<", ">", "dien_", "your_", "example", "placeholder", "changeme")
_LOCAL_HOSTS = {"localhost", "0.0.0.0", "::1"}
_RESERVED_HOST_SUFFIXES = (".example", ".invalid", ".localhost", ".test")


def looks_real_secret(value: str, *, min_length: int = 6) -> bool:
    stripped = (value or "").strip()
    if len(stripped) < min_length:
        return False
    lowered = stripped.lower()
    return not any(marker in lowered for marker in _PLACEHOLDER_MARKERS)


def looks_real_url(value: str) -> bool:
    stripped = (value or "").strip()
    if not stripped.startswith("https://"):
        return False
    if is_local_url(stripped) or is_reserved_test_url(stripped):
        return False
    return looks_real_secret(stripped)


def is_local_url(value: str) -> bool:
    host = (urlparse((value or "").strip()).hostname or "").lower()
    return host in _LOCAL_HOSTS or host.startswith("127.")


def is_reserved_test_url(value: str) -> bool:
    host = (urlparse((value or "").strip()).hostname or "").lower()
    return host.endswith(_RESERVED_HOST_SUFFIXES)
