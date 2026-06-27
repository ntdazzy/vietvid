"""Router notifications — list + unread count + mark-read (tenant, RLS)."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select, update

from app_api.db import tenant_session
from app_api.deps import Tenant, get_tenant
from app_api.models import Notification

router = APIRouter(prefix="/v1/notifications", tags=["notifications"])


class NotifOut(BaseModel):
    id: str
    type: str
    title: str
    body: str
    ref_type: str
    ref_id: str
    read: bool
    created_at: datetime | None


class NotifList(BaseModel):
    items: list[NotifOut]
    unread: int


class ReadReq(BaseModel):
    ids: list[str] | None = None  # None = đánh dấu đọc TẤT CẢ


@router.get("", response_model=NotifList)
def list_notifications(tenant: Tenant = Depends(get_tenant),
                       limit: int = Query(default=30, ge=1, le=100)) -> NotifList:
    with tenant_session(tenant.org_id) as s:
        rows = s.execute(
            select(Notification).where(Notification.org_id == tenant.org_id)
            .order_by(Notification.created_at.desc()).limit(limit)
        ).scalars().all()
        unread = int(s.execute(
            select(func.count()).select_from(Notification)
            .where(Notification.org_id == tenant.org_id, Notification.read_at.is_(None))
        ).scalar_one())
        items = [
            NotifOut(id=str(n.id), type=n.type, title=n.title, body=n.body or "",
                     ref_type=n.ref_type or "", ref_id=n.ref_id or "",
                     read=n.read_at is not None, created_at=n.created_at)
            for n in rows
        ]
    return NotifList(items=items, unread=unread)


@router.post("/read")
def mark_read(req: ReadReq, tenant: Tenant = Depends(get_tenant)) -> dict:
    with tenant_session(tenant.org_id) as s:
        stmt = update(Notification).where(
            Notification.org_id == tenant.org_id, Notification.read_at.is_(None)
        ).values(read_at=func.now())
        if req.ids:
            import uuid
            stmt = stmt.where(Notification.id.in_([uuid.UUID(i) for i in req.ids]))
        s.execute(stmt)
    return {"ok": True}
