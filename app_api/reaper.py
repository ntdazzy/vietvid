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
from app_api.models import Job, JobStatus, Org

log = logging.getLogger("vietvid")

# Trạng thái "đang treo" nếu quá hạn mà không tiến triển.
_STUCK_STATES = (
    JobStatus.RUNNING, JobStatus.QUEUED, JobStatus.HELD, JobStatus.WAITING_CONFIG,
)


def reap_stuck_jobs(*, older_than_minutes: int | None = None) -> dict:
    """Quét + hoàn HOLD cho job treo ở mọi org. Trả {reaped, orgs_scanned}."""
    minutes = older_than_minutes if older_than_minutes is not None else config.REAPER_STUCK_MINUTES
    cutoff = _dt.datetime.now(tz=_dt.timezone.utc) - _dt.timedelta(minutes=minutes)

    with session_scope() as s:
        org_ids = [str(x) for x in s.execute(select(Org.id)).scalars().all()]

    reaped = 0
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
        except Exception:  # noqa: BLE001 — 1 org lỗi không được chặn các org khác.
            log.exception("reaper: lỗi khi quét org %s", org_id)

    if reaped:
        log.info("reaper: đã hoàn HOLD + huỷ %s job treo (>%sm)", reaped, minutes)
    return {"reaped": reaped, "orgs_scanned": len(org_ids)}
