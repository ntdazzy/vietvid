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


def _float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, "").strip() or default)
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
CREDIT_PRICE_VND: int = _int("CREDIT_PRICE_VND", 150)   # 1 credit = 150đ (giá khách MUA credit)
USD_TO_VND: int = _int("USD_TO_VND", 25400)             # tỉ giá USD→VND (quy giá VỐN provider)

# Markup: GIÁ BÁN render = giá VỐN provider × hệ số này. 1.0 = bán đúng giá vốn (lời 0 → LỖ sau phí).
# 2.0 = lời ~50% trên mỗi video. CHỈ ảnh hưởng số credit TRỪ khi render job; KHÔNG đổi giá khách
# mua credit (pack/topup). Chỉnh 1 con số để đổi biên lợi nhuận toàn hệ.
VIDEO_MARGIN_MULTIPLIER: float = _float("VIDEO_MARGIN_MULTIPLIER", 2.0)

# Khuyến mãi NẠP LẦN ĐẦU: tặng thêm bấy nhiêu credit ở lần nạp thành công ĐẦU TIÊN của org.
# CỐ ĐỊNH (không theo %) → tặng tối đa đúng số này dù khách nạp bao nhiêu → KHÔNG bao giờ lỗ.
# Muốn được tặng phải TRẢ TIỀN (chống farm tài khoản free). 0 = tắt.
FIRST_TOPUP_BONUS_CREDITS: int = _int("FIRST_TOPUP_BONUS_CREDITS", 300)

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
# Credit tặng khi tạo tenant lần đầu (BONUS ledger).
# 0 = KHÔNG tặng khi đăng ký → chống farm (tạo nhiều nick KHÔNG nhận free xu nào). Người mới phải
# nạp mới tạo được; nạp lần đầu được tặng FIRST_TOPUP_BONUS_CREDITS (chỉ người TRẢ TIỀN mới có).
# Khách xem chất lượng qua video MẪU làm sẵn (không tốn chi phí render). Đổi qua env nếu muốn cho
# dùng thử free (chấp nhận rủi ro farm + lỗ phí render cho người không trả tiền).
FREE_GRANT_CREDITS: int = _int("FREE_GRANT_CREDITS", 0)

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


# ── MoMo (cổng chính, Sóng 3). Trống = chưa cấu hình → cổng momo báo lỗi. ──
MOMO_PARTNER_CODE: str = _str("VIETVID_MOMO_PARTNER_CODE")
MOMO_ACCESS_KEY: str = _str("VIETVID_MOMO_ACCESS_KEY")
MOMO_SECRET_KEY: str = _str("VIETVID_MOMO_SECRET_KEY")
MOMO_ENDPOINT: str = _str("VIETVID_MOMO_ENDPOINT", "https://test-payment.momo.vn/v2/gateway/api/create")
MOMO_RETURN_URL: str = _str("VIETVID_MOMO_RETURN_URL", "http://localhost:3000/billing/return")
MOMO_IPN_URL: str = _str("VIETVID_MOMO_IPN_URL", "http://localhost:8099/v1/billing/ipn/momo")


def momo_configured() -> bool:
    return bool(MOMO_PARTNER_CODE and MOMO_ACCESS_KEY and MOMO_SECRET_KEY)


# ── Chuyển khoản ngân hàng VietQR + tự đối soát SePay (Sóng 3B). ──────────
# QR sinh keyless qua img.vietqr.io; SePay đọc biến động số dư bank → webhook tự cộng.
# Trống = chưa cấu hình → cổng bank báo "chưa bật".
BANK_BIN: str = _str("VIETVID_BANK_BIN")               # mã BIN/định danh ngân hàng (vd 970436 = VCB)
BANK_ACCOUNT_NUMBER: str = _str("VIETVID_BANK_ACCOUNT")
BANK_ACCOUNT_NAME: str = _str("VIETVID_BANK_ACCOUNT_NAME")
BANK_NAME: str = _str("VIETVID_BANK_NAME")             # tên hiển thị (vd "Vietcombank")
BANK_QR_TEMPLATE: str = _str("VIETVID_BANK_QR_TEMPLATE", "compact2")
SEPAY_API_TOKEN: str = _str("VIETVID_SEPAY_TOKEN")     # token xác thực webhook SePay (hoặc nguồn báo-có tự host)

# ── Tự đối soát MIỄN PHÍ qua email báo-có (thay SePay). Poll hòm mail nhận email
# "biến động số dư" của ngân hàng (MB Bank) qua IMAP — KHÔNG lưu mật khẩu bank,
# chỉ cần app-password của email. Trống = poller không chạy. ───────────────────
BANK_EMAIL_IMAP_HOST: str = _str("VIETVID_BANK_EMAIL_IMAP", "imap.gmail.com")
BANK_EMAIL_USER: str = _str("VIETVID_BANK_EMAIL_USER")            # email nhận báo-có
BANK_EMAIL_PASSWORD: str = _str("VIETVID_BANK_EMAIL_PASSWORD")    # APP-PASSWORD (không phải pass bank)
BANK_EMAIL_SENDER: str = _str("VIETVID_BANK_EMAIL_SENDER")        # lọc người gửi (vd MB: no-reply@mbbank.com.vn)
BANK_POLL_INTERVAL_S: int = _int("VIETVID_BANK_POLL_INTERVAL_S", 45)

# Nạp số tiền tuỳ ý (ngoài gói): chặn dưới/trên.
TOPUP_MIN_VND: int = _int("VIETVID_TOPUP_MIN_VND", 20_000)
TOPUP_MAX_VND: int = _int("VIETVID_TOPUP_MAX_VND", 50_000_000)


def bank_configured() -> bool:
    return bool(BANK_BIN and BANK_ACCOUNT_NUMBER and BANK_ACCOUNT_NAME)


def bank_email_configured() -> bool:
    return bool(BANK_EMAIL_USER and BANK_EMAIL_PASSWORD)


# ── Quan sát + an toàn prod (Sóng 1A) ───────────────────────────────────
# Log: mức + định dạng. JSON cho prod (máy đọc), text cho dev (người đọc).
LOG_LEVEL: str = _str("VIETVID_LOG_LEVEL", "INFO").upper()
LOG_JSON: bool = _bool("VIETVID_LOG_JSON", IS_PROD)

# Security headers (HSTS/XFO/nosniff/referrer). Bật mặc định ở prod.
SECURITY_HEADERS_ENABLED: bool = _bool("VIETVID_SECURITY_HEADERS", IS_PROD)

# Rate limit (cửa sổ cố định trong-tiến-trình, MVP 1-box). "N/giây".
# Prod đa-instance nên chuyển sang Redis — knob giữ nguyên, chỉ đổi backend.
RATE_LIMIT_ENABLED: bool = _bool("VIETVID_RATE_LIMIT", True)
RATE_LIMIT_DEFAULT: str = _str("VIETVID_RL_DEFAULT", "120/60")   # mọi route / IP
RATE_LIMIT_AUTH: str = _str("VIETVID_RL_AUTH", "10/60")          # login/register/reset/dev-token
RATE_LIMIT_EXPENSIVE: str = _str("VIETVID_RL_EXPENSIVE", "30/60")  # jobs/images/voice/compose

# Giá trị placeholder của DEV_JWT_SECRET — startup gate từ chối boot prod nếu còn cái này.
_DEV_JWT_PLACEHOLDER: str = "vietvid-dev-secret-change-me-please-32b+"


# ── Vòng đời auth (Sóng 1B) ─────────────────────────────────────────────
# URL frontend để dựng link reset/verify trong email.
APP_BASE_URL: str = _str("VIETVID_APP_URL", "http://localhost:3000")
ACCESS_TOKEN_TTL: int = _int("VIETVID_ACCESS_TTL", 3600)            # 1h
REFRESH_TOKEN_TTL: int = _int("VIETVID_REFRESH_TTL", 60 * 60 * 24 * 30)  # 30 ngày
RESET_TOKEN_TTL: int = _int("VIETVID_RESET_TTL", 3600)             # 1h
VERIFY_TOKEN_TTL: int = _int("VIETVID_VERIFY_TTL", 60 * 60 * 24)   # 24h

# Email (SMTP). Để TRỐNG = dev: token/link ghi ra LOG để bạn lấy thử (không gửi thật).
SMTP_HOST: str = _str("VIETVID_SMTP_HOST")
SMTP_PORT: int = _int("VIETVID_SMTP_PORT", 587)
SMTP_USER: str = _str("VIETVID_SMTP_USER")
SMTP_PASSWORD: str = _str("VIETVID_SMTP_PASSWORD")
SMTP_FROM: str = _str("VIETVID_SMTP_FROM", "VietVid <no-reply@vietvid.vn>")


def email_configured() -> bool:
    return bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD)


# ── Reaper job treo (Sóng 2) ────────────────────────────────────────────
# Job inline kẹt RUNNING khi tiến trình chết (redeploy/crash) → HOLD treo mãi. Reaper quét
# job non-terminal quá hạn → hoàn HOLD + đặt CANCELLED. Chạy 1 lần lúc boot + định kỳ.
REAPER_ENABLED: bool = _bool("VIETVID_REAPER", True)
REAPER_STUCK_MINUTES: int = _int("VIETVID_REAPER_STUCK_MIN", 15)
REAPER_INTERVAL_SECONDS: int = _int("VIETVID_REAPER_INTERVAL", 600)

# ── Lưu trữ media (Sóng 2) — S3/R2. Trống = lưu file local (MVP 1-box). ──
STORAGE_BUCKET: str = _str("VIETVID_S3_BUCKET")
STORAGE_ENDPOINT: str = _str("VIETVID_S3_ENDPOINT")        # R2/minio; trống = AWS S3
STORAGE_ACCESS_KEY: str = _str("VIETVID_S3_ACCESS_KEY")
STORAGE_SECRET_KEY: str = _str("VIETVID_S3_SECRET_KEY")
STORAGE_REGION: str = _str("VIETVID_S3_REGION", "auto")
STORAGE_PUBLIC_BASE: str = _str("VIETVID_S3_PUBLIC_BASE")  # CDN base (tuỳ chọn)
# Token ký URL video (xem/chia sẻ không cần Bearer). Dùng DEV_JWT_SECRET nếu trống.
MEDIA_URL_TTL: int = _int("VIETVID_MEDIA_URL_TTL", 3600)
MEDIA_SHARE_TTL: int = _int("VIETVID_MEDIA_SHARE_TTL", 60 * 60 * 24 * 30)  # link chia sẻ 30 ngày


def storage_configured() -> bool:
    return bool(STORAGE_BUCKET and STORAGE_ACCESS_KEY and STORAGE_SECRET_KEY)


# ── Admin (Sóng 4) — email super-admin (phẩy phân tách). Bootstrap đơn giản, không cần bảng. ──
ADMIN_EMAILS: str = _str("VIETVID_ADMIN_EMAILS")


def admin_email_set() -> set[str]:
    return {e.strip().lower() for e in ADMIN_EMAILS.split(",") if e.strip()}


def is_admin_email(email: str) -> bool:
    return bool(email) and email.strip().lower() in admin_email_set()
