"""diagram_gen.py — sinh DIAGRAM bằng PIL template ($0, nét doodle-phẳng) thay vì tải ảnh web (lạc nét).

BOUNDED: chỉ template "2 cột VS" (so sánh 2 thứ — rất hay ở kênh cà-khịa) khi hint TÁCH SẠCH thành 2 vế.
Không tách được → trả None → caller (asset_resolver) lùi doodle (Gemini vẽ trong nét kênh). KHÔNG tự bịa
diagram vô nghĩa (đúng tinh thần "không làm bừa"). Màu PHẲNG + viền đen dày + font dự án (hợp nét doodle).
"""

from __future__ import annotations

import hashlib
import os
import re

from core.logger import logger

W, H = 1280, 720
_VS_MARKERS = re.compile(r"\s+(?:vs\.?|versus|đấu với|↔)\s+", re.IGNORECASE)


def _font(size: int):
    from PIL import ImageFont
    for p in (os.path.join("storage", "style-research", "fonts", "BeVietnamPro-Black.ttf"),
              r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\segoeui.ttf"):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:  # noqa: BLE001
                continue
    return ImageFont.load_default()


def _split_vs(hint: str) -> tuple[str, str] | None:
    """Tách hint thành (trái, phải) nếu có marker 'vs/versus/đấu với'. 2 vế đều ngắn-gọn mới nhận."""
    if not hint:
        return None
    parts = _VS_MARKERS.split(hint, maxsplit=1)
    if len(parts) != 2:
        return None

    def _entity(s: str, take_last: bool) -> str:
        words = s.strip(" -:,").split()
        if not words:
            return ""
        proper = [w for w in words if w[:1].isupper()]     # DANH TỪ RIÊNG (isupper Unicode-aware, đúng tiếng Việt)
        if proper:
            return (proper[-1] if take_last else proper[0])[:22]
        return (" ".join(words[-2:]) if take_last else " ".join(words[:2]))[:22]   # không tên riêng → 2 từ gần marker

    left = _entity(parts[0], take_last=True)               # tên gần 'vs' ở vế trái
    right = _entity(parts[1], take_last=False)             # tên gần 'vs' ở vế phải
    if not left or not right:
        return None
    return left, right


def _draw_text_center(d, cx, cy, text, font, fill, outline="black"):
    bb = d.textbbox((0, 0), text, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    x, y = cx - tw / 2, cy - th / 2
    for dx in (-2, 2):
        for dy in (-2, 2):
            d.text((x + dx, y + dy), text, font=font, fill=outline)   # viền đậm
    d.text((x, y), text, font=font, fill=fill)


def make_comparison(left: str, right: str, out_dir: str) -> str:
    """2 cột VS: 2 thẻ bo-góc viền đen + 'VS' giữa — nét phẳng doodle. Cache theo (left,right)."""
    from PIL import Image, ImageDraw

    os.makedirs(out_dir, exist_ok=True)
    key = hashlib.md5(f"{left}|{right}".encode("utf-8")).hexdigest()[:10]
    out = os.path.join(out_dir, f"diag_vs_{key}.png")
    if os.path.exists(out) and os.path.getsize(out) > 2000:
        return out
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))   # nền trong suốt (compositor đặt trên kem)
    d = ImageDraw.Draw(img)
    cardw, cardh, gap = 470, 360, 120
    x0 = (W - 2 * cardw - gap) // 2
    cols = [((230, 90, 90, 255), x0), ((70, 130, 220, 255), x0 + cardw + gap)]   # đỏ | xanh (flat)
    for (fill, cx) in cols:
        d.rounded_rectangle([cx, 180, cx + cardw, 180 + cardh], radius=28, fill=fill,
                            outline="black", width=8)
    f = _font(52)
    _draw_text_center(d, cols[0][1] + cardw / 2, 360, left, f, "white")
    _draw_text_center(d, cols[1][1] + cardw / 2, 360, right, f, "white")
    _draw_text_center(d, W / 2, 360, "VS", _font(76), (255, 220, 0))   # VS vàng giữa
    img.save(out)
    return out


def make_diagram(hint: str, kind: str, out_dir: str) -> str | None:
    """Dispatcher: 'diagram' + hint tách được VS → 2 cột. Còn lại (map, diagram mơ hồ) → None (caller lùi doodle)."""
    try:
        if kind == "diagram":
            vs = _split_vs(hint)
            if vs:
                return make_comparison(vs[0], vs[1], out_dir)
        return None
    except Exception as exc:  # noqa: BLE001 — fail-soft: lỗi → None, caller lùi doodle
        logger.warning(f"[diagram-gen] lỗi → None: {str(exc)[:120]}")
        return None
