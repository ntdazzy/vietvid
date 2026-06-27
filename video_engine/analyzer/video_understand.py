"""B7 — Phân tích VIDEO VIRAL mẫu → bóc "công thức" (như autovis Super VIP).

Gemini 2.5 đọc video link (YouTube đọc TRỰC TIẾP qua file_uri — không cần tải) → trích
hook + cấu trúc cảnh theo timecode + tone giọng + CTA + nhịp. Director dùng "công thức" này
remap sang sản phẩm/KOL của user (giữ cấu trúc video thắng, KHÔNG copy nội dung gốc).

Fail-soft: thiếu key / link không đọc được → trả {} (pipeline vẫn chạy không có reference).
"""

from __future__ import annotations

import json
import os
import re
import time
import uuid
from pathlib import Path

from config.settings import settings
from core.config_checks import looks_real_secret
from core.logger import logger

_INSTRUCTION = (
    "You are a viral video strategist. Watch this reference video and extract its WINNING FORMULA "
    "(do NOT copy its exact content). Return ONLY a JSON object with keys: "
    '"hook" (string: the 0-3s attention hook technique), '
    '"scenes" (array of {"t":"0-3s","beat":"what happens + camera/angle"} — the shot structure by timecode), '
    '"voice_style" (string: narration tone/energy), '
    '"cta" (string: call-to-action style at the end), '
    '"pacing" (string: editing rhythm — fast cuts / slow / etc.). '
    "Keep it concise and reusable for a DIFFERENT product."
)

_YOUTUBE = re.compile(r"(youtube\.com|youtu\.be)", re.IGNORECASE)


def analyze_reference_video(url: str) -> dict:
    """Trả breakdown {hook, scenes[], voice_style, cta, pacing} hoặc {} (fail-soft)."""
    url = (url or "").strip()
    if not url or not looks_real_secret(settings.gemini_api_key or ""):
        return {}
    if not _YOUTUBE.search(url):
        # v1: Gemini đọc trực tiếp được YouTube; TikTok/khác cần tải về (yt-dlp) — làm sau.
        logger.warning(f"[video-understand] v1 chỉ đọc trực tiếp YouTube; bỏ qua link: {url[:60]}")
        return {}
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.gemini_api_key)
        resp = client.models.generate_content(
            model=settings.gemini_model,
            contents=[
                types.Part.from_uri(file_uri=url, mime_type="video/*"),
                _INSTRUCTION,
            ],
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        data = _parse(resp)
        if data:
            logger.info(f"[video-understand] bóc công thức video ({len(data.get('scenes',[]))} cảnh)")
        return data
    except Exception as exc:  # noqa: BLE001 — fail-soft
        logger.warning(f"[video-understand] phân tích video lỗi → bỏ qua: {str(exc)[:200]}")
        return {}


_DOWNLOADABLE = re.compile(r"(tiktok\.com|instagram\.com|fb\.watch|facebook\.com)", re.IGNORECASE)


def analyze_video_any(url: str) -> dict:
    """Bậc 3 — bóc công thức từ link BẤT KỲ (YouTube/TikTok/Reels).

    - YouTube: Gemini đọc trực tiếp (``analyze_reference_video``).
    - TikTok/Reels/FB: phải tải về (yt-dlp) + upload Gemini Files API — CHỈ khi
      ``trend_tiktok_download_enabled`` (xám ToS/bản quyền, founder tự bật).
    Fail-soft: trả {} ở mọi lỗi (không sập loop ingest).
    """
    url = (url or "").strip()
    if not url or not looks_real_secret(settings.gemini_api_key or ""):
        return {}
    if _YOUTUBE.search(url):
        return analyze_reference_video(url)
    if not _DOWNLOADABLE.search(url):
        logger.warning(f"[video-understand] link không hỗ trợ (chỉ YouTube/TikTok/Reels/FB): {url[:60]}")
        return {}
    if not settings.trend_tiktok_download_enabled:
        logger.warning(
            "[video-understand] link TikTok/Reels nhưng TREND_TIKTOK_DOWNLOAD_ENABLED=False → bỏ qua "
            "(bật cờ + tự chịu rủi ro bản quyền để tải học cấu trúc)."
        )
        return {}
    path = _download_video(url)
    if not path:
        return {}
    try:
        return _analyze_uploaded_video(path)
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def _trend_dir() -> Path:
    d = Path(settings.video_engine_output_dir or "storage/video_engine") / "trends"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _download_video(url: str) -> str:
    """Tải video công khai về (yt-dlp). Trả path mp4 hoặc "" (fail-soft)."""
    try:
        import yt_dlp
    except Exception:  # noqa: BLE001 — chưa cài
        logger.warning("[video-understand] yt-dlp chưa cài → không tải được TikTok/Reels.")
        return ""
    work = _trend_dir() / f"trend_{uuid.uuid4().hex[:10]}"
    opts = {
        "format": "mp4/bestvideo*+bestaudio/best",
        "outtmpl": str(work) + ".%(ext)s",
        "quiet": True,
        "noplaylist": True,
        "no_warnings": True,
        "max_filesize": 100 * 1024 * 1024,  # 100MB — clip ngắn, chặn tải nhầm video dài
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            path = ydl.prepare_filename(info)
    except Exception as exc:  # noqa: BLE001 — fail-soft
        logger.warning(f"[video-understand] yt-dlp tải lỗi → bỏ qua: {str(exc)[:160]}")
        return ""
    if not path or not os.path.exists(path):
        cands = list(work.parent.glob(work.name + ".*"))
        path = str(cands[0]) if cands else ""
    return path if path and os.path.exists(path) else ""


def _analyze_uploaded_video(path: str) -> dict:
    """Upload video lên Gemini Files API → đọc → bóc công thức. Fail-soft → {}."""
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.gemini_api_key)
        f = client.files.upload(file=path)
        # Video cần xử lý server-side → poll tới ACTIVE (cap ~60s).
        for _ in range(30):
            state = getattr(getattr(f, "state", None), "name", "") or str(getattr(f, "state", ""))
            if state == "ACTIVE":
                break
            if state == "FAILED":
                logger.warning("[video-understand] Gemini Files xử lý video FAILED → bỏ qua.")
                return {}
            time.sleep(2)
            f = client.files.get(name=f.name)
        resp = client.models.generate_content(
            model=settings.gemini_model,
            contents=[f, _INSTRUCTION],
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        data = _parse(resp)
        try:
            client.files.delete(name=f.name)
        except Exception:  # noqa: BLE001 — dọn file Gemini best-effort
            pass
        if data:
            logger.info(f"[video-understand] bóc công thức (tải về, {len(data.get('scenes', []))} cảnh)")
        return data
    except Exception as exc:  # noqa: BLE001 — fail-soft
        logger.warning(f"[video-understand] phân tích video tải về lỗi → bỏ qua: {str(exc)[:200]}")
        return {}


def _parse(resp) -> dict:
    text = (getattr(resp, "text", "") or "").strip()
    if not text:
        return {}
    if text.startswith("```"):
        text = re.sub(r"^```[a-z]*\s*|\s*```$", "", text, flags=re.IGNORECASE | re.MULTILINE)
    try:
        d = json.loads(text)
        return d if isinstance(d, dict) else {}
    except ValueError:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        try:
            return json.loads(m.group(0)) if m else {}
        except ValueError:
            return {}


def format_breakdown_for_prompt(bd: dict) -> str:
    """Gói breakdown thành đoạn text để Director nhúng (remap theo công thức viral)."""
    if not bd:
        return ""
    parts = ["CÔNG THỨC VIRAL từ video mẫu (remake theo cấu trúc này, KHÔNG copy nội dung):"]
    if bd.get("hook"):
        parts.append(f"- Hook 0-3s: {bd['hook']}")
    for s in (bd.get("scenes") or [])[:8]:
        parts.append(f"- {s.get('t','')}: {s.get('beat','')}")
    if bd.get("pacing"):
        parts.append(f"- Nhịp dựng: {bd['pacing']}")
    if bd.get("cta"):
        parts.append(f"- CTA: {bd['cta']}")
    return "\n".join(parts)[:1500]
