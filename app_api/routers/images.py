"""Tạo ảnh AI (text → image) qua engine image provider (Gemini khi IMAGE_PROVIDER=gemini).

Cần đăng nhập; giới hạn độ dài prompt. Trả file PNG.
"""

from __future__ import annotations

import os
import tempfile
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app_api.auth import Principal
from app_api.deps import get_principal

router = APIRouter(prefix="/v1/images", tags=["images"])
_DIR = os.path.join(tempfile.gettempdir(), "vietvid_images")


class GenReq(BaseModel):
    prompt: str = Field(min_length=3, max_length=500)
    aspect: str | None = None  # "9:16" | "16:9" | ... (tùy chọn)


@router.post("/generate")
def generate_image(req: GenReq, _: Principal = Depends(get_principal)) -> FileResponse:
    from video_engine.image_stage import build_image_provider

    os.makedirs(_DIR, exist_ok=True)
    out = os.path.join(_DIR, f"{uuid.uuid4().hex}.png")
    try:
        provider = build_image_provider()
        result = provider.generate(prompt=req.prompt, out_path=out, aspect_ratio=req.aspect)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"Tạo ảnh lỗi: {str(exc)[:300]}") from exc
    if not result or not os.path.exists(out) or os.path.getsize(out) == 0:
        raise HTTPException(502, "Không tạo được ảnh (kiểm tra IMAGE_PROVIDER/GEMINI key)")
    # X-Image-Path: đường dẫn server để dùng làm khung video (text→video). Như /uploads trả image_path.
    return FileResponse(
        out, media_type="image/png", filename="vietvid-image.png",
        headers={"X-Image-Path": out},
    )
