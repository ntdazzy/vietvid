"""captions.py — phụ đề khớp lời 100% (chữ = KỊCH BẢN, giờ = giọng THẬT).

Vấn đề: Whisper transcribe sai tên riêng (Messi→"mét xi", "An-giê-ri"...) nên KHÔNG hiển thị
chữ Whisper. Giải: lấy CHỮ từ kịch bản (đúng 100%), lấy GIỜ từ Whisper word-timestamp, rồi
ALIGN script-words ↔ asr-words bằng `difflib.SequenceMatcher` (chuẩn hoá: thường hoá + bỏ dấu
+ bỏ dấu câu để khớp được dù Whisper nghe lệch). Từ kịch bản không có anchor ASR → NỘI SUY
tuyến tính thời gian giữa 2 anchor gần nhất. Gom cụm 5-7 từ; đánh dấu cụm "hot" (có từ khoá) để
karaoke nhấn vàng.

Fail-soft: thiếu Groq key / ASR lỗi → canh giờ TUYẾN TÍNH theo tỉ lệ ký tự trên tổng thời lượng
(captions vẫn chạy, kém chính xác hơn).
"""

from __future__ import annotations

import difflib
import re
import unicodedata
from dataclasses import dataclass, field

from video_engine.voice.asr import transcribe_words

# Từ khoá nhấn vàng (bóng đá/tin) — render karaoke tô đậm cụm chứa các từ này.
DEFAULT_HOT_KEYWORDS = (
    "messi", "met xi", "38", "16", "klose", "klo do", "zidane", "zi dan", "hat-trick",
    "hat trick", "world cup", "quo cap", "phat den", "penalty", "ky luc", "vo dich",
    "milla", "ronaldo", "pele", "argentina", "ac hen", "algeria", "an gie", "3-0",
    "lautaro", "11m", "200", "24",
)
_PUNCT_BREAK = re.compile(r"[,.!?…:;]$")
_CHUNK_MAX_WORDS = 6
_CHUNK_MAX_SECONDS = 2.0
_MIN_CHUNK_DUR = 0.12


@dataclass
class CaptionWord:
    text: str          # từ GỐC kịch bản (hiển thị đúng 100%)
    start: float
    end: float


@dataclass
class CaptionChunk:
    start: float
    end: float
    words: list[CaptionWord] = field(default_factory=list)
    hot: bool = False

    @property
    def text(self) -> str:
        return " ".join(w.text for w in self.words).strip()


def _strip_diacritics(s: str) -> str:
    s = s.replace("đ", "d").replace("Đ", "D")
    nfd = unicodedata.normalize("NFD", s)
    return "".join(c for c in nfd if not unicodedata.combining(c))


def _norm(token: str) -> str:
    t = _strip_diacritics(token or "").lower()
    t = re.sub(r"[^a-z0-9]", "", t)
    return t


def _tokenize_script(text: str) -> list[str]:
    """Tách từ hiển thị (giữ nguyên dấu câu cuối để biết chỗ ngắt cụm). Bỏ token rỗng-norm."""
    out: list[str] = []
    for raw in (text or "").split():
        if _norm(raw):
            out.append(raw)
    return out


def _align(script_tokens: list[str], asr_words: list[dict], win_start: float, win_end: float) -> list[CaptionWord]:
    """Gán (start,end) cho từng từ kịch bản TRONG cửa sổ [win_start, win_end]: anchor=equal block
    (mốc ASR thật), còn lại nội suy tuyến tính; đầu kẹp win_start, cuối kẹp win_end."""
    norm_script = [_norm(t) for t in script_tokens]
    norm_asr = [_norm(w.get("word", "")) for w in asr_words]
    timed: list[tuple[float, float] | None] = [None] * len(script_tokens)

    sm = difflib.SequenceMatcher(None, norm_script, norm_asr, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != "equal":
            continue
        for k in range(i2 - i1):
            a = asr_words[j1 + k]
            try:
                timed[i1 + k] = (float(a.get("start", 0.0)), float(a.get("end", 0.0)))
            except (TypeError, ValueError):
                pass

    # Nội suy các khoảng None giữa 2 anchor (và đầu/cuối) — neo trong cửa sổ block.
    anchors = [i for i, v in enumerate(timed) if v is not None]
    n = len(script_tokens)
    if not anchors:
        # không có anchor nào → rải đều trong cửa sổ
        return _linear_words(script_tokens, win_start, win_end)

    # đầu chuỗi: từ win_start tới anchor đầu
    first = anchors[0]
    if first > 0:
        t_end = timed[first][0]
        step = max(0.0, t_end - win_start) / (first + 1)
        for i in range(first):
            timed[i] = (round(win_start + step * i, 3), round(win_start + step * (i + 1), 3))
    # giữa các anchor
    for a, b in zip(anchors, anchors[1:]):
        if b - a <= 1:
            continue
        t0 = timed[a][1]
        t1 = timed[b][0]
        span = max(0.0, t1 - t0)
        gap = b - a
        step = span / gap if gap else 0.0
        for k in range(1, gap):
            s = round(t0 + step * (k - 1), 3)
            e = round(t0 + step * k, 3)
            timed[a + k] = (s, e)
    # cuối chuỗi: từ anchor cuối tới win_end
    last = anchors[-1]
    if last < n - 1:
        t0 = timed[last][1]
        span = max(0.0, win_end - t0)
        step = span / (n - last)
        for k in range(1, n - last):
            timed[last + k] = (round(t0 + step * (k - 1), 3), round(t0 + step * k, 3))

    words: list[CaptionWord] = []
    for tok, tv in zip(script_tokens, timed):
        s, e = tv if tv else (win_start, win_start)
        if e <= s:
            e = s + 0.12
        words.append(CaptionWord(tok, round(s, 3), round(e, 3)))
    return words


def _linear_words(script_tokens: list[str], win_start: float, win_end: float) -> list[CaptionWord]:
    """Fallback: rải đều theo tỉ lệ ký tự TRONG cửa sổ [win_start, win_end].
    Có blocks → gọi per-block (khớp ranh block thật) thay vì rải đều cả beat (lỗi drift cũ)."""
    span = max(0.01, win_end - win_start)
    total_chars = sum(len(t) for t in script_tokens) or 1
    words: list[CaptionWord] = []
    cum = 0
    for tok in script_tokens:
        s = win_start + span * cum / total_chars
        cum += len(tok)
        e = win_start + span * cum / total_chars
        words.append(CaptionWord(tok, round(s, 3), round(max(e, s + 0.12), 3)))
    return words


def _chunk(words: list[CaptionWord], hot_keywords: tuple[str, ...]) -> list[CaptionChunk]:
    chunks: list[CaptionChunk] = []
    cur: list[CaptionWord] = []
    for w in words:
        if not cur:
            cur = [w]
        else:
            cur.append(w)
        span = cur[-1].end - cur[0].start
        if _PUNCT_BREAK.search(w.text) or len(cur) >= _CHUNK_MAX_WORDS or span >= _CHUNK_MAX_SECONDS:
            chunks.append(_mk_chunk(cur, hot_keywords))
            cur = []
    if cur:
        chunks.append(_mk_chunk(cur, hot_keywords))
    # clamp end mỗi cụm < start cụm sau (tránh chồng), bỏ cụm quá ngắn
    out: list[CaptionChunk] = []
    for k, ch in enumerate(chunks):
        nxt = chunks[k + 1].start if k + 1 < len(chunks) else 1e9
        ch.end = min(ch.end, nxt - 0.03)
        if ch.end - ch.start >= _MIN_CHUNK_DUR and ch.text:
            out.append(ch)
    return out


def _mk_chunk(words: list[CaptionWord], hot_keywords: tuple[str, ...]) -> CaptionChunk:
    text_norm = _norm(" ".join(w.text for w in words))
    joined = " ".join(_norm(w.text) for w in words)
    hot = any(_norm(kw.replace(" ", "")) in text_norm or kw in joined for kw in hot_keywords)
    return CaptionChunk(start=words[0].start, end=words[-1].end, words=list(words), hot=hot)


def align_captions(
    narration_text: str,
    voice_wav: str,
    total_dur: float,
    *,
    blocks: list | None = None,
    hot_keywords: tuple[str, ...] = DEFAULT_HOT_KEYWORDS,
) -> list[CaptionChunk]:
    """Trả list CaptionChunk (mỗi cụm 5-7 từ, có word-timing để karaoke).

    Chữ = kịch bản (đúng 100%), giờ = Whisper align (nội suy chỗ lệch). ASR lỗi → canh tuyến tính.

    `blocks` (BeatVoice.blocks: list BlockTiming có .text/.start/.end — mốc giọng THẬT): nếu có,
    tính caption TỪNG BLOCK trong cửa sổ [start,end] của block đó → khớp giọng chuẩn cả khi ASR
    fail (canh tuyến tính per-block thay vì rải đều cả beat). None = hành vi cũ (cả beat).
    """
    asr_words = transcribe_words(voice_wav)
    if blocks:
        # CHUNK PER-BLOCK: chia cụm TRONG từng block → KHÔNG để 1 cụm vắt qua ranh block
        # (cụm trộn 2 block/2 speaker = sai; vd "sáu Block" nối cuối-block-1 với đầu-block-2).
        chunks: list[CaptionChunk] = []
        for blk in blocks:
            toks = _tokenize_script(getattr(blk, "text", "") or "")
            if not toks:
                continue
            bs = float(getattr(blk, "start", 0.0) or 0.0)
            be = float(getattr(blk, "end", bs) or bs)
            if be <= bs:
                be = bs + 0.12
            if asr_words:
                sub = [w for w in asr_words if bs - 0.06 <= _w_start(w) <= be + 0.06]
                bw = _align(toks, sub, bs, be)
            else:
                bw = _linear_words(toks, bs, be)
            chunks += _chunk(bw, hot_keywords)
        return chunks

    # back-compat: không có blocks → tính trên cả beat [0, total_dur]
    script_tokens = _tokenize_script(narration_text)
    if not script_tokens:
        return []
    if asr_words:
        words = _align(script_tokens, asr_words, 0.0, total_dur)
    else:
        words = _linear_words(script_tokens, 0.0, total_dur)
    return _chunk(words, hot_keywords)


def _w_start(w: dict) -> float:
    try:
        return float(w.get("start", 0.0))
    except (TypeError, ValueError):
        return 0.0
