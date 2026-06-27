"""Thư viện meme (seed tay ưu tiên VN + auto-fetch) + matcher khớp meme theo cảm xúc beat.

storage/long_narrative/memes/index.json = [{file, tags:[...], emotion, lang:"vn"|"intl"}].
Matcher: trục chính = beat.context (emotion chuẩn) ∩ beat.meme_tags, ưu tiên lang="vn", chống lặp (used).
Index rỗng (chưa seed) → match_meme trả None (fallback chain dùng ảnh thật/nền sân). Fail-soft.
"""
from __future__ import annotations

import json
import os

from config.settings import settings


def memes_root() -> str:
    return os.path.join(settings.storage_dir, "long_narrative", "memes")


def load_index(root: str | None = None) -> list[dict]:
    root = root or memes_root()
    try:
        with open(os.path.join(root, "index.json"), encoding="utf-8") as f:
            data = json.load(f)
        return [e for e in data if isinstance(e, dict) and e.get("file")] if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def _abs(root: str, entry: dict) -> str:
    f = entry["file"]
    return f if os.path.isabs(f) else os.path.join(root, f)


def match_meme(beat, *, used: set[str] | None = None, root: str | None = None,
               only: set[str] | None = None) -> str | None:
    """Chọn 1 meme khớp cảm xúc/cà-khịa beat. Ưu tiên VN. Chống lặp (used). Index rỗng → None.
    only: nếu cho → CHỈ xét entry có basename trong tập này (vd bộ ICONIC cho 'punch' meme thật)."""
    root = root or memes_root()
    idx = load_index(root)
    if only:
        idx = [e for e in idx if os.path.basename(e.get("file", "")) in only]
    if not idx:
        return None
    used = used if used is not None else set()
    ctx = (getattr(beat, "context", "") or "").lower()
    tags = {t.lower() for t in (getattr(beat, "meme_tags", None) or [])}

    def score(e: dict) -> int:
        s = 0
        if (e.get("emotion") or "").lower() == ctx:
            s += 2
        if tags & {t.lower() for t in (e.get("tags") or [])}:
            s += 2
        if (e.get("lang") or "") == "vn":
            s += 1
        return s

    cands = [e for e in idx if os.path.basename(_abs(root, e)) not in used and os.path.exists(_abs(root, e))]
    if not cands:
        return None
    # CHỈ chèn meme khi KHỚP cảm-xúc/tag (score>0). KHÔNG match → None để caller rơi meme-doodle/người dẫn
    # (bỏ 'or cands' cũ: nó kéo cả rổ → sort ABC → 'clown_applying_makeup' chèn lạc nội dung — founder báo).
    matched = [e for e in cands if score(e) > 0]
    if not matched:
        return None
    top_score = max(score(e) for e in matched)
    top = sorted([e for e in matched if score(e) == top_score], key=lambda e: e["file"])
    pick = top[(getattr(beat, "beat_id", 0) or 0) % len(top)]
    path = _abs(root, pick)
    used.add(os.path.basename(path))
    return path
