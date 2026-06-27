"""ASR Groq Whisper — kiểm tra giọng THẬT cho QA (có lời? đúng tiếng Việt? khớp kịch bản?).

Dùng trong cổng QA cuối: 'chấm lọc kĩ trước khi ra clip'. Fail-soft: thiếu key/lỗi mạng →
trả None (QA coi như chưa verify được, KHÔNG chặn job tay — giống fail-open của text_scan).
Whisper có thể nghe lệch vài từ + bịa trên nhạc/im lặng → lọc bằng no_speech_prob/avg_logprob.
"""

from __future__ import annotations

import os
import re
import subprocess
import tempfile

import httpx

from config.settings import settings
from core.config_checks import looks_real_secret
from core.logger import logger

_GROQ_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
_WORD_RE = re.compile(r"[0-9a-zàáảãạăắằẳẵặâấầẩẫậđèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵ]+")
# Video DÀI → ASR theo chunk: 1-phát ép ffmpeg+HTTP 120s timeout + upload nguyên file (Groq giới
# hạn 25MB) nên video nhiều phút hay timeout/quá cỡ → trả None → cổng kiểm giọng fail-open GẦN NHƯ
# LUÔN. Chunk ~90s (mp3 16k mono ~0.7MB/chunk) gọn trong timeout + dưới 25MB → cổng chạy thật.
_CHUNK_THRESHOLD_S = 100.0
_CHUNK_S = 90.0


def _media_duration(media_path: str) -> float | None:
    try:
        proc = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nokey=1:noprint_wrappers=1", media_path],
            capture_output=True, text=True, timeout=60,
        )
        if proc.returncode != 0:
            return None
        return float((proc.stdout or "").strip())
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def _groq_segment(media_path: str, ss: float | None = None, dur: float | None = None) -> dict | None:
    """Transcode 1 đoạn (ss/dur=None → cả file) → mp3 16k mono → Groq verbose_json. None nếu ffmpeg
    lỗi; ném lỗi mạng/HTTP để caller quyết fail-soft (1-phát) hay bỏ-chunk (chunked)."""
    fd, mp3 = tempfile.mkstemp(suffix=".mp3")
    os.close(fd)
    try:
        cmd = ["ffmpeg", "-y", "-loglevel", "error"]
        if ss is not None:
            cmd += ["-ss", f"{ss:.2f}"]
        cmd += ["-i", media_path]
        if dur is not None:
            cmd += ["-t", f"{dur:.2f}"]
        cmd += ["-vn", "-ac", "1", "-ar", "16000", "-b:a", "64k", mp3]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if proc.returncode != 0:
            return None
        with open(mp3, "rb") as f:
            content = f.read()
        resp = httpx.post(
            _GROQ_URL,
            headers={"Authorization": f"Bearer {settings.groq_api_key}"},
            files={"file": ("audio.mp3", content, "audio/mpeg")},
            data={"model": "whisper-large-v3", "response_format": "verbose_json", "temperature": "0"},
            timeout=120.0,
        )
        resp.raise_for_status()
        return resp.json()
    finally:
        try:
            os.remove(mp3)
        except FileNotFoundError:
            pass


def _transcribe_chunked(media_path: str, duration: float) -> dict | None:
    """ASR từng đoạn ~_CHUNK_S rồi GỘP về verbose_json (text+language+segments) cho check_voice.
    1 chunk lỗi → bỏ chunk đó, KHÔNG kéo cả video về None. Không chunk nào ra chữ → None.

    LƯU Ý: segments gộp giữ start/end CỤC BỘ TỪNG CHUNK (mỗi chunk transcode lại từ 0) → mốc giờ
    KHÔNG liên tục toàn video; chỉ `text`/`no_speech_prob`/`avg_logprob` đáng tin (đúng cho
    check_voice). Caption align dùng `transcribe_words()` riêng (không chunk), không đi đường này."""
    texts: list[str] = []
    segments: list[dict] = []
    langs: list[str] = []
    ss = 0.0
    while ss < duration:
        try:
            raw = _groq_segment(media_path, ss=ss, dur=_CHUNK_S)
        except Exception as exc:  # noqa: BLE001 — 1 chunk lỗi không kéo cả video về fail-open
            logger.warning(f"[asr] chunk @{ss:.0f}s lỗi → bỏ chunk: {str(exc)[:120]}")
            raw = None
        if raw is not None:
            if (raw.get("text") or "").strip():
                texts.append(raw["text"].strip())
            segments.extend(raw.get("segments") or [])
            lang = str(raw.get("language") or "").strip()
            if lang:
                langs.append(lang)
        ss += _CHUNK_S
    if not texts and not segments:
        return None
    # ngôn ngữ = phổ biến nhất (chunk nhạc/im lặng đầu/cuối có thể đoán sai 1 chunk).
    language = max(set(langs), key=langs.count) if langs else ""
    return {"text": " ".join(texts), "language": language, "segments": segments}


def transcribe(media_path: str) -> dict | None:
    """Trả raw verbose_json của Groq (text/language/segments) hoặc None (fail-soft).

    Video DÀI (> _CHUNK_THRESHOLD_S) → ASR theo chunk rồi gộp (xem chú thích _CHUNK_S). Video ngắn
    (clip product) → 1-phát như cũ, byte-identical.
    """
    if not looks_real_secret(settings.groq_api_key or "", min_length=12):
        return None
    if not media_path or not os.path.exists(media_path):
        return None
    dur = _media_duration(media_path)
    if dur is not None and dur > _CHUNK_THRESHOLD_S:
        return _transcribe_chunked(media_path, dur)
    try:
        return _groq_segment(media_path)
    except Exception as exc:  # noqa: BLE001 — fail-soft (giống text_scan)
        logger.warning(f"[asr] Groq lỗi → bỏ qua kiểm giọng: {str(exc)[:150]}")
        return None


def transcribe_words(media_path: str) -> list[dict] | None:
    """Word-level timestamps cho caption align (chữ = KỊCH BẢN, giờ = giọng THẬT).

    Khác `transcribe()`: xin thêm `timestamp_granularities[]=word`. Trả `[{word,start,end}]`
    (đã lọc rỗng) hoặc None (fail-soft: thiếu key/lỗi → captions.py degrade về canh giờ
    tuyến tính theo độ dài câu). Giữ gate `looks_real_secret` + fail-soft như `transcribe()`.
    """
    if not looks_real_secret(settings.groq_api_key or "", min_length=12):
        return None
    if not media_path or not os.path.exists(media_path):
        return None
    fd, mp3 = tempfile.mkstemp(suffix=".mp3")
    os.close(fd)
    try:
        proc = subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", media_path,
             "-vn", "-ac", "1", "-ar", "16000", "-b:a", "64k", mp3],
            capture_output=True, text=True, timeout=120,
        )
        if proc.returncode != 0:
            return None
        with open(mp3, "rb") as f:
            content = f.read()
        resp = httpx.post(
            _GROQ_URL,
            headers={"Authorization": f"Bearer {settings.groq_api_key}"},
            files={"file": ("audio.mp3", content, "audio/mpeg")},
            data={
                "model": "whisper-large-v3",
                "response_format": "verbose_json",
                "temperature": "0",
                "language": "vi",
                "timestamp_granularities[]": "word",
            },
            timeout=180.0,
        )
        resp.raise_for_status()
        words = resp.json().get("words") or []
        out: list[dict] = []
        for w in words:
            tok = str(w.get("word") or "").strip()
            if not tok:
                continue
            try:
                out.append({
                    "word": tok,
                    "start": float(w.get("start", 0.0)),
                    "end": float(w.get("end", 0.0)),
                })
            except (TypeError, ValueError):
                continue
        return out or None
    except Exception as exc:  # noqa: BLE001 — fail-soft (giống transcribe)
        logger.warning(f"[asr] Groq word-timestamp lỗi → caption canh tuyến tính: {str(exc)[:150]}")
        return None
    finally:
        try:
            os.remove(mp3)
        except FileNotFoundError:
            pass


def transcribe_words_with_segments(media_path: str, *, max_seconds: float | None = None) -> dict | None:
    """1 lần gọi Groq word+segment (CÙNG timebase) cho film_recap lọc caption hallucination.

    Trả `{"words":[{word,start,end}...], "segments":[{start,end,no_speech_prob,avg_logprob,
    compression_ratio}...]}` hoặc None (fail-soft). Khác `transcribe_words` (chỉ word) + `transcribe`
    (auto-lang, CHUNK video dài → mốc giờ cục bộ không khớp word): hàm này xin word+segment trong MỘT
    response nên 2 mảng CÙNG mốc giờ → film_recap gắn word↔segment chuẩn (xem understand.clean_words).

    `max_seconds`: chỉ transcode CỬA SỔ [0, max_seconds] (input-side `-t`, như make_shorts_9x16) = đúng
    phần được burn ra clip → phim DÀI (kể cả >1 giờ) vẫn gọn dưới 25MB + timeout Groq (90s ≈ 0.7MB).
    KHÔNG dùng cho long_narrative (giọng TTS sạch — xem transcribe_words).
    """
    if not looks_real_secret(settings.groq_api_key or "", min_length=12):
        return None
    if not media_path or not os.path.exists(media_path):
        return None
    fd, mp3 = tempfile.mkstemp(suffix=".mp3")
    os.close(fd)
    try:
        cmd = ["ffmpeg", "-y", "-loglevel", "error"]
        if max_seconds is not None:
            cmd += ["-t", f"{float(max_seconds):.2f}"]   # input-side: chỉ đọc N giây đầu (phim dài vẫn nhanh)
        cmd += ["-i", media_path, "-vn", "-ac", "1", "-ar", "16000", "-b:a", "64k", mp3]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if proc.returncode != 0:
            return None
        with open(mp3, "rb") as f:
            content = f.read()
        resp = httpx.post(
            _GROQ_URL,
            headers={"Authorization": f"Bearer {settings.groq_api_key}"},
            files={"file": ("audio.mp3", content, "audio/mpeg")},
            data={
                "model": "whisper-large-v3",
                "response_format": "verbose_json",
                "temperature": "0",
                "language": "vi",
                "timestamp_granularities[]": ["word", "segment"],
            },
            timeout=180.0,
        )
        resp.raise_for_status()
        payload = resp.json()
        return {"words": payload.get("words") or [], "segments": payload.get("segments") or []}
    except Exception as exc:  # noqa: BLE001 — fail-soft (giống transcribe_words)
        logger.warning(f"[asr] Groq word+segment lỗi → caption không lọc được hallucination: {str(exc)[:150]}")
        return None
    finally:
        try:
            os.remove(mp3)
        except FileNotFoundError:
            pass


def _tokens(text: str) -> set[str]:
    return set(_WORD_RE.findall((text or "").lower()))


def check_voice(media_path: str, expected_narration: str) -> tuple[bool | None, dict]:
    """Kiểm giọng final: có lời người THẬT? đúng tiếng Việt? khớp kịch bản?

    Trả (ok, detail). ok=None → không verify được (thiếu Groq key/lỗi) — QA fail-open.
    ok=False → nghi: không có lời / sai ngôn ngữ / lệch kịch bản nhiều (garbled/sai/cụt nặng).
    """
    raw = transcribe(media_path)
    if raw is None:
        return None, {"skipped": "không gọi được Groq ASR (thiếu key/lỗi)"}
    segs = raw.get("segments") or []
    real = [
        s for s in segs
        if (s.get("no_speech_prob", 1.0) < 0.5 and s.get("avg_logprob", -10) > -1.0
            and (s.get("text") or "").strip())
    ]
    text = (raw.get("text") or "").strip()
    lang = str(raw.get("language") or "")
    has_speech = bool(real)
    lang_ok = "iet" in lang.lower() or "vi" == lang.lower()  # "Vietnamese"/"vi"
    # khớp kịch bản: tỉ lệ token kịch bản XUẤT HIỆN trong ASR (chịu được Whisper nghe lệch).
    want = _tokens(expected_narration)
    got = _tokens(text)
    overlap = (len(want & got) / len(want)) if want else 1.0
    match_ok = overlap >= 0.4 if want else True
    ok = bool(has_speech and lang_ok and match_ok)
    return ok, {
        "has_speech": has_speech,
        "language": lang,
        "lang_ok": lang_ok,
        "match_ratio": round(overlap, 2),
        "match_ok": match_ok,
        "asr_text": text[:200],
        "asr_text_tail": text[-240:],   # đuôi transcript THẬT (để cổng cuối tái kiểm CTA đã thực sự đọc)
        "n_real_segments": len(real),
    }
