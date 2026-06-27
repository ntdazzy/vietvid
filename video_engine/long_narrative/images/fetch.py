"""Lõi tải ảnh an toàn dùng chung cho mode photo_meme — TÁI DÙNG helper proven của product_image_backfill
(safe_product_image_url + _download_image: redirect-cap 4, sniff magic bytes, <12MB). Fail-soft → None."""
from __future__ import annotations

import os

import httpx

from core.logger import logger

_UA = "Mozilla/5.0 (affiliatebot-longform; football recap)"


def cache_hit(stem: str) -> str | None:
    """Trả file `stem.*` đã tải (>5KB) nếu có — tránh tải lại / gọi API lại."""
    parent = os.path.dirname(stem) or "."
    base = os.path.basename(stem)
    if not os.path.isdir(parent):
        return None
    for f in os.listdir(parent):
        if f.startswith(base + ".") and os.path.getsize(os.path.join(parent, f)) > 5000:
            return os.path.join(parent, f)
    return None


def download_image_safe(url: str, out_stem: str, *, timeout: float = 20.0, headers: dict | None = None) -> str | None:
    """Tải 1 ảnh public về `out_stem.<ext>` (ext theo magic bytes). Cache hit → trả luôn. Fail-soft → None.

    headers: override/bổ sung (vd UA compliant cho upload.wikimedia.org, hoặc Referer cho CDN báo chặn hotlink).
    """
    hit = cache_hit(out_stem)
    if hit:
        return hit
    from pathlib import Path

    from module1_scraper.product_image_backfill import _download_image, safe_product_image_url

    if not safe_product_image_url(url):
        return None
    hdrs = {"User-Agent": _UA}
    if headers:
        hdrs.update(headers)
    try:
        with httpx.Client(timeout=timeout, headers=hdrs) as client:
            target = _download_image(client, url, Path(out_stem))
        return str(target) if target and os.path.getsize(target) > 1000 else None
    except Exception as exc:  # noqa: BLE001 — fail-soft: 1 nguồn ảnh lỗi không được làm hỏng job
        logger.warning(f"[images] tải ảnh lỗi {url[:80]}: {str(exc)[:120]}")
        return None
