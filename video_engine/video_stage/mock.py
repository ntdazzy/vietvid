"""Mock video provider — FFmpeg sinh clip placeholder (zoompan ảnh hoặc nền màu).

Dùng để test pipeline end-to-end không tốn tiền (USE_FAKE_CLIENTS / VIDEO_PROVIDER=mock).
"""

from __future__ import annotations

import os
import shutil
import subprocess

from core.logger import logger
from video_engine.providers.base import VideoEngineError

_RES = {"480p": (480, 854), "720p": (720, 1280), "1080p": (1080, 1920)}


class MockVideoProvider:
    name = "mock"

    def generate(
        self,
        *,
        prompt: str,
        out_path: str,
        seconds: int,
        aspect: str,
        resolution: str,
        model_id: str,
        image_paths: list[str] | None = None,
        **_ignored,  # on_created/resume_task_id — chỉ provider thật cần
    ) -> str:
        if shutil.which("ffmpeg") is None:
            raise VideoEngineError("Mock video cần ffmpeg trong PATH.")
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        width, height = _RES.get(resolution, (720, 1280))
        duration = max(4, min(15, int(seconds)))
        image = next((p for p in (image_paths or []) if p and os.path.exists(p)), None)
        if image:
            # zoompan nhẹ trên ảnh thật để có chuyển động kiểm tra compose/QA
            vf = (
                f"scale={width * 2}:{height * 2}:force_original_aspect_ratio=increase,"
                f"crop={width * 2}:{height * 2},"
                f"zoompan=z='min(zoom+0.0015,1.2)':d={duration * 25}:s={width}x{height},"
                f"fps=25"
            )
            cmd = [
                "ffmpeg", "-y", "-loglevel", "error",
                "-loop", "1", "-i", image,
                "-t", str(duration), "-vf", vf,
                "-pix_fmt", "yuv420p", "-an", out_path,
            ]
        else:
            cmd = [
                "ffmpeg", "-y", "-loglevel", "error",
                "-f", "lavfi",
                "-i", f"color=c=0x182030:s={width}x{height}:d={duration}",
                "-pix_fmt", "yuv420p", "-an", out_path,
            ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if proc.returncode != 0 or not os.path.exists(out_path):
            raise VideoEngineError(f"Mock ffmpeg lỗi: {proc.stderr[:300]}")
        logger.info(f"[video-stage] mock clip {duration}s {resolution} → {out_path}")
        return out_path
