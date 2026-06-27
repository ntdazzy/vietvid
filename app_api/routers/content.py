"""Router nội dung — templates / KOL personas / brand kits (Sóng 4).

templates & kol_personas: RLS NỚI (thấy system org_id NULL + của riêng org). Ghi/xoá LUÔN lọc
org_id = org hiện tại (không đụng row hệ thống). brand_kits: org-only.
KOL source='upload' (mặt thật) bắt buộc đồng ý + vào hàng kiểm duyệt (moderation PENDING).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from app_api.db import tenant_session
from app_api.deps import Tenant, get_tenant
from app_api.models import VvBrandKit, VvKolPersona, VvTemplate

router = APIRouter(prefix="/v1", tags=["content"])


# ── Templates ────────────────────────────────────────────────────────────
class TemplateIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=500)
    category: str = Field(default="product_ad", max_length=40)
    preset: dict = Field(default_factory=dict)
    thumbnail_url: str = Field(default="", max_length=500)


class TemplateOut(BaseModel):
    id: str
    name: str
    description: str
    category: str
    preset: dict
    thumbnail_url: str
    is_system: bool


@router.get("/templates", response_model=list[TemplateOut])
def list_templates(tenant: Tenant = Depends(get_tenant)) -> list[TemplateOut]:
    with tenant_session(tenant.org_id) as s:
        rows = s.execute(
            select(VvTemplate).where(VvTemplate.is_active.is_(True))
            .order_by(VvTemplate.sort_order, VvTemplate.created_at)
        ).scalars().all()
        return [
            TemplateOut(
                id=str(t.id), name=t.name, description=t.description or "",
                category=t.category, preset=dict(t.preset or {}),
                thumbnail_url=t.thumbnail_url or "", is_system=(t.org_id is None),
            )
            for t in rows
        ]


@router.post("/templates", response_model=TemplateOut, status_code=201)
def create_template(req: TemplateIn, tenant: Tenant = Depends(get_tenant)) -> TemplateOut:
    with tenant_session(tenant.org_id) as s:
        t = VvTemplate(
            org_id=uuid.UUID(tenant.org_id), created_by=tenant.uid, name=req.name.strip(),
            description=req.description.strip(), category=req.category, preset=req.preset,
            thumbnail_url=req.thumbnail_url,
        )
        s.add(t)
        s.flush()
        return TemplateOut(id=str(t.id), name=t.name, description=t.description,
                           category=t.category, preset=dict(t.preset or {}),
                           thumbnail_url=t.thumbnail_url, is_system=False)


@router.delete("/templates/{template_id}", status_code=204)
def delete_template(template_id: uuid.UUID, tenant: Tenant = Depends(get_tenant)) -> None:
    with tenant_session(tenant.org_id) as s:
        # CHỈ xoá của riêng org (lọc org_id tường minh → không đụng row hệ thống org_id NULL).
        t = s.execute(
            select(VvTemplate).where(
                VvTemplate.id == template_id, VvTemplate.org_id == uuid.UUID(tenant.org_id)
            )
        ).scalar_one_or_none()
        if t is None:
            raise HTTPException(404, "Không tìm thấy template của bạn")
        s.delete(t)


# ── KOL personas ─────────────────────────────────────────────────────────
class KolIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=800)
    gender: str = Field(default="female")
    voice_gender: str = Field(default="female")
    source: str = Field(default="ai")  # ai | upload
    avatar_url: str = Field(default="", max_length=500)
    consent_confirmed: bool = False


class KolOut(BaseModel):
    id: str
    name: str
    description: str
    gender: str
    voice_gender: str
    avatar_url: str
    source: str
    moderation_status: str
    is_system: bool


@router.get("/kol-personas", response_model=list[KolOut])
def list_kol(tenant: Tenant = Depends(get_tenant)) -> list[KolOut]:
    with tenant_session(tenant.org_id) as s:
        rows = s.execute(
            select(VvKolPersona).where(VvKolPersona.is_active.is_(True))
            .order_by(VvKolPersona.sort_order, VvKolPersona.created_at)
        ).scalars().all()
        return [
            KolOut(
                id=str(k.id), name=k.name, description=k.description or "", gender=k.gender,
                voice_gender=k.voice_gender, avatar_url=k.avatar_url or "", source=k.source,
                moderation_status=k.moderation_status, is_system=(k.org_id is None),
            )
            for k in rows
        ]


@router.post("/kol-personas", response_model=KolOut, status_code=201)
def create_kol(req: KolIn, tenant: Tenant = Depends(get_tenant)) -> KolOut:
    source = req.source if req.source in ("ai", "upload") else "ai"
    if source == "upload":
        # Mặt thật: bắt buộc xác nhận đồng ý + có ảnh; vào hàng kiểm duyệt trước khi dùng.
        if not req.consent_confirmed:
            raise HTTPException(400, "Cần xác nhận đồng ý sử dụng hình ảnh")
        if not req.avatar_url.strip():
            raise HTTPException(400, "Cần ảnh khuôn mặt để tạo KOL từ ảnh thật")
        moderation = "PENDING"
    else:
        moderation = "APPROVED"
    with tenant_session(tenant.org_id) as s:
        k = VvKolPersona(
            org_id=uuid.UUID(tenant.org_id), created_by=tenant.uid, name=req.name.strip(),
            description=req.description.strip(), gender=req.gender, voice_gender=req.voice_gender,
            avatar_url=req.avatar_url.strip(), source=source,
            consent_confirmed=req.consent_confirmed, moderation_status=moderation,
        )
        s.add(k)
        s.flush()
        return KolOut(id=str(k.id), name=k.name, description=k.description, gender=k.gender,
                      voice_gender=k.voice_gender, avatar_url=k.avatar_url, source=k.source,
                      moderation_status=k.moderation_status, is_system=False)


@router.delete("/kol-personas/{kol_id}", status_code=204)
def delete_kol(kol_id: uuid.UUID, tenant: Tenant = Depends(get_tenant)) -> None:
    with tenant_session(tenant.org_id) as s:
        k = s.execute(
            select(VvKolPersona).where(
                VvKolPersona.id == kol_id, VvKolPersona.org_id == uuid.UUID(tenant.org_id)
            )
        ).scalar_one_or_none()
        if k is None:
            raise HTTPException(404, "Không tìm thấy KOL của bạn")
        s.delete(k)


# ── Brand kits (org-only) ─────────────────────────────────────────────────
class BrandKitIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    logo_url: str = Field(default="", max_length=500)
    primary_color: str = Field(default="#7C3AED", max_length=20)
    secondary_color: str = Field(default="#2563EB", max_length=20)
    font: str = Field(default="", max_length=80)
    watermark_text: str = Field(default="", max_length=120)
    disclosure_text: str = Field(default="", max_length=300)
    is_default: bool = False


class BrandKitOut(BaseModel):
    id: str
    name: str
    logo_url: str
    primary_color: str
    secondary_color: str
    font: str
    watermark_text: str
    disclosure_text: str
    is_default: bool


def _bk_out(k: VvBrandKit) -> BrandKitOut:
    return BrandKitOut(
        id=str(k.id), name=k.name, logo_url=k.logo_url or "", primary_color=k.primary_color,
        secondary_color=k.secondary_color, font=k.font or "", watermark_text=k.watermark_text or "",
        disclosure_text=k.disclosure_text or "", is_default=bool(k.is_default),
    )


@router.get("/brand-kits", response_model=list[BrandKitOut])
def list_brand_kits(tenant: Tenant = Depends(get_tenant)) -> list[BrandKitOut]:
    with tenant_session(tenant.org_id) as s:
        rows = s.execute(
            select(VvBrandKit).where(VvBrandKit.org_id == uuid.UUID(tenant.org_id))
            .order_by(VvBrandKit.created_at)
        ).scalars().all()
        return [_bk_out(k) for k in rows]


@router.post("/brand-kits", response_model=BrandKitOut, status_code=201)
def create_brand_kit(req: BrandKitIn, tenant: Tenant = Depends(get_tenant)) -> BrandKitOut:
    with tenant_session(tenant.org_id) as s:
        if req.is_default:
            _clear_default(s, tenant.org_id)
        k = VvBrandKit(
            org_id=uuid.UUID(tenant.org_id), created_by=tenant.uid, name=req.name.strip(),
            logo_url=req.logo_url, primary_color=req.primary_color,
            secondary_color=req.secondary_color, font=req.font, watermark_text=req.watermark_text,
            disclosure_text=req.disclosure_text, is_default=req.is_default,
        )
        s.add(k)
        s.flush()
        return _bk_out(k)


@router.patch("/brand-kits/{kit_id}", response_model=BrandKitOut)
def update_brand_kit(kit_id: uuid.UUID, req: BrandKitIn, tenant: Tenant = Depends(get_tenant)) -> BrandKitOut:
    with tenant_session(tenant.org_id) as s:
        k = s.execute(
            select(VvBrandKit).where(
                VvBrandKit.id == kit_id, VvBrandKit.org_id == uuid.UUID(tenant.org_id)
            )
        ).scalar_one_or_none()
        if k is None:
            raise HTTPException(404, "Không tìm thấy brand kit")
        if req.is_default and not k.is_default:
            _clear_default(s, tenant.org_id)
        k.name = req.name.strip()
        k.logo_url = req.logo_url
        k.primary_color = req.primary_color
        k.secondary_color = req.secondary_color
        k.font = req.font
        k.watermark_text = req.watermark_text
        k.disclosure_text = req.disclosure_text
        k.is_default = req.is_default
        s.flush()
        return _bk_out(k)


@router.delete("/brand-kits/{kit_id}", status_code=204)
def delete_brand_kit(kit_id: uuid.UUID, tenant: Tenant = Depends(get_tenant)) -> None:
    with tenant_session(tenant.org_id) as s:
        k = s.execute(
            select(VvBrandKit).where(
                VvBrandKit.id == kit_id, VvBrandKit.org_id == uuid.UUID(tenant.org_id)
            )
        ).scalar_one_or_none()
        if k is None:
            raise HTTPException(404, "Không tìm thấy brand kit")
        s.delete(k)


def _clear_default(s, org_id: str) -> None:
    for k in s.execute(
        select(VvBrandKit).where(
            VvBrandKit.org_id == uuid.UUID(org_id), VvBrandKit.is_default.is_(True)
        )
    ).scalars().all():
        k.is_default = False
