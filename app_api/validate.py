"""validate_and_clamp (mục 7.1 plan) — chặn/giới hạn input TRƯỚC khi HOLD/enqueue.

Lỗi đầu vào (mode lạ, seconds≤0) → ValidationError (router → 422), CHƯA tốn credit/i2v.
Vượt giới hạn gói (seconds/độ phân giải) → CLAMP về trần gói + ghi note (không từ chối) →
est/hold tính trên giá trị đã clamp. M1 giới hạn tối thiểu; gói chi tiết = M2 (bảng plans).
"""

from __future__ import annotations

_KNOWN_MODES = {"product_ad", "premium", "kol_full", "long_narrative", "film_recap"}
_KNOWN_PURPOSES = {"final", "draft"}
_KNOWN_OVERLAY = {"allow", "require", "forbid"}
_RES_ORDER = {"480p": 1, "720p": 2, "1080p": 3}

# Giới hạn theo plan_code (M1 tối thiểu — Free ≤480p/≤20s; trả phí rộng hơn).
_PLAN_LIMITS = {
    "free": {"max_seconds": 20, "max_resolution": "480p"},
    "pro": {"max_seconds": 60, "max_resolution": "1080p"},
    "business": {"max_seconds": 120, "max_resolution": "1080p"},
}
_DEFAULT_LIMIT = {"max_seconds": 60, "max_resolution": "1080p"}


class ValidationError(Exception):
    """Lỗi đầu vào → 422, chưa enqueue/charge."""


def _cap_resolution(res: str, cap: str) -> str:
    if _RES_ORDER.get(res, 99) > _RES_ORDER.get(cap, 99):
        return cap
    return res


def validate_and_clamp(spec_input: dict, plan_code: str = "free") -> tuple[dict, list[str]]:
    """Trả (spec_input đã clamp, notes). Raise ValidationError nếu input hỏng."""
    d = dict(spec_input)
    mode = str(d.get("mode", "product_ad"))
    purpose = str(d.get("purpose", "final"))
    if mode not in _KNOWN_MODES:
        raise ValidationError(f"mode không hợp lệ: {mode}")
    if purpose not in _KNOWN_PURPOSES:
        raise ValidationError(f"purpose không hợp lệ: {purpose}")
    try:
        seconds = int(d.get("seconds", 15))
    except (ValueError, TypeError) as exc:
        raise ValidationError("seconds phải là số nguyên") from exc
    if seconds <= 0:
        raise ValidationError("seconds phải > 0")

    res = str(d.get("resolution", "720p"))
    if res not in _RES_ORDER:
        raise ValidationError(f"resolution không hợp lệ: {res}")

    overlay = str(d.get("overlay_policy", "allow") or "allow")
    if overlay not in _KNOWN_OVERLAY:
        raise ValidationError(f"overlay_policy không hợp lệ: {overlay} (allow|require|forbid)")

    limits = _PLAN_LIMITS.get(plan_code, _DEFAULT_LIMIT)
    notes: list[str] = []
    if seconds > limits["max_seconds"]:
        notes.append(f"thời lượng {seconds}s → trần gói {limits['max_seconds']}s")
        seconds = limits["max_seconds"]
    capped_res = _cap_resolution(res, limits["max_resolution"])
    if capped_res != res:
        notes.append(f"độ phân giải {res} → trần gói {capped_res}")
        res = capped_res

    d["seconds"] = seconds
    d["resolution"] = res
    return d, notes
