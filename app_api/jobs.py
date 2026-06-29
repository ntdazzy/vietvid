"""Jobs orchestration — nối ví ↔ engine (mục 7.1, 7.2 plan).

create_job: validate → est → HOLD credit → insert job(QUEUED). Idempotent theo (org, key).
build_job_spec: job row (params JSONB = JobSpec dict) → JobSpec stateless cho engine.
complete_job: theo RenderResult → SETTLE/REFUND ví + ghi video + cập nhật job.
"""

from __future__ import annotations

import math
import uuid

from sqlalchemy import func, select

from app_api import wallet
from app_api.models import Job, JobStatus, LedgerEntry, LedgerKind, Video
from app_api.pricing import usd_to_credits_billed
from video_engine.providers.routing import estimate_job_cost
from video_engine.spec import JobSpec, RenderResult

_ALLOWED_STATUS = {
    JobStatus.WAITING_CONFIG, JobStatus.QUEUED, JobStatus.HELD, JobStatus.RUNNING,
    JobStatus.QA_FAIL, JobStatus.READY, JobStatus.FAILED, JobStatus.REFUNDED, JobStatus.CANCELLED,
}


def _hold_of(session, job_id) -> int:
    """Số credit ĐÃ GIỮ cho job = -delta của ledger HOLD (nguồn chân lý)."""
    e = session.execute(
        select(LedgerEntry).where(
            LedgerEntry.job_id == job_id, LedgerEntry.entry_type == LedgerKind.HOLD
        )
    ).scalar_one_or_none()
    return int(-e.delta_credits) if e else 0


def estimate_hold(spec_input: dict) -> tuple[float, int, int]:
    """Trả (est_usd, est_credits, hold_credits). hold = ceil(est_credits × 1.5) (trần như max_cost_usd)."""
    est = estimate_job_cost(
        spec_input.get("mode", "product_ad"), spec_input.get("purpose", "final"),
        int(spec_input.get("seconds", 15)), spec_input.get("resolution", "720p"),
    )
    est_usd = float(est["total_usd"])               # giá VỐN thật (cho budget/ledger)
    est_credits = usd_to_credits_billed(est_usd)     # giá BÁN khách (đã markup)
    hold_credits = math.ceil(est_credits * 1.5)
    return est_usd, est_credits, hold_credits


def _as_uuid(v):
    try:
        return uuid.UUID(str(v)) if v else None
    except (ValueError, TypeError):
        return None


def create_job(session, org_id, user_id, *, idempotency_key: str, spec_input: dict,
               template_id=None, kol_persona_id=None, brand_kit_id=None, series_group=None):
    """Tạo job + HOLD credit (1 transaction của caller). Trả (job, hold_credits, duplicated)."""
    existing = session.execute(
        select(Job).where(Job.org_id == org_id, Job.idempotency_key == idempotency_key)
    ).scalar_one_or_none()
    if existing is not None:
        return existing, _hold_of(session, existing.id), True

    # self-heal: nếu bootstrap 2 pha crash giữa chừng (org có, ví chưa) → tạo ví trước khi HOLD,
    # tránh WalletNotFound. ensure_wallet idempotent + an toàn đồng thời.
    wallet.ensure_wallet(session, org_id)
    est_usd, est_credits, hold_credits = estimate_hold(spec_input)
    ref_group = uuid.uuid4()
    inner = spec_input.get("params") or {}
    job = Job(
        org_id=org_id, created_by=user_id, idempotency_key=idempotency_key,
        kind=spec_input.get("kind", spec_input.get("mode", "product_ad")),
        status=JobStatus.QUEUED, params=spec_input,
        template_id=_as_uuid(template_id), kol_persona_id=_as_uuid(kol_persona_id),
        brand_kit_id=_as_uuid(brand_kit_id), series_group=_as_uuid(series_group),
        aspect=inner.get("aspect", "9:16") or "9:16",
        resolution=spec_input.get("resolution", "720p"),
        seconds=int(spec_input.get("seconds", 15)),
        est_cost_usd=est_usd, est_credits=est_credits, credit_ref_group=ref_group,
    )
    session.add(job)
    session.flush()  # → job.id
    wallet.hold(session, org_id, job.id, hold_credits, ref_group=ref_group,
                note=f"hold {spec_input.get('mode', 'product_ad')}")
    return job, hold_credits, False


def build_job_spec(job, *, workdir: str = "") -> JobSpec:
    """job row → JobSpec. params JSONB CHÍNH LÀ dict JobSpec (lưu lúc create)."""
    d = dict(job.params or {})
    d["job_ref"] = str(job.id)
    if workdir:
        d["workdir"] = workdir
    return JobSpec.from_dict(d)


def mark_running(session, job_id) -> None:
    job = session.get(Job, job_id)
    if job is not None:
        job.status = JobStatus.RUNNING


def release_hold(session, org_id, job_id, *, note: str = "enqueue failed") -> None:
    """Giải phóng HOLD khi enqueue THẤT BẠI sau commit → credits KHÔNG kẹt HELD vĩnh viễn.

    Hoàn 100% hold (idempotent qua _terminal_done) + đặt job = CANCELLED. Chạy trong tenant_session.
    """
    job = session.get(Job, job_id)
    if job is None:
        return
    hold_credits = _hold_of(session, job_id)
    if hold_credits:
        wallet.refund(session, org_id, job_id, ref_group=job.credit_ref_group,
                      hold_credits=hold_credits, note=note)
    job.status = JobStatus.CANCELLED
    job.error = (note or "")[:1000]


def complete_job(session, org_id, job_id, result: RenderResult) -> None:
    """Theo RenderResult: cập nhật job + ghi video + SETTLE/REFUND ví. Chạy trong tenant_session."""
    job = session.get(Job, job_id)
    if job is None:
        return
    # Job đã bị huỷ (user cancel) → KHÔNG hồi sinh. HOLD đã hoàn ở release_hold; bỏ qua.
    if job.status == JobStatus.CANCELLED:
        return
    hold_credits = _hold_of(session, job_id)
    ref_group = job.credit_ref_group

    job.status = result.status if result.status in _ALLOWED_STATUS else JobStatus.QUEUED
    job.actual_cost_usd = result.cost_usd
    job.stage_timings = result.stage_timings or {}
    job.error = (result.error or "")[:1000]
    job.finished_at = func.now()
    if result.resume_task_id:
        p = dict(job.params or {})
        inner = dict(p.get("params") or {})
        inner["piapi_task_id"] = result.resume_task_id
        p["params"] = inner
        job.params = p

    if result.status == JobStatus.READY and result.path:
        session.add(Video(
            org_id=org_id, job_id=job_id, storage_url=result.path,
            duration_s=(result.stage_timings or {}).get("_duration", 0) or 0,
            aspect=job.aspect, has_watermark=True,
        ))

    # Thông báo in-app (best-effort, cùng tenant_session).
    from app_api import notify

    if result.status == JobStatus.READY:
        notify.create(session, org_id, type="job_ready", title="Video đã sẵn sàng 🎬",
                      body="Video của bạn đã render xong, bấm để xem.",
                      ref_type="job", ref_id=job_id, user_id=job.created_by)
    elif result.status in (JobStatus.FAILED, JobStatus.QA_FAIL):
        notify.create(session, org_id, type="job_failed", title="Video tạo chưa thành công",
                      body=(result.error or "Đã hoàn credit nếu lỗi hệ thống.")[:200],
                      ref_type="job", ref_id=job_id, user_id=job.created_by)

    # Ví: READY/QA_FAIL → SETTLE actual; FAILED+system → REFUND 100%; FAILED+input → SETTLE actual.
    if result.status in (JobStatus.READY, JobStatus.QA_FAIL):
        wallet.settle(session, org_id, job_id, ref_group=ref_group,
                      hold_credits=hold_credits, actual_usd=result.cost_usd)
    elif result.status == JobStatus.FAILED and result.fault_class == "system":
        wallet.refund(session, org_id, job_id, ref_group=ref_group, hold_credits=hold_credits)
    elif result.status == JobStatus.FAILED:  # input fault
        wallet.settle(session, org_id, job_id, ref_group=ref_group,
                      hold_credits=hold_credits, actual_usd=result.cost_usd)
    # WAITING_CONFIG/khác: giữ HOLD, retry sau (không settle/refund).
