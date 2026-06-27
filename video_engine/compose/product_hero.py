"""Beat 'khoe sản phẩm' (V8.6) — ảnh tĩnh SẠCH (clean-plate, pixel gốc) + Ken Burns pan/zoom,
KHÔNG qua i2v → GIỮ 100% sản phẩm. Prepend đầu video, xfade vào clip lifestyle (Seedance).

Tái dụng zoompan + codec của cta_tail (đã proven phát phổ thông). Khác CTA tail: KHÔNG vẽ
giá/MUA NGAY — chỉ khoe sản phẩm. Output video-only (voiceover thay audio ở compose); chỉ
dùng cho mode voiceover (native giữ audio Seedance → bỏ qua hero ở pipeline).
"""

from __future__ import annotations

import os
import subprocess

from core.logger import logger
from video_engine.compose.cta_tail import probe_video_specs, video_codec_args
from video_engine.providers.base import VideoEngineError

_XFADE = 0.4


def build_product_hero(
    *, clean_image: str, seconds: int, width: int, height: int, fps: float, out_path: str
) -> str:
    """Render hero.mp4 (Ken Burns ảnh sạch) CÙNG w/h/fps clip chính. Trả out_path."""
    if not os.path.exists(clean_image):
        raise VideoEngineError(f"Thiếu ảnh sạch cho product hero: {clean_image}")
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    frames = max(1, int(round(seconds * fps)))
    big_w, big_h = width * 4, height * 4
    # Nền BLUR (zoompan = Ken Burns) + sản phẩm SẠCH contained 86% ở giữa (luôn thấy trọn SP).
    filter_complex = (
        f"[0:v]scale={big_w}:{big_h}:force_original_aspect_ratio=increase,"
        f"crop={big_w}:{big_h},"
        f"zoompan=z='min(zoom+0.0006,1.10)':d={frames}"
        f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={width}x{height}:fps={fps:.6g},"
        f"gblur=sigma=14[bg];"
        f"[0:v]scale={int(width * 0.86)}:-2[fg];"
        f"[bg][fg]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]"
    )
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", clean_image,
        "-f", "lavfi", "-t", str(seconds), "-i", "anullsrc=r=48000:cl=mono",
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "1:a", "-t", str(seconds),
        *video_codec_args(),
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        out_path,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if proc.returncode != 0 or not os.path.exists(out_path):
        raise VideoEngineError(f"FFmpeg product hero lỗi: {proc.stderr[:300]}")
    return out_path


def prepend_product_hero(
    *, clip_path: str, clean_image: str, seconds: int, out_path: str
) -> str | None:
    """Dựng hero (specs theo clip) → xfade hero→clip → out_path (video-only). Fail-soft: None → caller giữ clip gốc."""
    try:
        _dur, width, height, fps = probe_video_specs(clip_path)
        workdir = os.path.dirname(out_path) or "."
        hero_path = os.path.join(workdir, "hero.mp4")
        build_product_hero(
            clean_image=clean_image, seconds=seconds,
            width=width, height=height, fps=fps, out_path=hero_path,
        )
        offset = max(0.0, seconds - _XFADE)
        # hero(0) →xfade→ clip(1). Output video-only: voiceover thay audio ở compose_final.
        # settb=AVTB CHUẨN HOÁ timebase 2 input TRƯỚC xfade — hero (lavfi 1/1000000) vs clip Seedance
        # (1/12288) lệch timebase thì xfade "do not match" → fail. full→limited range để yuv420p.
        filter_complex = (
            f"[0:v]settb=AVTB[h];[1:v]settb=AVTB[c];"
            f"[h][c]xfade=transition=fade:duration={_XFADE}:offset={offset:.3f},"
            "scale=in_range=pc:out_range=tv[v]"
        )
        cmd = [
            "ffmpeg", "-y", "-loglevel", "error",
            "-i", hero_path, "-i", clip_path,
            "-filter_complex", filter_complex,
            "-map", "[v]",
            *video_codec_args(),
            "-an", out_path,
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if proc.returncode != 0 or not os.path.exists(out_path):
            logger.warning(f"[product-hero] xfade lỗi → bỏ hero (clip gốc): {proc.stderr[:250]}")
            return None
        try:
            os.remove(hero_path)
        except OSError:
            pass
        return out_path
    except (VideoEngineError, OSError, subprocess.SubprocessError) as exc:
        logger.warning(f"[product-hero] dựng hero lỗi → bỏ hero (clip gốc): {str(exc)[:200]}")
        return None
