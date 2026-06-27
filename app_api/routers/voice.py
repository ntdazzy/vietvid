"""Nghe thử giọng Việt (wedge). Synthesize 1 câu ngắn bằng edge-tts → trả audio.

Dùng CÙNG engine giọng mà video thật dùng (edge-tts khi chưa có VieNeu/Vbee) → bản nghe thử
khớp giọng đầu ra thật. Cần đăng nhập; giới hạn độ dài để tránh lạm dụng.
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

router = APIRouter(prefix="/v1/voice", tags=["voice"])

_VOICE = {"female": "vi-VN-HoaiMyNeural", "male": "vi-VN-NamMinhNeural"}
_DIR = os.path.join(tempfile.gettempdir(), "vietvid_voice")


class PreviewReq(BaseModel):
    text: str = Field(min_length=1, max_length=200)
    gender: str = "female"


@router.post("/preview")
async def voice_preview(req: PreviewReq, _: Principal = Depends(get_principal)) -> FileResponse:
    import edge_tts

    voice = _VOICE.get(req.gender, _VOICE["female"])
    os.makedirs(_DIR, exist_ok=True)
    out = os.path.join(_DIR, f"{uuid.uuid4().hex}.mp3")
    try:
        await edge_tts.Communicate(req.text.strip(), voice).save(out)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"Tạo giọng lỗi: {exc}") from exc
    if not os.path.exists(out) or os.path.getsize(out) == 0:
        raise HTTPException(502, "Không tạo được audio")
    return FileResponse(out, media_type="audio/mpeg", filename="preview.mp3")
