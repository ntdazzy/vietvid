"""film_recap/ingest.py — tải clip nguồn về (yt-dlp). Pattern theo analyzer/video_understand._download_video.

Lazy import yt_dlp (chỉ khi cần), fail-soft hoàn toàn, max_filesize chống tải nhầm video dài.
"""
from __future__ import annotations

import os
import uuid

from core.logger import logger


def download(url: str, dest_dir: str, *, max_mb: int = 200) -> str:
    """Tải video công khai (TikTok/YouTube/Reels...) về dest_dir. Trả path file hoặc "" (fail-soft)."""
    url = (url or "").strip()
    if not url:
        return ""
    try:
        import yt_dlp
    except Exception:  # noqa: BLE001 — chưa cài
        logger.warning("[film_recap] yt-dlp chưa cài → không tải được clip nguồn.")
        return ""
    os.makedirs(dest_dir, exist_ok=True)
    out_base = os.path.join(dest_dir, f"src_{uuid.uuid4().hex[:10]}")
    opts = {
        "format": "mp4/bestvideo*+bestaudio/best",
        "outtmpl": out_base + ".%(ext)s",
        "quiet": True,
        "noplaylist": True,
        "no_warnings": True,
        "max_filesize": max(1, int(max_mb)) * 1024 * 1024,
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            path = ydl.prepare_filename(info)
    except Exception as exc:  # noqa: BLE001 — fail-soft
        logger.warning(f"[film_recap] yt-dlp tải lỗi: {str(exc)[:160]}")
        return ""
    if path and os.path.exists(path):
        return path
    # prepare_filename có thể trả ext khác sau merge (mkv/webm) — dò file thực tế.
    for ext in (".mp4", ".mkv", ".webm"):
        if os.path.exists(out_base + ext):
            return out_base + ext
    logger.warning(f"[film_recap] tải xong nhưng không thấy file: {out_base}.*")
    return ""
