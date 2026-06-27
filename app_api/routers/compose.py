"""Ghép nhiều ảnh thành 1 video slideshow (ffmpeg). Composite nhiều nguồn.

Chỉ nhận image_path nằm TRONG thư mục upload/images của VietVid (chống path-traversal/LFI).
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app_api.auth import Principal
from app_api.deps import get_principal

router = APIRouter(prefix="/v1/compose", tags=["compose"])

_TMP = tempfile.gettempdir()
_OUT_DIR = os.path.join(_TMP, "vietvid_compose")
_ALLOWED = (os.path.join(_TMP, "vietvid_uploads"), os.path.join(_TMP, "vietvid_images"))


class ComposeReq(BaseModel):
    image_paths: list[str] = Field(min_length=2, max_length=8)
    seconds_per: float = 3.0


def _safe(p: str) -> str:
    ap = os.path.abspath(p)
    if not any(ap.startswith(os.path.abspath(d) + os.sep) for d in _ALLOWED):
        raise HTTPException(400, "Ảnh không hợp lệ (ngoài thư mục cho phép)")
    if not os.path.exists(ap):
        raise HTTPException(400, "Ảnh không tồn tại")
    return ap


@router.post("")
def compose(req: ComposeReq, _: Principal = Depends(get_principal)) -> FileResponse:
    paths = [_safe(p) for p in req.image_paths]
    dur = max(1.0, min(6.0, req.seconds_per))
    os.makedirs(_OUT_DIR, exist_ok=True)
    out = os.path.join(_OUT_DIR, f"{uuid.uuid4().hex}.mp4")

    args = ["ffmpeg", "-y"]
    for p in paths:
        args += ["-loop", "1", "-t", str(dur), "-i", p]
    scale = "scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:-1:-1:color=black,setsar=1,fps=30"
    parts = [f"[{i}]{scale}[v{i}]" for i in range(len(paths))]
    concat = "".join(f"[v{i}]" for i in range(len(paths))) + f"concat=n={len(paths)}:v=1:a=0[v]"
    args += ["-filter_complex", ";".join(parts) + ";" + concat,
             "-map", "[v]", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out]
    try:
        subprocess.run(args, check=True, capture_output=True, timeout=150)
    except subprocess.CalledProcessError as exc:
        raise HTTPException(502, f"Ghép video lỗi: {exc.stderr.decode('utf-8', 'ignore')[:200]}") from exc
    except subprocess.TimeoutExpired as exc:
        raise HTTPException(504, "Ghép video quá lâu") from exc
    if not os.path.exists(out) or os.path.getsize(out) == 0:
        raise HTTPException(502, "Không tạo được video")
    return FileResponse(out, media_type="video/mp4", filename="vietvid-compose.mp4")
