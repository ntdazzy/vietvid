"""Router jobs — tạo (HOLD + enqueue), ước tính, danh sách, chi tiết, tải video.

POST /jobs: validate/clamp → tenant_session NGẮN { create_job = HOLD credit + insert } → COMMIT
→ submit_job (BackgroundTasks/Arq) SAU commit (worker thấy job). Idempotent theo (org, key).
RLS (tenant_session GUC) cô lập org; query vẫn lọc org_id tường minh (lưới + index — mục 6.2).
"""

from __future__ import annotations

import os
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app_api import jobs as jobs_svc
from app_api import tenancy
from app_api import wallet as wallet_svc
from app_api.db import tenant_session
from app_api.deps import Tenant, get_tenant
from app_api.executor import submit_job
from app_api.models import Job, JobEvent, Video
from app_api.schemas import (
    EstimateRequest,
    EstimateResponse,
    JobCreateRequest,
    JobCreateResponse,
    JobDetailOut,
    JobEventOut,
    JobListResponse,
    JobOut,
)
from app_api.validate import ValidationError, validate_and_clamp
from app_api.wallet import InsufficientCredits
from video_engine.providers.routing import estimate_job_cost

router = APIRouter(prefix="/v1/jobs", tags=["jobs"])


def _job_out(job: Job, *, has_video: bool) -> JobOut:
    return JobOut(
        id=str(job.id),
        status=job.status,
        kind=job.kind,
        seconds=int(job.seconds or 0),
        resolution=job.resolution or "",
        aspect=job.aspect or "",
        est_credits=int(job.est_credits or 0),
        est_cost_usd=float(job.est_cost_usd or 0),
        actual_cost_usd=float(job.actual_cost_usd or 0),
        error=job.error or "",
        stage_timings=dict(job.stage_timings or {}),
        has_video=has_video,
        created_at=job.created_at,
        finished_at=job.finished_at,
    )


@router.post("", response_model=JobCreateResponse, status_code=status.HTTP_201_CREATED)
def create_job(
    req: JobCreateRequest,
    background_tasks: BackgroundTasks,
    tenant: Tenant = Depends(get_tenant),
) -> JobCreateResponse:
    plan_code = tenancy.org_plan_code(tenant.org_id)
    try:
        spec_input, notes = validate_and_clamp(req.to_spec_input(), plan_code)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    org_uuid = uuid.UUID(tenant.org_id)
    job_pk = None
    try:
        with tenant_session(tenant.org_id) as s:
            job, hold_credits, duplicated = jobs_svc.create_job(
                s, org_uuid, tenant.uid,
                idempotency_key=req.idempotency_key, spec_input=spec_input,
            )
            job_pk = job.id
            job_id = str(job.id)
            job_status = job.status
            est_credits = int(job.est_credits or 0)
            est_usd = float(job.est_cost_usd or 0)
            w = wallet_svc.ensure_wallet(s, org_uuid)   # số dư sau HOLD (cùng txn)
            balance, held = int(w.balance_credits), int(w.held_credits)
    except InsufficientCredits as exc:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Không đủ credit: cần {exc.need}, có {exc.have}",
        ) from exc
    except IntegrityError as exc:
        # đua cùng (org, idempotency_key): request thắng đã commit job+HOLD → trả bản đó (duplicated),
        # KHÔNG enqueue lại, KHÔNG charge lần 2 (request thua INSERT job fail TRƯỚC khi HOLD).
        with tenant_session(tenant.org_id) as s:
            existing = s.execute(
                select(Job).where(Job.org_id == org_uuid, Job.idempotency_key == req.idempotency_key)
            ).scalar_one_or_none()
            if existing is None:
                raise HTTPException(status_code=409, detail="Tạo job xung đột, thử lại") from exc
            w = wallet_svc.ensure_wallet(s, org_uuid)
            return JobCreateResponse(
                job_id=str(existing.id), status=existing.status,
                hold_credits=jobs_svc._hold_of(s, existing.id),
                est_credits=int(existing.est_credits or 0), est_usd=float(existing.est_cost_usd or 0),
                duplicated=True, balance_credits=int(w.balance_credits),
                held_credits=int(w.held_credits), clamp_notes=notes,
            )

    # enqueue SAU commit (worker thấy job). Lỗi enqueue → giải phóng HOLD ngay (credits không kẹt HELD).
    if not duplicated:
        try:
            submit_job(org_uuid, job_pk, background_tasks=background_tasks)
        except Exception as exc:  # noqa: BLE001
            with tenant_session(tenant.org_id) as s:
                jobs_svc.release_hold(s, org_uuid, job_pk, note=f"enqueue failed: {exc}")
            raise HTTPException(
                status_code=500, detail="Không enqueue được job — đã hoàn HOLD, thử lại"
            ) from exc

    return JobCreateResponse(
        job_id=job_id, status=job_status, hold_credits=hold_credits,
        est_credits=est_credits, est_usd=est_usd, duplicated=duplicated,
        balance_credits=balance, held_credits=held, clamp_notes=notes,
    )


@router.post("/estimate", response_model=EstimateResponse)
def estimate(req: EstimateRequest, tenant: Tenant = Depends(get_tenant)) -> EstimateResponse:
    """Ước tính credit TRƯỚC khi tạo (wizard EstimateBadge). KHÔNG ghi DB, KHÔNG HOLD."""
    plan_code = tenancy.org_plan_code(tenant.org_id)
    try:
        spec_input, notes = validate_and_clamp(req.model_dump(), plan_code)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    est_usd, est_credits, hold_credits = jobs_svc.estimate_hold(spec_input)
    bd = estimate_job_cost(
        spec_input["mode"], spec_input["purpose"], spec_input["seconds"], spec_input["resolution"]
    )
    return EstimateResponse(
        est_usd=est_usd, est_credits=est_credits, hold_credits=hold_credits,
        model_id=bd.get("model_id", ""), resolution=bd.get("resolution", ""),
        seconds=int(spec_input["seconds"]), breakdown=bd, clamp_notes=notes,
    )


@router.get("", response_model=JobListResponse)
def list_jobs(
    tenant: Tenant = Depends(get_tenant),
    limit: int = Query(default=30, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status"),
) -> JobListResponse:
    with tenant_session(tenant.org_id) as s:
        q = select(Job).where(Job.org_id == tenant.org_id)
        if status_filter:
            q = q.where(Job.status == status_filter)
        jobs = s.execute(q.order_by(Job.created_at.desc()).limit(limit)).scalars().all()
        vids: set = set()
        if jobs:
            vids = set(
                s.execute(
                    select(Video.job_id).where(
                        Video.org_id == tenant.org_id,
                        Video.job_id.in_([j.id for j in jobs]),
                    )
                ).scalars().all()
            )
        items = [_job_out(j, has_video=j.id in vids) for j in jobs]
    return JobListResponse(items=items, count=len(items))


@router.get("/{job_id}", response_model=JobDetailOut)
def get_job(job_id: uuid.UUID, tenant: Tenant = Depends(get_tenant)) -> JobDetailOut:
    with tenant_session(tenant.org_id) as s:
        job = s.execute(
            select(Job).where(Job.id == job_id, Job.org_id == tenant.org_id)
        ).scalar_one_or_none()
        if job is None:
            raise HTTPException(status_code=404, detail="Không tìm thấy job")
        events = s.execute(
            select(JobEvent).where(JobEvent.job_id == job_id, JobEvent.org_id == tenant.org_id)
            .order_by(JobEvent.id.asc())
        ).scalars().all()
        has_video = s.execute(
            select(Video.id).where(Video.job_id == job_id, Video.org_id == tenant.org_id)
        ).first() is not None
        base = _job_out(job, has_video=has_video)
        ev = [
            JobEventOut(
                stage=e.stage, event_type=e.event_type, provider=e.provider or "",
                cost_usd=float(e.cost_usd or 0), asset_url=e.asset_url or "",
                detail=dict(e.detail or {}), created_at=e.created_at,
            )
            for e in events
        ]
    return JobDetailOut(**base.model_dump(), events=ev)


_CANCELLABLE = {jobs_svc.JobStatus.WAITING_CONFIG, jobs_svc.JobStatus.QUEUED, jobs_svc.JobStatus.HELD}
_DELETABLE = {
    jobs_svc.JobStatus.READY, jobs_svc.JobStatus.FAILED, jobs_svc.JobStatus.REFUNDED,
    jobs_svc.JobStatus.CANCELLED, jobs_svc.JobStatus.QA_FAIL,
}


@router.post("/{job_id}/cancel", response_model=JobOut)
def cancel_job(job_id: uuid.UUID, tenant: Tenant = Depends(get_tenant)) -> JobOut:
    """Huỷ job chưa chạy xong + HOÀN 100% HOLD. RUNNING không huỷ được (engine inline không ngắt
    được — hàng đợi bền ở Sóng 2 sẽ cho huỷ giữa chừng)."""
    with tenant_session(tenant.org_id) as s:
        job = s.execute(
            select(Job).where(Job.id == job_id, Job.org_id == tenant.org_id)
        ).scalar_one_or_none()
        if job is None:
            raise HTTPException(status_code=404, detail="Không tìm thấy job")
        if job.status not in _CANCELLABLE:
            raise HTTPException(
                status_code=409,
                detail=f"Không huỷ được job ở trạng thái {job.status}",
            )
        jobs_svc.release_hold(s, uuid.UUID(tenant.org_id), job_id, note="user cancel")
        s.flush()
        has_video = s.execute(
            select(Video.id).where(Video.job_id == job_id, Video.org_id == tenant.org_id)
        ).first() is not None
        out = _job_out(job, has_video=has_video)
    return out


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(job_id: uuid.UUID, tenant: Tenant = Depends(get_tenant)) -> None:
    """Xoá job đã ở trạng thái cuối + video của nó (sổ cái credit GIỮ NGUYÊN — bất biến)."""
    with tenant_session(tenant.org_id) as s:
        job = s.execute(
            select(Job).where(Job.id == job_id, Job.org_id == tenant.org_id)
        ).scalar_one_or_none()
        if job is None:
            raise HTTPException(status_code=404, detail="Không tìm thấy job")
        if job.status not in _DELETABLE:
            raise HTTPException(
                status_code=409, detail=f"Không xoá được job đang xử lý ({job.status})"
            )
        # xoá file video local (best-effort) trước khi xoá row.
        v = s.execute(
            select(Video).where(Video.job_id == job_id, Video.org_id == tenant.org_id)
        ).scalar_one_or_none()
        if v and v.storage_url and not v.storage_url.startswith(("http://", "https://")):
            try:
                if os.path.exists(v.storage_url):
                    os.remove(v.storage_url)
            except OSError:
                pass  # best-effort; row vẫn bị xoá
        s.delete(job)  # cascade: job_events + videos (FK ondelete=CASCADE)


@router.get("/{job_id}/video-url")
def get_video_signed_url(job_id: uuid.UUID, tenant: Tenant = Depends(get_tenant)) -> dict:
    """Cấp URL CÓ CHỮ KÝ (hết hạn) để <video src> phát được mà không cần Bearer header."""
    from app_api.media import sign_media_token

    with tenant_session(tenant.org_id) as s:
        exists = s.execute(
            select(Video.id).where(Video.job_id == job_id, Video.org_id == tenant.org_id)
        ).first()
    if not exists:
        raise HTTPException(status_code=404, detail="Chưa có video cho job này")
    token = sign_media_token(str(job_id), tenant.org_id)
    return {"url": f"/v1/media/video/{job_id}?token={token}"}


@router.get("/{job_id}/video")
def get_job_video(job_id: uuid.UUID, tenant: Tenant = Depends(get_tenant)):
    """Serve MP4 (không watermark — gói trả phí). M1 = file local; R2 URL → redirect (M1+)."""
    with tenant_session(tenant.org_id) as s:
        v = s.execute(
            select(Video).where(Video.job_id == job_id, Video.org_id == tenant.org_id)
        ).scalar_one_or_none()
        url = v.storage_url if v else None
    if not url:
        raise HTTPException(status_code=404, detail="Chưa có video cho job này")
    if url.startswith("http://") or url.startswith("https://"):
        return RedirectResponse(url)
    if not os.path.exists(url):
        raise HTTPException(status_code=404, detail="file_missing — tạo lại video")
    return FileResponse(url, media_type="video/mp4", filename=f"{job_id}.mp4")
