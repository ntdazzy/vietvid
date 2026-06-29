"""Mã hoá secret cấu hình (key thanh toán) trước khi lưu DB — Fernet (AES128-CBC + HMAC).

Master key từ ENV `VIETVID_CONFIG_SECRET` (chuỗi bất kỳ → dẫn xuất 32-byte qua SHA256).
DB bị dump cũng vô dụng nếu không có master key. Chưa đặt key → unconfigured (secret đọc env).
"""

from __future__ import annotations

import base64
import hashlib
import os

from cryptography.fernet import Fernet, InvalidToken

_SECRET = os.environ.get("VIETVID_CONFIG_SECRET", "").strip()
_PREFIX = "enc:v1:"  # đánh dấu giá trị đã mã hoá để phân biệt plaintext/env


def configured() -> bool:
    return bool(_SECRET)


def _fernet() -> Fernet:
    key = base64.urlsafe_b64encode(hashlib.sha256(_SECRET.encode()).digest())
    return Fernet(key)


def seal(plaintext: str) -> str:
    """Mã hoá 1 secret để lưu DB. Trả 'enc:v1:<token>'. Yêu cầu configured()."""
    if not _SECRET:
        raise RuntimeError("VIETVID_CONFIG_SECRET chưa đặt — không thể mã hoá secret.")
    if not plaintext:
        return ""
    return _PREFIX + _fernet().encrypt(plaintext.encode()).decode()


def unseal(value: str) -> str:
    """Giải mã giá trị từ DB. Không phải dạng mã hoá → trả nguyên (tương thích plaintext cũ)."""
    if not value or not value.startswith(_PREFIX):
        return value or ""
    if not _SECRET:
        return ""  # có token mã hoá nhưng mất master key → coi như rỗng
    try:
        return _fernet().decrypt(value[len(_PREFIX):].encode()).decode()
    except InvalidToken:
        return ""


def is_sealed(value: str) -> bool:
    return bool(value) and value.startswith(_PREFIX)
