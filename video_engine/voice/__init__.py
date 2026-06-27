"""Voice — gemini_tts (mặc định) → vbee → edge-tts; kho giọng nam/nữ theo KOL/analyzer.

V8.2: voice_pools/pick_voice tách giới tính; routing native/voiceover theo mode ở pipeline.
V8.3-Q2b: synthesize_narration_segmented — TTS TỪNG CÂU + pause 0.2s, trả starts[] từng câu
để overlay chữ hiện ĐÚNG lúc giọng đọc tới câu đó (±0.2s).
"""

from __future__ import annotations

import asyncio
import os
import re
import subprocess

from config.settings import settings
from core.logger import logger

_GENDER_RE = re.compile(r"_(male|female)_")
_SENT_SPLIT_RE = re.compile(r"(?<=[.!?…])\s+")
# Từ khoá khớp overlay↔câu giọng (narration đọc SỐ thành CHỮ nên không khớp token số được).
_PRICE_KW = ("ngàn", "nghìn", "trăm", "triệu", "đồng", "giá")
_PROOF_KW = ("sao", "đã bán", "bán", "người", "đánh giá", "tin chọn", "tin dùng",
             "lượt", "chọn", "đơn", "yêu thích", "review")


def align_overlay_times(narration: str, overlays: list[dict], starts: list[float]) -> None:
    """Gán overlay['t'] = mốc CÂU mà giọng THỰC SỰ đọc nội dung overlay (khớp chữ↔giọng).

    Overlay viết SỐ ('599K','4.8') còn narration đọc CHỮ ('năm trăm chín chín ngàn','bốn chấm tám')
    → token-overlap vô dụng. Khớp theo 'kind' bằng từ khoá tiếng Việt:
      price → CÂU có từ giá xuất hiện MUỘN NHẤT (giá thường ở CTA cuối).
      social_proof/rating → CÂU có từ proof xuất hiện SỚM NHẤT.
    Không khớp được → giữ overlay['sent'] Director đoán (clamp). Sửa tại chỗ (mutate overlays).
    """
    if not starts:
        return
    sentences = [s.strip().lower() for s in _SENT_SPLIT_RE.split((narration or "").strip()) if s.strip()]
    n = min(len(sentences), len(starts))

    def _find(keywords: tuple[str, ...], *, last: bool) -> int | None:
        hits = [i for i in range(n) if any(kw in sentences[i] for kw in keywords)]
        if not hits:
            return None
        return hits[-1] if last else hits[0]

    for ov in overlays:
        kind = (ov.get("kind") or "").strip().lower()
        idx: int | None = None
        if kind == "price":
            idx = _find(_PRICE_KW, last=True)
        elif kind in ("social_proof", "proof", "rating", "social"):
            idx = _find(_PROOF_KW, last=False)
        if idx is None:
            sent = ov.get("sent")
            idx = sent if isinstance(sent, int) and 0 <= sent < len(starts) else None
        if idx is not None and 0 <= idx < len(starts):
            ov["t"] = starts[idx]


def voice_pools() -> dict[str, list[str]]:
    """Kho giọng vbee theo giới tính: {"male": [...], "female": [...], "any": [...]}.

    V8.2 Phase 0: VBEE_VOICE_CODE_MALE/_FEMALE (CSV) là kho chính; mã trong
    VBEE_VOICE_CODE cũ suy giới tính qua pattern ``_(male|female)_`` (tương thích
    ngược), không suy được → pool "any". Trùng mã giữ 1 lần.
    """
    pools: dict[str, list[str]] = {"male": [], "female": [], "any": []}

    def _add(pool: str, raw: str) -> None:
        for code in (raw or "").split(","):
            code = code.strip()
            if code and code not in pools[pool]:
                pools[pool].append(code)

    _add("male", settings.vbee_voice_code_male)
    _add("female", settings.vbee_voice_code_female)
    for code in (settings.vbee_voice_code or "").split(","):
        code = code.strip()
        if not code or any(code in pools[p] for p in pools):
            continue
        match = _GENDER_RE.search(code)
        pools[match.group(1) if match else "any"].append(code)
    return pools


def pick_voice(gender: str = "", seed: str = "") -> str:
    """Chọn 1 mã giọng theo giới tính ("nam"/"nữ"/"male"/"female"/"") — deterministic theo seed.

    Fallback khi pool theo giới tính rỗng: any → female → male. Chưa cấu hình giọng nào → "".
    """
    pools = voice_pools()
    g = (gender or "").strip().lower()
    want = "male" if g in {"nam", "male", "m"} else "female" if g in {"nữ", "nu", "female", "f"} else ""
    order = [want] if want else []
    order += [p for p in ("any", "female", "male") if p not in order]
    for pool_name in order:
        pool = pools[pool_name]
        if pool:
            if not seed:
                return pool[0]
            return pool[sum(ord(c) for c in seed) % len(pool)]
    return ""


def _segment_engines(gender: str, voice_id: str):
    """Các engine thử theo thứ tự cho segmented TTS — TRẢ CẢ BỘ CÂU cùng 1 engine.

    Per-câu fallback sẽ TRỘN GIỌNG giữa các câu (phát hiện test thật 2026-06-12) →
    1 câu lỗi = bỏ cả bộ, redo toàn bộ bằng engine kế tiếp.
    """
    from video_engine.voice.tts_providers import build_tts_provider, vbee_if_configured

    if not settings.use_fake_clients:
        primary = build_tts_provider(gender)
        if primary is not None:
            yield primary.name, primary.synthesize
        if (settings.tts_provider or "").strip().lower() == "gemini_tts":
            vbee = vbee_if_configured()
            if vbee is not None:
                # Chọn giọng vbee: voice_id riêng (KOL/kho) > kho theo GENDER > giọng đầu.
                # (2026-06-13: trước đây gemini 429 rớt thẳng xuống edge monotone + sai gender;
                # giờ ưu tiên vbee giọng quảng cáo đúng nam/nữ.)
                vbee.voice_code = voice_id or pick_voice(gender) or vbee.voice_code
                yield "vbee", vbee.synthesize

    from video_engine.voice.tts import TTSEngine

    engine = TTSEngine()
    # Edge last-resort: giọng NAM nếu gender nam (tránh giọng nữ cho SP nam).
    if (gender or "").strip().lower() in {"nam", "male", "m"} and settings.tts_voice_male:
        engine.voice = settings.tts_voice_male
    yield "edge", lambda text, out: asyncio.run(engine._synthesize_one(text, out))  # noqa: SLF001


def synthesize_narration_segmented(
    text: str, out_path: str, *, voice_id: str = "", gender: str = "", delay_s: float = 0.0
) -> tuple[float, list[float], str]:
    """Synth CẢ ĐOẠN bằng 1 CALL → (dur, starts[], engine_used).

    2026-06-13 (fix "nhiều giọng khác nhau"): TRƯỚC synth TỪNG CÂU bằng call riêng →
    mỗi câu gemini sinh độc lập, chất giọng/nhân vật LỆCH giữa câu = tai nghe "nhiều giọng".
    GIỜ synth cả đoạn 1 lần = 1 giọng NHẤT QUÁN xuyên suốt (gemini → vbee → edge, mỗi engine
    thử 1 call cho cả đoạn). ``engine_used`` trả về để pipeline báo cáo (edge = degraded).

    ``starts[i]`` = mốc CÂU i (đã cộng ``delay_s``) ước lượng theo TỈ LỆ ký tự tích luỹ —
    single-call không có ranh giới câu chính xác; sai số ~0.3s, đủ cho overlay hook/giá/CTA.
    """
    from video_engine.compose.ffmpeg import FFmpegProcessor
    from video_engine.voice.tts_text import normalize_tts_text

    sentences = [s.strip() for s in _SENT_SPLIT_RE.split((text or "").strip()) if s.strip()]
    out_dir = os.path.dirname(out_path) or "."
    os.makedirs(out_dir, exist_ok=True)
    raw = out_path + ".raw.wav"  # đuôi chuẩn để ffmpeg/gemini-transcode nhận format (KHÔNG .raw.audio)
    clean = normalize_tts_text(text)

    def _resample(src: str) -> None:
        proc = subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", src,
             "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", out_path],
            capture_output=True, text=True, timeout=300,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"[voice] resample lỗi: {proc.stderr[:200]}")

    engine_used = ""
    last_error: Exception | None = None
    for engine_name, synth in _segment_engines(gender, voice_id):
        try:
            synth(clean, raw)  # CẢ đoạn 1 call → giọng nhất quán
            _resample(raw)
            engine_used = engine_name
            break
        except Exception as exc:  # noqa: BLE001 — đổi engine (KHÔNG trộn giọng)
            last_error = exc
            logger.warning(f"[voice] engine {engine_name} lỗi → thử engine kế: {exc}")
        finally:
            try:
                os.remove(raw)
            except FileNotFoundError:
                pass
    if not engine_used:
        raise RuntimeError(f"[voice] mọi engine TTS đều lỗi: {last_error}")

    dur = FFmpegProcessor.probe_duration(out_path)
    # starts[] CHO MỌI CÂU (kể cả <3 câu) — ước lượng theo tỉ lệ ký tự tích luỹ. Trước đây
    # <3 câu trả [delay] (1 phần tử) → overlay sent>=1 rớt bounds-check ở pipeline → mất sync.
    total_chars = sum(len(s) for s in sentences) or 1
    starts, cum = [], 0
    for s in sentences:
        starts.append(round(delay_s + dur * cum / total_chars, 3))
        cum += len(s)
    if not starts:
        starts = [round(delay_s, 3)]
    logger.info(f"[voice] 1-call engine={engine_used} dur={dur:.2f}s {len(sentences)} câu starts={starts}")
    return dur, starts, engine_used
