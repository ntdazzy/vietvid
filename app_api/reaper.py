"""Reaper job treo (Sóng 2) — fix rò credit khi tiến trình render chết giữa chừng.

Job inline chạy qua BackgroundTasks; nếu API restart/crash/redeploy lúc job đang RUNNING,
job kẹt RUNNING vĩnh viễn, HOLD không bao giờ được SETTLE/REFUND → credit đóng băng.
Reaper quét job non-terminal QUÁ HẠN ở MỌI org → hoàn 100% HOLD + đặt CANCELLED.

Tôn trọng RLS: KHÔNG bypass — lặp qua từng org (bảng global) rồi mở tenant_session cho org đó.
Chạy: 1 lần lúc boot (dọn job mồ côi từ tiến trình trước) + vòng lặp định kỳ.
"""

from __future__ import annotations

import datetime as _dt
import logging
import uuid

from sqlalchemy import select

from app_api import config
from app_api import jobs as jobs_svc
from app_api.db import session_scope, tenant_session
from app_api.models import Job, JobStatus, Org, Payment

log = logging.getLogger("vietvid")

# Payment PENDING quá hạn này (giờ) → đánh dấu FAILED (cổng bỏ dở / khách huỷ).
_PAYMENT_STALE_HOURS = 24

# Trạng thái "đang treo" nếu quá hạn mà không tiến triển.
_STUCK_STATES = (
    JobStatus.RUNNING, JobStatus.QUEUED, JobStatus.HELD, JobStatus.WAITING_CONFIG,
)


def reap_stuck_jobs(*, older_than_minutes: int | None = None) -> dict:
    """Quét + hoàn HOLD cho job treo ở mọi org. Trả {reaped, orgs_scanned}."""
    minutes = older_than_minutes if older_than_minutes is not None else config.REAPER_STUCK_MINUTES
    now = _dt.datetime.now(tz=_dt.timezone.utc)
    cutoff = now - _dt.timedelta(minutes=minutes)
    pay_cutoff = now - _dt.timedelta(hours=_PAYMENT_STALE_HOURS)

    with session_scope() as s:
        org_ids = [str(x) for x in s.execute(select(Org.id)).scalars().all()]

    reaped = 0
    expired_payments = 0
    for org_id in org_ids:
        try:
            with tenant_session(org_id) as s:
                stuck = s.execute(
                    select(Job).where(
                        Job.org_id == org_id,
                        Job.status.in_(_STUCK_STATES),
                        Job.updated_at < cutoff,
                    )
                ).scalars().all()
                for job in stuck:
                    jobs_svc.release_hold(
                        s, uuid.UUID(org_id), job.id,
                        note=f"reaped: job treo > {minutes} phút",
                    )
                    reaped += 1
                # Payment PENDING quá hạn → FAILED (cổng bỏ dở).
                stale_pay = s.execute(
                    select(Payment).where(
                        Payment.org_id == org_id,
                        Payment.status == "PENDING",
                        Payment.created_at < pay_cutoff,
                    )
                ).scalars().all()
                for p in stale_pay:
                    p.status = "FAILED"
                    expired_payments += 1
        except Exception:  # noqa: BLE001 — 1 org lỗi không được chặn các org khác.
            log.exception("reaper: lỗi khi quét org %s", org_id)

    if reaped or expired_payments:
        log.info("reaper: hoàn %s job treo + %s payment treo→FAILED", reaped, expired_payments)

    # Dọn workdir mồ côi (chỉ ở cloud-mode; local-mode giữ final.mp4 đang serve).
    swept = 0
    try:
        from app_api import storage
        swept = storage.sweep_old_workdirs()
    except Exception:  # noqa: BLE001
        log.exception("reaper: sweep_old_workdirs lỗi")
    return {"reaped": reaped, "orgs_scanned": len(org_ids),
            "expired_payments": expired_payments, "workdirs_swept": swept}
