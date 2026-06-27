"""QueueSink — sink của worker: forward stage events → bảng job_events (live progress),
persist piapi_task_id NGAY khi engine tạo i2v task (chống trả tiền i2v 2 lần khi worker crash).

Kế thừa NullSink (capture stage_timings/clips/piapi_task_id trong RAM cho RenderResult);
ghi thêm ra DB. Mỗi ghi DB = 1 tenant_session NGẮN (RLS GUC), không giữ lock qua render.
"""

from __future__ import annotations

from sqlalchemy import update

from app_api.db import tenant_session
from app_api.models import Job, JobEvent
from video_engine.sink import NullSink


class QueueSink(NullSink):
    def __init__(self, org_id, job_id) -> None:
        super().__init__()
        self.org_id = org_id
        self.job_id = job_id

    def stage_start(self, stage: str) -> None:
        super().stage_start(stage)
        self._event(stage, "STARTED")

    def stage_end(self, stage: str, status: str, note: str = "") -> None:
        super().stage_end(stage, status, note)
        self._event(stage, "SUCCEEDED" if status == "ok" else "FAILED", note=note)

    def add_asset(self, stage, path, provider, cost_usd, qa_report=None) -> None:
        super().add_asset(stage, path, provider, cost_usd, qa_report)
        self._event(stage, "PROGRESS", provider=provider, cost_usd=cost_usd,
                    asset_url=path, detail={"qa": qa_report} if qa_report else {})

    def merge_params(self, extra: dict) -> None:
        super().merge_params(extra)
        # piapi_task_id: persist NGAY → worker crash giữa i2v vẫn resume, KHÔNG tạo task mới.
        if extra and "piapi_task_id" in extra:
            try:
                with tenant_session(self.org_id) as s:
                    job = s.get(Job, self.job_id)
                    if job is not None:
                        # piapi_task_id nằm trong JobSpec.params (sub-dict), không phải top-level.
                        p = dict(job.params or {})
                        inner = dict(p.get("params") or {})
                        inner["piapi_task_id"] = extra["piapi_task_id"]
                        p["params"] = inner
                        s.execute(update(Job).where(Job.id == self.job_id).values(params=p))
            except Exception:  # noqa: BLE001 — ghi progress KHÔNG được làm hỏng render
                pass

    def _event(self, stage, event_type, *, provider="", cost_usd=0.0, asset_url="", detail=None, note="") -> None:
        try:
            with tenant_session(self.org_id) as s:
                s.add(JobEvent(
                    org_id=self.org_id, job_id=self.job_id, stage=stage, event_type=event_type,
                    provider=provider or "", cost_usd=cost_usd or 0.0, asset_url=asset_url or "",
                    detail={**(detail or {}), **({"note": note} if note else {})},
                ))
        except Exception:  # noqa: BLE001 — live progress best-effort
            pass
