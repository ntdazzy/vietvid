"""Tìm + tải ảnh CC của cầu thủ/CLB/entity từ Wikimedia Commons (no-key, free). Cache + fail-soft → None.

Chỉ nhận ảnh license CC/PD (kênh kiếm tiền — tránh strike). Founder có thể seed ảnh hay dùng vào
storage/long_narrative/photos/<entity-slug>/*.jpg → check local TRƯỚC khi gọi API.
"""
from __future__ import annotations

import hashlib
import os
import re

import httpx

from config.settings import settings
from core.logger import logger
from video_engine.long_narrative.images.fetch import cache_hit, download_image_safe

_COMMONS_API = "https://commons.wikimedia.org/w/api.php"
_WIKI_SUMMARY = "https://en.wikipedia.org/api/rest_v1/page/summary/"
# Wikimedia BẮT BUỘC User-Agent compliant (tool/version (contact-url)) — UA generic/browser bị 403.
_UA = {"User-Agent": "AffiliateBot/1.0 (https://github.com/ntdazzy/affiliatebot)"}
_OK_LICENSE = ("cc", "public domain", "pd", "creative commons", "cc0")


def _slug(entity: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", entity.lower()).strip("_")


def _seeded_local(entity: str) -> str | None:
    """Ảnh founder seed tay ở storage/long_narrative/photos/<slug>/ — ưu tiên trước API."""
    root = os.path.join(settings.storage_dir, "long_narrative", "photos", _slug(entity))
    if not os.path.isdir(root):
        return None
    for f in sorted(os.listdir(root)):
        if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            p = os.path.join(root, f)
            if os.path.getsize(p) > 5000:
                return p
    return None


def _commons_image_url(entity: str, *, timeout: float) -> str | None:
    """Query Commons → URL ảnh CC tốt nhất (width≥600, license CC/PD)."""
    try:
        r = httpx.get(
            _COMMONS_API, headers=_UA, timeout=timeout,
            params={
                "action": "query", "format": "json", "generator": "search",
                "gsrsearch": entity, "gsrnamespace": "6", "gsrlimit": "12",
                "prop": "imageinfo", "iiprop": "url|size|extmetadata",
                "iiurlwidth": "1280",   # LẤY BẢN SCALE 1280px (thumburl) — ảnh gốc Commons hay >12MB → bị từ chối.
            },
        )
        r.raise_for_status()
        pages = (r.json().get("query") or {}).get("pages") or {}
    except Exception as exc:  # noqa: BLE001 — fail-soft
        logger.warning(f"[wikimedia] commons query lỗi '{entity[:40]}': {str(exc)[:120]}")
        return None
    for pg in pages.values():
        info = (pg.get("imageinfo") or [{}])[0]
        orig = (info.get("url") or "").lower()
        if not orig.endswith((".jpg", ".jpeg", ".png")):
            continue  # bỏ svg/gif/tif
        if (info.get("width") or 0) < 600:
            continue  # ảnh gốc phải đủ nét
        lic = ((info.get("extmetadata") or {}).get("LicenseShortName") or {}).get("value", "")
        if not any(tok in lic.lower() for tok in _OK_LICENSE):
            continue  # thiếu/không phải CC → BỎ (an toàn bản quyền)
        # ưu tiên thumburl (scale 1280, nhẹ < 12MB); fallback url gốc.
        return info.get("thumburl") or info.get("url") or None
    return None


def search_player_photo(entity: str, out_dir: str, *, timeout: float = 15.0) -> str | None:
    entity = (entity or "").strip()
    if not entity:
        return None
    os.makedirs(out_dir, exist_ok=True)
    stem = os.path.join(out_dir, "wiki_" + hashlib.md5(entity.lower().encode("utf-8")).hexdigest())
    hit = cache_hit(stem)
    if hit:
        return hit
    seeded = _seeded_local(entity)
    if seeded:
        return seeded
    url = _commons_image_url(entity, timeout=timeout)
    if not url:
        # fallback: thumbnail trang Wikipedia (cũng Commons-backed)
        try:
            r = httpx.get(_WIKI_SUMMARY + entity.replace(" ", "_"), headers=_UA, timeout=timeout)
            if r.status_code == 200:
                url = ((r.json().get("thumbnail") or {}).get("source")) or ""
        except Exception:  # noqa: BLE001
            url = ""
    if not url:
        return None
    # upload.wikimedia.org cũng đòi UA compliant (Mozilla generic → 403) → truyền lại _UA khi tải.
    return download_image_safe(url, stem, timeout=timeout, headers=_UA)
