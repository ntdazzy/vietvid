"""cutout_compose.py — ghép cảnh 'doodle_cutout' kiểu Vui Vẻ: nền sáng + subject (ảnh chủ đề) +
NHÂN VẬT cut-out dán một bên → 1 ảnh 1920×1080 (oversize 1.12 cho parallax của _bg_shot).

Caller (visual.py) trả ảnh này qua bg_path → build_beat_visual._bg_shot render FULL-BLEED + drift
nhẹ (đúng look slideshow tĩnh + hard-cut của Vui Vẻ). Caption/callout do render.py phủ lên sau.
"""

from __future__ import annotations

import os

from core.logger import logger

W, H = 1920, 1080
OVERSIZE = 1.12                 # khớp stadium_bg: lớn hơn frame để _bg_shot drift không lộ mép
_BG = (247, 244, 236)          # nền kem nhạt (giống nền sáng kênh Vui Vẻ)


def compose_beat_scene(character_png: str, subject_path: str | None, out_path: str,
                       *, char_side: str = "left") -> str:
    """Nền kem + NỘI DUNG (subject) TO Ở GIỮA (ngôi sao khung) + người dẫn NHỎ NỬA NGƯỜI nép 1 GÓC DƯỚI
    (kiểu reaction streamer) → PNG oversize. Người dẫn KHÔNG che nội dung. Raise nếu character hỏng
    (caller fail-soft); subject lỗi → bỏ qua, vẫn để người dẫn góc."""
    from PIL import Image

    cw, ch = int(W * OVERSIZE), int(H * OVERSIZE)
    canvas = Image.new("RGBA", (cw, ch), _BG + (255,))

    # NỘI DUNG: subject TO ở GIỮA, hơi lệch xa góc người dẫn để không bị che.
    if subject_path and os.path.exists(subject_path):
        try:
            subj = Image.open(subject_path).convert("RGBA")
            try:
                from video_engine.long_narrative.images.character_library import _cutout_white

                subj = _cutout_white(subj)
            except Exception:
                pass
            bbox = subj.getbbox()
            if bbox:
                subj = subj.crop(bbox)
                pad = max(24, int(max(subj.width, subj.height) * 0.10))
                framed = Image.new("RGBA", (subj.width + pad * 2, subj.height + pad * 2), (0, 0, 0, 0))
                framed.alpha_composite(subj, (pad, pad))
                subj = framed
            sh = int(ch * 0.58)
            sw = max(1, int(subj.width * sh / subj.height))
            if sw > int(cw * 0.62):                       # quá rộng → fit theo bề ngang, chừa lề render
                sw = int(cw * 0.62)
                sh = max(1, int(subj.height * sw / subj.width))
            subj = subj.resize((sw, sh))
            nudge = int(cw * 0.02)
            sx = (cw - sw) // 2 + (nudge if char_side == "left" else -nudge)
            sy = int(ch * 0.05)
            canvas.alpha_composite(subj, (max(0, min(sx, cw - sw)), max(0, sy)))
        except Exception as exc:  # noqa: BLE001 — subject lỗi: vẫn để người dẫn góc
            logger.warning(f"[cutout] subject lỗi, bỏ qua: {str(exc)[:120]}")

    # NGƯỜI DẪN: NỬA NGƯỜI (đầu+thân) + NHỎ + nép 1 GÓC DƯỚI (trái/phải).
    # Chừa lề để khi render có drift nhẹ thì tay/chân không bị cắt.
    char = Image.open(character_png).convert("RGBA")
    bbox = char.getbbox()
    if bbox:
        char = char.crop(bbox)
        pad = max(16, int(max(char.width, char.height) * 0.08))
        framed = Image.new("RGBA", (char.width + pad * 2, char.height + pad * 2), (0, 0, 0, 0))
        framed.alpha_composite(char, (pad, pad))
        char = framed
    half = char                                                         # caller đã đưa PNG bán-thân sẵn
    hh = int(ch * 0.28)                                             # NHỎ — chỉ là góc reaction
    ww = max(1, int(half.width * hh / half.height))
    half = half.resize((ww, hh))
    margin = int(cw * 0.08)
    bottom_margin = int(ch * 0.12)
    px = margin if char_side == "left" else cw - ww - margin
    py = ch - hh - bottom_margin
    canvas.alpha_composite(half, (max(0, px), max(0, py)))

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    canvas.convert("RGB").save(out_path, quality=92)
    return out_path
