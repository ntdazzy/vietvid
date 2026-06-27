"""Ghi audit_log (Sóng 4) — best-effort, không làm hỏng hành động chính."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy.orm import Session

from app_api.models import AuditLog

log = logging.getLogger("vietvid")


def record(session: Session, *, action: str, actor_email: str = "", actor_user_id=None,
           org_id=None, detail: dict | None = None) -> None:
    try:
        session.add(AuditLog(
            action=action, actor_email=actor_email or "",
            actor_user_id=uuid.UUID(str(actor_user_id)) if actor_user_id else None,
            org_id=uuid.UUID(str(org_id)) if org_id else None,
            detail=detail or {},
        ))
        session.flush()
    except Exception:  # noqa: BLE001
        log.exception("audit.record lỗi (bỏ qua)")
