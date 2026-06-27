"""Quản lý tích hợp B2B trong app: khoá API + webhook. Người dùng đăng nhập (get_tenant).

Khoá API: vv_api_keys GLOBAL (lọc org_id tường minh). Webhook: vv_webhooks RLS tenant.
"""

from __future__ import annotations

import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from app_api import apikeys, audit
from app_api.db import session_scope, tenant_session
from app_api.deps import Tenant, get_tenant
from app_api.models import VvApiKey, VvWebhook

router = APIRouter(prefix="/v1", tags=["integrations"])


# ── API keys ──────────────────────────────────────────────────────────────
class KeyCreateReq(BaseModel):
    name: str = Field(default="", max_length=120)


class KeyRow(BaseModel):
    id: str
    name: str
    prefix: str
    last_used_at: str | None
    created_at: str | None


@router.post("/api-keys")
def create_key(req: KeyCreateReq, tenant: Tenant = Depends(get_tenant)) -> dict:
    org_uuid = uuid.UUID(tenant.org_id)
    with session_scope() as s:
        row, raw = apikeys.issue(s, org_uuid, tenant.uid, req.name)
        audit.record(s, action="apikey.create", actor_email=tenant.principal.email,
                     actor_user_id=tenant.uid, org_id=tenant.org_id,
                     detail={"key_id": str(row.id), "name": req.name})
        out = {"id": str(row.id), "name": row.name, "prefix": row.prefix, "key": raw}
    return out  # `key` (raw) CHỈ trả lần này


@router.get("/api-keys", response_model=list[KeyRow])
def list_keys(tenant: Tenant = Depends(get_tenant)) -> list[KeyRow]:
    org_uuid = uuid.UUID(tenant.org_id)
    with session_scope() as s:
        rows = s.execute(
            select(VvApiKey).where(VvApiKey.org_id == org_uuid, VvApiKey.revoked_at.is_(None))
            .order_by(VvApiKey.created_at.desc())
        ).scalars().all()
        return [
            KeyRow(id=str(r.id), name=r.name, prefix=r.prefix,
                   last_used_at=r.last_used_at.isoformat() if r.last_used_at else None,
                   created_at=r.created_at.isoformat() if r.created_at else None)
            for r in rows
        ]


@router.delete("/api-keys/{key_id}")
def revoke_key(key_id: uuid.UUID, tenant: Tenant = Depends(get_tenant)) -> dict:
    org_uuid = uuid.UUID(tenant.org_id)
    with session_scope() as s:
        row = s.execute(
            select(VvApiKey).where(VvApiKey.id == key_id, VvApiKey.org_id == org_uuid)
        ).scalar_one_or_none()
        if row is None:
            raise HTTPException(404, "Không tìm thấy khoá")
        row.revoked_at = func.now()
    return {"ok": True, "id": str(key_id)}


# ── Webhooks ──────────────────────────────────────────────────────────────
class HookCreateReq(BaseModel):
    url: str = Field(min_length=8, max_length=2000)


class HookRow(BaseModel):
    id: str
    url: str
    active: bool
    created_at: str | None


@router.post("/webhooks")
def create_webhook(req: HookCreateReq, tenant: Tenant = Depends(get_tenant)) -> dict:
    if not req.url.startswith(("http://", "https://")):
        raise HTTPException(422, "url phải bắt đầu http(s)://")
    secret = "whsec_" + secrets.token_urlsafe(24)
    with tenant_session(tenant.org_id) as s:
        row = VvWebhook(org_id=uuid.UUID(tenant.org_id), created_by=tenant.uid,
                        url=req.url.strip(), secret=secret)
        s.add(row)
        s.flush()
        out = {"id": str(row.id), "url": row.url, "secret": secret}
    return out  # `secret` để bên nhận verify HMAC — chỉ trả lần này


@router.get("/webhooks", response_model=list[HookRow])
def list_webhooks(tenant: Tenant = Depends(get_tenant)) -> list[HookRow]:
    with tenant_session(tenant.org_id) as s:
        rows = s.execute(select(VvWebhook).order_by(VvWebhook.created_at.desc())).scalars().all()
        return [HookRow(id=str(r.id), url=r.url, active=r.active,
                        created_at=r.created_at.isoformat() if r.created_at else None) for r in rows]


@router.delete("/webhooks/{hook_id}")
def delete_webhook(hook_id: uuid.UUID, tenant: Tenant = Depends(get_tenant)) -> dict:
    with tenant_session(tenant.org_id) as s:
        row = s.get(VvWebhook, hook_id)
        if row is None:
            raise HTTPException(404, "Không tìm thấy webhook")
        s.delete(row)
    return {"ok": True, "id": str(hook_id)}
