"""Worker render (M1) — pull job → render(spec, QueueSink) → complete_job (SETTLE/REFUND).

M1: hàm đồng bộ `run_job(org_id, job_id)` (Arq sẽ bọc sau). KHÔNG giữ DB transaction
trong lúc render (chỉ mở tenant_session ngắn ở đầu/cuối).
"""

from __future__ import annotations

import os
import tempfile

from app_api import config, storage
from app_api.db import tenant_session
from app_api.jobs import build_job_spec, complete_job, mark_running
from app_api.models import Job, JobStatus
from app_api.sink_queue import QueueSink
from video_engine.render_service import render
from video_engine.spec import RenderResult

_TERMINAL = {
    JobStatus.READY, JobStatus.FAILED, JobStatus.QA_FAIL,
    JobStatus.REFUNDED, JobStatus.CANCELLED,
}


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

    # 2b) lưu cloud (nếu cấu hình) TRƯỚC khi complete_job ghi storage_url.
    local_final = result.path
    if result.status == JobStatus.READY and result.path:
        result.path = storage.store_output(result.path, job_id)

    # 3) hoàn tất: cập nhật job + ghi video + SETTLE/REFUND ví (transaction ngắn)
    with tenant_session(org_id) as s:
        complete_job(s, org_id, job_id, result)

    # 4) dọn workdir khi job đã ở trạng thái CUỐI (WAITING_CONFIG giữ lại — resume cần intermediate).
    if result.status in _TERMINAL:
        if config.storage_configured():
            storage.cleanup_workdir(job_id, keep=None)          # đã upload cloud → xoá sạch
        else:
            storage.cleanup_workdir(job_id, keep=local_final)   # local → giữ final.mp4, xoá phần dư
    return result
