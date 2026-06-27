"""Lấy ảnh đại diện 1 bài tin (og:image / twitter:image) → tải về. Cache + fail-soft → None.

Nguồn URL = headlines[].link / source_url từ ingest.gather_source. Báo VN luôn có og:image chất lượng tốt,
ngữ cảnh đúng trận → ảnh phụ tốt khi Wikimedia thiếu.
"""
from __future__ import annotations

import hashlib
import os
import re
from urllib.parse import urljoin

import httpx

from core.logger import logger
from video_engine.long_narrative.images.fetch import cache_hit, download_image_safe

_UA = {"User-Agent": "Mozilla/5.0 (affiliatebot-longform; football recap)"}

# Regex thay bs4 (bs4 không chắc có trong .venv — chỉ là transitive dep của trafilatura). Đủ bền cho meta tag.
_META_OG = re.compile(
    r'<meta\b[^>]*?\b(?:property|name)\s*=\s*["\'](?:og:image(?::url|:secure_url)?|twitter:image(?::src)?)["\'][^>]*>',
    re.IGNORECASE | re.DOTALL,
)
_CONTENT = re.compile(r'\bcontent\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)
_LINK_IMGSRC = re.compile(r'<link\b[^>]*?\brel\s*=\s*["\']image_src["\'][^>]*>', re.IGNORECASE)
_HREF = re.compile(r'\bhref\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)


def _extract_og(html: str, base: str) -> str | None:
    for m in _META_OG.finditer(html or ""):
        c = _CONTENT.search(m.group(0))
        if c:
            return urljoin(base, c.group(1).strip())
    m = _LINK_IMGSRC.search(html or "")
    if m:
        h = _HREF.search(m.group(0))
        if h:
            return urljoin(base, h.group(1).strip())
    return None


def og_image_for_article(url: str, out_dir: str, *, timeout: float = 15.0) -> str | None:
    url = (url or "").strip()
    if not url.startswith("http"):
        return None
    os.makedirs(out_dir, exist_ok=True)
    stem = os.path.join(out_dir, "og_" + hashlib.md5(url.encode("utf-8")).hexdigest())
    hit = cache_hit(stem)
    if hit:
        return hit
    try:
        r = httpx.get(url, headers=_UA, timeout=timeout, follow_redirects=True)
        r.raise_for_status()
        html = r.text
    except Exception as exc:  # noqa: BLE001 — fail-soft
        logger.warning(f"[og_image] fetch lỗi {url[:80]}: {str(exc)[:120]}")
        return None
    img_url = _extract_og(html, url)
    if not img_url:
        return None
    # CDN báo VN (vnecdn...) chặn hotlink → cần Referer = trang bài + UA trình duyệt.
    return download_image_safe(img_url, stem, timeout=timeout,
                               headers={"User-Agent": _UA["User-Agent"], "Referer": url})
