"""Ký URL media (Sóng 2) — cho phép <video src> phát/chia sẻ KHÔNG cần Bearer header.

Token = HMAC-SHA256 của (job_id, org_id, exp) bằng DEV_JWT_SECRET. Hết hạn sau MEDIA_URL_TTL.
Cấp qua endpoint authed (chủ job), tiêu thụ ở endpoint public /v1/media/video/{job_id}?token=.
"""

from __future__ import annotations

import base64
import datetime as _dt
import hashlib
import hmac

from app_api import config


def _secret() -> bytes:
    return (config.DEV_JWT_SECRET or "vietvid-media").encode("utf-8")


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _unb64(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def sign_media_token(job_id: str, org_id: str, *, ttl: int | None = None) -> str:
    exp = int(
        (_dt.datetime.now(tz=_dt.timezone.utc)
         + _dt.timedelta(seconds=ttl if ttl is not None else config.MEDIA_URL_TTL)).timestamp()
    )
    msg = f"{job_id}:{org_id}:{exp}"
    sig = hmac.new(_secret(), msg.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{_b64(msg.encode('utf-8'))}.{sig}"


def verify_media_token(job_id: str, token: str) -> str | None:
    """Trả org_id nếu token hợp lệ cho job_id (chưa hết hạn); None nếu sai."""
    try:
        body, sig = token.rsplit(".", 1)
        msg = _unb64(body).decode("utf-8")
        jid, org_id, exp_s = msg.split(":")
    except (ValueError, UnicodeDecodeError):
        return None
    expected = hmac.new(_secret(), msg.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig):
        return None
    if jid != str(job_id):
        return None
    if int(exp_s) <= int(_dt.datetime.now(tz=_dt.timezone.utc).timestamp()):
        return None
    return org_id
