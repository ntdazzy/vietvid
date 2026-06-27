"""Router product import — dán link sản phẩm → bóc tên/giá/ảnh → prefill wizard (auto-ad)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app_api import scrape
from app_api.auth import Principal
from app_api.deps import get_principal

router = APIRouter(prefix="/v1/products", tags=["products"])


class ImportReq(BaseModel):
    url: str = Field(min_length=8, max_length=2000)


class ImportOut(BaseModel):
    name: str
    description: str
    price: str
    image_url: str
    images: list[str]
    source_url: str


@router.post("/import", response_model=ImportOut)
def import_product(req: ImportReq, _: Principal = Depends(get_principal)) -> ImportOut:
    try:
        data = scrape.scrape_product(req.url.strip())
    except scrape.ScrapeError as exc:
        raise HTTPException(422, str(exc)) from exc
    return ImportOut(**data)
