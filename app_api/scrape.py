"""Bóc thông tin sản phẩm từ link (Shopee/TikTok-Shop/Lazada/web bất kỳ) → prefill wizard.

Đọc Open Graph + JSON-LD (Product schema) — chuẩn chung mọi trang thương mại expose. Best-effort:
trang chặn bot thì trả những gì lấy được. Chặn SSRF (không cho fetch IP nội bộ/loopback).
"""

from __future__ import annotations

import ipaddress
import json
import re
import socket
from urllib.parse import urlparse

import httpx

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


class ScrapeError(Exception):
    pass


def _assert_safe_url(url: str) -> None:
    """Chặn SSRF: chỉ http(s), host không trỏ về IP nội bộ/loopback/link-local."""
    p = urlparse(url)
    if p.scheme not in ("http", "https") or not p.hostname:
        raise ScrapeError("URL phải là http(s) hợp lệ")
    try:
        infos = socket.getaddrinfo(p.hostname, None)
    except socket.gaierror as exc:
        raise ScrapeError("Không phân giải được tên miền") from exc
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise ScrapeError("URL trỏ tới địa chỉ nội bộ (bị chặn)")


def _meta(html: str, prop: str) -> str:
    # <meta property="og:title" content="..."> (thứ tự thuộc tính linh hoạt)
    for pat in (
        rf'<meta[^>]+(?:property|name)=["\']{re.escape(prop)}["\'][^>]+content=["\']([^"\']+)["\']',
        rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']{re.escape(prop)}["\']',
    ):
        m = re.search(pat, html, re.IGNORECASE)
        if m:
            return _unescape(m.group(1)).strip()
    return ""


def _unescape(s: str) -> str:
    import html as _h

    return _h.unescape(s)


def _jsonld_product(html: str) -> dict:
    """Lấy node JSON-LD @type Product (nếu có) → name/description/image/price."""
    for m in re.finditer(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html, re.IGNORECASE | re.DOTALL,
    ):
        try:
            data = json.loads(m.group(1).strip())
        except (json.JSONDecodeError, ValueError):
            continue
        for node in data if isinstance(data, list) else [data]:
            if not isinstance(node, dict):
                continue
            t = node.get("@type")
            types = t if isinstance(t, list) else [t]
            if "Product" in types:
                return node
    return {}


def parse_product_html(html: str) -> dict:
    """Pure (không mạng) — testable. Trả {name, description, price, image_url, images}."""
    ld = _jsonld_product(html)
    name = (ld.get("name") or _meta(html, "og:title") or "").strip()
    desc = (ld.get("description") or _meta(html, "og:description") or "").strip()
    image = _meta(html, "og:image")
    if isinstance(ld.get("image"), str):
        image = image or ld["image"]
    elif isinstance(ld.get("image"), list) and ld["image"]:
        image = image or (ld["image"][0] if isinstance(ld["image"][0], str) else "")
    price = ""
    offers = ld.get("offers")
    if isinstance(offers, dict):
        price = str(offers.get("price") or offers.get("lowPrice") or "")
    elif isinstance(offers, list) and offers and isinstance(offers[0], dict):
        price = str(offers[0].get("price") or "")
    if not price:
        price = _meta(html, "product:price:amount") or _meta(html, "og:price:amount")
    return {
        "name": name[:200],
        "description": desc[:2000],
        "price": price[:40],
        "image_url": image[:500],
        "images": [image] if image else [],
    }


def scrape_product(url: str) -> dict:
    _assert_safe_url(url)
    try:
        with httpx.Client(timeout=15, follow_redirects=True, headers={"User-Agent": _UA}) as c:
            resp = c.get(url)
            resp.raise_for_status()
            html = resp.text[:1_500_000]  # cap 1.5MB
    except httpx.HTTPError as exc:
        raise ScrapeError(f"Không tải được trang: {exc}") from exc
    data = parse_product_html(html)
    data["source_url"] = url
    return data
