"""Chuẩn bị nhạc ~20s cho clip KHÔNG LỜI (màn "Tạo video từ link sản phẩm TikTok").

2 nguồn (user chọn mỗi lần — xem TAI-LIEU mục 17):
- ``clean`` (mặc định, AN TOÀN): nhạc bản-quyền-sạch (royalty-free) từ BG_MUSIC_DIR. Hợp video CÓ
  link affiliate (không bị tắt tiếng/đánh gậy).
- ``tiktok``: tải ĐÚNG nhạc trend từ clip TikTok (yt-dlp) — CHỈ khi TIKTOK_AUDIO_DOWNLOAD_ENABLED=True.
  RỦI RO bản quyền cho video affiliate (UI cảnh báo + user tự chịu).

Cắt cố định TIKTOK_AUDIO_TRIM_SECONDS (mặc định 20s) từ mốc ``trim_start``. ffmpeg có sẵn ở OS.
"""

from __future__ import annotations

import os
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path

from config.settings import settings
from core.logger import logger


@dataclass
class MusicResult:
    ok: bool
    audio_path: str = ""
    duration: float = 0.0
    source: str = ""  # clean | tiktok
    track: str = ""
    reason: str = ""


_MUSIC_EXTS = (".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac")


def _audio_dir() -> Path:
    d = Path(settings.tiktok_audio_dir or "storage/audio/tiktok")
    d.mkdir(parents=True, exist_ok=True)
    return d


def _media_dur(path: str) -> float:
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=nokey=1:noprint_wrappers=1", path],
            capture_output=True, text=True, timeout=60,
        )
        return round(float(out.stdout.strip()), 2)
    except (ValueError, OSError, subprocess.SubprocessError):
        return 0.0


def _trim_to_mp3(src: str, out_path: str, start: float, seconds: int) -> bool:
    """Cắt [start, start+seconds] → mp3 chuẩn (44.1k stereo). Trả True nếu ra file HỢP LỆ.

    Kẹp ``start`` trong [0, dur-1] để không cắt QUÁ cuối nguồn — nếu không, ffmpeg vẫn exit 0 nhưng
    ra mp3 rỗng (~vài trăm byte) → clip KHÔNG LỜI sẽ câm. Gate kích thước >1KB loại file rỗng đó."""
    if not os.path.exists(src):
        return False
    start = max(0.0, float(start))
    src_dur = _media_dur(src)
    if src_dur > 1.0:
        start = min(start, src_dur - 1.0)  # chừa ≥1s từ mốc bắt đầu tới hết nguồn
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-ss", f"{start:.2f}", "-t", str(int(seconds)),
        "-i", src, "-vn", "-ac", "2", "-ar", "44100",
        "-c:a", "libmp3lame", "-q:a", "3", out_path,
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    except (OSError, subprocess.SubprocessError) as exc:
        logger.warning(f"[clip_audio] ffmpeg trim lỗi: {exc!r}")
        return False
    return proc.returncode == 0 and os.path.exists(out_path) and os.path.getsize(out_path) > 1000


def _from_clean(choice: str, hint: str, trim_start: float, seconds: int) -> MusicResult:
    """Nhạc royalty-free từ BG_MUSIC_DIR: ưu tiên ``choice`` (tên file), rồi mood theo ``hint``."""
    music_dir = (settings.bg_music_dir or "").strip()
    src = ""
    track = ""
    if music_dir and os.path.isdir(music_dir):
        if choice:
            cand = os.path.join(music_dir, os.path.basename(choice))
            if os.path.exists(cand):
                src, track = cand, os.path.basename(cand)
    if not src:
        # mood hợp ngành (force=True bỏ qua cờ BG_MUSIC_ENABLED — clip không lời cần nhạc).
        from video_engine.compose import _pick_bg_music

        src = _pick_bg_music(seed=hint or "tiktok", hint=hint, force=True)
        track = os.path.basename(src) if src else ""
    if not src or not os.path.exists(src):
        # Thư viện nhạc trống (BG_MUSIC_DIR mất/chưa seed) → báo rõ + cách khắc phục thay vì mã "no_clean_track".
        return MusicResult(
            ok=False, source="clean",
            reason="Chưa có nhạc nền sạch trong thư viện — thêm file .mp3/.wav vào BG_MUSIC_DIR "
                   "hoặc chạy: python -m scripts.gen_music_library",
        )
    out = str(_audio_dir() / f"clean_{uuid.uuid4().hex[:10]}.mp3")
    if not _trim_to_mp3(src, out, trim_start, seconds):
        return MusicResult(ok=False, source="clean", reason="trim_failed", track=track)
    return MusicResult(ok=True, audio_path=out, duration=_media_dur(out), source="clean", track=track)


def _from_tiktok(url: str, trim_start: float, seconds: int) -> MusicResult:
    """Tải audio clip TikTok (yt-dlp) → cắt 20s. CHỈ chạy khi cờ download bật (gọi từ prepare_music)."""
    try:
        import yt_dlp  # noqa: F401
    except Exception:  # noqa: BLE001 — chưa cài
        return MusicResult(ok=False, source="tiktok", reason="ytdlp_not_installed")
    work = _audio_dir() / f"ttsrc_{uuid.uuid4().hex[:10]}"
    raw_tmpl = str(work) + ".%(ext)s"
    opts = {
        "format": "bestaudio/best",
        "outtmpl": raw_tmpl,
        "quiet": True,
        "noplaylist": True,
        "no_warnings": True,
    }
    raw_path = ""
    try:
        import yt_dlp

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            raw_path = ydl.prepare_filename(info)
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"[clip_audio] yt-dlp tải lỗi: {exc!r}")
        return MusicResult(ok=False, source="tiktok", reason=f"download_failed:{type(exc).__name__}")
    if not raw_path or not os.path.exists(raw_path):
        # yt-dlp có thể đổi đuôi → tìm file vừa tải theo stem
        cands = list(work.parent.glob(work.name + ".*"))
        raw_path = str(cands[0]) if cands else ""
    if not raw_path or not os.path.exists(raw_path):
        return MusicResult(ok=False, source="tiktok", reason="download_missing")
    out = str(_audio_dir() / f"tiktok_{uuid.uuid4().hex[:10]}.mp3")
    ok = _trim_to_mp3(raw_path, out, trim_start, seconds)
    try:
        os.remove(raw_path)
    except OSError:
        pass
    if not ok:
        return MusicResult(ok=False, source="tiktok", reason="trim_failed")
    return MusicResult(
        ok=True, audio_path=out, duration=_media_dur(out), source="tiktok",
        track=os.path.basename(out),  # khớp _from_clean (đừng để track rỗng cho UI)
    )


def prepare_music(
    *,
    source: str = "clean",  # clean | tiktok
    url: str = "",
    choice: str = "",
    trim_start: float = 0.0,
    seconds: int | None = None,
    hint: str = "",
) -> MusicResult:
    """Trả MusicResult (audio_path đã cắt ~20s). source=tiktok cần cờ download bật (kẻo trả lý do)."""
    seconds = int(seconds or settings.tiktok_audio_trim_seconds or 20)
    src = (source or "clean").strip().lower()
    if src == "tiktok" and (url or "").strip():
        if not settings.tiktok_audio_download_enabled:
            # UI phải cảnh báo bản quyền + hướng dẫn bật cờ; mặc định chặn.
            return MusicResult(
                ok=False, source="tiktok",
                reason="tiktok_audio_disabled (bật TIKTOK_AUDIO_DOWNLOAD_ENABLED + tự chịu rủi ro bản quyền)",
            )
        return _from_tiktok(url.strip(), trim_start, seconds)
    return _from_clean(choice.strip(), hint, trim_start, seconds)
