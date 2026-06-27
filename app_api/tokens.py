"""Token vòng đời auth (Sóng 1B): reset mật khẩu / xác minh email / refresh.

Chỉ lưu sha256(token) trong DB. Raw token chỉ tồn tại trong email/response 1 lần.
One-time: consume đánh dấu used_at. Refresh: rotate = revoke cũ + issue mới.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import secrets
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app_api.models import AuthToken


def _now() -> _dt.datetime:
    return _dt.datetime.now(tz=_dt.timezone.utc)


def _hash(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def issue(session: Session, user_id, purpose: str, ttl_seconds: int, *, meta: dict | None = None) -> str:
    """Tạo token mới, lưu hash, trả RAW token (chỉ lần này thấy được)."""
    raw = secrets.token_urlsafe(32)
    session.add(
        AuthToken(
            user_id=uuid.UUID(str(user_id)),
            purpose=purpose,
            token_hash=_hash(raw),
            expires_at=_now() + _dt.timedelta(seconds=ttl_seconds),
            meta=meta or {},
        )
    )
    session.flush()
    return raw


def _lookup_active(session: Session, raw: str, purpose: str) -> AuthToken | None:
    tok = session.execute(
        select(AuthToken).where(
            AuthToken.token_hash == _hash(raw), AuthToken.purpose == purpose
        )
    ).scalar_one_or_none()
    if tok is None:
        return None
    if tok.used_at is not None or tok.revoked_at is not None:
        return None
    if tok.expires_at <= _now():
        return None
    return tok


def consume(session: Session, raw: str, purpose: str) -> uuid.UUID | None:
    """Xác thực token one-time (reset/verify) → trả user_id và đánh dấu used. None nếu sai/hết hạn."""
    tok = _lookup_active(session, raw, purpose)
    if tok is None:
        return None
    tok.used_at = _now()
    session.flush()
    return tok.user_id


def verify_refresh(session: Session, raw: str) -> AuthToken | None:
    """Trả bản ghi refresh token còn hiệu lực (KHÔNG đánh dấu — caller rotate)."""
    return _lookup_active(session, raw, "REFRESH")


def revoke(session: Session, tok: AuthToken) -> None:
    tok.revoked_at = _now()
    session.flush()


def revoke_all(session: Session, user_id, purpose: str) -> int:
    """Thu hồi mọi token còn sống của user theo purpose (vd logout-all, hoặc trước khi đổi mật khẩu)."""
    rows = session.execute(
        select(AuthToken).where(
            AuthToken.user_id == uuid.UUID(str(user_id)),
            AuthToken.purpose == purpose,
            AuthToken.used_at.is_(None),
            AuthToken.revoked_at.is_(None),
        )
    ).scalars().all()
    now = _now()
    for t in rows:
        t.revoked_at = now
    session.flush()
    return len(rows)
