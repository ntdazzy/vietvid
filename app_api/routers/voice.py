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

from app_api import voices
from app_api.auth import Principal
from app_api.deps import get_principal

router = APIRouter(prefix="/v1/voice", tags=["voice"])

_DIR = os.path.join(tempfile.gettempdir(), "vietvid_voice")


@router.get("/personas")
async def list_personas(_: Principal = Depends(get_principal)) -> list[dict]:
    return voices.VOICE_PERSONAS


class PreviewReq(BaseModel):
    text: str = Field(min_length=1, max_length=200)
    gender: str = "female"
    persona: str = ""


@router.post("/preview")
async def voice_preview(req: PreviewReq, _: Principal = Depends(get_principal)) -> FileResponse:
    import edge_tts

    voice, rate, pitch = voices.resolve(req.persona, req.gender)
    os.makedirs(_DIR, exist_ok=True)
    out = os.path.join(_DIR, f"{uuid.uuid4().hex}.mp3")
    try:
        await edge_tts.Communicate(req.text.strip(), voice, rate=rate, pitch=pitch).save(out)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"Tạo giọng lỗi: {exc}") from exc
    if not os.path.exists(out) or os.path.getsize(out) == 0:
        raise HTTPException(502, "Không tạo được audio")
    return FileResponse(out, media_type="audio/mpeg", filename="preview.mp3")
