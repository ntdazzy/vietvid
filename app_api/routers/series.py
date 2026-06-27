"""Router auto-series (Sóng 4 — parity autovis): 1 brief → N biến thể video.

Tạo N job từ cùng sản phẩm, mỗi job 1 "góc nhìn" hook khác nhau (A/B). Atomic: nếu không đủ
credit cho cả loạt → 402 rollback (không tạo nửa vời). Enqueue từng job sau commit.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app_api import jobs as jobs_svc
from app_api import tenancy
from app_api.db import tenant_session
from app_api.deps import Tenant, get_tenant
from app_api.executor import submit_job
from app_api.schemas import ProductIn
from app_api.validate import ValidationError, validate_and_clamp
from app_api.wallet import InsufficientCredits

router = APIRouter(prefix="/v1/series", tags=["series"])

# Góc nhìn hook cho từng biến thể (A/B) — tiếng Việt, khác nhau để loạt video đa dạng.
_ANGLES = [
    "nhấn mạnh ưu điểm nổi bật nhất của sản phẩm",
    "nhấn vào giá tốt và ưu đãi, tạo lý do mua ngay",
    "kể trải nghiệm sử dụng thực tế, gần gũi đời thường",
    "tạo cảm giác khan hiếm / nhanh tay kẻo hết",
    "so sánh trước - sau khi dùng sản phẩm",
]


class SeriesRequest(BaseModel):
    idempotency_key: str = Field(min_length=1, max_length=200)
    count: int = Field(default=3, ge=2, le=5)
    mode: str = "product_ad"
    purpose: str = "final"
    seconds: int = Field(default=8, ge=1, le=300)
    resolution: str = "720p"
    brief: str = ""
    voice_gender: str = "female"
    product: ProductIn = Field(default_factory=ProductIn)
    template_id: str | None = None
    kol_persona_id: str | None = None
    brand_kit_id: str | None = None


class SeriesResponse(BaseModel):
    job_ids: list[str]
    count: int
    total_hold_credits: int
    balance_credits: int
    held_credits: int


@router.post("", response_model=SeriesResponse, status_code=201)
def create_series(
    req: SeriesRequest, background_tasks: BackgroundTasks, tenant: Tenant = Depends(get_tenant)
) -> SeriesResponse:
    plan_code = tenancy.org_plan_code(tenant.org_id)
    org_uuid = uuid.UUID(tenant.org_id)
    created: list[uuid.UUID] = []
    total_hold = 0
    try:
        with tenant_session(tenant.org_id) as s:
            for i in range(req.count):
                angle = _ANGLES[i % len(_ANGLES)]
                brief = (req.brief + f" — góc nhìn: {angle}").strip(" —")
                spec_raw = {
                    "mode": req.mode, "purpose": req.purpose, "seconds": req.seconds,
                    "resolution": req.resolution,
                    "product": req.product.model_dump(),
                    "params": {"brief": brief, "voice_gender": req.voice_gender},
                }
                try:
                    spec_input, _ = validate_and_clamp(spec_raw, plan_code)
                except ValidationError as exc:
                    raise HTTPException(status_code=422, detail=str(exc)) from exc
                job, hold, _dup = jobs_svc.create_job(
                    s, org_uuid, tenant.uid,
                    idempotency_key=f"{req.idempotency_key}-{i}", spec_input=spec_input,
                    template_id=req.template_id, kol_persona_id=req.kol_persona_id,
                    brand_kit_id=req.brand_kit_id,
                )
                created.append(job.id)
                total_hold += hold
            from app_api import wallet as wallet_svc
            w = wallet_svc.ensure_wallet(s, org_uuid)
            balance, held = int(w.balance_credits), int(w.held_credits)
    except InsufficientCredits as exc:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Không đủ credit cho loạt {req.count} video: cần {exc.need}, có {exc.have}",
        ) from exc

    # enqueue từng job sau commit (best-effort; reaper dọn nếu lỗi).
    for jid in created:
        try:
            submit_job(org_uuid, jid, background_tasks=background_tasks)
        except Exception:  # noqa: BLE001
            with tenant_session(tenant.org_id) as s:
                jobs_svc.release_hold(s, org_uuid, jid, note="series enqueue failed")

    return SeriesResponse(
        job_ids=[str(j) for j in created], count=len(created),
        total_hold_credits=total_hold, balance_credits=balance, held_credits=held,
    )
