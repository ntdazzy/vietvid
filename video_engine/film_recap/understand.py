"""film_recap/understand.py — ASR sạch cho film_recap.

clean_words: 1 lần gọi Groq word+segment (CÙNG timebase, asr.transcribe_words_with_segments), gán mỗi
word vào segment GẦN NHẤT rồi BỎ từ rơi vào đoạn Whisper BỊA (nhạc/im lặng → caption "subscribe" rác).
Lọc theo no_speech_prob/avg_logprob (đúng 2 ngưỡng asr.check_voice) + compression_ratio (đoạn LẶP vô
nghĩa "ừ ừ ừ" mà no_speech vẫn thấp). Chỉ xét cửa sổ [0, max_seconds] = đúng phần burn ra clip → phim
DÀI (kể cả >1 giờ) vẫn gọn dưới 25MB/timeout Groq. Fail-soft: lỗi → [] (clip sạch, không caption rác).
Scoped film_recap — KHÔNG đụng transcribe_words chung (long_narrative align kịch bản cần giữ nguyên).

Vì sao 'segment gần nhất' chứ không 'segment chứa word' + 1 call chứ không 2 (đo thật /real-qa):
 - Whisper đặt mốc từ đoạn BỊA lệch RA NGOÀI biên segment (seg outro [59.5-60.0] nhưng từ "Hẹn gặp
   lại..." ở 60.2-60.7) → 'chứa' bỏ sót; 'gần nhất' bắt được.
 - transcribe() CHUNK video >100s → mốc giờ segment cục-bộ-từng-chunk, KHÔNG khớp mốc word toàn cục
   (transcribe_words không chunk) → lọc so sai timebase. 1 call word+segment → cùng timebase.
"""
from __future__ import annotations

from core.logger import logger

_NO_SPEECH = 0.5        # no_speech_prob ≥ = im lặng/nhạc (đúng ngưỡng asr.check_voice)
_MIN_LOGPROB = -1.0     # avg_logprob < = ASR đoán bừa độ tin thấp (đúng ngưỡng asr.check_voice)
_MAX_COMPRESSION = 2.4  # compression_ratio ≥ = văn bản LẶP vô nghĩa Whisper bịa (chuẩn OpenAI Whisper)


def _seg_is_bad(seg: dict) -> bool:
    """Segment KHÔNG phải lời người thật (nhạc/im lặng/lặp Whisper bịa)?"""
    try:
        nsp = float(seg.get("no_speech_prob", 0.0))
        alp = float(seg.get("avg_logprob", 0.0))
        cr = float(seg.get("compression_ratio", 0.0))
    except (TypeError, ValueError):
        return False
    return nsp >= _NO_SPEECH or alp < _MIN_LOGPROB or cr >= _MAX_COMPRESSION


def _nearest_is_bad(mid: float, segs: list[tuple[float, float, bool]]) -> bool:
    """Word (mốc giữa `mid`) thuộc segment GẦN NHẤT — segment đó có phải đoạn bịa không?

    'Gần nhất' (khoảng cách 0 nếu nằm trong) thay vì 'segment chứa' vì mốc từ đoạn bịa hay lệch ra
    ngoài biên segment. segs rỗng → False (không lọc được → giữ từ).
    """
    if not segs:
        return False
    best_bad, best_d = False, None
    for a, b, bad in segs:
        d = 0.0 if a <= mid <= b else min(abs(mid - a), abs(mid - b))
        if best_d is None or d < best_d:
            best_d, best_bad = d, bad
    return best_bad


def clean_words(src_path: str, *, max_seconds: float | None = None) -> list[dict]:
    """[{word,start,end}] đã lọc hallucination trong cửa sổ [0, max_seconds]. Lỗi ASR → [] (clip sạch)."""
    from video_engine.voice.asr import transcribe_words_with_segments
    payload = transcribe_words_with_segments(src_path, max_seconds=max_seconds)
    if payload is None:
        return []   # fail-soft: thà KHÔNG caption còn hơn burn caption bịa
    words: list[dict] = []
    for w in payload.get("words") or []:
        tok = str(w.get("word") or "").strip()
        if not tok:
            continue
        try:
            words.append({"word": tok, "start": float(w.get("start", 0.0)), "end": float(w.get("end", 0.0))})
        except (TypeError, ValueError):
            continue
    if not words:
        return []
    segs: list[tuple[float, float, bool]] = []
    for s in payload.get("segments") or []:
        try:
            segs.append((float(s.get("start", 0.0)), float(s.get("end", 0.0)), _seg_is_bad(s)))
        except (TypeError, ValueError):
            continue
    if not any(bad for _, _, bad in segs):
        return words   # không đoạn bịa nào → giữ nguyên timing
    kept = [w for w in words if not _nearest_is_bad((w["start"] + w["end"]) / 2.0, segs)]
    dropped = len(words) - len(kept)
    if dropped:
        logger.info(f"[film_recap] lọc {dropped}/{len(words)} từ ASR bịa (nhạc/im lặng/lặp)")
    return kept   # lọc sạch hết (vd clip toàn nhạc) → ĐÚNG là không caption
