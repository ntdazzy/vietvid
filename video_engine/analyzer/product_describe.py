"""B3 — Gemini Vision bóc MÔ TẢ SẢN PHẨM SIÊU CHI TIẾT (bí quyết fidelity của autovis).

Nhìn ảnh sản phẩm → 1 đoạn tiếng Anh tả brand / CHỮ IN trên bao bì / màu / chất liệu /
texture / chi tiết nhận diện. Đoạn này nhúng vào KHỐI 2 của video_prompt để model video
(Seedance) giữ đúng logo/nhãn kể cả ở 480p — quan trọng hơn cả tăng độ phân giải.

Fail-soft: thiếu key / tải ảnh lỗi → trả "" (Director vẫn chạy với tên sản phẩm).
"""

from __future__ import annotations

import mimetypes
import os

from config.settings import settings
from core.config_checks import looks_real_secret
from core.logger import logger

_INSTRUCTION = (
    "You describe products for an AI video-ad prompt. Look at the product image and write ONE "
    "English paragraph (60-120 words) describing it in EXTREME detail so a video model keeps the "
    "exact identity: brand name, ANY printed TEXT/lettering on the product or packaging (quote it "
    "verbatim), precise colors, material, texture, shape, and signature details (logo, stripes, "
    "patterns). No markup, no dialogue, no camera directions — just the dense product description."
)


def describe_product(
    *, image_path: str = "", image_url: str = "", product_name: str = ""
) -> str:
    """Trả đoạn mô tả siêu chi tiết (tiếng Anh) hoặc "" nếu không khả dụng (fail-soft)."""
    if not looks_real_secret(settings.gemini_api_key or ""):
        return ""
    data, mime = _load_image(image_path, image_url)
    if not data:
        return ""
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.gemini_api_key)
        resp = client.models.generate_content(
            model=settings.gemini_model,
            contents=[
                types.Part.from_bytes(data=data, mime_type=mime),
                f"Product name: {product_name}\n{_INSTRUCTION}",
            ],
        )
        text = (getattr(resp, "text", "") or "").strip()
        if text:
            logger.info(f"[analyzer] đã bóc mô tả SP ({len(text)} ký tự) cho '{product_name}'")
        return text[:1200]
    except Exception as exc:  # noqa: BLE001 — fail-soft, không chặn pipeline
        logger.warning(f"[analyzer] bóc mô tả SP lỗi → bỏ qua: {str(exc)[:200]}")
        return ""


def _load_image(path: str, url: str) -> tuple[bytes | None, str]:
    if path and os.path.exists(path):
        return open(path, "rb").read(), (mimetypes.guess_type(path)[0] or "image/jpeg")
    if url and url.startswith("http"):
        try:
            import httpx

            r = httpx.get(url, timeout=20.0, follow_redirects=True)
            if r.status_code == 200 and r.content:
                return r.content, (r.headers.get("content-type", "image/jpeg").split(";")[0])
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"[analyzer] tải ảnh SP lỗi: {str(exc)[:150]}")
    return None, ""
