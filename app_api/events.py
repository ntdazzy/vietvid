"""Pub/sub trong-tiến-trình (asyncio) cho push real-time — hiện dùng push trạng thái thanh toán.

Đơn-tiến-trình (uvicorn 1 worker trên laptop) → dict[key, set[Queue]] là đủ. Đa-worker sau này
→ thay bằng Redis pub/sub cùng interface (subscribe/unsubscribe/publish).

publish() THREAD-SAFE: gọi được từ route async (loop thread) lẫn route sync (threadpool) —
dùng loop.call_soon_threadsafe để đẩy vào Queue đúng event loop. Không có subscriber → no-op.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict

_subs: dict[str, set[asyncio.Queue]] = defaultdict(set)
_loop: asyncio.AbstractEventLoop | None = None


def subscribe(key: str) -> asyncio.Queue:
    """Đăng ký nghe 1 key (gọi trong endpoint SSE — luôn ở event loop)."""
    global _loop
    _loop = asyncio.get_running_loop()  # bắt loop để publish cross-thread
    q: asyncio.Queue = asyncio.Queue(maxsize=16)
    _subs[key].add(q)
    return q


def unsubscribe(key: str, q: asyncio.Queue) -> None:
    subs = _subs.get(key)
    if subs:
        subs.discard(q)
        if not subs:
            _subs.pop(key, None)


def _deliver(key: str, data: dict) -> None:
    for q in list(_subs.get(key, ())):
        try:
            q.put_nowait(data)
        except asyncio.QueueFull:
            pass  # subscriber chậm → bỏ event, không chặn publisher


def publish(key: str, data: dict) -> None:
    """Gửi event tới mọi subscriber của key. An toàn từ mọi thread; no-op nếu chưa có loop/subscriber."""
    loop = _loop
    if loop is None or not _subs.get(key):
        return
    try:
        loop.call_soon_threadsafe(_deliver, key, data)
    except RuntimeError:
        pass  # loop đã đóng
