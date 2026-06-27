"""film_recap/compose_recap.py — dựng video review (9:16 hoặc 16:9, chất lượng cao).

reupload (single-pass): clip nguồn → khung aspect (blur-pad lanczos) → burn caption ASS (font Be
Vietnam Pro đủ dấu) → GIỮ audio gốc (-c:a copy). KHÔNG chia beat (tránh drift).
recap: mỗi (clip minh hoạ aspect CÂM ↔ giọng MỚI) → _mux_voice → concat_beats. KHÔNG dùng compose_final
(nó ép cứng 9:16) → tự mux để hỗ trợ 16:9.

Chất lượng (cả 2 mode): scale lanczos + unsharp nhẹ + H.264 High profile + faststart + AAC 160k.
"""
from __future__ import annotations

import os
import subprocess

from core.exceptions import RenderError
from core.logger import logger
from video_engine.compose.ffmpeg import FFmpegProcessor
from video_engine.compose.overlays import ass_filter, cleanup_overlay_files

_DIMS = {"9:16": (1080, 1920), "16:9": (1920, 1080)}
_CAP_CHARS = 38          # ngắt câu caption ~38 ký tự (≤ vừa 2 dòng)
_CAP_MAX_DUR = 4.0       # caption hiện TỐI ĐA 4s (chống ASR thưa tạo caption dài + chồng)
# Chữ ký hallucination Whisper-vi (cụm outro hay bịa trên đoạn nhạc/im lặng) → bỏ caption chứa nó.
# Đây là các cụm gần như KHÔNG có trong lời phim/clip gốc; nếu nguồn là creator có outro "đăng ký
# kênh" thì cũng là phần nên cắt khi recap. Bổ trợ cho lọc no_speech_prob ở understand.clean_words.
_HALLU_SIGS = (
    "ghiền mì gõ", "ghien mi go", "subscribe", "đăng ký kênh", "like và đăng ký", "đừng quên like",
    "không bỏ lỡ những video", "cảm ơn các bạn đã theo dõi", "cảm ơn đã theo dõi",
    "nhấn chuông", "hẹn gặp lại các bạn",
)


def _is_hallu(text: str) -> bool:
    t = text.lower()
    return any(sig in t for sig in _HALLU_SIGS)


def _dims(aspect: str) -> tuple[int, int]:
    return _DIMS.get((aspect or "9:16").strip(), _DIMS["9:16"])


def _safe_duration(path: str) -> float:
    try:
        return FFmpegProcessor.probe_duration(path)
    except Exception:  # noqa: BLE001 — probe hỏng không nên làm fail cả job
        return 0.0


def _frame_clip(src_path: str, out_path: str, *, aspect: str, max_seconds: float,
                keep_audio: bool) -> str | None:
    """Đưa clip về khung aspect chất lượng cao: scale lanczos + blur-pad + unsharp nhẹ + H.264 High.

    keep_audio=False (recap) → bỏ audio. Lấy ~max_seconds đầu. Fail-soft → None.
    """
    if not os.path.exists(src_path):
        return None
    w, h = _dims(aspect)
    vf = (
        f"[0:v]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},gblur=sigma=24[bg];"
        f"[0:v]scale={w}:{h}:force_original_aspect_ratio=decrease:flags=lanczos,"
        f"unsharp=5:5:0.5:5:5:0.0[fg];"
        f"[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1[v]"
    )
    audio = ["-an"] if not keep_audio else ["-map", "0:a?", "-c:a", "aac", "-b:a", "160k", "-ar", "48000"]
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error", "-t", f"{max_seconds:.1f}", "-i", src_path,
        "-filter_complex", vf, "-map", "[v]", *audio,
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-profile:v", "high", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out_path,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    if proc.returncode != 0 or not os.path.exists(out_path):
        logger.warning(f"[film_recap] frame_clip ({aspect}) lỗi: {proc.stderr[-200:]}")
        return None
    return out_path


def _mux_voice(video_path: str, voice_path: str, out_path: str) -> str:
    """Mux clip (đã đúng khung+chất lượng, câm) + giọng MỚI: loudnorm giọng, freeze frame cuối nếu
    video ngắn hơn giọng (tpad), độ dài = giọng. KHÔNG ép khung → giữ aspect của clip vào."""
    vdur, adur = _safe_duration(video_path), _safe_duration(voice_path)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", video_path, "-i", voice_path]
    if adur > vdur + 0.1:  # giọng dài hơn video → freeze frame cuối cho đủ (re-encode)
        cmd += ["-vf", f"tpad=stop_mode=clone:stop_duration={adur - vdur + 0.1:.2f}",
                "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-profile:v", "high", "-pix_fmt", "yuv420p"]
    else:
        cmd += ["-c:v", "copy"]
    cmd += ["-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "160k", "-ar", "48000",
            "-map", "0:v:0", "-map", "1:a:0", "-shortest", "-movflags", "+faststart", out_path]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if proc.returncode != 0 or not os.path.exists(out_path):
        raise RenderError(f"film_recap recap mux lỗi: {proc.stderr[-220:]}")
    return out_path


def _words_to_overlays(words: list[dict], *, max_seconds: float) -> list[dict]:
    """Gom word-timings (Groq: {word,start,end}) thành câu caption → overlay dict cho ass_filter.

    Mỗi khối {text, t, dur, pos}. pos=0.80 (đáy khung). Ngắt khi đủ dài hoặc gặp dấu kết câu.
    """
    overlays: list[dict] = []
    cur: list[str] = []
    cur_start: float | None = None
    cur_chars = 0
    for w in words:
        word = str(w.get("word") or "").strip()
        if not word:
            continue
        start = float(w.get("start") or 0.0)
        end = float(w.get("end") or start)
        if start >= max_seconds:
            break
        if cur_start is None:
            cur_start = start
        cur.append(word)
        cur_chars += len(word) + 1
        if cur_chars >= _CAP_CHARS or word.endswith((".", "!", "?", "…")):
            _txt = " ".join(cur).strip(" ,")
            if _txt and not _is_hallu(_txt):   # bỏ caption chữ-ký-hallucination
                overlays.append({
                    "text": _txt,
                    "t": round(cur_start, 2),
                    "dur": round(min(_CAP_MAX_DUR, max(0.8, end - cur_start)), 2),
                    "pos": 0.80,
                })
            cur, cur_start, cur_chars = [], None, 0
    if cur and cur_start is not None:
        _txt = " ".join(cur).strip(" ,")
        if _txt and not _is_hallu(_txt):
            last_end = min(float(words[-1].get("end") or cur_start + 1.0), max_seconds)
            overlays.append({
                "text": _txt,
                "t": round(cur_start, 2),
                "dur": round(min(_CAP_MAX_DUR, max(0.8, last_end - cur_start)), 2),
                "pos": 0.80,
            })
    return overlays


def compose_reupload(src_path: str, words: list[dict], out_path: str, *,
                     max_seconds: float, aspect: str = "9:16") -> dict:
    """Single-pass reupload: khung aspect + caption ASS + giữ audio gốc. Trả {path, duration}."""
    if not os.path.exists(src_path):
        raise RenderError(f"film_recap: clip nguồn không tồn tại: {src_path}")
    w, h = _dims(aspect)
    work = os.path.dirname(out_path) or "."
    os.makedirs(work, exist_ok=True)

    framed = os.path.join(work, "framed.mp4")
    if _frame_clip(src_path, framed, aspect=aspect, max_seconds=float(max_seconds), keep_audio=True) is None:
        raise RenderError(f"film_recap: dựng khung {aspect} thất bại.")
    try:
        overlays = _words_to_overlays(words or [], max_seconds=float(max_seconds))
        vf = ass_filter(overlays, work, w, h)
        if not vf:
            os.replace(framed, out_path)  # không caption: bản framed CHÍNH là output
            dur = _safe_duration(out_path)
            logger.info(f"[film_recap] reupload {aspect} (no caption) → {out_path} ~{dur:.1f}s")
            return {"path": out_path, "duration": dur}
        # burn caption. -c:a copy: KHÔNG nén audio lần 2 (đã AAC ở _frame_clip) → khỏi drift.
        cmd = [
            "ffmpeg", "-y", "-loglevel", "error", "-i", framed,
            "-vf", ",".join(vf), "-c:v", "libx264", "-preset", "medium",
            "-crf", "18", "-profile:v", "high", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart", "-c:a", "copy", out_path,
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
        if proc.returncode != 0:
            raise RenderError(f"film_recap: burn caption lỗi: {proc.stderr[-300:]}")
        dur = _safe_duration(out_path)
        logger.info(f"[film_recap] reupload {aspect} → {out_path} ~{dur:.1f}s · {len(overlays)} caption")
        return {"path": out_path, "duration": dur}
    finally:
        cleanup_overlay_files(work)
        try:
            if os.path.exists(framed):
                os.remove(framed)
        except OSError:  # noqa: BLE001 — best-effort cleanup
            pass


def compose_recap_mode(src_path, segments, voices, out_path, *, max_seconds, aspect: str = "9:16") -> dict:
    """recap: mỗi (clip minh hoạ aspect CÂM ↔ giọng beat MỚI) → _mux_voice → concat_beats.

    segments: [(start,end)] cắt từ nguồn; voices: [wav giọng mới] CÙNG độ dài. clip dài = giọng
    (dùng start cảnh) → khỏi freeze. Trả {path, duration}.
    """
    from video_engine.film_recap.scene_select import cut_segment
    from video_engine.long_narrative.render import concat_beats

    if not segments or not voices or len(segments) != len(voices):
        raise RenderError("film_recap recap: segments/voices rỗng hoặc không khớp độ dài.")
    work = os.path.dirname(out_path) or "."
    os.makedirs(work, exist_ok=True)
    beat_mp4s: list[str] = []
    used = 0.0
    try:
        for i, ((start, _end), voice_wav) in enumerate(zip(segments, voices)):
            if not os.path.exists(voice_wav):
                continue
            voice_dur = _safe_duration(voice_wav)
            if voice_dur <= 0.1:
                continue
            clip_len = voice_dur + 0.3   # clip dài = giọng → KHÔNG freeze; start cảnh = điểm bắt đầu
            if beat_mp4s and used + clip_len > float(max_seconds):  # cap từ beat 2 (LUÔN dựng beat đầu)
                break
            raw_clip = os.path.join(work, f"seg_{i}.mp4")
            if cut_segment(src_path, float(start), clip_len, raw_clip) is None:
                continue
            framed = os.path.join(work, f"framed_{i}.mp4")
            if _frame_clip(raw_clip, framed, aspect=aspect, max_seconds=clip_len + 0.5, keep_audio=False) is None:
                continue
            beat_mp4 = os.path.join(work, f"beat_{i}.mp4")
            _mux_voice(framed, voice_wav, beat_mp4)
            beat_mp4s.append(beat_mp4)
            used += clip_len
        if not beat_mp4s:
            raise RenderError("film_recap recap: không dựng được beat nào (cut/mux lỗi).")
        concat_beats(beat_mp4s, out_path)
        dur = _safe_duration(out_path)
        logger.info(f"[film_recap] recap {aspect} → {out_path} ~{dur:.1f}s · {len(beat_mp4s)} beat")
        return {"path": out_path, "duration": dur}
    finally:
        for name in os.listdir(work):  # dọn clip trung gian (giữ final.mp4 + voice_*.wav)
            if name.endswith(".mp4") and name.startswith(("seg_", "framed_", "beat_")):
                try:
                    os.remove(os.path.join(work, name))
                except OSError:  # noqa: BLE001 — best-effort
                    pass
