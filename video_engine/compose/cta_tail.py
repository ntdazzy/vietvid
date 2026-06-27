"""Đuôi CTA local (V8.3-Q3) — ảnh SP THẬT → clip tĩnh động nhẹ + tên/GIÁ/MUA NGAY, $0.

Trick chống giật zoompan: upscale 4x TRƯỚC rồi ``s=`` về ĐÚNG resolution clip chính
(không phải 1080p cứng). Audio anullsrc câm — đủ track cho bước ghép xfade.
Chữ vẽ bằng drawtext local (reuse overlays.py — font vector, đủ dấu).
"""

from __future__ import annotations

import json
import os
import subprocess

from video_engine.compose.overlays import build_drawtext_filters, cleanup_overlay_files
from video_engine.providers.base import VideoEngineError


def probe_video_specs(path: str) -> tuple[float, int, int, float]:
    """(duration, width, height, fps) của clip — tail build khớp 100% clip chính."""
    proc = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height,r_frame_rate:format=duration",
            "-of",
            "json",
            path,
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if proc.returncode != 0:
        raise VideoEngineError(f"ffprobe specs lỗi: {proc.stderr[:200]}")
    data = json.loads(proc.stdout)
    stream = (data.get("streams") or [{}])[0]
    num, _, den = (stream.get("r_frame_rate") or "30/1").partition("/")
    fps = float(num) / float(den or 1)
    return (
        float((data.get("format") or {}).get("duration") or 0.0),
        int(stream.get("width") or 0),
        int(stream.get("height") or 0),
        fps,
    )


def build_cta_tail(
    *,
    product_image: str,
    price_text: str,
    short_name: str,
    seconds: int,
    width: int,
    height: int,
    fps: float,
    out_path: str,
) -> str:
    """Render tail.mp4 CÙNG w/h/fps/pixfmt clip chính. Trả out_path."""
    if not os.path.exists(product_image):
        raise VideoEngineError(f"Thiếu ảnh sản phẩm cho CTA tail: {product_image}")
    workdir = os.path.dirname(out_path) or "."
    os.makedirs(workdir, exist_ok=True)
    frames = max(1, int(round(seconds * fps)))
    big_w, big_h = width * 4, height * 4
    # Layout dọc: tên (trắng, ~62%) → giá (vàng to, ~70%) → MUA NGAY (~82%).
    overlays = [
        {"t": 0, "dur": seconds, "text": short_name[:42], "pos": "0.60", "kind": "hook"},
        {"t": 0, "dur": seconds, "text": price_text, "pos": "0.70", "kind": "price"},
        {"t": 0.2, "dur": seconds, "text": "MUA NGAY", "pos": "0.82", "kind": "cta"},
    ]
    try:
        drawtexts = ",".join(build_drawtext_filters(overlays, workdir))
        filter_complex = (
            f"[0:v]scale={big_w}:{big_h}:force_original_aspect_ratio=increase,"
            f"crop={big_w}:{big_h},"
            f"zoompan=z='min(zoom+0.0003,1.06)':d={frames}"
            f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={width}x{height}:fps={fps:.6g},"
            f"gblur=sigma=12[bg];"
            f"[0:v]scale={int(width * 0.72)}:-2[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2-40,format=yuv420p,{drawtexts}[v]"
        )
        cmd = [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-i",
            product_image,
            "-f",
            "lavfi",
            "-t",
            str(seconds),
            "-i",
            "anullsrc=r=48000:cl=mono",
            "-filter_complex",
            filter_complex,
            "-map",
            "[v]",
            "-map",
            "1:a",
            "-t",
            str(seconds),
            *video_codec_args(),
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            "48000",
            out_path,
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if proc.returncode != 0 or not os.path.exists(out_path):
            raise VideoEngineError(f"FFmpeg CTA tail lỗi: {proc.stderr[:300]}")
    finally:
        cleanup_overlay_files(workdir)
    return out_path


_NVENC_AVAILABLE: bool | None = None


def video_codec_args() -> list[str]:
    """Args encode theo settings.ffmpeg_video_codec (V8.3-Q3.6) — fallback libx264.

    h264_nvenc (RTX): ``-cq 19 -preset p5`` thay ``-crf 19 -preset medium``;
    nvenc không có trong build/máy → tự rơi về libx264 (probe 1 lần, cache).
    """
    from config.settings import settings

    codec = (settings.ffmpeg_video_codec or "libx264").strip().lower()
    if codec == "h264_nvenc" and _nvenc_available():
        args = ["-c:v", "h264_nvenc", "-preset", "p5", "-cq", "19"]
    else:
        args = ["-c:v", "libx264", "-preset", "medium", "-crf", "19"]
    # 2026-06-13: ÉP yuv420p — BẮT BUỘC để phát phổ thông. xfade/overlay/drawtext có thể
    # đẩy chain lên yuvj444p (4:4:4); file 4:4:4 phát được trên web (Chromium software decode)
    # nhưng KHÔNG phát trên Windows Media Player / hardware decoder (chỉ 4:2:0). Bug "clip xem
    # web được, Windows không" (job_33/34 trước fix là yuvj444p).
    # 2026-06-13 (job 36): nguồn Seedance/JPEG là full-range → libx264 vẫn ghi yuvj420p (full).
    # Chuyển range full→limited trong filter graph (scale=...out_range=tv) + gắn metadata tv ở đây
    # → ÉP yuv420p (limited-range) chuẩn, mọi player Windows decode được, không lệch màu.
    # -g 48 (keyframe mỗi ~2s @24fps): libx264 mặc định keyint=250 (~10s) → GOP quá dài, player
    # Windows (Films&TV/Media Player) giật khi tua/decode. Ép 2s cho mượt + tua nhạy.
    # -profile:v high: TikTok/đa số player ưu tiên High (8x8 transform) → nén hiệu quả hơn,
    # NÉT hơn ở cùng CRF so với Main. yuv420p tương thích High. nvenc cũng nhận "high".
    return args + ["-profile:v", "high", "-g", "48", "-keyint_min", "48", "-pix_fmt", "yuv420p", "-color_range", "tv"]


def _nvenc_available() -> bool:
    global _NVENC_AVAILABLE
    if _NVENC_AVAILABLE is None:
        try:
            proc = subprocess.run(
                ["ffmpeg", "-hide_banner", "-encoders"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            _NVENC_AVAILABLE = "h264_nvenc" in proc.stdout
        except (OSError, subprocess.SubprocessError):
            _NVENC_AVAILABLE = False
        if not _NVENC_AVAILABLE:
            from core.logger import logger

            logger.warning("[compose] h264_nvenc không khả dụng → dùng libx264")
    return _NVENC_AVAILABLE
