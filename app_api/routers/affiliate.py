"""Router affiliate (Sóng 4 — vượt autovis: video → click → doanh thu).

Quản lý link (authed, lọc org_id) + redirect PUBLIC /r/{code} ghi click append-only.
Bảng global (xem GLOBAL_ORG_TABLES) → redirect resolve được mà không cần tenant context.
"""

from __future__ import annotations

import hashlib
import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from app_api import config
from app_api.db import session_scope
from app_api.deps import Tenant, get_tenant
from app_api.models import VvAffiliateLink, VvLinkClick

router = APIRouter(prefix="/v1/affiliate", tags=["affiliate"])
redirect_router = APIRouter(tags=["affiliate"])  # /r/{code} — KHÔNG prefix


class LinkIn(BaseModel):
    target_url: str = Field(min_length=4, max_length=2000)
    label: str = Field(default="", max_length=120)
    network: str = Field(default="", max_length=40)
    job_id: str | None = None


class LinkOut(BaseModel):
    id: str
    code: str
    short_url: str
    target_url: str
    label: str
    network: str
    clicks: int


def _short_url(code: str) -> str:
    return f"{config.APP_BASE_URL.rstrip('/')}/r/{code}"


@router.get("/links", response_model=list[LinkOut])
def list_links(tenant: Tenant = Depends(get_tenant)) -> list[LinkOut]:
    with session_scope() as s:
        rows = s.execute(
            select(VvAffiliateLink).where(VvAffiliateLink.org_id == uuid.UUID(tenant.org_id))
            .order_by(VvAffiliateLink.created_at.desc())
        ).scalars().all()
        return [
            LinkOut(id=str(r.id), code=r.code, short_url=_short_url(r.code), target_url=r.target_url,
                    label=r.label or "", network=r.network or "", clicks=int(r.clicks))
            for r in rows
        ]


@router.post("/links", response_model=LinkOut, status_code=201)
def create_link(req: LinkIn, tenant: Tenant = Depends(get_tenant)) -> LinkOut:
    if not req.target_url.startswith(("http://", "https://")):
        raise HTTPException(422, "target_url phải là http(s)")
    code = secrets.token_urlsafe(6).replace("-", "x").replace("_", "y")[:8]
    with session_scope() as s:
        link = VvAffiliateLink(
            org_id=uuid.UUID(tenant.org_id), created_by=tenant.uid, code=code,
            target_url=req.target_url, label=req.label.strip(), network=req.network.strip(),
            job_id=uuid.UUID(req.job_id) if req.job_id else None,
        )
        s.add(link)
        s.flush()
        out = LinkOut(id=str(link.id), code=code, short_url=_short_url(code),
                      target_url=link.target_url, label=link.label, network=link.network, clicks=0)
    return out


@router.delete("/links/{link_id}", status_code=204)
def delete_link(link_id: uuid.UUID, tenant: Tenant = Depends(get_tenant)) -> None:
    with session_scope() as s:
        link = s.execute(
            select(VvAffiliateLink).where(
                VvAffiliateLink.id == link_id,
                VvAffiliateLink.org_id == uuid.UUID(tenant.org_id),
            )
        ).scalar_one_or_none()
        if link is None:
            raise HTTPException(404, "Không tìm thấy link")
        s.delete(link)


@router.get("/stats")
def stats(tenant: Tenant = Depends(get_tenant)) -> dict:
    with session_scope() as s:
        total_links = s.execute(
            select(func.count()).select_from(VvAffiliateLink)
            .where(VvAffiliateLink.org_id == uuid.UUID(tenant.org_id))
        ).scalar_one()
        total_clicks = int(s.execute(
            select(func.coalesce(func.sum(VvAffiliateLink.clicks), 0))
            .where(VvAffiliateLink.org_id == uuid.UUID(tenant.org_id))
        ).scalar_one())
    return {"links": total_links, "clicks": total_clicks}


@redirect_router.get("/r/{code}")
def redirect(code: str, request: Request):
    """PUBLIC: resolve short-link → ghi click → 302 tới target_url."""
    with session_scope() as s:
        link = s.execute(
            select(VvAffiliateLink).where(VvAffiliateLink.code == code)
        ).scalar_one_or_none()
        if link is None:
            raise HTTPException(404, "Link không tồn tại")
        ua = request.headers.get("user-agent", "")
        s.add(VvLinkClick(
            org_id=link.org_id, link_id=link.id,
            referer=(request.headers.get("referer", "") or "")[:500],
            ua_hash=hashlib.sha256(ua.encode("utf-8")).hexdigest()[:32] if ua else "",
        ))
        link.clicks = int(link.clicks) + 1
        target = link.target_url
    return RedirectResponse(target, status_code=302)
