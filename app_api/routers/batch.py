"""Router LÀM HÀNG LOẠT (batch): N sản phẩm KHÁC nhau → N video (mỗi SP 1 clip).

Khác /v1/series (N biến thể của CÙNG 1 SP). Đây là "dán 20 link → 20 video" —
điểm khác biệt vs autovis (autovis không có luồng nhiều-SP).

An toàn tiền: mirror y hệt series.create_series — atomic hold cả loạt trong 1
tenant_session (thiếu credit → 402 rollback, KHÔNG tạo nửa vời), enqueue từng
job SAU commit. Gom chung bằng series_group để tái dùng màn theo dõi + attribution.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app_api import jobs as jobs_svc
from app_api import tenancy
from app_api import wallet as wallet_svc
from app_api.db import tenant_session
from app_api.deps import Tenant, get_tenant
from app_api.executor import submit_job
from app_api.schemas import ProductIn
from app_api.validate import ValidationError, validate_and_clamp
from app_api.wallet import InsufficientCredits

router = APIRouter(prefix="/v1/batch", tags=["batch"])


class BatchItem(BaseModel):
    product: ProductIn = Field(default_factory=ProductIn)
    brief: str = Field(default="", max_length=2000)  # brief riêng/SP (rỗng = dùng brief chung)


class BatchRequest(BaseModel):
    idempotency_key: str = Field(min_length=1, max_length=200)
    items: list[BatchItem] = Field(min_length=2, max_length=20)  # 2..20 sản phẩm
    mode: str = "product_ad"
    purpose: str = "final"
    seconds: int = Field(default=8, ge=1, le=300)
    resolution: str = "720p"
    brief: str = ""  # brief chung (áp cho item không có brief riêng)
    voice_gender: str = "female"
    voice_persona: str = Field(default="", max_length=40)
    aspect: str = Field(default="9:16", max_length=10)
    template_id: str | None = None
    kol_persona_id: str | None = None
    brand_kit_id: str | None = None


class BatchResponse(BaseModel):
    batch_group: str
    job_ids: list[str]
    count: int
    total_hold_credits: int
    balance_credits: int
    held_credits: int


@router.post("", response_model=BatchResponse, status_code=201)
def create_batch(
    req: BatchRequest, background_tasks: BackgroundTasks, tenant: Tenant = Depends(get_tenant)
) -> BatchResponse:
    plan_code = tenancy.org_plan_code(tenant.org_id)
    org_uuid = uuid.UUID(tenant.org_id)
    group = uuid.uuid4()
    created: list[uuid.UUID] = []
    total_hold = 0
    try:
        with tenant_session(tenant.org_id) as s:
            for i, item in enumerate(req.items):
                brief = (item.brief or req.brief or "").strip()
                spec_raw = {
                    "mode": req.mode, "purpose": req.purpose, "seconds": req.seconds,
                    "resolution": req.resolution,
                    "product": item.product.model_dump(),
                    "params": {
                        "brief": brief, "voice_gender": req.voice_gender,
                        "voice_persona": req.voice_persona, "aspect": req.aspect,
                    },
                }
                try:
                    spec_input, _ = validate_and_clamp(spec_raw, plan_code)
                except ValidationError as exc:
                    raise HTTPException(status_code=422, detail=f"SP #{i + 1}: {exc}") from exc
                job, hold, _dup = jobs_svc.create_job(
                    s, org_uuid, tenant.uid,
                    idempotency_key=f"{req.idempotency_key}-{i}", spec_input=spec_input,
                    template_id=req.template_id, kol_persona_id=req.kol_persona_id,
                    brand_kit_id=req.brand_kit_id, series_group=group,
                )
                created.append(job.id)
                total_hold += hold
            w = wallet_svc.ensure_wallet(s, org_uuid)
            balance, held = int(w.balance_credits), int(w.held_credits)
    except InsufficientCredits as exc:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Không đủ credit cho loạt {len(req.items)} video: cần {exc.need}, có {exc.have}",
        ) from exc

    # enqueue từng job SAU commit (best-effort; reaper dọn nếu lỗi) — y hệt series.
    for jid in created:
        try:
            submit_job(org_uuid, jid, background_tasks=background_tasks)
        except Exception:  # noqa: BLE001
            with tenant_session(tenant.org_id) as s:
                jobs_svc.release_hold(s, org_uuid, jid, note="batch enqueue failed")

    return BatchResponse(
        batch_group=str(group), job_ids=[str(j) for j in created], count=len(created),
        total_hold_credits=total_hold, balance_credits=balance, held_credits=held,
    )
