"""JobSink — kênh báo trạng thái/asset của engine, thay cho việc ghi thẳng DB.

Engine gọi sink.* thay vì _set_status(job_id,...)/_stage_*/_add_stage_asset(...).
- NullSink: mặc định cho CLI/test/Product C standalone — KHÔNG forward đi đâu, chỉ CAPTURE
  cục bộ (stage_timings, merged params để lấy piapi_task_id, shot_plan, assets) để render()
  điền vào RenderResult.
- QueueSink (worker, M1): forward stage_start/stage_end/set_status thành job_events về app_api
  + buffer merge_params({"piapi_task_id":...}) về bảng jobs. (stub ở M0.)
"""

from __future__ import annotations

import time
from typing import Any, Protocol


class JobSink(Protocol):
    def set_status(self, status: str, error: str = "") -> None: ...
    def update_job(self, **fields: Any) -> None: ...
    def merge_params(self, extra: dict) -> None: ...
    def stage_start(self, stage: str) -> None: ...
    def stage_end(self, stage: str, status: str, note: str = "") -> None: ...
    def save_shot_plan(self, plan: dict | None, critic: dict | None = None) -> None: ...
    def update_overlays(self, overlays: list) -> None: ...
    def add_asset(
        self, stage: str, path: str, provider: str, cost_usd: float,
        qa_report: dict | None = None,
    ) -> None: ...

    # render() đọc TRỰC TIẾP 3 thứ này để điền RenderResult — MỌI sink phải cung cấp,
    # nếu không sẽ mất piapi_task_id (retry trả tiền i2v 2 lần), clip count, timings.
    stage_timings: dict
    @property
    def piapi_task_id(self) -> str: ...
    @property
    def clips_used(self) -> int: ...


class NullSink:
    """Capture cục bộ, không forward. Dùng cho runner_cli + Product C standalone."""

    def __init__(self) -> None:
        self.status: str = ""
        self.error: str = ""
        self.job_fields: dict = {}
        self.params: dict = {}
        self.shot_plan: dict | None = None
        self.critic: dict | None = None
        self.overlays: list = []
        self.assets: list[dict] = []
        self.stage_timings: dict[str, dict] = {}
        self._stage_started: dict[str, float] = {}

    def set_status(self, status: str, error: str = "") -> None:
        self.status = status
        self.error = error

    def update_job(self, **fields: Any) -> None:
        self.job_fields.update(fields)

    def merge_params(self, extra: dict) -> None:
        self.params.update(extra or {})

    def stage_start(self, stage: str) -> None:
        self._stage_started[stage] = time.monotonic()
        self.stage_timings.setdefault(stage, {})["status"] = "running"

    def stage_end(self, stage: str, status: str, note: str = "") -> None:
        started = self._stage_started.get(stage)
        dur = round(time.monotonic() - started, 2) if started is not None else None
        self.stage_timings[stage] = {"status": status, "note": note, "seconds": dur}

    def save_shot_plan(self, plan: dict | None, critic: dict | None = None) -> None:
        self.shot_plan = plan
        self.critic = critic

    def update_overlays(self, overlays: list) -> None:
        self.overlays = overlays or []

    def add_asset(
        self, stage: str, path: str, provider: str, cost_usd: float,
        qa_report: dict | None = None,
    ) -> None:
        self.assets.append(
            {"stage": stage, "path": path, "provider": provider,
             "cost_usd": cost_usd, "qa_report": qa_report}
        )

    # tiện ích cho render()/RenderResult
    @property
    def piapi_task_id(self) -> str:
        return str(self.params.get("piapi_task_id", "") or "")

    @property
    def clips_used(self) -> int:
        return sum(1 for a in self.assets if a["stage"] == "video")
