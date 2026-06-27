"""Worker render (M1) — pull job → render(spec, QueueSink) → complete_job (SETTLE/REFUND).

M1: hàm đồng bộ `run_job(org_id, job_id)` (Arq sẽ bọc sau). KHÔNG giữ DB transaction
trong lúc render (chỉ mở tenant_session ngắn ở đầu/cuối).
"""

from __future__ import annotations

import os
import tempfile

from app_api.db import tenant_session
from app_api.jobs import build_job_spec, complete_job, mark_running
from app_api.models import Job
from app_api.sink_queue import QueueSink
from video_engine.render_service import render
from video_engine.spec import RenderResult


def run_job(org_id, job_id) -> RenderResult | None:
    # 1) load + RUNNING + build spec (transaction ngắn)
    with tenant_session(org_id) as s:
        job = s.get(Job, job_id)
        if job is None:
            return None
        mark_running(s, job_id)
        workdir = os.path.join(tempfile.gettempdir(), "vietvid_jobs", str(job_id))
        os.makedirs(workdir, exist_ok=True)
        spec = build_job_spec(job, workdir=workdir)

    # 2) render (KHÔNG giữ DB; QueueSink tự mở session ngắn cho job_events)
    sink = QueueSink(org_id, job_id)
    result = render(spec, sink)

    # 3) hoàn tất: cập nhật job + ghi video + SETTLE/REFUND ví (transaction ngắn)
    with tenant_session(org_id) as s:
        complete_job(s, org_id, job_id, result)
    return result
