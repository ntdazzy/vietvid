"""Router sinh kịch bản — xem trước + sửa trước khi đốt credit render (parity Arcads/autovis).

POST /v1/script/generate: nhận thông tin sản phẩm + góc + thời lượng → trả kịch bản có cấu trúc
(hook, beats theo timecode, narration, captions, CTA). Bản template chạy ngay không cần key; khi
có key Gemini/Groq thì phủ CreativeBrief của Strategist lên (fail-soft).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app_api import claims, scriptgen
from app_api.auth import Principal
from app_api.deps import get_principal

router = APIRouter(prefix="/v1/script", tags=["script"])


class ProductIn(BaseModel):
    name: str = Field(default="", max_length=200)
    category: str = Field(default="", max_length=120)
    price: str = Field(default="", max_length=60)
    description: str = Field(default="", max_length=2000)


class GenReq(BaseModel):
    product: ProductIn
    angle: str = "problem_solution"
    seconds: int = Field(default=15, ge=6, le=60)
    voice_gender: str = "female"


@router.get("/angles")
def list_angles(_: Principal = Depends(get_principal)) -> list[dict]:
    return [{"value": k, "label": v} for k, v in scriptgen.ANGLE_LABELS.items()]


@router.post("/generate")
def generate(req: GenReq, _: Principal = Depends(get_principal)) -> dict:
    script = scriptgen.generate_script(
        product=req.product.model_dump(),
        angle=req.angle,
        seconds=req.seconds,
        voice_gender=req.voice_gender,
    )
    brief = _try_strategist(req)
    if brief is not None:
        script = scriptgen.apply_strategist(script, brief)
    script["cues"] = scriptgen.build_captions(script)
    script["claim_warnings"] = claims.scan_script(script)
    return script


class ClaimCheckReq(BaseModel):
    text: str = Field(default="", max_length=8000)


@router.post("/check-claims")
def check_claims(req: ClaimCheckReq, _: Principal = Depends(get_principal)) -> dict:
    """Quét claim cấm (y tế/tài chính/tuyệt đối) trong 1 đoạn text → cảnh báo theo luật QC VN."""
    findings = claims.scan_claims(req.text)
    return {"findings": findings, "has_blocking": claims.has_blocking(findings)}


class CaptionReq(BaseModel):
    beats: list[dict] = Field(default_factory=list)
    fmt: str = "srt"  # srt | vtt | json


@router.post("/captions")
def captions(req: CaptionReq, _: Principal = Depends(get_principal)) -> dict:
    """Phụ đề frame-perfect từ beats của kịch bản (timing từ script, KHÔNG ASR)."""
    cues = scriptgen.build_captions({"beats": req.beats})
    fmt = req.fmt.lower()
    if fmt == "vtt":
        return {"format": "vtt", "content": scriptgen.to_vtt(cues), "cues": cues}
    if fmt == "json":
        return {"format": "json", "cues": cues}
    return {"format": "srt", "content": scriptgen.to_srt(cues), "cues": cues}


def _try_strategist(req: GenReq) -> dict | None:
    """Gọi Strategist nếu có key (fail-soft hoàn toàn — lỗi/không key → None → giữ template)."""
    try:
        from video_engine.director.strategist import build_creative_brief

        return build_creative_brief(
            product=req.product.model_dump(),
            product_description=req.product.description,
            format_label=scriptgen.ANGLE_LABELS.get(req.angle, ""),
            seconds=req.seconds,
        )
    except Exception:  # noqa: BLE001 — preview không được vỡ vì engine render
        return None
