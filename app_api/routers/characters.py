"""Router nhân vật AI — vv_characters (Studio Tier 3, clone openart /suite/character).

RLS NỚI: thấy nhân vật hệ thống (org_id NULL) + của riêng org. Ghi/xoá LUÔN lọc org_id của org
hiện tại (không đụng row hệ thống). 3 lối tạo (source): 'image' (từ ảnh), 'describe' (prompt),
'build' (thuộc tính). Nhân vật = diễn viên nhất quán, dùng lại xuyên ảnh & video.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from app_api.db import tenant_session
from app_api.deps import Tenant, get_tenant
from app_api.models import VvCharacter

router = APIRouter(prefix="/v1", tags=["characters"])

_SOURCES = ("image", "describe", "build")


class CharacterIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=2000)
    # avatar_url chứa URL thường (describe/build) HOẶC data-URL thumbnail (lối image upload,
    # vì /v1/uploads lưu file local không serve được). Nới đủ cho ảnh ~512px JPEG base64.
    avatar_url: str = Field(default="", max_length=2_000_000)
    images: list[str] = Field(default_factory=list, max_length=12)
    source: str = Field(default="build", max_length=20)
    gender: str = Field(default="", max_length=40)
    ethnicity: str = Field(default="", max_length=60)
    age_range: str = Field(default="", max_length=40)
    vibe: str = Field(default="", max_length=160)
    voice_gender: str = Field(default="female", max_length=20)


class CharacterOut(BaseModel):
    id: str
    name: str
    description: str
    avatar_url: str
    images: list[str]
    source: str
    gender: str
    ethnicity: str
    age_range: str
    vibe: str
    voice_gender: str
    is_system: bool


def _out(c: VvCharacter) -> CharacterOut:
    return CharacterOut(
        id=str(c.id), name=c.name, description=c.description or "", avatar_url=c.avatar_url or "",
        images=list(c.images or []), source=c.source, gender=c.gender or "",
        ethnicity=c.ethnicity or "", age_range=c.age_range or "", vibe=c.vibe or "",
        voice_gender=c.voice_gender, is_system=(c.org_id is None),
    )


def _norm_source(s: str) -> str:
    return s if s in _SOURCES else "build"


@router.get("/characters", response_model=list[CharacterOut])
def list_characters(tenant: Tenant = Depends(get_tenant)) -> list[CharacterOut]:
    with tenant_session(tenant.org_id) as s:
        rows = s.execute(
            select(VvCharacter).where(VvCharacter.is_active.is_(True))
            .order_by(VvCharacter.sort_order, VvCharacter.created_at)
        ).scalars().all()
        return [_out(c) for c in rows]


@router.post("/characters", response_model=CharacterOut, status_code=201)
def create_character(req: CharacterIn, tenant: Tenant = Depends(get_tenant)) -> CharacterOut:
    with tenant_session(tenant.org_id) as s:
        c = VvCharacter(
            org_id=uuid.UUID(tenant.org_id), created_by=tenant.uid, name=req.name.strip(),
            description=req.description.strip(), avatar_url=req.avatar_url.strip(),
            images=[u.strip() for u in req.images if u.strip()], source=_norm_source(req.source),
            gender=req.gender.strip(), ethnicity=req.ethnicity.strip(),
            age_range=req.age_range.strip(), vibe=req.vibe.strip(), voice_gender=req.voice_gender,
        )
        s.add(c)
        s.flush()
        return _out(c)


@router.patch("/characters/{character_id}", response_model=CharacterOut)
def update_character(
    character_id: uuid.UUID, req: CharacterIn, tenant: Tenant = Depends(get_tenant)
) -> CharacterOut:
    with tenant_session(tenant.org_id) as s:
        # CHỈ sửa của riêng org (lọc org_id tường minh → không đụng nhân vật hệ thống org_id NULL).
        c = _load(s, character_id, tenant.org_id)
        c.name = req.name.strip()
        c.description = req.description.strip()
        c.avatar_url = req.avatar_url.strip()
        c.images = [u.strip() for u in req.images if u.strip()]
        c.source = _norm_source(req.source)
        c.gender = req.gender.strip()
        c.ethnicity = req.ethnicity.strip()
        c.age_range = req.age_range.strip()
        c.vibe = req.vibe.strip()
        c.voice_gender = req.voice_gender
        s.flush()
        return _out(c)


@router.delete("/characters/{character_id}", status_code=204)
def delete_character(character_id: uuid.UUID, tenant: Tenant = Depends(get_tenant)) -> None:
    with tenant_session(tenant.org_id) as s:
        c = _load(s, character_id, tenant.org_id)
        s.delete(c)


def _load(s, character_id: uuid.UUID, org_id: str) -> VvCharacter:
    c = s.execute(
        select(VvCharacter).where(
            VvCharacter.id == character_id, VvCharacter.org_id == uuid.UUID(org_id)
        )
    ).scalar_one_or_none()
    if c is None:
        raise HTTPException(404, "Không tìm thấy nhân vật của bạn")
    return c
