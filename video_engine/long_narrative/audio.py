"""audio.py — mix audio cho long_narrative: voice + nhạc nền (ducking) + foley + ambient.

Mix ở tầng FFMPEG (`sidechaincompress` ducking nhạc né giọng, `amix`+`alimiter`+`loudnorm` —
khớp filter `compose/__init__.py:243`). Nhạc nền: ưu tiên track THẬT trong `BG_MUSIC_DIR` (reuse
cơ chế `_pick_bg_music`); KHÔNG có → tự SYNTH "atmos bed" (ambience đám đông + drone theo context)
vì Pixabay KHÔNG có music API public. Foley $0 synth (whoosh/impact/cheer) đặt theo từ khoá.

Whoosh chuyển beat (Gemini 6.7) nướng vào ĐUÔI audio beat ở render.py để sống qua `concat -c copy`.
"""

from __future__ import annotations

import hashlib
import os
import subprocess

import numpy as np

from config.settings import settings
from core.logger import logger

SR = 48000
_MUSIC_EXTS = (".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac")

# context → (freqs hợp âm cho drone, hệ số sáng). Drone RẤT khẽ, chỉ làm nền khí quyển.
_MOOD_FREQS = {
    "drama": [110.00, 130.81, 164.81],     # A thứ — căng
    "climax": [130.81, 164.81, 196.00],    # C trưởng — vỡ oà
    "hype": [146.83, 185.00, 220.00],      # D trưởng — phấn khích
    "whisper": [98.00, 123.47, 146.83],    # trầm, mềm
    "joke": [164.81, 207.65, 246.94],      # sáng, nhẹ
    "normal": [110.00, 164.81, 220.00],
}


def _wwav(path: str, sig: np.ndarray, sr: int = SR) -> None:
    import wave
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((np.clip(sig, -1, 1) * 32767).astype("<i2").tobytes())


def ensure_sfx_bank(asset_dir: str) -> dict[str, str]:
    """Synth foley $0 (whoosh/impact/cheer), cache. Trả {name: path}."""
    os.makedirs(asset_dir, exist_ok=True)
    bank = {
        "whoosh": os.path.join(asset_dir, "sfx_whoosh.wav"),
        "whoosh_out": os.path.join(asset_dir, "sfx_whoosh_out.wav"),
        "impact": os.path.join(asset_dir, "sfx_impact.wav"),
        "cheer": os.path.join(asset_dir, "sfx_cheer.wav"),
    }
    if all(os.path.exists(p) and os.path.getsize(p) > 1000 for p in bank.values()):
        return bank
    rng = np.random.default_rng(7)
    t = np.linspace(0, 0.45, int(SR * 0.45), endpoint=False)
    noise = np.convolve(rng.standard_normal(t.size), np.ones(80) / 80, "same")
    # whoosh (IN / đầu beat): ĐỈNH ở t=0 rồi tắt — phủ MÉP SAU vết cắt (cảnh tới vừa mở ra).
    _wwav(bank["whoosh"], noise * np.exp(-t * 8) * np.minimum(1, t * 40) * 0.18)
    # whoosh_out (OUT / đuôi beat): SWELL lên ĐỈNH ở CUỐI (t→0.45) — đỉnh TRÙNG vết cắt, phủ MÉP TRƯỚC.
    # Sửa lỗi audit: cũ dùng đúng envelope decay cho đuôi → đỉnh rơi 0.45s TRƯỚC seam, tới seam đã im.
    _wwav(bank["whoosh_out"], noise * np.exp(-(t[-1] - t) * 8) * 0.20)
    # impact: sub-boom 60Hz decay
    t3 = np.linspace(0, 0.6, int(SR * 0.6), endpoint=False)
    _wwav(bank["impact"], np.sin(2 * np.pi * 60 * t3) * np.exp(-t3 * 6) * 0.28)
    # cheer: đám đông reo (noise mượt + envelope swell)
    t2 = np.linspace(0, 1.6, int(SR * 1.6), endpoint=False)
    env = np.minimum(1, t2 * 3) * np.exp(-np.maximum(0, t2 - 0.7) * 2.2)
    _wwav(bank["cheer"], np.convolve(rng.standard_normal(t2.size), np.ones(260) / 260, "same") * env * 0.16)
    return bank


def synth_atmos_bed(duration: float, context: str, out_path: str) -> str:
    """Atmos bed tự synth: ambience đám đông rì rào + drone hợp âm theo context. RẤT khẽ (làm nền).

    Cache theo (context, duration làm tròn). Đây là fallback khi không có nhạc thật — chủ ý SUBTLE
    để không lộ chất 'synth'; ducking + loudnorm sẽ dìm thêm dưới giọng.
    """
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    n = max(1, int(SR * duration))
    t = np.linspace(0, duration, n, endpoint=False)
    rng = np.random.default_rng(abs(hash((context, round(duration, 1)))) % (2**32))
    # ambience: noise mượt thành tiếng rì rào (không phải hiss)
    amb = np.convolve(rng.standard_normal(n), np.ones(500) / 500, "same")
    amb = amb / (np.max(np.abs(amb)) + 1e-6) * 0.07
    # drone hợp âm theo context, tremolo chậm + fade in/out mép
    freqs = _MOOD_FREQS.get(context, _MOOD_FREQS["normal"])
    drone = sum(np.sin(2 * np.pi * f * t) for f in freqs) / len(freqs)
    trem = 0.85 + 0.15 * np.sin(2 * np.pi * 0.13 * t)
    edge = np.minimum(np.minimum(1.0, t / 0.8), np.minimum(1.0, (duration - t) / 0.8))
    drone = drone * trem * edge * 0.05
    bed = amb + drone
    if context == "joke":
        bed *= 0.45  # joke: bed lùi để nhường nhịp hài
    _wwav(out_path, np.clip(bed, -1, 1))
    return out_path


# context beat → từ khoá MOOD trong TÊN FILE nhạc (đặt tên track có 1 trong các từ này để khớp cảm xúc).
_MOOD_KW = {
    "hype": ("hype", "upbeat", "epic", "energetic", "energy"),
    "climax": ("epic", "hype", "intense", "climax", "triumph"),
    "drama": ("drama", "tense", "dark", "suspense", "dramatic"),
    "whisper": ("calm", "soft", "ambient", "chill"),
    "joke": ("comedy", "fun", "quirky", "happy", "playful"),
    "normal": ("neutral", "chill", "light", "groove"),
}


def pick_music(duration: float, context: str, asset_dir: str, *, hint: str = "") -> str:
    """Track nhạc nền THẬT trong BG_MUSIC_DIR, ưu tiên track KHỚP MOOD theo tên file (vd 'epic_*.mp3'
    cho beat climax). KHÔNG có nhạc thật → trả "" (GIỌNG SẠCH).

    Quyết định 2026-06-19: KHÔNG synth "atmos drone" giả (nghe ù ù, kéo chất xuống). Thả file nhạc
    CC0/commercial-free vào BG_MUSIC_DIR (đặt tên có từ mood: hype/epic/drama/comedy/calm/chill...) là
    tự dùng + khớp cảm xúc beat. Nguồn sạch cho kênh kiếm tiền: Pixabay Music, YouTube Audio Library."""
    music_dir = (settings.bg_music_dir or "").strip()
    if not (music_dir and os.path.isdir(music_dir)):
        return ""
    tracks = sorted(f for f in os.listdir(music_dir) if f.lower().endswith(_MUSIC_EXTS))
    if not tracks:
        return ""
    kws = _MOOD_KW.get((context or "normal").strip().lower(), _MOOD_KW["normal"])
    pool = [t for t in tracks if any(k in t.lower() for k in kws)] or tracks   # khớp mood, không thì mọi track
    idx = sum(ord(c) for c in (hint or context)) % len(pool)
    return os.path.join(music_dir, pool[idx])


def foley_events(narration_text: str, duration: float, context: str, sfx_bank: dict[str, str],
                 *, beat_id: int = 0) -> list[tuple[str, float]]:
    """Quét từ khoá → [(sfx_path, start_s)]. Swish CHÉO vết cắt: whoosh_out SWELL đỉnh-trùng-seam ở
    ĐUÔI beat (che mép trước) + whoosh IN decay-từ-đỉnh ở ĐẦU beat (che mép sau) — cộng lại thành 1
    tiếng "vút" liền mạch qua hard-cut concat. Beat đầu (id=0) không có cảnh trước → bỏ whoosh đầu.
    cheer/impact ở mốc bàn thắng/cao trào."""
    events: list[tuple[str, float]] = [(sfx_bank["whoosh_out"], max(0.0, duration - 0.45))]
    if beat_id > 0:
        events.append((sfx_bank["whoosh"], 0.0))
    low = (narration_text or "").lower()
    goal_kw = ("ghi bàn", "nổ súng", "hat-trick", "hat trick", "bàn thắng", "sút tung", "đệm cận", "cú sút", "cú cuộn")
    if context in {"climax"} or any(k in low for k in goal_kw):
        # đặt cheer + impact quanh 55% beat (lúc cao trào kể bàn thắng)
        at = round(duration * 0.55, 2)
        events.append((sfx_bank["impact"], at))
        events.append((sfx_bank["cheer"], at + 0.05))
    return events


def mix_beat_audio(
    voice_wav: str,
    duration: float,
    out_wav: str,
    *,
    context: str = "normal",
    music_path: str = "",
    sfx_events: list[tuple[str, float]] | None = None,
    music_volume: float = 0.55,
    sfx_volume: float = 0.5,
) -> str:
    """Mix voice + nhạc (ducked) + foley → out_wav 48k mono, loudnorm -16. ffmpeg filtergraph."""
    sfx_events = sfx_events or []
    inputs: list[str] = ["-i", voice_wav]
    parts: list[str] = []
    mix_labels: list[str] = ["[0:a]"]

    next_idx = 1
    # context=joke → TẮT HẲN nhạc nền (kể cả track thật) để SFX hài + khoảng lặng "đập" (plan "mute on joke").
    if music_path and os.path.exists(music_path) and context != "joke":
        inputs += ["-i", music_path]
        mi = next_idx
        next_idx += 1
        # nhạc: cắt đúng dur, hạ volume, rồi sidechaincompress theo giọng (né giọng).
        parts.append(
            f"[{mi}:a]atrim=0:{duration:.3f},asetpts=PTS-STARTPTS,volume={music_volume}[mus]"
        )
        parts.append(
            "[mus][0:a]sidechaincompress=threshold=0.04:ratio=8:attack=20:release=300[musd]"
        )
        mix_labels.append("[musd]")

    for k, (sfx_path, start) in enumerate(sfx_events):
        if not sfx_path or not os.path.exists(sfx_path):
            continue
        inputs += ["-i", sfx_path]
        si = next_idx
        next_idx += 1
        ms = max(0, int(start * 1000))
        parts.append(f"[{si}:a]adelay={ms}|{ms},volume={sfx_volume}[s{k}]")
        mix_labels.append(f"[s{k}]")

    mixn = len(mix_labels)
    tail = (
        "".join(mix_labels)
        + f"amix=inputs={mixn}:duration=first:normalize=0,"
        + "alimiter=limit=0.95,loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000,aformat=channel_layouts=mono[out]"
    )
    filtergraph = ";".join(parts + [tail]) if parts else tail
    cmd = ["ffmpeg", "-y", "-loglevel", "error", *inputs,
           "-filter_complex", filtergraph, "-map", "[out]",
           "-ar", str(SR), "-ac", "1", "-c:a", "pcm_s16le", out_wav]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if proc.returncode != 0:
        logger.warning(f"[audio] mix lỗi ({proc.stderr[:200]}) → fallback voice trần.")
        # fail-soft: chỉ loudnorm voice (không nhạc) để beat vẫn có tiếng.
        fb = subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", voice_wav,
             "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", str(SR), "-ac", "1",
             "-c:a", "pcm_s16le", out_wav],
            capture_output=True, text=True, timeout=180,
        )
        if fb.returncode != 0:
            raise RuntimeError(f"[audio] mix + fallback đều lỗi: {fb.stderr[:200]}")
    return out_wav
