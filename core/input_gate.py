"""Cổng input CỨNG (V7-B2): chặn pipeline khi sản phẩm thiếu data thật.

Trước đây render "fail-open": thiếu ảnh thật vẫn lặng lẽ lấy stock → video rác ("ép tạo
rác"). Cổng này chặn cứng: thiếu ≥3 ảnh thật / giá / tên / mô tả → `Product.input_status=
BLOCKED_INPUT` + lý do (hiện web) → KHÔNG cho brain gọi LLM / KHÔNG render.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from core.logger import logger

MIN_REAL_IMAGES = 3
# Nguồn ingest-qua-link (TikTok) chỉ lấy được 1 og:image (không có máy gặt gallery như Shopee)
# và thường KHÔNG có giá/mô tả từ og-tags. i2v chỉ cần 1 ảnh khung đầu → cổng cho các nguồn này
# chỉ bắt buộc ẢNH (>=1), bỏ ràng buộc giá/mô tả (điền sau, không chặn tạo clip).
MIN_REAL_IMAGES_BY_SOURCE = {"tiktok_shop": 1}
_IMAGE_ONLY_SOURCES = frozenset({"tiktok_shop"})
INPUT_READY = "READY"
INPUT_BLOCKED = "BLOCKED_INPUT"


@dataclass(frozen=True)
class InputReadiness:
    ready: bool
    missing: dict[str, str]  # field → lý do (hiển thị trên web/Telegram)

    def reason_text(self) -> str:
        return "; ".join(self.missing.values()) if self.missing else "đủ điều kiện"


def real_image_paths(product) -> list[str]:  # noqa: ANN001
    """Danh sách ảnh thật local từ Product.image_paths_json (bỏ rỗng)."""
    try:
        items = json.loads(getattr(product, "image_paths_json", "") or "[]")
    except (ValueError, TypeError):
        items = []
    return [str(p) for p in items if p]


def evaluate_input(product) -> InputReadiness:  # noqa: ANN001
    """Đánh giá đủ điều kiện input (KHÔNG ghi DB). Theo nguồn: mặc định ≥3 ảnh thật + tên + giá + mô tả;
    nguồn image-only (tiktok_shop) chỉ cần ≥1 ảnh thật + tên (bỏ qua giá/mô tả)."""
    missing: dict[str, str] = {}
    source = (getattr(product, "source", "") or "")
    min_images = MIN_REAL_IMAGES_BY_SOURCE.get(source, MIN_REAL_IMAGES)
    n_images = len(real_image_paths(product))
    if n_images < min_images:
        missing["images"] = f"Cần ≥{min_images} ảnh thật của sản phẩm (hiện có {n_images})."
    if not (getattr(product, "name", "") or "").strip():
        missing["name"] = "Thiếu tên sản phẩm."
    if source not in _IMAGE_ONLY_SOURCES:
        price = getattr(product, "price", 0) or 0
        if price <= 0:
            missing["price"] = "Thiếu giá sản phẩm (>0)."
        if not (getattr(product, "description", "") or "").strip():
            missing["description"] = "Thiếu mô tả sản phẩm."
    return InputReadiness(ready=not missing, missing=missing)


def gate_product_input(product) -> InputReadiness:  # noqa: ANN001
    """Đánh giá + GHI `input_status`/`input_missing_json` vào product (caller commit)."""
    readiness = evaluate_input(product)
    product.input_status = INPUT_READY if readiness.ready else INPUT_BLOCKED
    product.input_missing_json = json.dumps(readiness.missing, ensure_ascii=False)
    if not readiness.ready:
        logger.debug(
            f"[input-gate] SP #{getattr(product, 'id', '?')} BLOCKED_INPUT — {readiness.reason_text()}"
        )
    return readiness


def record_blocked_input_event(session, *, product_id, product_name, reason) -> None:  # noqa: ANN001
    """Ghi SystemEvent BLOCKED_INPUT (dashboard + Telegram bridge đọc). Caller commit session."""
    from core.models import SystemEvent

    session.add(
        SystemEvent(
            level="WARNING",
            module="input_gate",
            message=f"SP #{product_id} '{(product_name or '')[:40]}' BLOCKED_INPUT — {reason}",
        )
    )
