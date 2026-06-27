"""Router sinh kịch bản — xem trước + sửa trước khi đốt credit render (parity Arcads/autovis).

POST /v1/script/generate: nhận thông tin sản phẩm + góc + thời lượng → trả kịch bản có cấu trúc
(hook, beats theo timecode, narration, captions, CTA). Bản template chạy ngay không cần key; khi
có key Gemini/Groq thì phủ CreativeBrief của Strategist lên (fail-soft).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app_api import scriptgen
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
    return script


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
