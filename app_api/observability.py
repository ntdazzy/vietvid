"""Quan sát hệ thống (Sóng 1A): logging có request-id + access log + bắt lỗi toàn cục.

app_api trước đây KHÔNG log gì → mù khi sự cố prod. Module này:
- gắn mỗi request một `request_id` (header X-Request-Id, tạo nếu thiếu) qua contextvar,
- log 1 dòng access mỗi request (method, path, status, thời gian ms, request_id, org),
- bắt MỌI lỗi chưa xử lý → log kèm traceback + trả envelope 500 an toàn (không lộ stack).

Dùng stdlib `logging` (không kéo loguru của project cũ vào lớp HTTP).
"""

from __future__ import annotations

import json
import logging
import sys
import time
import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app_api import config

# request_id của request hiện tại — đọc được ở bất kỳ đâu trong cùng task.
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")

log = logging.getLogger("vietvid")


class _RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get()
        return True


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "request_id": getattr(record, "request_id", "-"),
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging() -> None:
    """Cấu hình root logger một lần. JSON ở prod, text ở dev."""
    root = logging.getLogger()
    root.setLevel(config.LOG_LEVEL)
    # bỏ handler cũ để gọi nhiều lần không nhân đôi dòng log.
    for h in list(root.handlers):
        root.removeHandler(h)
    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(_RequestIdFilter())
    if config.LOG_JSON:
        handler.setFormatter(_JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)-5s [%(request_id)s] %(name)s: %(message)s",
                datefmt="%H:%M:%S",
            )
        )
    root.addHandler(handler)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Gắn request_id, đo thời gian, log 1 dòng access mỗi request."""

    async def dispatch(self, request: Request, call_next) -> Response:
        rid = request.headers.get("x-request-id") or uuid.uuid4().hex[:16]
        token = request_id_ctx.set(rid)
        started = time.monotonic()
        try:
            response = await call_next(request)
            dur_ms = round((time.monotonic() - started) * 1000, 1)
            response.headers["X-Request-Id"] = rid
            # log TRƯỚC khi reset contextvar để dòng access mang đúng request_id.
            log.info(
                "%s %s -> %s (%sms)",
                request.method,
                request.url.path,
                response.status_code,
                dur_ms,
            )
            return response
        finally:
            request_id_ctx.reset(token)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Thêm header bảo mật chuẩn (chống clickjacking / MIME-sniffing / rò referrer).

    HSTS chỉ phát khi đã HTTPS (tránh tự khoá khi chạy http local).
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("X-XSS-Protection", "0")
        if request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https":
            response.headers.setdefault(
                "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
            )
        return response


def install_exception_handlers(app) -> None:
    """Bắt lỗi chưa xử lý → 500 envelope an toàn + log traceback (kèm request_id)."""

    from fastapi.exceptions import RequestValidationError
    from starlette.exceptions import HTTPException as StarletteHTTPException

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:  # noqa: ANN001
        log.exception("unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Lỗi hệ thống. Vui lòng thử lại.",
                "request_id": request_id_ctx.get(),
            },
        )

    # giữ hành vi mặc định của HTTPException/Validation nhưng kèm request_id để debug.
    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException) -> JSONResponse:  # noqa: ANN001
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "request_id": request_id_ctx.get()},
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError) -> JSONResponse:  # noqa: ANN001
        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors(), "request_id": request_id_ctx.get()},
        )
