"""Cấu hình nền tảng runtime — admin sửa không cần deploy.

Đọc merge lên DEFAULTS (thiếu key luôn có giá trị an toàn). Ghi chỉ qua admin endpoint.
Giữ cấu hình "đổi được lúc chạy": chuỗi provider video, quota API, feature-flag theo gói.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app_api.models import VvPlatformConfig

DEFAULTS: dict = {
    # override chuỗi provider video (rỗng = dùng settings/env mặc định).
    "video_provider_chain": "",
    # quota tạo video qua API theo NGÀY cho mỗi org (0 = không giới hạn).
    "max_api_jobs_per_day": 200,
    # feature-flag theo gói — bật/tắt năng lực không cần deploy.
    "feature_flags": {
        "free": {"api_access": True, "batch": True},
        "pro": {"api_access": True, "batch": True},
    },
}

_ALLOWED = set(DEFAULTS.keys())


def get_config(session: Session) -> dict:
    """DEFAULTS ⊕ data đã lưu (shallow merge, feature_flags merge 1 cấp gói)."""
    row = session.get(VvPlatformConfig, 1)
    data = dict(row.data) if row and row.data else {}
    merged = {**DEFAULTS, **{k: v for k, v in data.items() if k in _ALLOWED}}
    # merge feature_flags theo từng gói để thiếu gói vẫn có default.
    ff = {**DEFAULTS["feature_flags"]}
    for plan, flags in (data.get("feature_flags") or {}).items():
        ff[plan] = {**ff.get(plan, {}), **(flags or {})}
    merged["feature_flags"] = ff
    return merged


def set_config(session: Session, patch: dict) -> dict:
    """Ghi đè các key hợp lệ trong patch vào hàng id=1. Trả config sau khi merge."""
    row = session.get(VvPlatformConfig, 1)
    if row is None:
        row = VvPlatformConfig(id=1, data={})
        session.add(row)
        session.flush()
    cur = dict(row.data or {})
    for k, v in patch.items():
        if k in _ALLOWED:
            cur[k] = v
    row.data = cur
    session.flush()
    return get_config(session)


def plan_flag(session: Session, plan_code: str, flag: str, default: bool = True) -> bool:
    """Cờ feature theo gói (thiếu → default)."""
    ff = get_config(session)["feature_flags"]
    return bool(ff.get(plan_code, ff.get("free", {})).get(flag, default))
