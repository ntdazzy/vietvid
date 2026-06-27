"""Config app_api — đọc từ env (M1). M2+ sẽ hợp nhất vào config/registry.py.

CREDIT_PRICE_VND / USD_TO_VND là ĐIỂM QUY ĐỔI USD→credit DUY NHẤT (mục 6.3 plan):
credits(usd) = ceil(usd * USD_TO_VND / CREDIT_PRICE_VND). Snapshot vào mỗi ledger row.
"""

from __future__ import annotations

import os


def _int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, "").strip() or default)
    except ValueError:
        return default


def _str(name: str, default: str = "") -> str:
    return (os.environ.get(name) or "").strip() or default


def _bool(name: str, default: bool) -> bool:
    v = (os.environ.get(name) or "").strip().lower()
    if not v:
        return default
    return v in ("1", "true", "yes", "on")


# Môi trường: "production" tự TẮT các cổng dev (dev-token, dev-billing) để an toàn.
ENV: str = _str("VIETVID_ENV", "development").lower()
IS_PROD: bool = ENV == "production"


# DB: ưu tiên VIETVID_DATABASE_URL, fallback DATABASE_URL, cuối cùng local vietvid.
DATABASE_URL: str = (
    os.environ.get("VIETVID_DATABASE_URL")
    or os.environ.get("DATABASE_URL")
    or "postgresql+psycopg2://vietvid:vietvid@localhost:5432/vietvid"
)

# Role app connect (non-superuser để FORCE RLS có hiệu lực — mục 6.1 plan). Để rỗng = dùng URL.
DB_APP_ROLE: str = os.environ.get("VIETVID_DB_APP_ROLE", "").strip()

# Quy đổi tiền (mục 6.3, 10.8 plan)
CREDIT_PRICE_VND: int = _int("CREDIT_PRICE_VND", 150)   # 1 credit = 150đ
USD_TO_VND: int = _int("USD_TO_VND", 25400)             # tỉ giá USD→VND

# GUC key cho RLS (mục 6.1)
RLS_GUC: str = "vietvid.current_org"

# ── Auth (mục 7, 4 plan) — DUAL-MODE ────────────────────────────────────
# Supabase: verify JWT bằng JWKS (RS256/ES256, khoá bất đối xứng mới) HOẶC HS256 legacy secret.
# Nếu KHÔNG cấu hình Supabase → mode "dev": tự verify/ phát HS256 bằng DEV_JWT_SECRET (verify ngay
# trên Postgres thật, không cần Supabase). Cắm Supabase thật sau = chỉ set env, KHÔNG sửa code.
SUPABASE_JWKS_URL: str = _str("SUPABASE_JWKS_URL")           # vd https://<ref>.supabase.co/auth/v1/.well-known/jwks.json
SUPABASE_JWT_SECRET: str = _str("SUPABASE_JWT_SECRET")       # HS256 legacy (project JWT secret)
SUPABASE_JWT_AUD: str = _str("SUPABASE_JWT_AUD", "authenticated")
SUPABASE_JWT_ISSUER: str = _str("SUPABASE_JWT_ISSUER")       # tuỳ chọn, vd https://<ref>.supabase.co/auth/v1
DEV_JWT_SECRET: str = _str("DEV_JWT_SECRET", "vietvid-dev-secret-change-me-please-32b+")
# /v1/dev/token chỉ bật khi đang ở dev-mode (không có Supabase) VÀ cờ này bật. Prod → tắt.
DEV_AUTH_ENABLED: bool = _bool("VIETVID_DEV_AUTH", not IS_PROD)


def auth_mode() -> str:
    """\"supabase\" nếu có JWKS_URL hoặc JWT_SECRET; ngược lại \"dev\" (HS256 DEV_JWT_SECRET)."""
    return "supabase" if (SUPABASE_JWKS_URL or SUPABASE_JWT_SECRET) else "dev"


# ── Tenancy / jobs runtime ──────────────────────────────────────────────
# Credit tặng khi tạo tenant lần đầu (BONUS ledger). Reset hàng tháng = M2.
# Mặc định 300: 1 draft 5s/480p HOLD = ceil(70×1.5) = 105 → phải > 1 hold, nếu không user free
# mới KHÔNG tạo nổi 1 video nào (402 ngay). 300 ≈ vài draft thử. Chỉnh qua env theo kinh tế thật.
FREE_GRANT_CREDITS: int = _int("FREE_GRANT_CREDITS", 300)

# inline = chạy render qua BackgroundTasks ngay tiến trình app (M1, chưa có Arq);
# queue  = enqueue Arq (item 2). POST /jobs giữ nguyên hợp đồng, chỉ đổi cách thực thi.
JOB_EXECUTION_MODE: str = _str("JOB_EXECUTION_MODE", "inline").lower()

# CORS cho frontend (item 4). "*" cho dev; production set domain cụ thể (phẩy phân tách).
CORS_ORIGINS: str = _str("CORS_ORIGINS", "*")

# ── Billing (mục 7.3) ───────────────────────────────────────────────────
# VNPay: để TRỐNG = chưa cấu hình → cổng vnpay báo "chưa cấu hình"; dev adapter vẫn nạp được.
VNPAY_TMN_CODE: str = _str("VNPAY_TMN_CODE")
VNPAY_HASH_SECRET: str = _str("VNPAY_HASH_SECRET")
VNPAY_URL: str = _str("VNPAY_URL", "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html")
VNPAY_RETURN_URL: str = _str("VNPAY_RETURN_URL", "http://localhost:3000/billing/return")
# Bật cổng "dev" (nạp credit tức thì, KHÔNG qua cổng thật) — chỉ local/test. Prod → tắt.
BILLING_DEV_ENABLED: bool = _bool("VIETVID_BILLING_DEV", not IS_PROD)


def vnpay_configured() -> bool:
    return bool(VNPAY_TMN_CODE and VNPAY_HASH_SECRET)
