"""Tạo thông báo in-app (Sóng 4). Chạy trong tenant_session(org) của caller (RLS WITH CHECK
yêu cầu org_id = GUC). Best-effort: lỗi thông báo KHÔNG được làm hỏng luồng chính."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy.orm import Session

from app_api.models import Notification

log = logging.getLogger("vietvid")


def create(session: Session, org_id, *, type: str, title: str, body: str = "",
           ref_type: str = "", ref_id: str = "", user_id=None) -> None:
    try:
        session.add(Notification(
            org_id=uuid.UUID(str(org_id)),
            user_id=uuid.UUID(str(user_id)) if user_id else None,
            type=type, title=title, body=body, ref_type=ref_type, ref_id=str(ref_id or ""),
        ))
        session.flush()
    except Exception:  # noqa: BLE001
        log.exception("notify.create lỗi (bỏ qua)")
