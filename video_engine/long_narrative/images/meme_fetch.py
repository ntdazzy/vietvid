"""Nạp thư viện meme. ĐƯỜNG CHÍNH = `rebuild_index`: founder bỏ ảnh meme vào storage/long_narrative/memes/
{vn,intl}/ rồi gọi hàm này để quét + dựng index.json (auto-tag emotion từ TÊN FILE). Đây là cách TIN CẬY +
hợp RULES (founder kiểm soát chất lượng/bản quyền meme, nhất là meme VN).

`refresh_meme_library` (auto-fetch Reddit) chỉ là BEST-EFFORT: Reddit chặn .json (403) nếu không OAuth, và
meme VN không có API sạch (FB cần login/anti-bot — cấm né detection theo RULES). Đừng phụ thuộc."""
from __future__ import annotations

import hashlib
import json
import os

import httpx

from core.logger import logger
from video_engine.long_narrative.images.fetch import download_image_safe
from video_engine.long_narrative.images.meme_library import load_index, memes_root

# keyword trong TÊN FILE → emotion (khớp VALID_CONTEXTS). Founder đặt tên gợi cảm xúc, vd 'troll_var.jpg'.
_EMO_KW = {
    "hype": ("hype", "anmung", "an_mung", "celebrat", "win", "vodich", "vui", "mung"),
    "drama": ("drama", "sad", "buon", "thatvong", "that_vong", "cry", "khoc", "fail", "thua"),
    "climax": ("climax", "soc", "shock", "epic", "kyluc", "ky_luc"),
    "joke": ("joke", "troll", "cakhia", "ca_khia", "funny", "hai", "cuoi", "var", "meme", "kheo"),
}


def _emotion_from_name(name: str) -> str:
    n = name.lower()
    for emo, kws in _EMO_KW.items():
        if any(k in n for k in kws):
            return emo
    return "joke"


def rebuild_index(root: str | None = None) -> dict:
    """Quét storage/long_narrative/memes/{vn,intl}/ → dựng lại index.json (auto-tag emotion theo tên file).
    ĐƯỜNG CHÍNH nạp meme: founder bỏ ảnh vào folder rồi gọi hàm này. lang theo thư mục (vn ưu tiên khi khớp)."""
    root = root or memes_root()
    out: list[dict] = []
    for lang in ("vn", "intl"):
        d = os.path.join(root, lang)
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                out.append({"file": f"{lang}/{f}", "tags": [], "emotion": _emotion_from_name(f), "lang": lang})
    os.makedirs(root, exist_ok=True)
    with open(os.path.join(root, "index.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    logger.info(f"[meme] rebuild_index → {len(out)} meme (vn+intl) tại {root}")
    return {"total": len(out)}

_SUBS = ("soccermemes", "footballmemes")
_UA = {"User-Agent": "affiliatebot-longform/1.0 meme-fetch"}
_EMO = [  # keyword trong title → emotion thô (khớp VALID_CONTEXTS của Beat)
    (("win", "won", "celebrat", "champion", "scudetto", "trophy"), "hype"),
    (("lose", "lost", "sad", "cry", "tears", "relegat", "fail"), "drama"),
    (("ref", "var", "penalty", "offside", "red card", "troll"), "joke"),
]


def _emotion(title: str) -> str:
    t = (title or "").lower()
    for kws, emo in _EMO:
        if any(k in t for k in kws):
            return emo
    return "joke"


def refresh_meme_library(*, limit: int = 60, timeout: float = 20.0, root: str | None = None) -> dict:
    root = root or memes_root()
    intl = os.path.join(root, "intl")
    os.makedirs(intl, exist_ok=True)
    idx = load_index(root)
    have = {e.get("file") for e in idx}
    fetched = skipped = errors = 0
    for sub in _SUBS:
        try:
            r = httpx.get(
                f"https://www.reddit.com/r/{sub}/top.json", headers=_UA, timeout=timeout,
                params={"t": "month", "limit": str(limit)},
            )
            r.raise_for_status()
            posts = [c.get("data") or {} for c in (r.json().get("data") or {}).get("children", [])]
        except Exception as exc:  # noqa: BLE001 — fail-soft
            logger.warning(f"[meme_fetch] r/{sub} lỗi: {str(exc)[:120]}")
            errors += 1
            continue
        for p in posts:
            url = p.get("url_overridden_by_dest") or p.get("url") or ""
            if not url.lower().endswith((".jpg", ".jpeg", ".png")):
                skipped += 1
                continue
            stem = os.path.join(intl, "rd_" + hashlib.md5(url.encode("utf-8")).hexdigest())
            path = download_image_safe(url, stem, timeout=timeout)
            if not path:
                errors += 1
                continue
            rel = os.path.relpath(path, root)
            if rel in have:
                skipped += 1
                continue
            idx.append({"file": rel, "tags": [sub], "emotion": _emotion(p.get("title")),
                        "lang": "intl", "source": f"reddit/{sub}"})
            have.add(rel)
            fetched += 1
    with open(os.path.join(root, "index.json"), "w", encoding="utf-8") as f:
        json.dump(idx, f, ensure_ascii=False, indent=1)
    logger.info(f"[meme_fetch] fetched={fetched} skipped={skipped} errors={errors} total={len(idx)}")
    return {"fetched": fetched, "skipped": skipped, "errors": errors, "total": len(idx)}
