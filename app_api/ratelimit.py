"""Rate limit chống lạm dụng (Sóng 1A).

Cửa sổ cố định TRONG-TIẾN-TRÌNH (dict + lock) — đủ cho MVP 1-box và KHÔNG cần Redis/khoá.
Prod đa-instance: thay `_hits` bằng Redis INCR+EXPIRE (knob config giữ nguyên).

Chặn:
- auth (login/register/reset/dev-token): mặc định 10 req / 60s / IP → cản brute-force + farm
  300 credit free.
- expensive (jobs POST / images / voice / compose): 30 / 60s → cản đốt tiền provider + ffmpeg.
- default: 120 / 60s / IP cho mọi route còn lại.

Khoá theo (IP, bucket). IP lấy từ X-Forwarded-For (sau proxy) rồi tới client trực tiếp.
"""

from __future__ import annotations

import threading
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app_api import config

# (ip, bucket) -> (window_start_epoch, count)
_hits: dict[tuple[str, str], tuple[float, int]] = {}
_lock = threading.Lock()

_AUTH_PATHS = ("/v1/auth/login", "/v1/auth/register", "/v1/auth/forgot",
               "/v1/auth/reset", "/v1/auth/verify", "/v1/auth/resend-verify",
               "/v1/auth/change-password", "/v1/dev/token")
_EXPENSIVE_PATHS = ("/v1/jobs", "/v1/images/generate", "/v1/voice/preview", "/v1/compose")


def _parse(spec: str, fallback: tuple[int, int]) -> tuple[int, int]:
    try:
        n, s = spec.split("/")
        return int(n), int(s)
    except (ValueError, AttributeError):
        return fallback


def _bucket_for(method: str, path: str) -> tuple[str, tuple[int, int]]:
    if path.startswith(_AUTH_PATHS):
        return "auth", _parse(config.RATE_LIMIT_AUTH, (10, 60))
    if method == "POST" and path.startswith(_EXPENSIVE_PATHS):
        return "expensive", _parse(config.RATE_LIMIT_EXPENSIVE, (30, 60))
    return "default", _parse(config.RATE_LIMIT_DEFAULT, (120, 60))


def _client_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _allow(ip: str, bucket: str, limit: int, window: int) -> tuple[bool, int]:
    """True nếu còn quota. Trả (allowed, retry_after_seconds)."""
    now = time.time()
    key = (ip, bucket)
    with _lock:
        start, count = _hits.get(key, (now, 0))
        if now - start >= window:
            start, count = now, 0          # cửa sổ mới
        count += 1
        _hits[key] = (start, count)
        if count > limit:
            return False, int(window - (now - start)) + 1
        return True, 0


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if not config.RATE_LIMIT_ENABLED:
            return await call_next(request)
        bucket, (limit, window) = _bucket_for(request.method, request.url.path)
        ip = _client_ip(request)
        allowed, retry = _allow(ip, bucket, limit, window)
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Quá nhiều yêu cầu, thử lại sau."},
                headers={"Retry-After": str(retry)},
            )
        return await call_next(request)
