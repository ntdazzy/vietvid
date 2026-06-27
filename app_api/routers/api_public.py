"""API công khai B2B (/api/v1) — xác thực bằng KHOÁ API (X-API-Key), không JWT.

Tái dùng TOÀN BỘ luồng tạo job của router nội bộ (validate + HOLD + idempotency + enqueue)
bằng cách gọi thẳng handler create_job với Tenant suy từ khoá API → 0 trùng lặp logic.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from app_api.db import tenant_session
from app_api.deps import Tenant, get_api_tenant
from app_api.models import Job, Video
from app_api.routers.jobs import create_job as _create_job_handler
from app_api.schemas import JobCreateRequest, ProductIn

router = APIRouter(prefix="/api/v1", tags=["public-api"])


class GenerateReq(BaseModel):
    idempotency_key: str = Field(min_length=1, max_length=200)
    product: ProductIn = Field(default_factory=ProductIn)
    seconds: int = Field(default=15, ge=1, le=300)
    resolution: str = Field(default="720p", max_length=20)
    aspect: str = Field(default="9:16", max_length=10)
    purpose: str = Field(default="final", max_length=20)
    brief: str = Field(default="", max_length=4000)
    voice_gender: str = Field(default="female", max_length=20)
    voice_persona: str = Field(default="", max_length=40)


@router.post("/videos", status_code=201)
def generate(req: GenerateReq, background_tasks: BackgroundTasks,
             tenant: Tenant = Depends(get_api_tenant)) -> dict:
    """Tạo video qua API. Trả {id, status, est_credits}. HOLD credit như tạo trong app."""
    job_req = JobCreateRequest(
        idempotency_key=req.idempotency_key, mode="product_ad", purpose=req.purpose,
        seconds=req.seconds, resolution=req.resolution, product=req.product,
        params={"brief": req.brief, "voice_gender": req.voice_gender,
                "voice_persona": req.voice_persona, "aspect": req.aspect},
    )
    resp = _create_job_handler(job_req, background_tasks, tenant)
    return {"id": resp.job_id, "status": resp.status, "est_credits": resp.est_credits,
            "duplicated": resp.duplicated}


@router.get("/videos/{job_id}")
def get_video(job_id: uuid.UUID, tenant: Tenant = Depends(get_api_tenant)) -> dict:
    with tenant_session(tenant.org_id) as s:
        job = s.execute(
            select(Job).where(Job.id == job_id, Job.org_id == uuid.UUID(tenant.org_id))
        ).scalar_one_or_none()
        if job is None:
            raise HTTPException(404, "Không tìm thấy job")
        video = s.execute(select(Video).where(Video.job_id == job_id)).scalar_one_or_none()
        return {
            "id": str(job.id), "status": job.status, "seconds": job.seconds,
            "aspect": job.aspect, "resolution": job.resolution,
            "error": job.error or "", "has_video": video is not None,
        }


@router.get("/videos")
def list_videos(tenant: Tenant = Depends(get_api_tenant), limit: int = 20) -> dict:
    limit = max(1, min(limit, 100))
    with tenant_session(tenant.org_id) as s:
        jobs = s.execute(
            select(Job).where(Job.org_id == uuid.UUID(tenant.org_id))
            .order_by(Job.created_at.desc()).limit(limit)
        ).scalars().all()
        return {"items": [{"id": str(j.id), "status": j.status, "aspect": j.aspect,
                           "seconds": j.seconds} for j in jobs], "count": len(jobs)}
