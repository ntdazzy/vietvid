"""Pydantic request/response (M1 HTTP). Khớp JobSpec (video_engine.spec) cho POST /jobs.

JobCreateRequest.to_spec_input() → dict shape JobSpec (= job.params trong DB), để
jobs.create_job / estimate_hold / build_job_spec tái dùng nguyên (KHÔNG map lại).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ── request ─────────────────────────────────────────────────────────────
class ProductIn(BaseModel):
    name: str = ""
    category: str = ""
    price: str = ""
    description: str = ""
    image_path: str = ""
    image_paths_json: str = "[]"
    image_url: str = ""
    rating: float = 0.0
    rating_count: int = 0
    sales_volume: float = 0.0


class KolIn(BaseModel):
    id: int | None = None
    name: str = ""
    gender: str = ""
    style: str = ""
    character_sheet: str = ""
    image_path: str = ""
    voice_id: str = ""


class JobCreateRequest(BaseModel):
    idempotency_key: str = Field(min_length=1, max_length=200)
    mode: str = "product_ad"
    purpose: str = "final"
    seconds: int = Field(default=15, ge=1, le=300)
    resolution: str = "720p"
    format_key: str = ""
    format_label: str = ""
    format_prompt: str = ""
    overlay_policy: str = "allow"
    product: ProductIn = Field(default_factory=ProductIn)
    kol: KolIn | None = None
    params: dict[str, Any] = Field(default_factory=dict)
    scene_prompt: str = ""
    structure_reference: str = ""
    # M2 FK (Sóng 4): nối job với template/KOL/brand-kit đã chọn từ gallery.
    template_id: str | None = None
    kol_persona_id: str | None = None
    brand_kit_id: str | None = None

    def to_spec_input(self) -> dict:
        """dict JobSpec (không gồm job_ref/workdir/FK — app gán lúc build_job_spec/create_job)."""
        d = self.model_dump(
            exclude={"idempotency_key", "template_id", "kol_persona_id", "brand_kit_id"}
        )
        if d.get("kol") is None:
            d.pop("kol", None)
        return d


class EstimateRequest(BaseModel):
    mode: str = "product_ad"
    purpose: str = "final"
    seconds: int = Field(default=15, ge=1, le=300)
    resolution: str = "720p"


class DevTokenRequest(BaseModel):
    user_id: str | None = None
    email: str | None = None
    ttl_seconds: int = Field(default=3600, ge=60, le=86400)


# ── response ────────────────────────────────────────────────────────────
class BootstrapResponse(BaseModel):
    org_id: str
    user_id: str
    created: bool
    granted_credits: int
    balance_credits: int


class MeResponse(BaseModel):
    user_id: str
    email: str
    org_id: str
    role: str
    auth_mode: str
    balance_credits: int
    held_credits: int
    is_admin: bool = False


class WalletResponse(BaseModel):
    org_id: str
    balance_credits: int
    held_credits: int


class LedgerEntryOut(BaseModel):
    id: int
    entry_type: str
    delta_credits: int
    balance_after: int
    job_id: str | None = None
    payment_id: str | None = None
    note: str = ""
    created_at: datetime | None = None


class EstimateResponse(BaseModel):
    est_usd: float
    est_credits: int
    hold_credits: int
    model_id: str = ""
    resolution: str = ""
    seconds: int = 0
    breakdown: dict[str, Any] = Field(default_factory=dict)
    clamp_notes: list[str] = Field(default_factory=list)


class JobCreateResponse(BaseModel):
    job_id: str
    status: str
    hold_credits: int
    est_credits: int
    est_usd: float
    duplicated: bool
    balance_credits: int
    held_credits: int
    clamp_notes: list[str] = Field(default_factory=list)


class JobEventOut(BaseModel):
    stage: str
    event_type: str
    provider: str = ""
    cost_usd: float = 0.0
    asset_url: str = ""
    detail: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class JobOut(BaseModel):
    id: str
    status: str
    kind: str
    seconds: int
    resolution: str
    aspect: str
    est_credits: int
    est_cost_usd: float
    actual_cost_usd: float
    error: str = ""
    stage_timings: dict[str, Any] = Field(default_factory=dict)
    has_video: bool = False
    created_at: datetime | None = None
    finished_at: datetime | None = None


class JobDetailOut(JobOut):
    events: list[JobEventOut] = Field(default_factory=list)


class JobListResponse(BaseModel):
    items: list[JobOut]
    count: int


class DevTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    expires_in: int
