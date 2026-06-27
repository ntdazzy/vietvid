"""film_recap/scene_select.py — chọn cảnh minh hoạ từ clip nguồn.

B1: chia-đều theo timeline (even_segments) + cắt clip CÂM (cut_segment — vứt audio nguồn vì recap
dùng GIỌNG MỚI). B2 (scene-detect thông minh, cần scenedetect[opencv]) thêm sau khi /real-qa B1.
"""
from __future__ import annotations

import os
import subprocess

from core.logger import logger
from video_engine.compose.ffmpeg import FFmpegProcessor


def even_segments(src_path: str, n: int) -> list[tuple[float, float]]:
    """probe_duration(src) → chia đều thành n đoạn [(start,end)]. [] nếu không đo được thời lượng."""
    n = max(1, int(n))
    try:
        dur = FFmpegProcessor.probe_duration(src_path)
    except Exception:  # noqa: BLE001
        dur = 0.0
    if dur <= 0:
        return []
    seg = dur / n
    return [(round(i * seg, 2), round((i + 1) * seg, 2)) for i in range(n)]


def cut_segment(src_path: str, start: float, dur: float, out_path: str) -> str | None:
    """ffmpeg cắt clip CÂM (-an bỏ audio nguồn), re-encode (mốc chính xác, đầu không đen). Fail-soft → None."""
    if dur <= 0.05:
        return None
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error", "-ss", f"{max(0.0, start):.2f}",
        "-i", src_path, "-t", f"{dur:.2f}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
        "-an", out_path,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if proc.returncode != 0 or not os.path.exists(out_path):
        logger.warning(f"[film_recap] cut_segment lỗi: {proc.stderr[-200:]}")
        return None
    return out_path


# ── B2: chọn cảnh hay bằng PySceneDetect (fail-soft về even_segments) ──
def detect_scenes(src_path: str) -> list[tuple[float, float]]:
    """PySceneDetect AdaptiveDetector → [(start_s, end_s)]. Fail-soft → [] (caller chia đều)."""
    try:
        from scenedetect import AdaptiveDetector, detect
        scenes = detect(src_path, AdaptiveDetector())
    except Exception as exc:  # noqa: BLE001 — lib/opencv lỗi → fallback chia đều
        logger.warning(f"[film_recap] scene-detect lỗi, dùng chia đều: {str(exc)[:140]}")
        return []
    out: list[tuple[float, float]] = []
    for s, e in scenes:
        try:
            out.append((float(s.get_seconds()), float(e.get_seconds())))
        except Exception:  # noqa: BLE001
            pass
    return out


def _score_scene(start: float, end: float, total: float) -> float:
    """Heuristic RẺ (không LLM): độ dài gần 3s = tốt; phạt cảnh ở intro/outro."""
    d = end - start
    mid = (start + end) / 2 / max(total, 1.0)
    len_fit = -abs(d - 3.0)
    pos_pen = 0.0 if 0.1 <= mid <= 0.9 else -2.0   # né 10% đầu/cuối (intro/credit)
    return len_fit + pos_pen


def rank_scenes(scenes: list[tuple[float, float]], src_path: str, *, want: int,
                min_len: float = 1.2, max_len: float = 8.0) -> list[tuple[float, float]]:
    """Lọc cảnh theo độ dài → chấm điểm → lấy top `want` → SẮP theo thời gian.

    Thiếu cảnh hay (< want) hoặc detect rỗng → fallback chia đều cho đủ count.
    """
    want = max(1, int(want))
    good = [(s, e) for (s, e) in scenes if min_len <= (e - s) <= max_len]
    if len(good) < want:
        return even_segments(src_path, want)
    total = scenes[-1][1] if scenes else 0.0
    top = sorted(good, key=lambda se: _score_scene(se[0], se[1], total), reverse=True)[:want]
    return sorted(top, key=lambda se: se[0])
