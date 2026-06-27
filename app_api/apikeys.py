"""Khoá API B2B — phát/tra/thu hồi. Chỉ lưu sha256(key); raw chỉ trả 1 lần lúc tạo.

Tra cứu GLOBAL theo hash (chưa biết org lúc auth /api/v1) → service nhận session global.
"""

from __future__ import annotations

import hashlib
import secrets
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app_api.models import VvApiKey

_PREFIX = "vv_live_"


def _hash(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def issue(session: Session, org_id: uuid.UUID, created_by: uuid.UUID | None, name: str) -> tuple[VvApiKey, str]:
    """Tạo khoá mới → trả (row, RAW key). RAW chỉ thấy được lần này."""
    raw = _PREFIX + secrets.token_urlsafe(32)
    row = VvApiKey(
        org_id=org_id, created_by=created_by, name=(name or "")[:120],
        key_hash=_hash(raw), prefix=raw[:14],  # 'vv_live_' + 6 ký tự → hiển thị
    )
    session.add(row)
    session.flush()
    return row, raw


def verify(session: Session, raw: str) -> VvApiKey | None:
    """Tra khoá active theo hash (global). Đụng → cập nhật last_used_at. Sai/thu hồi → None."""
    raw = (raw or "").strip()
    if not raw.startswith(_PREFIX):
        return None
    row = session.execute(
        select(VvApiKey).where(VvApiKey.key_hash == _hash(raw), VvApiKey.revoked_at.is_(None))
    ).scalar_one_or_none()
    if row is None:
        return None
    row.last_used_at = func.now()
    return row
