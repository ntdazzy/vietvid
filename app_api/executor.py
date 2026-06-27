"""Seam thực thi job — POST /jobs gọi submit_job sau khi HOLD credit.

- inline (M1, mặc định): chạy worker.run_job qua FastAPI BackgroundTasks ngay trong tiến trình
  app → POST trả về NGAY (job_id), render chạy nền, complete_job SETTLE/REFUND khi xong.
- queue (item 2): enqueue Arq (q_fast/q_slow). Hợp đồng POST /jobs KHÔNG đổi — chỉ đổi runner.

Đổi JOB_EXECUTION_MODE = chuyển M1→Arq mà không sửa router.
"""

from __future__ import annotations

from app_api import config


def submit_job(org_id, job_id, *, background_tasks=None) -> None:
    mode = config.JOB_EXECUTION_MODE
    if mode == "queue":
        # item 2: from app_api.queue import enqueue_render; enqueue_render(org_id, job_id)
        raise RuntimeError(
            "JOB_EXECUTION_MODE=queue cần Arq worker (item 2) — chưa nối. Dùng 'inline' cho M1."
        )
    # inline
    from app_api.worker import run_job

    if background_tasks is not None:
        # run_job là sync → Starlette chạy trong threadpool, KHÔNG chặn event loop.
        background_tasks.add_task(run_job, str(org_id), str(job_id))
    else:
        run_job(org_id, job_id)
