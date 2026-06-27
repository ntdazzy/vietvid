"""Routing model video + ước tính chi phí — khóa theo PiAPI docs 2026-06-10.

Luật chốt (cập nhật 2026-06-11 sau khi bắt payload autovis THẬT):
autovis tạo video người bằng TEXT mô tả + 1 ảnh SẢN PHẨM (KHÔNG gửi ảnh mặt) →
né tường kiểm duyệt deepfake của PiAPI. Vì vậy KHÔNG còn dùng less-restriction:
- draft            → seedance-2-fast 480p (rẻ, CHỈ xem trước — không đăng)
- product_only     → seedance-2-fast 480p (mặc định như autovis; ảnh SP thật làm khung đầu)
- kol_full         → seedance-2-fast 480p, người = TEXT persona trong prompt (KHÔNG gửi mặt
                     → strict OK, không cần less-restriction, không cần Asset Library $15)
- premium          → seedance-2 (pro), 720p (upsell chất lượng cao hơn autovis)
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from config.settings import settings


@dataclass(frozen=True)
class VideoRoute:
    provider: str
    model_id: str
    resolution: str
    speed_tier: str  # fast | pro
    moderation_policy: str  # strict | less_restriction
    usd_per_second: float
    retry_allowed: bool  # strict: 1 retry; less_restriction: reject là final


def _price_table() -> dict[str, dict[str, float]]:
    try:
        return json.loads(settings.video_seedance_prices_json)
    except (ValueError, TypeError):
        return {}


def _price(model_id: str, resolution: str) -> float:
    table = _price_table()
    price = (table.get(model_id) or {}).get(resolution)
    if price is None:
        raise ValueError(
            f"Không có đơn giá cho model={model_id} resolution={resolution} — "
            "kiểm tra VIDEO_SEEDANCE_PRICES_JSON."
        )
    return float(price)


def route_video(mode: str, purpose: str, resolution: str | None = None) -> VideoRoute:
    """Chọn (model, resolution, giá) theo mode + purpose. ``resolution`` chỉ để override premium."""
    if purpose == "draft":
        model_id, res = "seedance-2-fast", settings.video_draft_resolution or "480p"
        speed, policy, retry = "fast", "strict", True
    elif mode == "premium":
        model_id, res = "seedance-2", (resolution or settings.video_premium_resolution or "720p")
        speed, policy, retry = "pro", "strict", True
    else:  # product_only & kol_full — đều text-based, ảnh SP thật, KHÔNG gửi mặt
        model_id, res = "seedance-2-fast", settings.video_resolution or "480p"
        speed, policy, retry = "fast", "strict", True
    return VideoRoute(
        provider=settings.video_provider,
        model_id=model_id,
        resolution=res,
        speed_tier=speed,
        moderation_policy=policy,
        usd_per_second=_price(model_id, res),
        retry_allowed=retry,
    )


def estimate_job_cost(
    mode: str, purpose: str, seconds: int, resolution: str | None = None
) -> dict:
    """Chi phí ước tính TRƯỚC khi chạy — web hiện số này ở nút Tạo."""
    route = route_video(mode, purpose, resolution)
    # Text-based như autovis: ảnh sản phẩm làm khung đầu. premium sinh ảnh hero Gemini; non-premium
    # bật clean-plate (V8.6 — tách SP khỏi ảnh marketing) cũng dùng tới 1 ảnh Gemini → reserve 1 ảnh
    # để settle khớp (crop pixel-gốc tốn $0, chỉ generative fallback tốn — reserve theo worst-case rẻ).
    n_images = (
        1
        if (purpose != "draft" and (mode == "premium" or settings.video_clean_plate_enabled))
        else 0
    )
    image_usd = round(n_images * float(settings.video_image_cost_usd), 4)
    video_usd = round(max(1, int(seconds)) * route.usd_per_second, 4)
    other_usd = 0.01  # voice vbee + compose/QA local
    total = round(image_usd + video_usd + other_usd, 4)
    return {
        "mode": mode,
        "purpose": purpose,
        "seconds": int(seconds),
        "model_id": route.model_id,
        "resolution": route.resolution,
        "speed_tier": route.speed_tier,
        "moderation_policy": route.moderation_policy,
        "usd_per_second": route.usd_per_second,
        "n_images": n_images,
        "image_usd": image_usd,
        "video_usd": video_usd,
        "other_usd": other_usd,
        "total_usd": total,
        "total_vnd": int(total * settings.fx_vnd_per_usd),
    }
