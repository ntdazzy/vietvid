"""Chuẩn hoá ảnh sản phẩm về định dạng render-an-toàn (V7-B1).

Shopee trả ảnh `.webp` (đôi khi nền trong suốt RGBA). FFmpeg/NVENC dễ lỗi với webp/
animated; JPG nền-trắng an toàn cho render. Ảnh để GHÉP NỀN (cảnh hook mức A) giữ PNG
có alpha. Loại ảnh quá nhỏ (<400px) vì zoom Full HD sẽ vỡ nét.

Rủi ro #2 + #3 của founder (review): WebP→JPG, RGBA→JPG mà không xử lý alpha sẽ lỗi
`cannot write RGBA as JPEG` / nền đen → bắt buộc dán lên nền trắng trước khi lưu JPG.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter, ImageOps, UnidentifiedImageError

try:  # logger tập trung (Loguru)
    from core.logger import logger
except Exception:  # noqa: BLE001
    from loguru import logger

MIN_DIMENSION = 400  # cạnh nhỏ nhất chấp nhận (px) — dưới ngưỡng zoom Full HD bị vỡ.
_WHITE = (255, 255, 255)
_JPEG_QUALITY = 90


@dataclass(frozen=True)
class NormalizeResult:
    ok: bool
    src_path: str
    out_path: str = ""
    width: int = 0
    height: int = 0
    fmt: str = ""  # "JPEG" | "PNG"
    reason: str = ""  # lý do khi ok=False (too_small_WxH / error:Type / open_failed)


@dataclass(frozen=True)
class ImageQualityReport:
    ok: bool
    path: str
    width: int = 0
    height: int = 0
    brightness: float = 0.0
    edge_density: float = 0.0
    border_density: float = 0.0
    text_like_density: float = 0.0
    reasons: tuple[str, ...] = ()


def normalize_image(
    src_path: str | Path,
    out_dir: str | Path,
    *,
    for_compositing: bool = False,
    min_dimension: int = MIN_DIMENSION,
    stem: str | None = None,
) -> NormalizeResult:
    """Đọc 1 ảnh (webp/png/jpg…) → xuất bản render-an-toàn.

    - `for_compositing=False` (mặc định): dán lên nền trắng → JPG (hiển thị trực tiếp).
    - `for_compositing=True`: giữ alpha → PNG (để tách nền/ghép cảnh hook).
    Trả `NormalizeResult.ok=False` nếu ảnh nhỏ hơn `min_dimension` hoặc lỗi đọc.
    """
    src = Path(src_path)
    out = Path(out_dir)
    try:
        out.mkdir(parents=True, exist_ok=True)
        with Image.open(src) as raw:
            im = ImageOps.exif_transpose(raw)  # sửa hướng theo EXIF
            width, height = im.size
            if width < min_dimension or height < min_dimension:
                logger.info(
                    f"[image-normalize] bỏ {src.name}: nhỏ {width}x{height} (<{min_dimension})"
                )
                return NormalizeResult(
                    ok=False,
                    src_path=str(src),
                    width=width,
                    height=height,
                    reason=f"too_small_{width}x{height}",
                )
            base = stem or src.stem
            if for_compositing:
                target = out / f"{base}.png"
                im.convert("RGBA").save(target, "PNG")
                fmt = "PNG"
            else:
                if im.mode in ("RGBA", "LA", "P"):
                    rgba = im.convert("RGBA")
                    flat = Image.new("RGB", rgba.size, _WHITE)
                    flat.paste(rgba, mask=rgba.split()[-1])  # dán theo kênh alpha
                    out_im = flat
                else:
                    out_im = im.convert("RGB")
                target = out / f"{base}.jpg"
                out_im.save(target, "JPEG", quality=_JPEG_QUALITY)
                fmt = "JPEG"
        logger.info(f"[image-normalize] {src.name} → {target.name} ({width}x{height}, {fmt})")
        return NormalizeResult(
            ok=True,
            src_path=str(src),
            out_path=str(target.resolve()),
            width=width,
            height=height,
            fmt=fmt,
        )
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, ValueError) as exc:
        # V7 review P1: ảnh khổng lồ (decompression bomb) raise ngoài OSError/ValueError → bắt
        # tường minh để 1 ảnh xấu không làm sập cả luồng ingest sản phẩm hợp lệ.
        logger.warning(f"[image-normalize] lỗi đọc {src}: {exc!r}")
        return NormalizeResult(ok=False, src_path=str(src), reason=f"error:{type(exc).__name__}")


def pad_image_to_aspect(
    src_path: str | Path,
    out_dir: str | Path,
    *,
    aspect_w: int = 9,
    aspect_h: int = 16,
    short_edge: int = 720,
    stem: str | None = None,
) -> str:
    """Đệm ảnh về ĐÚNG tỉ lệ khung (mặc định 9:16) trên canvas nền-mờ (blurred-fill), sản phẩm
    căn giữa nét nguyên.

    Vì sao: Seedance i2v lấy TỈ LỆ video theo ẢNH khung đầu và BỎ QUA tham số ``aspect_ratio``
    (đã đo thật: ảnh gần vuông → video ra 1:1/3:4 dù xin 9:16). Đệm khung đầu về 9:16 → video ra
    đúng dọc. Nền = chính ảnh phủ kín + GaussianBlur (backdrop tự nhiên, không viền cứng).

    Trả đường dẫn ảnh đã đệm; lỗi → trả ``src_path`` gốc (fail-soft, không chặn render)."""
    src = Path(src_path)
    out = Path(out_dir)
    try:
        out.mkdir(parents=True, exist_ok=True)
        resample = getattr(Image, "Resampling", Image).LANCZOS
        with Image.open(src) as raw:
            im = ImageOps.exif_transpose(raw)
            if im.mode in ("RGBA", "LA", "P"):  # dán alpha lên nền TRẮNG (né nền ĐEN khi RGBA→JPG)
                rgba = im.convert("RGBA")
                flat = Image.new("RGB", rgba.size, _WHITE)
                flat.paste(rgba, mask=rgba.split()[-1])
                im = flat
            else:
                im = im.convert("RGB")
        # short_edge = cạnh NGẮN thật: dọc/vuông (9:16) → là width; ngang (16:9) → là height.
        if aspect_w <= aspect_h:
            cw = int(short_edge)
            ch = round(short_edge * aspect_h / aspect_w)
        else:
            ch = int(short_edge)
            cw = round(short_edge * aspect_w / aspect_h)
        bg = ImageOps.fit(im, (cw, ch), method=resample).filter(ImageFilter.GaussianBlur(28))
        fg = im.copy()
        fg.thumbnail((int(cw * 0.92), int(ch * 0.92)), resample)  # contain + lề ~8%
        bg.paste(fg, ((cw - fg.width) // 2, (ch - fg.height) // 2))
        target = out / f"{stem or (src.stem + '_pad')}.jpg"
        bg.save(target, "JPEG", quality=_JPEG_QUALITY)
        logger.info(f"[image-normalize] đệm {src.name} → {target.name} ({cw}x{ch}, {aspect_w}:{aspect_h})")
        return str(target.resolve())
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, ValueError) as exc:
        logger.warning(f"[image-normalize] pad_to_aspect lỗi {src}: {exc!r}")
        return str(src)


_NEAR_BLANK_BRIGHTNESS = 244.0  # >ngưỡng = gần như TRẮNG (sản phẩm tí xíu trên nền trắng)
_MAX_TEXT_LIKE_DENSITY = 0.72  # P1 fix (2026-06-10): 0.23 quá thấp — loại nhầm ảnh sản phẩm chi tiết / người mẫu / hoạ tiết rậm (text_like 0.5–0.7 là BÌNH THƯỜNG). Chỉ chặn ảnh CHỮ promo dày đặc (>0.72); ảnh trắng + viền-promo-rậm vẫn chặn riêng.
_MAX_BORDER_DENSITY = 0.34


def is_near_blank(
    path: str | Path, *, brightness_threshold: float = _NEAR_BLANK_BRIGHTNESS
) -> bool:
    """Ảnh gần-trắng/trống: full-frame trông như cảnh TRỐNG (lỗi founder thấy ở scene @30s).

    Đo độ sáng trung bình trên bản thu nhỏ 32x32 (rẻ). Lỗi đọc → False (không loại oan).
    """
    try:
        with Image.open(path) as raw:
            data = _pixels(raw.convert("L").resize((32, 32)))
        return bool(data) and (sum(data) / len(data)) > brightness_threshold
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, ValueError):
        return False


def analyze_product_image_quality(path: str | Path) -> ImageQualityReport:
    """Đánh giá ảnh sản phẩm local bằng heuristic rẻ để tránh render ảnh trắng/promo nhiều chữ.

    Không OCR nặng: dùng PIL đo nền gần trắng + mật độ cạnh sắc. Ảnh Shopee promo thường có rất
    nhiều chữ/khung/label nên edge density cao, đặc biệt ở viền. Lỗi đọc ảnh → fail để không đưa
    ảnh hỏng xuống render.
    """
    src = Path(path)
    try:
        with Image.open(src) as raw:
            im = ImageOps.exif_transpose(raw).convert("RGB")
            width, height = im.size
            small = ImageOps.fit(im, (96, 96))
            gray = small.convert("L")
            pixels = _pixels(gray)
            brightness = sum(pixels) / len(pixels)
            edges = gray.filter(ImageFilter.FIND_EDGES)
            edge_pixels = _pixels(edges)
            edge_density = sum(1 for value in edge_pixels if value > 42) / len(edge_pixels)
            border_density = _border_edge_density(edges)
            text_like_density = _text_like_density(gray)
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, ValueError) as exc:
        return ImageQualityReport(ok=False, path=str(src), reasons=(f"error:{type(exc).__name__}",))

    reasons: list[str] = []
    if width < MIN_DIMENSION or height < MIN_DIMENSION:
        reasons.append(f"too_small_{width}x{height}")
    if brightness > _NEAR_BLANK_BRIGHTNESS:
        reasons.append("near_blank_white")
    if text_like_density > _MAX_TEXT_LIKE_DENSITY:
        reasons.append("too_much_text_or_promo")
    if border_density > _MAX_BORDER_DENSITY:
        reasons.append("busy_promo_border")
    return ImageQualityReport(
        ok=not reasons,
        path=str(src),
        width=width,
        height=height,
        brightness=round(brightness, 2),
        edge_density=round(edge_density, 4),
        border_density=round(border_density, 4),
        text_like_density=round(text_like_density, 4),
        reasons=tuple(reasons),
    )


def product_image_is_render_ready(path: str | Path) -> bool:
    return analyze_product_image_quality(path).ok


def _border_edge_density(edges) -> float:  # noqa: ANN001
    width, height = edges.size
    band = max(4, min(width, height) // 10)
    mask = Image.new("L", edges.size, 0)
    for box in (
        (0, 0, width, band),
        (0, height - band, width, height),
        (0, 0, band, height),
        (width - band, 0, width, height),
    ):
        mask.paste(255, box)
    border = ImageChops.multiply(edges, mask)
    values = _pixels(border)
    mask_values = _pixels(mask)
    active = sum(1 for value in values if value > 42)
    area = sum(1 for value in mask_values if value > 0)
    return active / max(1, area)


def _text_like_density(gray) -> float:  # noqa: ANN001
    width, height = gray.size
    block = 8
    busy = 0
    total = 0
    for y in range(0, height, block):
        for x in range(0, width, block):
            crop = gray.crop((x, y, min(width, x + block), min(height, y + block)))
            vals = _pixels(crop)
            if not vals:
                continue
            total += 1
            if max(vals) - min(vals) >= 96:
                busy += 1
    return busy / max(1, total)


def _pixels(image) -> list[int]:  # noqa: ANN001
    if hasattr(image, "get_flattened_data"):
        return list(image.get_flattened_data())
    return list(image.getdata())
