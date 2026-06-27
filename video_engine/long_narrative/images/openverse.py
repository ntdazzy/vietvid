"""openverse.py — tìm ẢNH web theo keyword qua Openverse API (800M+ ảnh CC/PD, KHÔNG cần key).

Mở rộng nguồn ảnh ngoài Wikimedia (vốn chỉ theo entity). Lọc license_type=commercial (commercial-OK,
hợp kênh kiếm tiền + RULES — không scrape, license sạch). Fail-soft → None. Tải qua download_image_safe
(SSRF guard + sniff magic bytes + cache) như mọi nguồn ảnh khác.
"""

from __future__ import annotations

import os

import httpx

from core.logger import logger
from video_engine.long_narrative.images.fetch import cache_hit, download_image_safe

_API = "https://api.openverse.org/v1/images/"
_UA = {"User-Agent": "AffiliateBot/1.0 (https://github.com/ntdazzy/affiliatebot)"}


def _stem(query: str, out_dir: str) -> str:
    slug = "".join(c for c in (query or "").lower() if c.isalnum() or c == " ").strip().replace(" ", "_")
    return os.path.join(out_dir, "ov_" + slug[:40])


def search_web_image(query: str, out_dir: str, *, timeout: float = 15.0) -> str | None:
    """1 ảnh web CC/PD commercial-OK đúng keyword → path (đã tải) hoặc None. Cache theo keyword."""
    q = (query or "").strip()
    if not q:
        return None
    stem = _stem(q, out_dir)
    hit = cache_hit(stem)
    if hit:
        return hit
    os.makedirs(out_dir, exist_ok=True)
    try:
        r = httpx.get(_API, headers=_UA, timeout=timeout, params={
            "q": q, "license_type": "commercial", "page_size": 8, "mature": "false",
        })
        r.raise_for_status()
        results = r.json().get("results") or []
    except Exception as exc:  # noqa: BLE001 — 1 nguồn lỗi không làm hỏng job
        logger.warning(f"[openverse] tìm ảnh lỗi '{q[:40]}': {str(exc)[:120]}")
        return None
    for it in results:
        url = (it.get("url") or "").strip()
        if url:
            p = download_image_safe(url, stem, timeout=timeout)
            if p:
                return p
    return None
