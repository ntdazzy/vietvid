"""Clean product plate: crop/seg product pixels, never redraw the product with AI.

Pixel fidelity is the rule here:
1. Gemini Vision may locate the product box only.
2. PIL crops original pixels.
3. rembg may remove background from the crop.
4. normalize_image writes a PiAPI-safe image.

If crop/seg is weak, the caller falls back to the original product image.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import settings
from core.config_checks import looks_real_secret
from video_engine.director.critic import _loads_lenient
from core.image_normalize import normalize_image
from core.logger import logger
from video_engine.qa import qa_image_match

_CROP_PAD = 0.04  # nới bbox 4% mỗi cạnh — tránh cắt sát quá làm mất viền sản phẩm
_CROP_ACCEPT_SCORE = 0.5  # crop = pixel gốc → ngưỡng nới (dưới = nghi cắt nhầm vùng → giữ làm floor)
_SEG_BG = (245, 245, 247)  # nền trung tính sáng cho ảnh tách nền (e-commerce)


@dataclass
class CleanPlateResult:
    path: str  # CHỈ dùng khi passed=True; passed=False → caller dùng ảnh gốc
    cost: float
    method: str  # "crop" | "crop+seg" | "original"
    passed: bool
    reports: list[dict] = field(default_factory=list)


def generate_clean_plate(
    *,
    product: dict,
    product_image: str,
    product_desc: str = "",
    out_dir: str,
    aspect: str = "9:16",
) -> CleanPlateResult:
    """Trả CleanPlateResult. ``passed=False`` → caller fail-soft về ảnh gốc.

    Ưu tiên pixel gốc: crop → seg → floor crop → ảnh gốc.
    """
    name = (product.get("name") or "").strip()
    category = (product.get("category") or "").strip()
    reports: list[dict] = []

    # ── 1+2+3: định vị → crop (pixel gốc) → seg → normalize ────────────────
    floor_path: str | None = None  # crop pixel-gốc bị nghi cắt nhầm nhưng VẪN > ảnh marketing gốc
    floor_method = ""
    loc = None
    try:
        loc = _locate_product(product_image, name, category)
    except Exception as exc:  # noqa: BLE001 — định vị lỗi thì bỏ qua crop
        logger.warning(f"[clean-plate] định vị sản phẩm lỗi: {str(exc)[:200]}")

    if loc and loc.get("bbox"):
        crop_path = _crop_to_bbox(product_image, loc["bbox"], out_dir, "clean_crop")
        if crop_path:
            seg_path = _segment(crop_path, out_dir, "clean_seg")
            candidate = seg_path or crop_path
            method = "crop+seg" if seg_path else "crop"
            # Crop sản phẩm (từ collage marketing) thường nhỏ hơn 400px 1 chiều → min_dimension
            # Hạ floor xuống 256 để giữ crop thật khi ảnh marketing/collage nhỏ.
            norm = normalize_image(candidate, out_dir, stem="clean", min_dimension=256)
            if norm.ok:
                report = qa_image_match(product_image, norm.out_path)
                reports.append(report)
                if _accept_crop(report):
                    logger.info(
                        f"[clean-plate] {method} OK (score={report.get('score')}, "
                        f"collage={bool(loc.get('is_collage'))}) → {norm.out_path}"
                    )
                    return CleanPlateResult(
                        path=norm.out_path, cost=0.0, method=method, passed=True, reports=reports
                    )
                # Score thấp: có thể cắt nhầm vùng HOẶC false-negative do so với ảnh collage gốc.
                # Pixel gốc vẫn quý → GIỮ làm floor; không sinh lại sản phẩm bằng AI.
                floor_path, floor_method = norm.out_path, method
                logger.warning(
                    f"[clean-plate] {method} score thấp ({report.get('score')}) → giữ làm floor pixel gốc"
                )
            else:
                logger.warning(f"[clean-plate] normalize crop fail ({norm.reason})")

    if floor_path:
        logger.info(f"[clean-plate] dùng floor crop ({floor_method}, pixel gốc)")
        return CleanPlateResult(
            path=floor_path, cost=0.0, method=floor_method, passed=True, reports=reports
        )
    logger.warning("[clean-plate] không có ảnh sạch đạt yêu cầu → fail-soft (caller dùng ảnh gốc)")
    return CleanPlateResult(
        path=product_image, cost=0.0, method="original", passed=False, reports=reports
    )


def _accept_crop(report: dict) -> bool:
    """Crop = pixel GỐC → tin tưởng; chỉ ngờ khi score RẤT thấp (nghi cắt nhầm prop/vùng).

    score=None (Gemini không quyết được / mock-skip) vẫn nhận (crop là pixel gốc); chỉ <0.5 mới ngờ.
    Khi ngờ, caller KHÔNG vứt crop — giữ làm floor (xem generate_clean_plate).
    """
    score = report.get("score")
    if score is None:
        return True
    return float(score) >= _CROP_ACCEPT_SCORE


# ── định vị bằng Gemini Vision (quy ước box_2d native [ymin,xmin,ymax,xmax] 0-1000) ─────────
def _locate_product(image_path: str, product_name: str, category: str) -> dict | None:
    """Trả {bbox:[x0,y0,x1,y1] (0..1), is_collage, confidence} hoặc None (fail → caller bỏ qua)."""
    if not looks_real_secret(settings.gemini_api_key or "") or not os.path.exists(image_path):
        return None
    obj = _gemini_locate(image_path, product_name, category)
    raw = obj.get("box_2d") or obj.get("bbox")
    if not (isinstance(raw, list) and len(raw) == 4):
        return None
    bbox = _normalize_bbox(raw)
    if not bbox:
        return None
    return {"bbox": bbox, "is_collage": bool(obj.get("is_collage")), "confidence": obj.get("confidence")}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=12), reraise=True)
def _gemini_locate(image_path: str, product_name: str, category: str) -> dict:
    """1 call Gemini Vision (retry 503 transient — như _gemini_compare). Trả dict JSON."""
    import mimetypes

    from google import genai
    from google.genai import types

    with open(image_path, "rb") as f:
        data = f.read()
    mime = mimetypes.guess_type(image_path)[0] or "image/jpeg"
    prompt = (
        f"Ảnh marketing của sản phẩm: {product_name!r} (ngành: {category}). "
        "Tìm bounding box bao trọn DUY NHẤT 1 sản phẩm chính (rõ/lớn nhất). "
        "Dùng ĐÚNG quy ước box_2d của Gemini: [ymin, xmin, ymax, xmax], giá trị chuẩn hoá 0-1000 "
        "(gốc góc trên-trái, ymin/ymax theo chiều dọc, xmin/xmax theo chiều ngang). "
        "Nếu ảnh là COLLAGE/lưới nhiều món/nhiều khung → is_collage=true và box bao ĐÚNG 1 ô đại diện. "
        'Trả JSON thuần: {"box_2d":[ymin,xmin,ymax,xmax],"is_collage":bool,"confidence":0..1}'
    )
    # Giữ reference client vào biến — KHÔNG gọi inline genai.Client(...).models... (Client không
    # được giữ → GC đóng httpx client giữa chừng → "Cannot send a request, client has been closed").
    client = genai.Client(api_key=settings.gemini_api_key)
    resp = client.models.generate_content(
        model=settings.gemini_model,
        contents=[types.Part.from_bytes(data=data, mime_type=mime), prompt],
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    return _loads_lenient(getattr(resp, "text", "") or "")


def _normalize_bbox(box: list) -> list[float] | None:
    """[ymin,xmin,ymax,xmax] (Gemini, thang 0-1000) → [x0,y0,x1,y1] trong 0..1.

    Chia 1000 nếu thang 0-1000 (mặc định Gemini); thang 0..1 (hiếm) giữ nguyên. Clamp + reject box quá nhỏ.
    """
    try:
        ymin, xmin, ymax, xmax = (float(v) for v in box)
    except (TypeError, ValueError):
        return None
    scale = 1000.0 if max(abs(ymin), abs(xmin), abs(ymax), abs(xmax)) > 1.5 else 1.0
    x0, x1 = sorted((xmin / scale, xmax / scale))
    y0, y1 = sorted((ymin / scale, ymax / scale))
    x0 = max(0.0, min(1.0, x0))
    y0 = max(0.0, min(1.0, y0))
    x1 = max(0.0, min(1.0, x1))
    y1 = max(0.0, min(1.0, y1))
    if (x1 - x0) < 0.05 or (y1 - y0) < 0.05:  # box quá nhỏ = định vị hỏng
        return None
    return [x0, y0, x1, y1]


# ── crop pixel gốc ─────────────────────────────────────────────────────────
def _crop_to_bbox(image_path: str, bbox: list[float], out_dir: str, stem: str) -> str | None:
    from PIL import Image, ImageOps, UnidentifiedImageError

    try:
        with Image.open(image_path) as raw:
            im = ImageOps.exif_transpose(raw).convert("RGB")
            W, H = im.size
            x0, y0, x1, y1 = bbox
            px0 = max(0, int((x0 - _CROP_PAD) * W))
            py0 = max(0, int((y0 - _CROP_PAD) * H))
            px1 = min(W, int((x1 + _CROP_PAD) * W))
            py1 = min(H, int((y1 + _CROP_PAD) * H))
            if px1 - px0 < 2 or py1 - py0 < 2:
                return None
            os.makedirs(out_dir, exist_ok=True)
            out = os.path.join(out_dir, f"{stem}.png")
            im.crop((px0, py0, px1, py1)).save(out, "PNG")
            return out
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        logger.warning(f"[clean-plate] crop lỗi: {str(exc)[:150]}")
        return None


# ── segmentation (rembg, tuỳ chọn) ──────────────────────────────────────────
def _segment(crop_path: str, out_dir: str, stem: str) -> str | None:
    """Tách nền khỏi crop → ghép SP lên nền trung tính. Pixel SP GIỮ NGUYÊN.

    rembg không cài/lỗi → trả None, caller dùng crop (vẫn pixel gốc).
    """
    try:
        from rembg import remove
    except Exception as exc:  # noqa: BLE001 — chưa cài/không import được → degrade về crop
        logger.info(f"[clean-plate] rembg không khả dụng ({type(exc).__name__}) → dùng crop pixel gốc")
        return None
    from PIL import Image

    try:
        with Image.open(crop_path) as im:
            cut = remove(im.convert("RGBA"))  # RGBA, nền trong suốt
        if not isinstance(cut, Image.Image):
            return None
        bg = Image.new("RGBA", cut.size, (*_SEG_BG, 255))
        bg.alpha_composite(cut.convert("RGBA"))
        out = os.path.join(out_dir, f"{stem}.png")
        bg.convert("RGB").save(out, "PNG")
        return out
    except Exception as exc:  # noqa: BLE001 — seg lỗi → degrade về crop (vẫn pixel gốc)
        logger.warning(f"[clean-plate] segmentation lỗi → dùng crop: {str(exc)[:150]}")
        return None
