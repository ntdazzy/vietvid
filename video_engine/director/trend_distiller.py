"""Bậc 3 — chưng cất video trend THỜI TRANG thành ScriptFormula (few-shot cho Director).

URL (YouTube/TikTok/Reels) → Gemini bóc {hook, scenes, voice_style, cta, pacing}
(``video_understand.analyze_video_any``) → map thành ``ScriptFormula`` PENDING (founder duyệt
mới ACTIVE). KHÔNG copy nội dung gốc — chỉ trích CẤU TRÚC/NHỊP. Dedup idempotent theo key.

Fail-soft: link không bóc được / Gemini lỗi → trả None (không tạo rác, không sập loop).
"""

from __future__ import annotations

import re

from sqlalchemy import select

from config.settings import settings
from core.database import db
from core.logger import logger
from core.models import ScriptFormula
from video_engine.analyzer.video_understand import analyze_video_any, format_breakdown_for_prompt

# Công thức trend mặc định gắn ngách THỜI TRANG (formula_bank khớp keyword theo category SP).
_FASHION_KEYWORDS = "thời trang,quần áo,outfit,phối đồ,nữ,fashion,áo,váy,đầm,set đồ"
_FASHION_FORMAT = "ugc_review"  # format thời trang UGC an toàn; founder đổi khi duyệt nếu muốn


def _platform(url: str) -> str:
    u = url.lower()
    if "youtube.com" in u or "youtu.be" in u:
        return "youtube"
    if "tiktok" in u:
        return "tiktok"
    if "instagram" in u:
        return "reels"
    return "web"


def _external_id(url: str) -> str:
    """Lấy id ổn định từ URL để dedup; fallback = số từ chuỗi (đủ phân biệt)."""
    for pat in (
        r"(?:youtu\.be/|/shorts/|[?&]v=)([\w-]{6,})",
        r"/video/(\d{6,})",  # tiktok
        r"/reel/([\w-]{6,})",  # instagram
    ):
        m = re.search(pat, url)
        if m:
            return m.group(1)
    return re.sub(r"\W+", "", url)[-24:] or "x"


def _duration_from_scenes(scenes: list) -> int:
    """Ước thời lượng từ timecode cuối ('8-12s' → 12). Mặc định 15s, kẹp 6..30."""
    end = 0
    for s in scenes or []:
        for n in re.findall(r"(\d+)\s*s", str((s or {}).get("t", ""))):
            end = max(end, int(n))
    return max(6, min(30, end or 15))


def distill_trend(url: str, *, source: str = "manual", force: bool = False) -> str | None:
    """Bóc 1 video trend → upsert ScriptFormula. Trả key formula hoặc None (fail-soft).

    ``force=False`` (mặc định): nếu link này ĐÃ chưng cất (row có prompt_vi) → trả key luôn,
    KHÔNG gọi lại Gemini (tiết kiệm token khi loop gặp lại video cũ). ``force=True`` bóc lại.
    """
    url = (url or "").strip()
    if not url:
        return None
    platform = _platform(url)
    key = f"trend_{platform}_{_external_id(url)}"[:64]
    if not force:
        with db.transaction() as session:
            existing = session.get(ScriptFormula, key)
            if existing is not None and (existing.prompt_vi or "").strip():
                logger.info(f"[trend] '{key}' đã chưng cất ({existing.status}) → bỏ qua Gemini")
                return key
    breakdown = analyze_video_any(url)
    if not breakdown or not (breakdown.get("hook") or breakdown.get("scenes")):
        logger.info(f"[trend] không bóc được công thức từ: {url[:70]}")
        return None

    prompt_vi = format_breakdown_for_prompt(breakdown)
    if not prompt_vi:
        return None
    title = f"Trend {platform} · {(breakdown.get('hook') or 'thời trang')[:80]}"
    duration = _duration_from_scenes(breakdown.get("scenes") or [])
    # Auto-approve TẮT mặc định → PENDING (founder duyệt). Bật → ACTIVE ngay.
    status = "ACTIVE" if settings.trend_auto_approve else "PENDING"

    with db.transaction() as session:
        row = session.get(ScriptFormula, key)
        if row is None:
            row = ScriptFormula(key=key, source=f"trend_{source}")
            session.add(row)
        row.source = f"trend_{source}"
        row.autovis_category = "thời trang"
        row.format_key = _FASHION_FORMAT
        row.title = title[:256]
        row.prompt_vi = prompt_vi
        row.prompt_en = f"REF VIDEO: {url}"  # link gốc để founder soi khi duyệt (không copy nội dung)
        row.product_keywords = _FASHION_KEYWORDS
        row.duration = duration
        # Giữ status nếu đã ACTIVE (founder duyệt rồi) — không tự hạ về PENDING khi re-ingest.
        if row.status not in ("ACTIVE",):
            row.status = status
    logger.info(f"[trend] chưng cất '{key}' ({status}) từ {platform}: {title[:50]}")
    return key


def distill_many(urls: list[str], *, source: str = "manual") -> list[str]:
    """Bóc nhiều link (mỗi link try/except riêng — 1 lỗi không chặn phần còn lại)."""
    keys: list[str] = []
    for url in urls:
        try:
            k = distill_trend(url, source=source)
            if k:
                keys.append(k)
        except Exception:  # noqa: BLE001 — fail-open từng item
            logger.exception(f"[trend] lỗi chưng cất link: {url[:70]}")
    return keys


def pending_count() -> int:
    with db.transaction() as session:
        return len(
            session.scalars(
                select(ScriptFormula.key).where(ScriptFormula.status == "PENDING")
            ).all()
        )
