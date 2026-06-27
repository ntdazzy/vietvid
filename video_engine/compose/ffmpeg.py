"""Wrapper FFmpeg tối giản: dò thời lượng media (ffprobe).

Lịch sử: file này từng chứa `FFmpegProcessor` với nhiều method dựng/ghép video
(image_to_video, build, concat_*, mux_audio, clip_from_broll, silent_audio…) cho
per-scene composer (P2) + lớp Variation A/B. Toàn bộ đã bị thay bằng
``video_engine/compose/__init__.py::compose_final`` và được gỡ (legacy, không còn
caller). Chỉ ``probe_duration`` còn dùng (voice/tts để dò độ dài audio).
"""

from __future__ import annotations

import json
import subprocess

from core.exceptions import RenderError


class FFmpegProcessor:
    """Tiện ích ffprobe — chỉ còn ``probe_duration`` (gọi static, không cần khởi tạo)."""

    @staticmethod
    def probe_duration(path: str) -> float:
        out = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", path],
            capture_output=True,
            text=True,
        )
        if out.returncode != 0:
            raise RenderError(f"ffprobe lỗi: {out.stderr[-400:]}")
        return float(json.loads(out.stdout)["format"]["duration"])
