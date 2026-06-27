"""FastAPI app (M1) — auth · tenancy · wallet · jobs. Đứng trên engine stateless.

Chạy:  PYTHONUTF8=1 VIETVID_DATABASE_URL=... python -m uvicorn app_api.main:app --port 8099
Health: GET /health  →  {status, auth_mode, exec_mode}
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app_api import config
from app_api.observability import (
    RequestContextMiddleware,
    SecurityHeadersMiddleware,
    configure_logging,
    install_exception_handlers,
)
from app_api.ratelimit import RateLimitMiddleware
from app_api.routers import admin as admin_router
from app_api.routers import affiliate as affiliate_router
from app_api.routers import auth as auth_router
from app_api.routers import billing as billing_router
from app_api.routers import compose as compose_router
from app_api.routers import content as content_router
from app_api.routers import images as images_router
from app_api.routers import jobs as jobs_router
from app_api.routers import media as media_router
from app_api.routers import notifications as notifications_router
from app_api.routers import orgs as orgs_router
from app_api.routers import products as products_router
from app_api.routers import script as script_router
from app_api.routers import series as series_router
from app_api.routers import uploads as uploads_router
from app_api.routers import voice as voice_router
from app_api.routers import wallet as wallet_router
from app_api.startup_checks import db_healthy, validate_prod_config
from app_api.wallet import WalletError, WalletNotFound

configure_logging()


@asynccontextmanager
async def lifespan(_: FastAPI):
    import asyncio
    import logging

    # Fail-fast: từ chối boot nếu cấu hình prod không an toàn (placeholder secret, CORS=*, ...).
    validate_prod_config()

    log = logging.getLogger("vietvid")
    reaper_task = None
    if config.REAPER_ENABLED:
        from app_api.reaper import reap_stuck_jobs

        # 1) quét ngay lúc boot — dọn job mồ côi từ tiến trình trước (redeploy/crash).
        try:
            await asyncio.to_thread(reap_stuck_jobs)
        except Exception:  # noqa: BLE001
            log.exception("reaper: lỗi lúc boot")

        # 2) vòng lặp định kỳ.
        async def _loop():
            while True:
                await asyncio.sleep(config.REAPER_INTERVAL_SECONDS)
                try:
                    await asyncio.to_thread(reap_stuck_jobs)
                except Exception:  # noqa: BLE001
                    log.exception("reaper: lỗi vòng lặp")

        reaper_task = asyncio.create_task(_loop())

    try:
        yield
    finally:
        if reaper_task is not None:
            reaper_task.cancel()


app = FastAPI(
    title="VietVid API",
    version="0.1.0-m1",
    description="SaaS tạo video AI giọng Việt — lớp HTTP đa-tenant (M1).",
    lifespan=lifespan,
)

install_exception_handlers(app)

# Thứ tự add = NGƯỢC với thứ tự chạy (cái add SAU bọc NGOÀI). Mong muốn từ ngoài vào:
# CORS → RequestContext(request-id+log) → RateLimit → SecurityHeaders → app.
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestContextMiddleware)

_origins = [o.strip() for o in (config.CORS_ORIGINS or "*").split(",") if o.strip()] or ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials="*" not in _origins,   # credentials không hợp lệ với wildcard
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Image-Path", "X-Request-Id"],  # text→video đọc path khung ảnh AI sinh ra
)

app.include_router(auth_router.router)
app.include_router(orgs_router.router)
app.include_router(wallet_router.router)
app.include_router(jobs_router.router)
app.include_router(uploads_router.router)
app.include_router(voice_router.router)
app.include_router(billing_router.router)
app.include_router(images_router.router)
app.include_router(compose_router.router)
app.include_router(content_router.router)
app.include_router(media_router.router)
app.include_router(admin_router.router)
app.include_router(affiliate_router.router)
app.include_router(affiliate_router.redirect_router)
app.include_router(notifications_router.router)
app.include_router(series_router.router)
app.include_router(products_router.router)
app.include_router(script_router.router)


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {
        "status": "ok",
        "auth_mode": config.auth_mode(),
        "exec_mode": config.JOB_EXECUTION_MODE,
    }


@app.get("/health/ready", tags=["meta"])
def health_ready() -> JSONResponse:
    """Readiness: kiểm tra Postgres thật. 503 nếu DB chết → load balancer ngừng route."""
    ok = db_healthy()
    return JSONResponse(
        status_code=200 if ok else 503,
        content={"status": "ready" if ok else "degraded", "db": ok},
    )


@app.exception_handler(WalletNotFound)
def _wallet_notfound_handler(_: Request, exc: WalletNotFound) -> JSONResponse:
    # Ví thiếu = lỗi TRẠNG THÁI hệ thống (đáng lẽ tạo lúc bootstrap), KHÔNG phải lỗi client → 500.
    return JSONResponse(status_code=500, content={"detail": "Ví không tồn tại (lỗi trạng thái)"})


@app.exception_handler(WalletError)
def _wallet_error_handler(_: Request, exc: WalletError) -> JSONResponse:
    # InsufficientCredits đã được router map 402; còn lại = lỗi ví → 400.
    return JSONResponse(status_code=400, content={"detail": str(exc)})
