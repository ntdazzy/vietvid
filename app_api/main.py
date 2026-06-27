"""FastAPI app (M1) — auth · tenancy · wallet · jobs. Đứng trên engine stateless.

Chạy:  PYTHONUTF8=1 VIETVID_DATABASE_URL=... python -m uvicorn app_api.main:app --port 8099
Health: GET /health  →  {status, auth_mode, exec_mode}
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app_api import config
from app_api.routers import auth as auth_router
from app_api.routers import billing as billing_router
from app_api.routers import compose as compose_router
from app_api.routers import images as images_router
from app_api.routers import jobs as jobs_router
from app_api.routers import uploads as uploads_router
from app_api.routers import voice as voice_router
from app_api.routers import wallet as wallet_router
from app_api.wallet import WalletError, WalletNotFound

app = FastAPI(
    title="VietVid API",
    version="0.1.0-m1",
    description="SaaS tạo video AI giọng Việt — lớp HTTP đa-tenant (M1).",
)

_origins = [o.strip() for o in (config.CORS_ORIGINS or "*").split(",") if o.strip()] or ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials="*" not in _origins,   # credentials không hợp lệ với wildcard
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Image-Path"],         # text→video đọc path khung ảnh AI sinh ra
)

app.include_router(auth_router.router)
app.include_router(wallet_router.router)
app.include_router(jobs_router.router)
app.include_router(uploads_router.router)
app.include_router(voice_router.router)
app.include_router(billing_router.router)
app.include_router(images_router.router)
app.include_router(compose_router.router)


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {
        "status": "ok",
        "auth_mode": config.auth_mode(),
        "exec_mode": config.JOB_EXECUTION_MODE,
    }


@app.exception_handler(WalletNotFound)
def _wallet_notfound_handler(_: Request, exc: WalletNotFound) -> JSONResponse:
    # Ví thiếu = lỗi TRẠNG THÁI hệ thống (đáng lẽ tạo lúc bootstrap), KHÔNG phải lỗi client → 500.
    return JSONResponse(status_code=500, content={"detail": "Ví không tồn tại (lỗi trạng thái)"})


@app.exception_handler(WalletError)
def _wallet_error_handler(_: Request, exc: WalletError) -> JSONResponse:
    # InsufficientCredits đã được router map 402; còn lại = lỗi ví → 400.
    return JSONResponse(status_code=400, content={"detail": str(exc)})
