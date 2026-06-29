"""Kiểm tra lúc khởi động (Sóng 1A): fail-fast khi cấu hình prod KHÔNG an toàn + DB liveness.

Trước đây app boot prod vẫn chạy dù `DEV_JWT_SECRET` còn là placeholder (ai cũng giả mạo
được token) hoặc `CORS_ORIGINS=*`. Gate này CHẶN boot trong các trường hợp đó.

Chỉ siết khi IS_PROD. Dev vẫn thoải mái.
"""

from __future__ import annotations

import logging

from sqlalchemy import text

from app_api import config
from app_api.db import _get_engine
from core.config_checks import looks_real_secret

log = logging.getLogger("vietvid")


class UnsafeProdConfig(RuntimeError):
    """Cấu hình prod thiếu an toàn — từ chối khởi động."""


def validate_prod_config() -> None:
    """Ném UnsafeProdConfig nếu đang prod mà có lỗ hổng cấu hình nghiêm trọng."""
    if not config.IS_PROD:
        return

    problems: list[str] = []

    # 1) Dev-auth (HS256 tự phát) KHÔNG được bật ở prod khi không dùng Supabase — token giả mạo được.
    if config.auth_mode() == "dev":
        if config.DEV_JWT_SECRET == config._DEV_JWT_PLACEHOLDER or not looks_real_secret(
            config.DEV_JWT_SECRET, min_length=24
        ):
            problems.append(
                "DEV_JWT_SECRET vẫn là placeholder/yếu trong khi không có Supabase → "
                "token có thể bị giả mạo. Đặt SUPABASE_* (khuyến nghị) hoặc DEV_JWT_SECRET mạnh."
            )

    # 2) CORS không được để wildcard ở prod.
    if (config.CORS_ORIGINS or "*").strip() == "*":
        problems.append("CORS_ORIGINS=* ở prod → API mở cho mọi origin. Đặt domain cụ thể.")

    # 3) Cổng dev (dev-token / dev-billing) phải tắt ở prod.
    if config.DEV_AUTH_ENABLED:
        problems.append("VIETVID_DEV_AUTH bật ở prod → tắt (để rỗng).")
    if config.BILLING_DEV_ENABLED:
        problems.append("VIETVID_BILLING_DEV bật ở prod → tắt (để rỗng).")

    # 4) RLS phải được enforce ở prod: app KHÔNG được kết nối Postgres bằng role
    #    superuser / BYPASSRLS — nếu không, FORCE RLS bị vượt mặt và cách ly tenant
    #    (vietvid.current_org) coi như vô hiệu → rò dữ liệu chéo tổ chức.
    try:
        with _get_engine().connect() as conn:
            row = conn.execute(
                text("SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = current_user")
            ).first()
        if row and (row[0] or row[1]):
            problems.append(
                "App kết nối Postgres bằng role superuser/BYPASSRLS → FORCE RLS bị vô hiệu, "
                "cách ly tenant KHÔNG đảm bảo. Dùng role thường (VIETVID_DB_APP_ROLE) không có "
                "SUPERUSER/BYPASSRLS và đã GRANT đủ quyền bảng."
            )
    except Exception:  # noqa: BLE001 — lỗi kiểm tra không chặn boot; chỉ cảnh báo.
        log.warning("startup: không kiểm tra được RLS role (bỏ qua assertion).")

    if problems:
        msg = "Cấu hình prod không an toàn:\n  - " + "\n  - ".join(problems)
        log.error(msg)
        raise UnsafeProdConfig(msg)
    log.info("startup: cấu hình prod hợp lệ.")


def db_healthy() -> bool:
    """SELECT 1 — dùng cho readiness probe ở /health."""
    try:
        with _get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:  # noqa: BLE001 — readiness check phải trả bool, không ném.
        log.exception("db_healthy: kết nối Postgres lỗi")
        return False
