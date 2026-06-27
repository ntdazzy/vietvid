"""visual_shots.py — shot builders MoviePy cho long_narrative (tách từ visual.py).

Cụm dựng SHOT: thẻ ảnh 16:9 Ken Burns, footage b-roll, nền parallax 2.5D, scene cut-out,
chia nhịp shot, layered (compositor). LEAF: chỉ phụ thuộc np/PIL/moviepy(lazy)/compositor(lazy)
+ hằng W/H/SHOT_DUR/CARD_W; KHÔNG gọi ngược vào visual.py. visual.py import lại các tên này.
"""

from __future__ import annotations

import os

import numpy as np
from PIL import Image, ImageFilter

W, H = 1920, 1080
SHOT_DUR = 4.2                  # độ dài 1 shot (nhịp ~3-5s)
CARD_W = 1120                   # bề ngang thẻ ảnh 16:9 (chừa dải callout trên + caption dưới)


def stadium_bg(out_path: str) -> str:
    """Nền tối điện ảnh (lớn hơn frame 1.1x để parallax drift không lộ mép). Cache."""
    if os.path.exists(out_path) and os.path.getsize(out_path) > 3000:
        return out_path
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    bw, bh = int(W * 1.12), int(H * 1.12)
    base = Image.new("RGB", (bw, bh), (12, 18, 30))
    # vignette nhẹ cho có chiều sâu
    grad = Image.new("L", (bw, bh), 0)
    arr = np.zeros((bh, bw), dtype=np.uint8)
    yy, xx = np.mgrid[0:bh, 0:bw]
    cx, cy = bw / 2, bh / 2
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / np.sqrt(cx ** 2 + cy ** 2)
    arr = (np.clip(d, 0, 1) * 60).astype(np.uint8)
    grad = Image.fromarray(arr)
    dark = Image.new("RGB", (bw, bh), (4, 8, 16))
    base = Image.composite(dark, base, grad)
    base.save(out_path)
    return out_path


def make_card_169(src_png: str) -> tuple[str, int, int]:
    """Bọc ảnh thành 'thẻ' viền trắng + bóng đổ (proven make_sample.make_card_169)."""
    out = src_png.rsplit(".", 1)[0] + "_card.png"
    s = Image.open(src_png).convert("RGB")
    cw = CARD_W
    chh = int(CARD_W * s.height / s.width)
    s = s.resize((cw, chh))
    pad = 8
    card = Image.new("RGBA", (cw + pad * 2, chh + pad * 2), (255, 255, 255, 255))
    card.paste(s, (pad, pad))
    sh = Image.new("RGBA", (card.width + 70, card.height + 70), (0, 0, 0, 0))
    sh.paste(Image.new("RGBA", card.size, (0, 0, 0, 150)), (35, 45))
    sh = sh.filter(ImageFilter.GaussianBlur(20))
    sh.alpha_composite(card, (35, 24))
    sh.save(out)
    return out, sh.width, sh.height


def _card_shot(card_png: str, card_wh: tuple[int, int], bg_png: str, dur: float, *, zoom_in: bool):
    """1 shot dạng THẺ: nền sân parallax drift + thẻ ảnh Ken Burns (2 lớp lệch chuyển động = 2.5D).

    Ken Burns `resized(lambda t)` zoom chậm cinematic (kiểu Lóng) — founder ưu tiên CHẤT LƯỢNG; long_narrative
    chạy lane worker riêng nên render chậm KHÔNG chặn queue product → giữ zoom để có cảm giác điện ảnh.
    """
    from moviepy import CompositeVideoClip, ImageClip, vfx

    bg_im = Image.open(bg_png)
    bgw, bgh = bg_im.size
    offx, offy = (W - bgw) // 2, (H - bgh) // 2
    bg = (
        ImageClip(bg_png).with_duration(dur)
        .with_position(lambda t: (offx + int(26 * np.sin(0.16 * t)), offy + int(16 * np.sin(0.11 * t))))
    )
    cw, chh = card_wh
    ycenter = 515  # tâm thẻ ở dải giữa (chừa callout trên ~104, caption dưới ~885)
    ytop = ycenter - chh // 2

    def _zoom(t):
        k = 0.05
        return 1.0 + k * (t / dur) if zoom_in else 1.0 + k * (1 - t / dur)

    card = (
        ImageClip(card_png).with_duration(dur)
        .resized(_zoom)
        .with_position(lambda t: ("center", ytop + int(8 * np.sin(0.3 * t))))
        .with_effects([vfx.CrossFadeIn(0.35)])
    )
    return CompositeVideoClip([bg, card], size=(W, H)).with_duration(dur)


def _broll_shot(video_path: str, dur: float):
    """1 shot FOOTAGE full-bleed: cover-crop 1920×1080, loop/trim đúng dur, Ken Burns nhẹ.

    Giữ ref reader GỐC (`out.lf_source`) để render đóng sau khi xuất — CompositeVideoClip.close() KHÔNG
    đóng clip con, nên không stash thì mỗi b-roll rò 1 ffmpeg reader + file handle qua cả video dài.
    """
    from moviepy import VideoFileClip, vfx

    raw = VideoFileClip(video_path)
    clip = raw.without_audio()
    scale = max(W / clip.w, H / clip.h)
    clip = clip.resized(scale)
    # crop center về đúng khung
    x1 = max(0, (clip.w - W) / 2)
    y1 = max(0, (clip.h - H) / 2)
    clip = clip.cropped(x1=x1, y1=y1, width=W, height=H)
    if clip.duration < dur:
        clip = clip.with_effects([vfx.Loop(duration=dur)])
    else:
        clip = clip.subclipped(0, dur)
    out = clip.with_duration(dur).with_effects([vfx.CrossFadeIn(0.3)])
    out.lf_source = raw
    return out


def _bg_shot(bg_png: str, dur: float):
    """Shot NỀN sân parallax drift (KHÔNG thẻ) — fallback khi thiếu cả ảnh AI lẫn footage.
    Tránh 'màn hình đen phẳng' (ColorClip) khi Gemini ảnh fail (504): vẫn có nền động + chữ đè đọc được."""
    from moviepy import CompositeVideoClip, ImageClip

    bg_im = Image.open(bg_png)
    bgw, bgh = bg_im.size
    offx, offy = (W - bgw) // 2, (H - bgh) // 2
    bg = (
        ImageClip(bg_png).with_duration(dur)
        .with_position(lambda t: (offx + int(26 * np.sin(0.16 * t)), offy + int(16 * np.sin(0.11 * t))))
    )
    return CompositeVideoClip([bg], size=(W, H)).with_duration(dur)


def _scene_shot(scene_png: str, dur: float, variant: int):
    """1 shot từ ảnh CẢNH doodle_cutout: Ken Burns NHẸ full-bleed (zoom in/out luân phiên theo variant)
    — giữ NGUYÊN bố cục (nội dung GIỮA + người dẫn nhỏ góc), KHÔNG crop vùng (crop làm phóng to nhân
    vật méo/cắt cụt). Cut mềm 0.25s giữa đoạn → động mà không hỏng khung."""
    from moviepy import CompositeVideoClip, ImageClip, vfx

    im = Image.open(scene_png)
    iw, ih = im.size
    cover = max(W / iw, H / ih)
    zoom_in = (variant % 2 == 0)
    k = 0.0

    def _zoom(t: float) -> float:
        p = min(1.0, t / dur) if dur > 0 else 0.0
        return cover * ((1.0 + k * p) if zoom_in else (1.0 + k * (1.0 - p)))

    clip = (
        ImageClip(scene_png).with_duration(dur).resized(_zoom)
        .with_position(lambda t: ("center", "center"))
        .with_effects([vfx.CrossFadeIn(0.25)])
    )
    return CompositeVideoClip([clip], size=(W, H)).with_duration(dur)


def _plan_segments(duration: float, blocks=None) -> list[tuple[float, float, int]]:
    """Chia beat thành các shot → [(start, dur, block_index)]. CẮT ĐÚNG RANH BLOCK (đổi shot khi đổi
    lượt nói) để hình khớp giọng; block dài > SHOT_DUR thì chia đều TRONG block giữ nhịp. blocks rỗng →
    lưới SHOT_DUR cố định như cũ. Phủ liền mạch [block0.start .. duration] (gồm cả gap+tail cuối beat)."""
    if not blocks:
        segs, t = [], 0.0
        while t < duration - 0.3:
            sd = min(SHOT_DUR, duration - t)
            segs.append((t, sd, 0))
            t += sd
        return segs or [(0.0, duration, 0)]
    bounds = sorted((max(0.0, float(b.start)), bi) for bi, b in enumerate(blocks))
    segs: list[tuple[float, float, int]] = []
    for j, (bs, bi) in enumerate(bounds):
        be = bounds[j + 1][0] if j + 1 < len(bounds) else duration  # đoạn cuối kéo tới hết beat
        seg = be - bs
        if seg <= 0.1:
            continue
        nsub = max(1, round(seg / SHOT_DUR))
        sub = seg / nsub
        for k in range(nsub):
            segs.append((bs + k * sub, sub, bi))
    return segs or [(0.0, duration, 0)]


def _build_layered(shots, duration: float):
    """Mode vuive_layered: render MỖI Shot qua compositor.render_shot → concat hard-cut → gom .lf_sources.

    Transition (fade/glitch) GHI trong shot.transition_in nhưng Stage 2 realize = hard-cut (method='compose');
    realize fade/glitch để Stage 4 (đúng roadmap). Bao try/except đóng sources nếu render giữa chừng lỗi.
    """
    from moviepy import ColorClip, concatenate_videoclips

    from video_engine.long_narrative.compositor import render_shot

    clips, sources = [], []
    try:
        for sh in shots:
            c = render_shot(sh)
            sources.extend(getattr(c, "lf_sources", None) or [])
            clips.append(c)
        if not clips:
            out = ColorClip(size=(W, H), color=(247, 244, 236)).with_duration(duration)
        elif len(clips) == 1:
            out = clips[0].with_duration(duration)
        else:
            out = concatenate_videoclips(clips, method="compose").with_duration(duration)
    except BaseException:
        for s in sources:
            try:
                s.close()
            except Exception:  # noqa: BLE001 — best-effort
                pass
        raise
    out.lf_sources = sources
    return out
