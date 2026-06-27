"""ingest.py — lấy nguồn tin cho Director (RSS-first, commercial-safe).

Theo Section K plan: KHÔNG hosted news API (dính commercial-use trap) — dùng RSS VN-native
(VnExpress/Thanh Niên) free, no-key. Lấy nội dung bài: httpx + trafilatura (fallback bs4/regex).
Footage Pexels + fact-API (football-data.org/Wikimedia) ở visual.py/sau; module này lo TEXT.
"""

from __future__ import annotations

import re

import httpx

from config.settings import settings
from core.logger import logger

_UA = {"User-Agent": "Mozilla/5.0 (compatible; AffiliateBot/1.0; +news-recap)"}

# Category (chuẩn hoá không dấu) → RSS feeds VN-native (free, no-key). BẪY: thêm thể loại ở v8.py
# (_YT_CATEGORIES) thì NHỚ thêm feed tương ứng ở đây, kẻo rơi về _DEFAULT_FEEDS → gợi ý lạc mảng.
_RSS = {
    "bong da": ["https://vnexpress.net/rss/the-thao.rss", "https://thanhnien.vn/rss/the-thao.rss"],
    "the thao": ["https://vnexpress.net/rss/the-thao.rss"],
    "tin the gioi": ["https://vnexpress.net/rss/the-gioi.rss"],
    "the gioi": ["https://vnexpress.net/rss/the-gioi.rss"],
    "giai tri": ["https://vnexpress.net/rss/giai-tri.rss"],
    "showbiz": ["https://vnexpress.net/rss/giai-tri.rss"],
    "cong nghe": ["https://vnexpress.net/rss/so-hoa.rss"],
    "thoi su": ["https://vnexpress.net/rss/thoi-su.rss"],
    "su kien": ["https://vnexpress.net/rss/thoi-su.rss"],
    "kinh doanh": ["https://vnexpress.net/rss/kinh-doanh.rss"],
    "phap luat": ["https://vnexpress.net/rss/phap-luat.rss"],
    "khoa hoc": ["https://vnexpress.net/rss/khoa-hoc.rss"],
    "suc khoe": ["https://vnexpress.net/rss/suc-khoe.rss"],
    "doi song": ["https://vnexpress.net/rss/gia-dinh.rss"],
    "gia dinh": ["https://vnexpress.net/rss/gia-dinh.rss"],
    "xe": ["https://vnexpress.net/rss/oto-xe-may.rss"],
    "oto xe may": ["https://vnexpress.net/rss/oto-xe-may.rss"],
    "du lich": ["https://vnexpress.net/rss/du-lich.rss"],
    "giao duc": ["https://vnexpress.net/rss/giao-duc.rss"],
    # evergreen (thường-xanh) → KHÔNG RSS (không có "tin mới"); Director kể từ kiến thức, né lạc-đề.
    "lich su": [],
    "than thoai": [],
    "kien thuc": [],
}
# Thể loại thường-xanh: gather_source KHÔNG kéo RSS (tránh nhồi tin lạc-đề + phá fact-grounding).
_EVERGREEN = {"lich su", "than thoai", "kien thuc"}
# Từ khoá thể loại "đang hot" → dùng Google Trends Daily RSS theo geo (cờ qua registry).
_TREND_KEYS = ("dang hot", "xu huong", "trend", "hot")
_DEFAULT_FEEDS = ["https://vnexpress.net/rss/tin-moi-nhat.rss"]
_TAG_RE = re.compile(r"<[^>]+>")


def _trends_url() -> str:
    """Google Trends Daily Trends RSS theo geo (LONGFORM_TRENDS_GEO, vd 'VN'). Rỗng = tắt trend."""
    geo = (settings.longform_trends_geo or "").strip()
    return f"https://trends.google.com/trending/rss?geo={geo}" if geo else ""


def _strip_accents(s: str) -> str:
    import unicodedata
    s = s.replace("đ", "d").replace("Đ", "D")
    return "".join(c for c in unicodedata.normalize("NFD", s) if not unicodedata.combining(c)).lower()


def _feeds_for(category: str) -> list[str]:
    key = _strip_accents((category or "").strip())
    if not key:
        return _DEFAULT_FEEDS
    if any(t in key for t in _TREND_KEYS):           # "đang hot" → Google Trends RSS
        u = _trends_url()
        return [u] if u else _DEFAULT_FEEDS
    for k, feeds in _RSS.items():
        if k and (k in key or key in k):              # khớp thể loại (evergreen → [] = không RSS)
            return feeds
    return _DEFAULT_FEEDS


def fetch_rss_headlines(category: str, limit: int = 10) -> list[dict]:
    """Trả [{title, link, summary}] từ RSS theo category. Fail-soft → []."""
    import feedparser
    out: list[dict] = []
    for url in _feeds_for(category):
        try:
            r = httpx.get(url, headers=_UA, timeout=20.0, follow_redirects=True)
            r.raise_for_status()
            feed = feedparser.parse(r.content)
            for e in feed.entries[:limit]:
                title = (getattr(e, "title", "") or "").strip()
                if not title:
                    continue
                summary = _TAG_RE.sub("", getattr(e, "summary", "") or "").strip()
                out.append({"title": title, "link": getattr(e, "link", "") or "",
                            "summary": summary[:400]})
        except Exception as exc:  # noqa: BLE001 — fail-soft per feed
            logger.warning(f"[ingest] RSS {url} lỗi: {str(exc)[:120]}")
        if len(out) >= limit:
            break
    return out[:limit]


def fetch_article_text(url: str, *, max_chars: int = 4000) -> str:
    """Tải + làm sạch bài báo → text phẳng cho LLM. trafilatura → bs4 → regex. Fail-soft → ''."""
    if not (url or "").startswith("http"):
        return ""
    try:
        r = httpx.get(url, headers=_UA, timeout=25.0, follow_redirects=True)
        r.raise_for_status()
        html = r.text
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"[ingest] tải bài {url} lỗi: {str(exc)[:120]}")
        return ""
    # 1) trafilatura (sạch nhất cho LLM)
    try:
        import trafilatura
        txt = trafilatura.extract(html, include_comments=False, include_tables=False) or ""
        if len(txt) > 120:
            return txt[:max_chars]
    except Exception:  # noqa: BLE001
        pass
    # 2) bs4
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "iframe", "header", "footer", "nav", "aside", "form"]):
            tag.decompose()
        paras = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
        txt = "\n".join(p for p in paras if len(p) > 20)
        if len(txt) > 120:
            return txt[:max_chars]
    except Exception:  # noqa: BLE001
        pass
    # 3) regex fallback
    return _TAG_RE.sub(" ", html)[:max_chars]


def gather_source(topic_or_url: str, category: str = "") -> dict:
    """Gom nguồn cho Director: nếu là URL → tải bài; nếu là chủ đề → RSS headlines liên quan."""
    t = (topic_or_url or "").strip()
    if t.startswith("http"):
        return {"mode": "url", "topic": t, "article": fetch_article_text(t)}
    heads = fetch_rss_headlines(category or "tin nóng", limit=12)
    # ưu tiên headline khớp từ khoá chủ đề
    tl = _strip_accents(t)
    related = [h for h in heads if any(w in _strip_accents(h["title"]) for w in tl.split() if len(w) > 2)]
    picked = (related or heads)[:5]
    article = ""
    if picked and picked[0].get("link"):
        article = fetch_article_text(picked[0]["link"])
    ctx = "\n".join(f"- {h['title']}: {h['summary']}" for h in picked)
    return {"mode": "topic", "topic": t, "headlines": picked, "context": ctx, "article": article}
