"""Cầu nối gọi coroutine LLM (async) từ code đồng bộ.

Bộ não V5 (variant_batch/variant_review) giữ API ĐỒNG BỘ (orchestrator/dashboard gọi sync),
nhưng client LLM chỉ có complete() async. Helper này chạy coroutine an toàn ở mọi ngữ cảnh:
- Không có event loop đang chạy (orchestrator worker, FastAPI sync route, test sync) → asyncio.run thẳng.
- Đang trong event loop (vd async route) → chạy ở thread riêng với loop mới, tránh lỗi nested asyncio.run.

CHỈ chạm tới khi ONLINE (use_fake_clients=false); đường offline/fake không gọi helper này.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine
from concurrent.futures import ThreadPoolExecutor
from typing import Any, TypeVar

T = TypeVar("T")


def run_coro_blocking(make_coro: Callable[[], Coroutine[Any, Any, T]]) -> T:
    """Chạy coroutine (do make_coro tạo) đồng bộ, an toàn cả khi đã ở trong event loop."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(make_coro())
    # Đang trong event loop → chạy coroutine mới ở thread riêng để không nested-run.
    with ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(lambda: asyncio.run(make_coro())).result()
