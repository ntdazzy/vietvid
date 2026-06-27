"""compositor.py — renderer ĐA-LỚP cho engine auto-edit kiểu Vui Vẻ (Stage 0).

Khác build_beat_visual (nung/Ken Burns 1 ảnh tĩnh): ở đây 1 Shot = nhiều Layer ĐỘC LẬP, mỗi Layer
→ 1 clip MoviePy (ColorClip nền / ImageClip cut-out RGBA / TextClip) ghép LIVE bằng
CompositeVideoClip — KHÔNG flatten PNG. Từng cut-out trượt/pop/zoom/lắc riêng theo chuỗi Keyframe
(scene_schema.sample). Clip trả về MANG `.lf_sources` (list VideoFileClip cần đóng) → tái dùng đúng
contract cleanup của render._render_beat_clip (finally đóng lf_sources, chống rò handle Windows).

Toạ độ: schema dùng TÂM (cx,cy fraction). MoviePy định vị bằng TOP-LEFT → khi scale động phải quy đổi
  x = cx*W - base_w*sc/2 + shake   (không quy đổi → vật trượt chéo lúc zoom). Bind biến trong closure
lambda (l=layer, bw=...) để tránh late-binding trong vòng for.

API MoviePy 2.x ONLY: with_position/with_duration/with_start/with_effects/resized/with_opacity, vfx.*.
"""

from __future__ import annotations

import os

import numpy as np
from PIL import Image

from core.logger import logger
from video_engine.long_narrative.scene_schema import H, W, Layer, Shot, sample, shake_offset

_FONT = os.path.join("storage", "style-research", "fonts", "BeVietnamPro-Black.ttf")
_CREAM = (255, 255, 255)        # nền TRẮNG (founder 2026-06-21; kênh gốc nền trắng — trước kem 247,244,236)
_TEXT_COLOR = {"doodle": "#ffd23f", "tech": "#7CFC00"}   # vàng doodle / xanh terminal (Stage 4 mở rộng)


def _font_path() -> str:
    """Font dự án (BeVietnamPro-Black) — dựng standalone, KHÔNG import render.py (tránh vòng import)."""
    if os.path.exists(_FONT):
        return _FONT
    alt = os.path.join(os.getcwd(), _FONT)
    return alt if os.path.exists(alt) else _FONT


def _clamp_onscreen(x: float, y: float, cur_w: float, cur_h: float) -> tuple[float, float]:
    """Giữ top-left sao cho clip CÒN ≥1px trong khung W×H.

    MoviePy 2.1.2 CompositeVideoClip.compose_mask VỠ (broadcast (h,0)) khi clip có MASK nằm HOÀN TOÀN
    ngoài khung: vùng overlap nền rộng 0px nhưng slice clip_mask ra âm. Cut-out luôn có mask → mọi
    slide-in/out đi qua trạng thái off-canvas sẽ crash. Clamp về sliver 1px (vô hình) khử triệt để mà
    KHÔNG đổi schema/motion preset — renderer an toàn với mọi keyframe shot_planner sinh ra (Stage 2).
    """
    return (min(max(x, 1.0 - cur_w), W - 1.0), min(max(y, 1.0 - cur_h), H - 1.0))


def _apply_fade(clip, layer: Layer):
    """CrossFadeIn/Out theo layer.fade_in/out (chỉ bọc khi >0 — with_effects([]) vô ích)."""
    from moviepy import vfx

    effects = []
    if layer.fade_in > 0:
        effects.append(vfx.CrossFadeIn(layer.fade_in))
    if layer.fade_out > 0:
        effects.append(vfx.CrossFadeOut(layer.fade_out))
    return clip.with_effects(effects) if effects else clip


def _load_rgba_clip(asset: str, base_w_px: int, base_h_px: int, *, mirror: bool = False):
    """ImageClip cut-out RGBA ở base size, GIỮ trong suốt (rủi ro #1).

    Cách chắc: nạp PIL→RGBA→numpy, ImageClip(arr, transparent=True) dùng kênh alpha làm mask. Nếu
    transparent=True không ăn (mask trắng đặc → mất nền trong suốt) thì tách thủ công: rgb + mask alpha.
    mirror=True: lật ngang (np.fliplr) để người dẫn quay mặt đối diện nội dung.
    """
    from moviepy import ImageClip

    arr = np.array(Image.open(asset).convert("RGBA"))
    if mirror:
        arr = np.ascontiguousarray(np.fliplr(arr))
    try:
        clip = ImageClip(arr, transparent=True)
        if clip.mask is None:   # transparent=True không tạo mask → tách tay
            raise ValueError("no mask")
    except Exception as exc:  # noqa: BLE001 — fallback tách mask alpha (an toàn cho mọi build MoviePy)
        logger.info(f"[compositor] RGBA transparent=True không ăn → tách mask tay ({str(exc)[:60]})")
        rgb = ImageClip(arr[:, :, :3])
        mask = ImageClip(arr[:, :, 3].astype("float64") / 255.0, is_mask=True)
        clip = rgb.with_mask(mask)
    return clip.resized((base_w_px, base_h_px))


def _clip_dur(layer: Layer, shot_dur: float) -> float:
    """Thời lượng hiển thị layer: layer.end>0 → TẮT sau end giây (glitch-flash); else tới hết shot."""
    end = layer.end if layer.end > 0 else shot_dur
    return max(0.1, min(shot_dur, end) - layer.start)


def _fullbleed_layer(layer: Layer, shot_dur: float):
    """Layer phủ KÍN khung (fx glitch/tv_static): cover W×H + center + fade. KHÔNG base_h/keyframe scale."""
    from moviepy import ImageClip

    clip_dur = _clip_dur(layer, shot_dur)
    with Image.open(layer.asset) as pil:
        cover = max(W / pil.width, H / pil.height)
    clip = ImageClip(layer.asset).with_duration(clip_dur).resized(cover).with_position("center")
    if layer.start > 0:
        clip = clip.with_start(layer.start)
    return _apply_fade(clip, layer)


def _img_layer(layer: Layer, shot_dur: float):
    """Layer content/presenter/fx (ảnh): base size theo base_h, scale+pos động theo Keyframe.

    fullbleed=True (fx phủ khung) → cover W×H. Còn lại: Keyframe tính theo THỜI GIAN CLIP-LOCAL (0-based từ
    lúc layer xuất hiện = layer.start) — khớp đồng hồ MoviePy: with_start dời clip, lambda nhận t clip-local.
    """
    if layer.fullbleed:
        return _fullbleed_layer(layer, shot_dur)
    clip_dur = _clip_dur(layer, shot_dur)
    with Image.open(layer.asset) as pil:   # đóng handle ngay (Windows lock-safe) — chỉ đọc size
        orig_w, orig_h = pil.size
    base_h_px = max(1, int(layer.base_h * H))
    base_w_px = max(1, int(base_h_px * orig_w / orig_h))

    kfs = layer.keyframes
    scales = [kf.scale for kf in kfs]
    # FAST-PATH: scale CỐ ĐỊNH (static/slide_*/static-anchor — đa số shot) → BAKE size 1 lần, BỎ resized(lambda)
    # → khử resample LANCZOS ×2 (RGB+mask) MỖI FRAME (~200 lần/shot vô ích). Chỉ pop_in/zoom mới resize động.
    if not scales or all(abs(s - scales[0]) < 1e-6 for s in scales):
        s_const = scales[0] if scales else 1.0
        cur_w = max(1, int(round(base_w_px * s_const)))
        cur_h = max(1, int(round(base_h_px * s_const)))
        clip = _load_rgba_clip(layer.asset, cur_w, cur_h, mirror=layer.mirror).with_duration(clip_dur)
        cxs = [kf.cx for kf in kfs]
        cys = [kf.cy for kf in kfs]
        pos_static = (not kfs or (all(abs(c - cxs[0]) < 1e-6 for c in cxs)
                                  and all(abs(c - cys[0]) < 1e-6 for c in cys))) and layer.shake <= 0
        if pos_static:   # cả scale lẫn vị trí cố định → tuple tĩnh (MoviePy khỏi gọi lambda mỗi frame)
            cx0, cy0 = (cxs[0] if cxs else 0.5), (cys[0] if cys else 0.5)
            clip = clip.with_position(_clamp_onscreen(cx0 * W - cur_w / 2.0, cy0 * H - cur_h / 2.0, cur_w, cur_h))
        else:            # scale cố định nhưng VỊ TRÍ đổi (slide) → pos lambda, size đã bake (cur_w/h cố định)
            def _pos(t, l=layer, cw=cur_w, ch=cur_h):
                cx, cy, _sc = sample(l, t)
                sx, sy = shake_offset(l.shake, t)
                return _clamp_onscreen(cx * W - cw / 2.0 + sx, cy * H - ch / 2.0 + sy, cw, ch)
            clip = clip.with_position(_pos)
    else:
        # DYNAMIC scale (pop_in/zoom): resize động + pos động (cur size = base*sc theo t).
        clip = _load_rgba_clip(layer.asset, base_w_px, base_h_px, mirror=layer.mirror).with_duration(clip_dur)
        clip = clip.resized(lambda t, l=layer: max(0.02, sample(l, t)[2]))

        def _pos(t, l=layer, bw=base_w_px, bh=base_h_px):
            cx, cy, sc = sample(l, t)
            sx, sy = shake_offset(l.shake, t)
            cur_w, cur_h = bw * sc, bh * sc
            return _clamp_onscreen(cx * W - cur_w / 2.0 + sx, cy * H - cur_h / 2.0 + sy, cur_w, cur_h)

        clip = clip.with_position(_pos)

    if layer.start > 0:
        clip = clip.with_start(layer.start)
    return _apply_fade(clip, layer)


def _bg_layer(layer: Layer, shot_dur: float):
    """Layer nền: không asset → ColorClip kem; có asset → ImageClip cover kín W×H (CompositeVideoClip crop)."""
    from moviepy import ColorClip, ImageClip

    if layer.asset and os.path.exists(layer.asset):
        with Image.open(layer.asset) as pil:
            cover = max(W / pil.width, H / pil.height)
        return (ImageClip(layer.asset).with_duration(shot_dur)
                .resized(cover).with_position("center"))
    return ColorClip(size=(W, H), color=_CREAM).with_duration(shot_dur)


def _text_layer(layer: Layer, shot_dur: float):
    """Layer chữ (TextClip): font dự án + viền đen dày (style doodle/tech). base_h = cỡ chữ theo fraction H.

    Stage 0: vị trí theo keyframe (tâm), KHÔNG scale chữ (TextClip resize động dễ vỡ — để Stage 4 lo
    pop chữ như caption). margin chừa DẤU tiếng Việt (Ố/Ờ/Ậ) khỏi bị cắt đỉnh — bài học rv9.
    """
    from moviepy import TextClip

    clip_dur = max(0.1, shot_dur - layer.start)
    fsize = max(12, int(layer.base_h * H))
    color = _TEXT_COLOR.get(layer.text_style, _TEXT_COLOR["doodle"])
    clip = TextClip(
        font=_font_path(), text=layer.text, font_size=fsize, color=color,
        stroke_color="black", stroke_width=max(2, fsize // 18), method="label", margin=(8, 16),
    ).with_duration(clip_dur)
    tw, th = clip.size

    def _pos(t, l=layer, tw=tw, th=th):
        cx, cy, _sc = sample(l, t)
        sx, sy = shake_offset(l.shake, t)
        return _clamp_onscreen(cx * W - tw / 2.0 + sx, cy * H - th / 2.0 + sy, tw, th)

    clip = clip.with_position(_pos)
    if layer.start > 0:
        clip = clip.with_start(layer.start)
    return _apply_fade(clip, layer)


def render_shot(shot: Shot):
    """Ghép các Layer của 1 Shot → CompositeVideoClip(1920×1080). Mỗi Layer 1 clip ĐỘC LẬP (KHÔNG flatten).

    - Thứ tự `shot.layers` = z-index (đầu = dưới cùng); layer kind=bg nên đứng đầu.
    - FAIL-SOFT per-layer: 1 layer lỗi (asset thiếu/cut-out hỏng) → BỎ QUA + log, KHÔNG làm vỡ shot.
      Hết clip → ColorClip kem (không bao giờ trả màn đen).
    - Clip trả về mang `.lf_sources` (rỗng ở Stage 0; fx/video layer các stage sau push VideoFileClip
      reader vào đây để render._render_beat_clip đóng trong finally — chống rò handle).
    """
    from moviepy import ColorClip, CompositeVideoClip

    clips = []
    lf_sources = []
    for layer in shot.layers:
        try:
            if layer.kind == "bg":
                c = _bg_layer(layer, shot.duration)
            elif layer.kind == "text":
                c = _text_layer(layer, shot.duration)
            elif layer.kind in ("content", "presenter", "fx"):
                c = _img_layer(layer, shot.duration)
            else:
                logger.warning(f"[compositor] layer kind lạ '{layer.kind}' → bỏ qua")
                continue
        except Exception as exc:  # noqa: BLE001 — fail-soft per-layer (asset thiếu/cut-out hỏng)
            logger.warning(f"[compositor] layer '{layer.kind}' lỗi → bỏ qua: {str(exc)[:140]}")
            continue
        src = getattr(c, "lf_source", None)
        if src is not None:
            lf_sources.append(src)
        clips.append(c)

    if not clips:
        out = ColorClip(size=(W, H), color=_CREAM).with_duration(shot.duration)
    else:
        out = CompositeVideoClip(clips, size=(W, H)).with_duration(shot.duration)
    out.lf_sources = lf_sources
    return out
