"""pixabay.py — ẢNH Pixabay theo keyword (Pixabay Content License: dùng THƯƠNG MẠI OK, KHÔNG cần ghi
công). Dùng `pixabay_api_key` (đã khai registry nhưng trước CHƯA client nào xài). Fail-soft → None.

ToS Pixabay: phải tải file về server (không hotlink) + cache — download_image_safe đã làm đúng.
"""

from __future__ import annotations

import os

import httpx

from config.settings import settings
from core.logger import logger
from video_engine.long_narrative.images.fetch import cache_hit, download_image_safe

_API = "https://pixabay.com/api/"


def _stem(query: str, out_dir: str) -> str:
    slug = "".join(c for c in (query or "").lower() if c.isalnum() or c == " ").strip().replace(" ", "_")
    return os.path.join(out_dir, "px_" + slug[:40])


def search_web_image(query: str, out_dir: str, *, timeout: float = 15.0) -> str | None:
    """1 ảnh Pixabay đúng keyword → path (đã tải) hoặc None. Thiếu key/keyword → None. Cache theo keyword."""
    key = (settings.pixabay_api_key or "").strip()
    q = (query or "").strip()
    if not key or not q:
        return None
    stem = _stem(q, out_dir)
    hit = cache_hit(stem)
    if hit:
        return hit
    os.makedirs(out_dir, exist_ok=True)
    try:
        r = httpx.get(_API, timeout=timeout, params={
            "key": key, "q": q, "image_type": "photo", "safesearch": "true",
            "per_page": 8, "order": "popular",
        })
        r.raise_for_status()
        hits = r.json().get("hits") or []
    except Exception as exc:  # noqa: BLE001 — 1 nguồn lỗi không làm hỏng job
        logger.warning(f"[pixabay] tìm ảnh lỗi '{q[:40]}': {str(exc)[:120]}")
        return None
    for h in hits:
        url = (h.get("largeImageURL") or h.get("webformatURL") or "").strip()
        if url:
            p = download_image_safe(url, stem, timeout=timeout)
            if p:
                return p
    return None
