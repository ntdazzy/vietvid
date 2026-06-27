"""EventBus hướng sự kiện trên multiprocessing.Queue.

NGUYÊN TẮC: sự kiện chỉ chở **kiểu cơ bản** (ID, đường dẫn) để làm "tiếng chuông".
Không bao giờ đẩy object ORM hay text lớn qua Queue — object ORM khi pickle sẽ bị
"detached" khỏi Session (gây DetachedInstanceError), và payload lớn làm phình hàng đợi.
Tiến trình con nhận ID → tự query DB lấy chi tiết.
"""

from __future__ import annotations

from dataclasses import dataclass
from multiprocessing import Queue
from queue import Empty, Full

from core.logger import log_event, logger


@dataclass(frozen=True)
class Event:
    """Lớp gốc cho mọi sự kiện. Chỉ chứa primitive để pickle nhẹ và an toàn."""


@dataclass(frozen=True)
class ProductQualified(Event):
    product_id: int
    trace_id: str = ""


@dataclass(frozen=True)
class ScriptReady(Event):
    script_id: int
    json_path: str


@dataclass(frozen=True)
class RenderCompleted(Event):
    render_job_id: int


class EventBus:
    """Bọc multiprocessing.Queue, có backpressure qua maxsize."""

    def __init__(self, maxsize: int = 1000) -> None:
        self._queue: "Queue[Event]" = Queue(maxsize=maxsize)

    def publish(self, event: Event, timeout: float = 5.0) -> bool:
        try:
            self._queue.put(event, timeout=timeout)
            log_event("core", "event_publish", event_type=type(event).__name__)
            return True
        except Full:
            logger.warning(f"EventBus đầy (maxsize), bỏ sự kiện: {event!r}")
            return False

    def consume(self, timeout: float = 1.0) -> Event | None:
        try:
            event = self._queue.get(timeout=timeout)
            log_event("core", "event_consume", event_type=type(event).__name__)
            return event
        except Empty:
            return None

    def close(self) -> None:
        # cancel_join_thread: không chờ feeder thread → tiến trình thoát ngay, không treo lúc exit.
        self._queue.close()
        self._queue.cancel_join_thread()
