"""voice.py — multi-voice nhập vai cho long_narrative (FIX hụt hơi: đọc NGUYÊN BLOCK).

Mỗi `NarrationBlock` → 1 call Vbee NGUYÊN VĂN (KHÔNG chẻ câu rồi ghép — đó là lỗi gây hụt
hơi ở prototype). Giọng theo `speaker` (voice_map). Gọi Vbee TRỰC TIẾP (không qua TTS budget
gate của product — long_narrative reserve riêng qua ledger video_engine). LUFS -16 mỗi block,
nối block bằng numpy + gap 0.28s. Trả `BeatVoice(wav, duration, blocks[(speaker,text,start,end)])`
cho captions.py (align) + audio.py (ducking) + render.py.

Reuse: `normalize_tts_text` (tts_text.py, đã mở rộng _NAME_READINGS), creds qua config.settings.
Engine theo LONGFORM_TTS_ENGINE: 'vbee' (mặc định, ổn định, đọc phẳng) | 'gemini' (Gemini 2.5
TTS, nhấn nhá per-block theo field `context`). Gemini lỗi từng block → fallback Vbee block đó.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import time
import wave
from dataclasses import dataclass, field

import httpx
import numpy as np
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import settings
from core.config_checks import looks_real_secret
from core.logger import logger
from video_engine.long_narrative.script_schema import Beat
from video_engine.voice.tts_text import normalize_tts_text

_VBEE_BASE = "https://vbee.vn/api/v1"
_VBEE_POLL_MAX = 40
_VBEE_POLL_S = 2.0
SR = 48000
GAP_BLOCK_S = 0.28          # nghỉ giữa block (đủ để tách lượt thoại, không lê thê)
TAIL_S = 0.35              # nghỉ cuối beat (tránh cụt đuôi khi concat)
LONGFORM_SPEED = 1.0       # giọng đọc TỰ NHIÊN (founder: 1.15 nhanh quá → hụt hơi, nghe không rõ). 1.0 =
#                            _atempo_wav tự bỏ qua nén → giữ khoảng nghỉ tự nhiên. Muốn nhanh nhẹ: tối đa 1.08.
# Cache giọng DÙNG CHUNG (persistent, KHÔNG bó theo thư mục render) — block giống nhau (cùng text+giọng+
# context+persona) TÁI DÙNG across MỌI render → KHÔNG gọi lại API TTS trả phí (founder: đừng gọi Gemini
# liên tục). Key cache đã là md5 nội-dung nên dùng chung an toàn; đổi persona/anchor vẫn tự bust.
VOICE_CACHE_DIR = os.path.join("storage", "long_narrative", "voice_cache")

# voice_map theo speaker (plan C2). Narrator = giọng review cà khịa; nhân vật = giọng khác để
# tai phân biệt được "nhập vai". Mở rộng khi có speaker mới (đối thủ/BLV...).
VOICE_MAP = {
    "narrator": "n_haiduong_male_namreviewhehe_review_vc",
    "messi": "n_hanoi_male_hnquanganhreviewphim_review_vc",
    "referee": "n_vinhphuc_male_tuannguyenvan_review_vc",
    "opponent": "n_vinhphuc_male_tuannguyenvan_review_vc",
}
DEFAULT_VOICE = VOICE_MAP["narrator"]

# ── Gemini 2.5 TTS (engine biểu cảm — bật qua LONGFORM_TTS_ENGINE=gemini) ──────
# GIỌNG: narrator = 1 giọng kênh NHẤT QUÁN (GEMINI_TTS_VOICE_MALE — chọn giọng nam RÕ, KHÔNG
# androgynous như Puck → tránh "câu đầu nữ, câu sau nam"). CHỈ ĐỔI GIỌNG khi NHẬP VAI thật:
# director tách block speaker != 'narrator' cho lời thoại nhân vật (kiểu Thanh Pahm). Mỗi nhân
# vật 1 giọng riêng ỔN ĐỊNH theo tên (cùng nhân vật = cùng giọng cả video). Narration thường
# KHÔNG bao giờ đổi giọng.
_CHARACTER_VOICE_POOL = ("Orus",)  # giọng NHÂN VẬT thứ 2 (nhập vai/nhập tâm thoại) — founder chọn Orus
# context (schema beat) → chỉ đạo cảm xúc cho Gemini — đây là điểm Vbee KHÔNG làm được.
_CONTEXT_STYLE = {
    "normal": "giọng kể tự nhiên, đời thường",
    "hype": "giọng phấn khích, hào hứng, đẩy năng lượng cao",
    "joke": "giọng tinh nghịch, trêu chọc, cà khịa khoái trá",
    "climax": "BÙNG NỔ, hét phấn khích, dồn dập, đây là cao trào",
    "whisper": "hạ giọng thì thầm, nén lại, gần như bí mật",
    "drama": "giọng căng thẳng, kịch tính, nén cảm xúc",
}
_GEMINI_PERSONA = (
    "Đọc bằng giọng ĐÀN ÔNG TRƯỞNG THÀNH, trầm, nam tính, dứt khoát — TUYỆT ĐỐI KHÔNG đọc "
    "giọng con gái hay trẻ con (anchor khóa nam cho Puck — giọng vốn androgynous dễ lật nữ ở câu "
    "cao trào). Bạn là người dẫn kênh điểm tin bóng đá Gen Z, cà khịa, đời thường, đọc tiếng Việt "
    "như đang livestream tám với hội bạn. Diễn ĐÚNG chỉ đạo cảm xúc, KHÔNG đọc đều đều. "
    "Chỉ đọc phần lời sau, không đọc nhãn chỉ đạo: "
)


@dataclass
class BlockTiming:
    speaker: str
    text: str
    context: str
    start: float
    end: float


@dataclass
class BeatVoice:
    wav: str
    duration: float
    blocks: list[BlockTiming] = field(default_factory=list)
    engine: str = "vbee"

    @property
    def narration_text(self) -> str:
        return " ".join(b.text for b in self.blocks if b.text).strip()


class VoiceError(RuntimeError):
    pass


def voice_for_speaker(speaker: str, voice_map: dict[str, str] | None = None) -> str:
    vm = voice_map or VOICE_MAP
    return vm.get((speaker or "").strip().lower()) or vm.get("narrator") or DEFAULT_VOICE


def _vbee_ready() -> bool:
    return (
        looks_real_secret(settings.vbee_api_token or "", min_length=12)
        and bool((settings.vbee_app_id or "").strip())
    )


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=8), reraise=True)
def _vbee_create(text: str, voice_code: str, speed: float) -> str:
    """Tạo job Vbee → request_id. @retry ở ĐÂY an toàn: create lỗi = CHƯA tạo job (chưa tính phí)."""
    headers = {"Authorization": f"Bearer {settings.vbee_api_token}"}
    callback = (settings.vbee_callback_url or "").strip() or "https://vbee.vn/tts-callback"
    create = httpx.post(
        f"{_VBEE_BASE}/tts",
        headers=headers,
        json={
            "app_id": settings.vbee_app_id,
            "input_text": text,
            "voice_code": voice_code,
            "audio_type": "wav",
            "speed_rate": float(speed),
            "callback_url": callback,
        },
        timeout=60.0,
    )
    create.raise_for_status()
    rid = str((create.json().get("result") or {}).get("request_id") or "").strip()
    if not rid:
        raise VoiceError("Vbee không trả request_id")
    return rid


@retry(stop=stop_after_attempt(4), wait=wait_exponential(min=2, max=8), reraise=True)
def _vbee_poll_download(rid: str) -> bytes:
    """Poll job đã tạo + tải WAV. @retry CHỈ re-poll/tải LẠI cùng rid — KHÔNG tạo job mới (không
    tính phí lặp). Đây là điểm khác cốt lõi: tách create khỏi poll để poll-fail không re-bill."""
    headers = {"Authorization": f"Bearer {settings.vbee_api_token}"}
    for _ in range(_VBEE_POLL_MAX):
        st = httpx.get(f"{_VBEE_BASE}/tts/{rid}", headers=headers, timeout=60.0)
        if st.status_code >= 400:
            raise VoiceError(f"Vbee poll HTTP {st.status_code}")
        res = st.json().get("result") or {}
        state = str(res.get("status") or "").upper()
        if state in {"SUCCESS", "DONE", "COMPLETED"}:
            link = str(res.get("audio_link") or "").strip()
            if not link.startswith("http"):
                raise VoiceError("Vbee thiếu audio_link")
            dl = httpx.get(link, follow_redirects=True, timeout=120.0)
            dl.raise_for_status()
            return dl.content
        if state in {"FAILED", "ERROR", "FAILURE"}:
            raise VoiceError(f"Vbee {state}")
        time.sleep(_VBEE_POLL_S)
    raise VoiceError("Vbee timeout poll")


def _vbee_fetch_wav(text: str, voice_code: str, speed: float) -> bytes:
    """create (1 job, retry an toàn) → poll/download (retry KHÔNG re-tạo job). Trả WAV bytes."""
    rid = _vbee_create(text, voice_code, speed)
    return _vbee_poll_download(rid)


def _loudnorm_resample(src_wav: str, dst_wav: str) -> None:
    """loudnorm I=-16 + resample 48k mono s16le (đồng nhất chuỗi audio cho concat/mix)."""
    proc = subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", src_wav,
         "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
         "-ar", str(SR), "-ac", "1", "-c:a", "pcm_s16le", dst_wav],
        capture_output=True, text=True, timeout=180,
    )
    if proc.returncode != 0:
        raise VoiceError(f"loudnorm/resample lỗi: {proc.stderr[:200]}")


def _resample_only(src_wav: str, dst_wav: str) -> None:
    """CHỈ resample 48k mono s16le — KHÔNG loudnorm (GIỮ dynamic to/nhỏ giữa block: climax to,
    whisper nhỏ). Dùng cho Gemini (đã biểu cảm); loudnorm cuối mix ở audio.py chuẩn hoá tổng."""
    proc = subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", src_wav,
         "-ar", str(SR), "-ac", "1", "-c:a", "pcm_s16le", dst_wav],
        capture_output=True, text=True, timeout=180,
    )
    if proc.returncode != 0:
        raise VoiceError(f"resample lỗi: {proc.stderr[:200]}")


_EDGE_VOICE = {"narrator": "vi-VN-NamMinhNeural", "female": "vi-VN-HoaiMyNeural"}


def edge_voice_for_speaker(speaker: str | None) -> str:
    """Giọng edge-tts (Microsoft, FREE) theo speaker — nam/narrator mặc định NamMinh; nữ → HoaiMy."""
    sp = (speaker or "narrator").strip().lower()
    if any(k in sp for k in ("nu", "nữ", "female", "cô", "bà", "chị")):
        return _EDGE_VOICE["female"]
    return _EDGE_VOICE["narrator"]


def _synth_block_edge(text: str, voice_code: str, speed: float, cache_dir: str) -> str:
    """Synth 1 block bằng edge-tts (Microsoft, FREE — engine TEST tiết kiệm credit) → wav 48k loudnorm, cache.
    edge nhận rate %; speed bake luôn vào đây (như Vbee) nên KHÔNG cần atempo hậu kỳ."""
    import asyncio
    import edge_tts
    os.makedirs(cache_dir, exist_ok=True)
    key = hashlib.md5(f"edge|{text}|{voice_code}|{speed}".encode("utf-8")).hexdigest()
    out = os.path.join(cache_dir, f"blk_{key}.wav")
    if os.path.exists(out) and os.path.getsize(out) > 2000:
        return out
    raw = out + ".raw.mp3"
    rate_s = f"{int(round((speed - 1.0) * 100)):+d}%"
    try:
        asyncio.run(edge_tts.Communicate(text, voice_code, rate=rate_s).save(raw))
        _loudnorm_resample(raw, out)
    finally:
        if os.path.exists(raw):
            os.remove(raw)
    return out


def _synth_block(text: str, voice_code: str, speed: float, cache_dir: str) -> str:
    """Synth 1 block (đã normalize) → wav 48k đã loudnorm. Cache theo md5(text+voice+speed)."""
    os.makedirs(cache_dir, exist_ok=True)
    key = hashlib.md5(f"{text}|{voice_code}|{speed}".encode("utf-8")).hexdigest()
    out = os.path.join(cache_dir, f"blk_{key}.wav")
    if os.path.exists(out) and os.path.getsize(out) > 2000:
        return out
    raw = out + ".raw.wav"
    try:
        data = _vbee_fetch_wav(text, voice_code, speed)
        with open(raw, "wb") as f:
            f.write(data)
        _loudnorm_resample(raw, out)
    finally:
        if os.path.exists(raw):
            os.remove(raw)
    return out


def _gemini_ready() -> bool:
    return (
        looks_real_secret(settings.gemini_api_key or "", min_length=12)
        and bool((settings.gemini_tts_model or "").strip())
    )


def gemini_voice_for_speaker(speaker: str) -> str:
    """narrator/rỗng → giọng kênh NHẤT QUÁN. Nhân vật (nhập vai, speaker != narrator) → 1 giọng
    riêng ỔN ĐỊNH theo tên (khác giọng kênh) để tai phân biệt 'ai đang nói'. Tên lạ vẫn ra giọng
    ổn định, KHÔNG random giữa các lần render (chống đổi-giọng-vô-cớ)."""
    channel = settings.gemini_tts_voice_male or "Charon"
    sp = (speaker or "narrator").strip().lower()
    if sp in ("", "narrator"):
        return channel
    pool = [v for v in _CHARACTER_VOICE_POOL if v != channel] or [channel]
    return pool[sum(ord(c) for c in sp) % len(pool)]


def _clean_for_gemini(text: str) -> str:
    """Gemini đọc tên nước ngoài + số TỐT → CHỈ bỏ chỉ-dẫn-sân-khấu [ ]( ), giữ tên riêng (KHÁC Vbee).
    NHƯNG slang Anh (GOAT/aura/fan...) Gemini cũng đọc sai → áp phiên âm slang (P0-1), KHÔNG áp _NAME_READINGS."""
    from video_engine.voice.tts_text import apply_slang_readings, strip_stage_directions
    return apply_slang_readings(strip_stage_directions(text))


_GEMINI_MIN_INTERVAL_S = 0.5   # giãn cách tối thiểu giữa 2 call Gemini TTS (né burst 429)
_gemini_last = [0.0]
_GEMINI_TRANSIENT = (
    "429", "rate", "quota", "resource", "exhaust", "500", "503",
    "unavailable", "timeout", "deadline", "overloaded",
)
# AUTO fallback: gặp credit-out 1 lần → LATCH cả run còn lại dùng Vbee (giữ giọng đồng nhất, KHÔNG
# trộn gemini↔vbee từng block như cũ). reset_engine_state() mỗi video để re-thử khi founder nạp lại.
_gemini_disabled_run = [False]
_vieneu_disabled_run = [False]   # latch: 1 block vieneu lỗi (daemon chết) → cả video còn lại lùi Vbee
_GEMINI_CREDIT_OUT = ("prepayment", "credit", "deplet", "billing", "insufficient")
_GEMINI_MALE_HARD = "Charon"   # giọng nam CHẮC CHẮN để re-synth khi narrator-block bị lật nữ (Puck)
_F0_FEMALE_HZ = 205.0          # F0 median > ngưỡng này ở block narrator = nghi lật giọng nữ


def reset_engine_state() -> None:
    """Gọi 1 lần đầu mỗi video (render_script): bỏ latch credit-out → re-thử Gemini khi đã nạp lại."""
    _gemini_disabled_run[0] = False
    _vieneu_disabled_run[0] = False


def _is_credit_out(exc: Exception) -> bool:
    """Lỗi HẾT TIỀN/credit (bền vững) — khác rate-limit/transient (tạm thời, retry được)."""
    return any(k in str(exc).lower() for k in _GEMINI_CREDIT_OUT)


def _median_f0(sig: np.ndarray, sr: int) -> float:
    """F0 median (Hz) trên frame CÓ TIẾNG, autocorrelation. 0.0 nếu không đủ tiếng. Bắt narrator-block
    bị 'lật nữ' (Puck androgynous) để re-synth giọng nam cứng. Best-effort, ngưỡng cao chống báo nhầm."""
    x = sig.astype(np.float64)
    if x.size < sr // 4:
        return 0.0
    fl, hop = int(sr * 0.04), int(sr * 0.02)
    lo, hi = int(sr / 320), int(sr / 75)   # F0 trong 75–320 Hz
    energy = np.sqrt(np.mean(x ** 2)) + 1e-9
    f0s: list[float] = []
    for i in range(0, x.size - fl, hop):
        fr = x[i:i + fl]
        if np.sqrt(np.mean(fr ** 2)) < 0.4 * energy:   # bỏ frame im
            continue
        fr = fr - fr.mean()
        ac = np.correlate(fr, fr, "full")[fl - 1:]
        if ac[0] <= 0 or hi <= lo:
            continue
        seg = ac[lo:hi]
        if seg.size == 0:
            continue
        lag = lo + int(np.argmax(seg))
        if ac[lag] > 0.3 * ac[0]:   # đủ tuần hoàn = voiced
            f0s.append(sr / lag)
        if len(f0s) >= 60:
            break
    return float(np.median(f0s)) if f0s else 0.0


def _gemini_rate_limit() -> None:
    now = time.monotonic()
    wait = _GEMINI_MIN_INTERVAL_S - (now - _gemini_last[0])
    if wait > 0:
        time.sleep(wait)
    _gemini_last[0] = time.monotonic()


def _gemini_tts_pcm(text: str, voice: str, style: str) -> bytes:
    """1 call Gemini TTS → PCM 24k. RETRY transient (429/5xx) có backoff 1→2→4s; lỗi chặn-nội-dung
    /khác → raise NGAY để caller fallback Vbee block đó. Rate-limit toàn cục né 429 burst khi video
    dài gọi vài chục block (lỗi cũ: 429 hàng loạt → block rớt Vbee phẳng → giọng TRỘN)."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=settings.gemini_api_key)
    cfg = types.GenerateContentConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
            )
        ),
    )
    contents = f"[CHỈ ĐẠO: {style}] {_GEMINI_PERSONA}{text}"
    last: Exception | None = None
    for attempt in range(4):
        _gemini_rate_limit()
        try:
            resp = client.models.generate_content(
                model=settings.gemini_tts_model, contents=contents, config=cfg
            )
        except Exception as exc:  # noqa: BLE001
            if not any(k in str(exc).lower() for k in _GEMINI_TRANSIENT):
                raise  # không phải transient (vd chặn nội dung) → fallback ngay, đừng phí retry
            last = exc
            if attempt < 3:
                time.sleep(min(8.0, 2.0 ** attempt))
            continue
        try:
            pcm = resp.candidates[0].content.parts[0].inline_data.data
        except (AttributeError, IndexError, TypeError) as exc:
            raise VoiceError(f"Gemini không trả audio (chặn nội dung?): {exc}") from exc
        if not pcm:
            raise VoiceError("Gemini trả audio rỗng (có thể bị chặn nội dung).")
        return pcm
    raise last or VoiceError("Gemini TTS thất bại sau retry.")


def _synth_block_gemini(text: str, voice: str, context: str, cache_dir: str) -> str:
    """Synth 1 block qua Gemini 2.5 TTS, style theo context → wav 48k (RESAMPLE-ONLY, giữ dynamic).
    Cache md5. Lỗi → raise để caller fallback Vbee block đó.
    """
    os.makedirs(cache_dir, exist_ok=True)
    style = _CONTEXT_STYLE.get((context or "").strip().lower(), _CONTEXT_STYLE["normal"])
    # persona vào key → đổi anchor/persona thì BUST cache (tránh trả audio đọc bằng persona cũ).
    key = hashlib.md5(f"gemini|{text}|{voice}|{context}|{_GEMINI_PERSONA}".encode("utf-8")).hexdigest()
    out = os.path.join(cache_dir, f"blk_{key}.wav")
    if os.path.exists(out) and os.path.getsize(out) > 2000:
        return out
    pcm = _gemini_tts_pcm(text, voice, style)
    raw = out + ".raw.wav"
    try:  # try/finally GỘP ghi wav + transcode → raw không rò khi lỗi
        with wave.open(raw, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(24000)
            w.writeframes(pcm)
        _resample_only(raw, out)  # KHÔNG loudnorm per-block — giữ tương phản hét/thì-thầm
    finally:
        if os.path.exists(raw):
            os.remove(raw)
    return out


# ── VieNeu: giọng CLONE local (engine 'vieneu') qua daemon venv riêng ─────────
_vieneu_ref_hash_cache: dict[str, str] = {}


def _vieneu_ref_hash(ref: str) -> str:
    """Hash danh tính ref (1 lần/đường dẫn) → vào cache key; đổi ref thì BUST cache."""
    if ref in _vieneu_ref_hash_cache:
        return _vieneu_ref_hash_cache[ref]
    h = "default"
    try:
        if ref and os.path.exists(ref):
            with open(ref, "rb") as f:
                h = hashlib.md5(f.read()).hexdigest()[:12]
    except OSError:
        h = "default"
    _vieneu_ref_hash_cache[ref] = h
    return h


def _vieneu_ready() -> bool:
    try:
        from video_engine.voice.vieneu_client import vieneu_ready
        return vieneu_ready()
    except Exception:  # noqa: BLE001 — thiếu module/daemon → coi như chưa sẵn sàng
        return False


def _synth_block_vieneu(text: str, emotion: str, cache_dir: str) -> str:
    """Synth 1 block bằng giọng CLONE VieNeu (qua daemon) → wav 48k mono s16le, cache md5.
    Tốc độ lấy từ voiceclone_speed (atempo, giữ cao độ); resample-only GIỮ dynamic cảm xúc."""
    from video_engine.voice.vieneu_client import synth_via_daemon
    cache_dir = os.path.abspath(cache_dir)   # daemon ở process KHÁC (cwd khác) → out_path PHẢI tuyệt đối
    os.makedirs(cache_dir, exist_ok=True)
    ref = (settings.voiceclone_ref_audio_path or "").strip()
    sp = round(float(settings.voiceclone_speed or 1.0), 3)
    silp = round(float(settings.voiceclone_silence_p or 0.12), 3)
    key = hashlib.md5(
        f"vieneu|{text}|{_vieneu_ref_hash(ref)}|{emotion}|{sp}|{silp}".encode("utf-8")).hexdigest()
    out = os.path.join(cache_dir, f"blk_{key}.wav")
    if os.path.exists(out) and os.path.getsize(out) > 2000:
        return out
    raw = out + ".raw.wav"
    try:
        synth_via_daemon(text, raw, ref_audio=ref, emotion=emotion, silence_p=silp)
        if abs(sp - 1.0) > 0.01:   # atempo: nhanh hơn xíu, GIỮ cao độ → không chuột-chít
            proc = subprocess.run(
                ["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-filter:a", f"atempo={sp}",
                 "-ar", str(SR), "-ac", "1", "-c:a", "pcm_s16le", out],
                capture_output=True, text=True, timeout=180,
            )
            if proc.returncode != 0:
                raise VoiceError(f"vieneu atempo lỗi: {proc.stderr[:200]}")
        else:
            _resample_only(raw, out)
    finally:
        if os.path.exists(raw):
            os.remove(raw)
    return out


def _read_wav_mono(path: str) -> tuple[np.ndarray, int]:
    with wave.open(path, "rb") as w:
        sr, ch, n = w.getframerate(), w.getnchannels(), w.getnframes()
        raw = w.readframes(n)
    a = np.frombuffer(raw, dtype=np.int16)
    if ch > 1:
        a = a.reshape(-1, ch).mean(axis=1).astype(np.int16)
    return a, sr


def _atempo_wav(wav_path: str, speed: float) -> str:
    """Tăng tốc audio bằng ffmpeg atempo (GIỮ cao độ) → file _spd. Dùng cho path GEMINI (không có speed_rate
    như Vbee) → video nhanh đúng LONGFORM_SPEED. atempo hỗ trợ 0.5-2.0. Fail-soft → giữ tốc gốc."""
    if abs(speed - 1.0) < 0.01:
        return wav_path
    out = wav_path[:-4] + f"_spd{int(round(speed * 100))}.wav"
    if os.path.exists(out) and os.path.getsize(out) > 1000:
        return out
    try:
        subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-i", wav_path,
                        "-filter:a", f"atempo={speed:.3f}", "-ar", str(SR), "-ac", "1", out],
                       check=True, capture_output=True)
        return out if (os.path.exists(out) and os.path.getsize(out) > 1000) else wav_path
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"[voice] atempo speed lỗi (giữ tốc gốc): {str(exc)[:120]}")
        return wav_path


def synthesize_beat(
    beat: Beat,
    out_wav: str,
    *,
    voice_map: dict[str, str] | None = None,
    speed: float = LONGFORM_SPEED,
    cache_dir: str | None = None,
) -> BeatVoice:
    """Synth toàn bộ block của 1 beat (mỗi block 1 call Vbee) → out_wav + timeline.

    out_wav = 48k mono s16le (đồng nhất để concat chunk + mix ffmpeg ở audio.py).
    """
    engine = (settings.longform_tts_engine or "vbee").strip().lower()
    use_edge = engine == "edge"          # edge-tts (Microsoft) = FREE: engine TEST tiết kiệm credit (không cần key)
    use_gemini = engine in ("gemini", "auto") and _gemini_ready() and not _gemini_disabled_run[0]
    use_vieneu = engine == "vieneu" and _vieneu_ready()   # giọng CLONE local NVL qua daemon VieNeu
    if not use_edge and not use_vieneu:
        if not use_gemini and not _vbee_ready():
            raise VoiceError("Thiếu VBEE_APP_ID/VBEE_API_TOKEN thật → không synth được giọng.")
        if use_gemini and not _vbee_ready():
            logger.warning("[voice] engine=gemini, Vbee chưa cấu hình → KHÔNG có fallback nếu Gemini lỗi.")
    # Lọc theo text ĐÃ-NORMALIZE (giống _synth_block dùng) — block chỉ chứa chỉ-dẫn-sân-khấu ('[cười]',
    # '(nhạc)') normalize ra RỖNG: nếu lọc theo text gốc thì lọt xuống _synth_block gọi Vbee input rỗng.
    blocks = [b for b in beat.narration_blocks if normalize_tts_text(b.text).strip()]
    if not blocks:
        raise VoiceError(f"Beat {beat.beat_id} không có narration text.")
    cache_dir = cache_dir or VOICE_CACHE_DIR   # mặc định: cache CHUNG persistent → tái dùng, không gọi lại API
    vm = voice_map or VOICE_MAP

    parts: list[np.ndarray] = []
    timings: list[BlockTiming] = []
    t = 0.0
    for blk in blocks:
        block_wav = None
        if use_gemini:
            try:
                gv = gemini_voice_for_speaker(blk.speaker)
                block_wav = _synth_block_gemini(_clean_for_gemini(blk.text), gv, blk.context, cache_dir)
                # gender-net (best-effort): narrator block lật NỮ (Puck androgynous) → re-synth giọng nam cứng.
                sp = (blk.speaker or "narrator").strip().lower()
                if sp in ("", "narrator") and gv != _GEMINI_MALE_HARD:
                    try:
                        _fsig, _fsr = _read_wav_mono(block_wav)
                        _f0 = _median_f0(_fsig, _fsr)
                        if _f0 > _F0_FEMALE_HZ:
                            logger.warning(f"[voice] beat {beat.beat_id} narrator F0={_f0:.0f}Hz nghi lật nữ "
                                           f"→ re-synth giọng nam cứng {_GEMINI_MALE_HARD}")
                            block_wav = _synth_block_gemini(
                                _clean_for_gemini(blk.text), _GEMINI_MALE_HARD, blk.context, cache_dir)
                    except Exception as exc:  # noqa: BLE001 — pitch-net best-effort, lỗi thì kệ
                        logger.debug(f"[voice] pitch-net bỏ qua: {str(exc)[:100]}")
            except Exception as exc:  # noqa: BLE001 — fallback Vbee
                if _is_credit_out(exc):
                    _gemini_disabled_run[0] = True   # latch: cả video còn lại dùng Vbee
                    use_gemini = False                # các block sau của beat này cũng Vbee → đồng nhất
                    logger.warning(f"[voice] Gemini HẾT CREDIT → chuyển CẢ video còn lại sang Vbee "
                                   f"(giữ giọng đồng nhất): {str(exc)[:120]}")
                else:
                    logger.warning(f"[voice] gemini block lỗi → fallback vbee block này: {str(exc)[:160]}")
        if block_wav is not None and abs(speed - 1.0) > 0.01:
            # GEMINI path: block_wav≠None ở đây ⟺ gemini synth THÀNH CÔNG (vbee chạy ở dưới khi None).
            # Gemini bỏ qua speed → atempo hậu-kỳ cho nhanh đúng LONGFORM_SPEED (Vbee dưới đã bake speed).
            block_wav = _atempo_wav(block_wav, speed)
        if block_wav is None and use_vieneu and not _vieneu_disabled_run[0]:
            try:
                block_wav = _synth_block_vieneu(
                    normalize_tts_text(blk.text),
                    (settings.voiceclone_emotion or "natural").strip(), cache_dir)
            except Exception as exc:  # noqa: BLE001 — daemon lỗi → latch lùi Vbee cả video còn lại
                _vieneu_disabled_run[0] = True
                logger.warning(f"[voice] vieneu lỗi (daemon?) → lùi Vbee cả video còn lại: {str(exc)[:160]}")
        if block_wav is None:
            if use_edge:
                block_wav = _synth_block_edge(
                    normalize_tts_text(blk.text), edge_voice_for_speaker(blk.speaker), speed, cache_dir)
            elif _vbee_ready():
                voice = voice_for_speaker(blk.speaker, vm)
                block_wav = _synth_block(normalize_tts_text(blk.text), voice, speed, cache_dir)
            else:
                raise VoiceError("TTS lỗi và Vbee chưa cấu hình → không engine nào synth được block.")
        sig, sr = _read_wav_mono(block_wav)
        if sr != SR:  # an toàn: mọi block đã resample 48k, nhưng phòng cache cũ
            logger.warning(f"[voice] block sr={sr}≠{SR}, vẫn nối (kiểm cache).")
        dur = len(sig) / float(sr or SR)
        start = round(t, 3)
        end = round(t + dur, 3)
        timings.append(BlockTiming(blk.speaker, blk.text, blk.context, start, end))
        parts.append(sig)
        parts.append(np.zeros(int(sr * GAP_BLOCK_S), dtype=np.int16))
        t = end + GAP_BLOCK_S
    parts.append(np.zeros(int(SR * TAIL_S), dtype=np.int16))

    os.makedirs(os.path.dirname(out_wav) or ".", exist_ok=True)
    merged = np.concatenate(parts)
    with wave.open(out_wav, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(merged.tobytes())
    total = round(len(merged) / float(SR), 3)
    # _vieneu_disabled_run: nếu vieneu fallback giữa chừng → 'used' phải phản ánh ĐÚNG engine thực (Vbee), không ghi nhầm 'vieneu'
    used = "gemini" if use_gemini else (
        "vieneu" if (use_vieneu and not _vieneu_disabled_run[0]) else ("edge" if use_edge else "vbee"))
    logger.info(
        f"[voice] beat {beat.beat_id}: {len(blocks)} block, {total:.1f}s, "
        f"engine={used}, speakers={beat.speakers} → {out_wav}"
    )
    return BeatVoice(wav=out_wav, duration=total, blocks=timings, engine=used)
