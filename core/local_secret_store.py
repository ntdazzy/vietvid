"""Local encrypted secret helpers for workstation-only browser QA data.

The dashboard may accept raw values in requests, but persisted local QA
credentials must be encrypted and API responses must expose only configured
flags. This module never logs plaintext or encrypted blobs.
"""

from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from config.settings import settings
from core.config_checks import looks_real_secret

LOCAL_SECRET_PREFIX = "local-fernet:v1:"
MIN_SESSION_SECRET_LENGTH = 32


class LocalSecretStoreError(ValueError):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail

    def __str__(self) -> str:
        return self.detail


def derive_fernet_key(secret: str) -> bytes:
    """Derive a Fernet key from a normal dashboard session secret."""
    cleaned = str(secret or "").strip()
    if not looks_real_secret(cleaned, min_length=MIN_SESSION_SECRET_LENGTH):
        raise LocalSecretStoreError(
            "LOCAL_SECRET_KEY_NOT_READY",
            "DASHBOARD_SESSION_SECRET is missing, weak, or still a placeholder.",
        )
    digest = hashlib.sha256(cleaned.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def encrypt_local_secret(value: str, *, secret: str | None = None) -> str:
    """Encrypt a local secret value for DB storage."""
    plaintext = str(value or "")
    if plaintext == "":
        return ""
    fernet = Fernet(
        derive_fernet_key(settings.dashboard_session_secret if secret is None else secret)
    )
    token = fernet.encrypt(plaintext.encode("utf-8")).decode("ascii")
    return LOCAL_SECRET_PREFIX + token


def decrypt_local_secret(value: str, *, secret: str | None = None) -> str:
    """Decrypt a local secret value from DB storage."""
    encrypted = str(value or "")
    if encrypted == "":
        return ""
    if not encrypted.startswith(LOCAL_SECRET_PREFIX):
        raise LocalSecretStoreError(
            "LOCAL_SECRET_FORMAT_UNSUPPORTED",
            "Local secret has an unsupported encrypted format.",
        )
    token = encrypted[len(LOCAL_SECRET_PREFIX) :].encode("ascii")
    fernet = Fernet(
        derive_fernet_key(settings.dashboard_session_secret if secret is None else secret)
    )
    try:
        return fernet.decrypt(token).decode("utf-8")
    except (InvalidToken, UnicodeDecodeError) as exc:
        raise LocalSecretStoreError(
            "SECRET_KEY_MISMATCH",
            "Cannot decrypt local secret; check DASHBOARD_SESSION_SECRET.",
        ) from exc


def secret_configured(value: str | None) -> bool:
    return bool(str(value or "").strip())


def redact_secret_label(value: str | None) -> str:
    return "CONFIGURED" if secret_configured(value) else "NOT_CONFIGURED"


__all__ = [
    "LOCAL_SECRET_PREFIX",
    "LocalSecretStoreError",
    "decrypt_local_secret",
    "derive_fernet_key",
    "encrypt_local_secret",
    "redact_secret_label",
    "secret_configured",
]
