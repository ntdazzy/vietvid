"""Product import — bóc OG/JSON-LD (pure, không mạng) + chặn SSRF."""

from __future__ import annotations

import pytest

from app_api import scrape

_HTML = """
<html><head>
<meta property="og:title" content="Áo thun cotton cao cấp">
<meta property="og:image" content="https://cdn.shop.vn/ao.jpg">
<meta property="og:description" content="Áo thun 100% cotton, mềm mát.">
<script type="application/ld+json">
{"@type":"Product","name":"Áo thun cotton cao cấp","description":"Cotton 100%",
 "image":["https://cdn.shop.vn/ao1.jpg"],"offers":{"@type":"Offer","price":"199000","priceCurrency":"VND"}}
</script>
</head><body>...</body></html>
"""


def test_parse_extracts_product_fields():
    d = scrape.parse_product_html(_HTML)
    assert d["name"] == "Áo thun cotton cao cấp"
    assert d["price"] == "199000"          # từ JSON-LD offers
    assert d["image_url"].endswith(".jpg")
    assert "cotton" in d["description"].lower()


def test_parse_og_only_fallback():
    html = '<meta property="og:title" content="Sản phẩm X"><meta property="og:image" content="https://x/y.png">'
    d = scrape.parse_product_html(html)
    assert d["name"] == "Sản phẩm X" and d["image_url"] == "https://x/y.png"


def test_ssrf_blocks_localhost():
    for bad in ("http://localhost/x", "http://127.0.0.1/y", "http://[::1]/z"):
        with pytest.raises(scrape.ScrapeError):
            scrape._assert_safe_url(bad)


def test_ssrf_blocks_non_http():
    with pytest.raises(scrape.ScrapeError):
        scrape._assert_safe_url("file:///etc/passwd")
