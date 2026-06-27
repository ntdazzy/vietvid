"""shot_builder.py — DỊCH TẤT ĐỊNH ShotSpec (+asset đã resolve) → scene_schema.Shot.

ĐÂY là nơi DUY NHẤT toạ độ/z-index/keyframe xuất hiện — sinh từ ENUM của đạo diễn qua bảng tra +
motion_keyframes + presenter_layer, KHÔNG từ LLM. Ép thứ tự lớp [bg, content/fx, presenter, text] = z-index
(diệt lỗi "người dẫn nằm sau nền"). Xử lý blank-content (phóng người dẫn / placeholder). build_fallback_shot
= look doodle_cutout an toàn (cam kết "không tệ hơn bây giờ").

KHÔNG gọi LLM, KHÔNG mạng (asset đã resolve sẵn). Ranh giới rõ cho review.
"""

from __future__ import annotations

from core.logger import logger
from video_engine.long_narrative.images import character_library as clib
from video_engine.long_narrative.presenter import presenter_layer
from video_engine.long_narrative.scene_schema import Keyframe, Layer, Shot, motion_keyframes

# Chất liệu → chiều cao base. CAP để nội dung ở DẢI GIỮA (anchor center cy≈0.46) KHÔNG đụng tiêu đề
# (trên ~0.12) lẫn phụ đề (dưới ~0.82): base_h 0.60 → spans 0.16-0.76. Trước đây map/diagram 0.78 = tràn.
_KIND_BASE_H = {"real_photo": 0.56, "logo": 0.42, "screenshot": 0.58, "map": 0.60, "diagram": 0.60,
                "meme": 0.56, "doodle": 0.60, "terminal": 0.62, "countryball": 0.46}
_FX_KINDS = {"glitch", "tv_static"}
_PLACEHOLDER_POSES = ("think_chin", "sideeye_suspect")   # lấp khi content rỗng (mặt-meme kho mới)
# Cut-out NGƯỜI/VẬT (bán-thân hay bị cắt ngang ngực) → GROUND cạnh-dưới sát đáy như người dẫn (hết "lửng
# giữa khung" founder báo). Chừa đáy 0.18 (CAO hơn presenter 0.12) để KHÔNG đụng phụ đề (CAPTION_Y≈0.82).
# logo/diagram/screenshot/map GIỮ center (chúng là đồ-hoạ, không phải nhân vật cắt).
_CONTENT_BOTTOM = 0.18
_GROUND_KINDS = {"doodle", "meme", "countryball", "real_photo", "terminal"}

# Lật mặt người dẫn: gate sau cờ (mặc định TẮT ở Pha A — pose bất đối xứng dễ ngược chữ/tay).
_ENABLE_MIRROR = False
_NON_MIRROR_SAFE = {"chi_tay_man_hinh", "gio_mot_ngon_tay", "dem_ngon_tay", "chi_camera_ban", "chi_len_subscribe"}


def _content_keyframes(motion: str, anchor: str, dur: float):
    """motion enum → keyframes (shake = static + lắc qua Layer.shake)."""
    if motion == "shake":
        return motion_keyframes("static", anchor, dur), 14.0
    return motion_keyframes(motion, anchor, dur), 0.0


def _maybe_mirror(layer: Layer | None, presenter_side: str) -> None:
    """Bật lật mặt nếu được phép + pose an toàn (đối diện nội dung). Mặc định TẮT ở Pha A."""
    if not _ENABLE_MIRROR or layer is None or presenter_side != "left":
        return
    import os
    name = os.path.splitext(os.path.basename(layer.asset))[0]   # bỏ .png
    for suf in ("_bust", "_tight", "_cut"):                     # bỏ hậu-tố biến-thể (hết bóc-tên-sai)
        if name.endswith(suf):
            name = name[: -len(suf)]
    if name not in _NON_MIRROR_SAFE:
        layer.mirror = True


# Lưới icon_grid (nói số-nhiều/lan-rộng): 6 ô — 2 hàng GROUND thấp hơn (né tiêu đề trên, đỡ lửng).
_GRID_POS = [(0.28, 0.48), (0.50, 0.48), (0.72, 0.48), (0.28, 0.72), (0.50, 0.72), (0.72, 0.72)]


def _mk_presenter(spec, beat, duration, used, *, role, side):
    """Tạo presenter layer (override role/side theo layout) + lật mặt nếu cần. None nếu spec.presenter rỗng."""
    if not spec.presenter:
        return None
    pl = presenter_layer(beat, role, duration, side=side, used=used,
                         motion=spec.presenter.get("motion", "static"),
                         pose_hint=spec.presenter.get("pose_hint"))   # 6.1: pose theo hành động shot
    if pl:
        _maybe_mirror(pl, side)
    return pl


def _mk_content(content_asset, kind, motion, duration, *, base_h=None, anchor="center"):
    bh = base_h or _KIND_BASE_H.get(kind, 0.58)
    kf, shake = _content_keyframes(motion, anchor, duration)
    if kind in _GROUND_KINDS:        # cut-out người/vật → ÉP cy ground sát đáy (giữ cx/scale/timing motion)
        gcy = 1.0 - _CONTENT_BOTTOM - bh / 2.0
        kf = [Keyframe(k.t, k.cx, gcy, k.scale, k.ease) for k in kf]
    return Layer(kind="content", asset=content_asset, base_h=bh,
                 keyframes=kf, shake=shake, fade_in=(0.0 if motion != "static" else 0.2))


def _mk_text_layer(spec, duration: float):
    """Chữ TO per-shot từ spec.text{label} (≤24 ký tự — planner đặt THƯA ở shot chốt, ví dụ 'VÀO TRẬN').
    Dải GIỮA-TRÊN cy=0.32 → né callout cấp-beat (top CALLOUT_Y=104≈cy0.10) + phụ đề (đáy CAPTION_Y=885≈cy0.82).
    None nếu rỗng. (Trước đây build_shot RỚT trường này — planner tốn token mà người xem không thấy chữ.)"""
    lbl = (spec.text or {}).get("label") if isinstance(spec.text, dict) else None
    if not lbl:
        return None
    return Layer(kind="text", text=lbl, text_style="doodle", base_h=0.075, fade_in=0.2,
                 keyframes=[Keyframe(0, 0.5, 0.32, 1.0), Keyframe(duration, 0.5, 0.32, 1.0)])


def _finalize(layers: list, spec, duration: float) -> Shot:
    """Gắn chữ per-shot (nếu có) lên Z-TOP rồi trả Shot — DÙNG CHUNG mọi layout (hết rớt spec.text)."""
    tl = _mk_text_layer(spec, duration)
    if tl:
        layers.append(tl)
    return Shot(duration=duration, transition_in=spec.transition_in, layers=layers)


def build_shot(spec, duration: float, *, content_asset: str | None, bg_asset: str | None,
               beat, used=None) -> Shot:
    """1 ShotSpec → Shot, DISPATCH theo spec.layout (8 kiểu) để CHỐNG ĐƠN ĐIỆU (founder báo). Thứ tự
    lớp = z-index. Fail-soft. Bố cục an-toàn (presenter_corner) là mặc định."""
    layout = getattr(spec, "layout", "presenter_corner")
    kind = spec.content.get("kind", "doodle")
    has_fx = kind in _FX_KINDS
    motion = spec.content_motion
    # spec.text (label do planner đề xuất trong CÙNG JSON — 0 chi phí AI thêm) CỐ Ý không dựng ở đây:
    # render.py đã vẽ CHỮ cấp-beat (title LABEL_Y + callout CALLOUT_Y + sub chọn-lọc); thêm chữ per-shot
    # sẽ ĐÈ lên đó (bug "3 lớp tiêu đề chồng"). Chữ per-shot để Stage 4 (khi tách vùng riêng) — KHÔNG bỏ thầm.
    layers: list[Layer] = [Layer(kind="bg", asset=bg_asset or "")]   # z0: nền (rỗng → kem)

    # FULL-BLEED: cảnh/terminal phủ KÍN khung; người dẫn (nếu có, chỉ fullbleed_scene) tí ở góc.
    # (glitch_interstitial ĐÃ BỎ khỏi menu — colorbar 2s quá chói; glitch giờ CHỈ là FLASH transition 0.12s.)
    if has_fx or layout in ("fullbleed_scene", "terminal_fullbleed"):
        if content_asset:
            layers.append(Layer(kind=("fx" if has_fx else "content"), asset=content_asset, fullbleed=True,
                                fade_in=(0.12 if has_fx else 0.0), fade_out=(0.12 if has_fx else 0.0),
                                keyframes=motion_keyframes("static", "center", duration)))
        if content_asset and not has_fx and layout == "fullbleed_scene":
            pl = _mk_presenter(spec, beat, duration, used, role="accent", side=spec.presenter.get("side", "right") if spec.presenter else "right")
            if pl:
                layers.append(pl)
        return _finalize(layers, spec, duration)

    # ICON-GRID: lặp 1 icon nhiều ô (số-nhiều/lan-rộng) + người dẫn tí góc.
    if layout == "icon_grid" and content_asset:
        for i, (cx, cy) in enumerate(_GRID_POS):
            layers.append(Layer(kind="content", asset=content_asset, base_h=0.24, start=i * 0.06,
                                keyframes=[Keyframe(0, cx, cy, 0.01), Keyframe(0.18, cx, cy, 1.0),
                                           Keyframe(max(0.4, duration - i * 0.06), cx, cy, 1.0)]))
        pl = _mk_presenter(spec, beat, duration, used, role="accent", side="left")
        if pl:
            layers.append(pl)
        return _finalize(layers, spec, duration)

    # PRESENTER-HERO: người dẫn TO (độc thoại/chốt). XOAY side mỗi shot (center/trái/phải) để KHÔNG shot nào
    # GIỐNG shot nào (founder: 'toàn center-big y hệt'). content (nếu có) = ảnh tham chiếu nhỏ góc ĐỐI side.
    if layout == "presenter_hero":
        _HERO_SIDES = ("center", "left", "center", "right")
        vside = _HERO_SIDES[len(used or ()) % len(_HERO_SIDES)]
        if content_asset:   # content ở góc ĐỐI DIỆN side người dẫn (cân bố cục) — né callout giữa-top
            ccx = 0.78 if vside in ("center", "left") else 0.22
            layers.append(Layer(kind="content", asset=content_asset, base_h=0.22,
                                keyframes=[Keyframe(0, ccx, 0.30, 0.01), Keyframe(0.2, ccx, 0.30, 1.0),
                                           Keyframe(duration, ccx, 0.30, 1.0)]))
        pl = (_mk_presenter(spec, beat, duration, used, role="subject", side=vside)
              or presenter_layer(beat, "subject", duration, side=vside, used=used, motion="rise_in"))
        if pl:
            layers.append(pl)
        return _finalize(layers, spec, duration)

    # SIDE-BY-SIDE: content 1 bên + người dẫn bên kia (so sánh/đối thoại).
    if layout == "side_by_side" and content_asset:
        layers.append(_mk_content(content_asset, kind, motion, duration, base_h=0.50, anchor="beside_left"))
        pl = _mk_presenter(spec, beat, duration, used, role="reaction", side="right")
        if pl:
            layers.append(pl)
        return _finalize(layers, spec, duration)

    # OBJECT-CENTER: 1 vật/logo giữa, KHÔNG người dẫn (giới thiệu 1 thứ).
    if layout == "object_center" and content_asset:
        layers.append(_mk_content(content_asset, kind, motion, duration,
                                  base_h=min(0.5, _KIND_BASE_H.get(kind, 0.5))))
        return _finalize(layers, spec, duration)

    # PRESENTER-CORNER (mặc định): content giữa dải-giữa + người dẫn nhỏ góc; blank→subject/placeholder.
    if content_asset:
        layers.append(_mk_content(content_asset, kind, motion, duration))
    pl = None
    if spec.presenter:
        side = spec.presenter.get("side", "right")
        if content_asset and side == "center":
            side = "right"
        pl = _mk_presenter(spec, beat, duration, used,
                           role=("reaction" if content_asset else "subject"), side=side)
        if pl:
            layers.append(pl)
    if not content_asset and pl is None:    # blank → placeholder pose sẵn (chữ do render.py lo)
        for name in _PLACEHOLDER_POSES:
            ph = clib.pose_asset(name)
            if ph:
                layers.append(Layer(kind="content", asset=ph, base_h=0.6,
                                    keyframes=motion_keyframes("pop_in", "center", duration)))
                break
    return _finalize(layers, spec, duration)


# FALLBACK an toàn KHÔNG nằm ở đây: planner trả [] → visual.prepare_beat_assets rơi xuống nhánh
# doodle_cutout (look đã chứng minh, _compose_cutout_one + _scene_shot). Tái dùng code proven thay vì
# dựng fallback Shot riêng = cam kết "không tệ hơn bây giờ" với ít bề mặt lỗi nhất.


# ── orchestrate: list[ShotSpec] → list[Shot] (chuẩn-hoá thời lượng theo đoạn + resolve asset) ──
def build_shots_for_beat(specs: list, segments: list, beat, asset_dir: str, *,
                         source_urls=None, used=None) -> list[Shot]:
    """Resolve asset từng shot + chuẩn-hoá duration_weight KHÍT đúng đoạn _plan_segments → list[Shot].

    duration shot = seg_dur × weight / Σweight(trong đoạn) → tổng hình KHÍT giọng (chống vỡ nhịp).
    """
    import dataclasses
    import json
    import os

    from video_engine.long_narrative import asset_resolver

    # LƯU shot-plan đã chọn (soi đạo diễn QUYẾT gì — minh bạch + debug 'toàn 1 ảnh'). Fail-soft.
    try:
        os.makedirs(asset_dir, exist_ok=True)
        json.dump([dataclasses.asdict(s) for s in specs],
                  open(os.path.join(asset_dir, "shotplan.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
    except Exception:  # noqa: BLE001
        pass

    # nhóm theo đoạn + tính Σweight MỖI ĐOẠN 1 LẦN (không lặp/shot)
    by_seg: dict[int, list] = {}
    for s in specs:
        by_seg.setdefault(s.seg, []).append(s)
    wsum_by_seg = {seg: (sum(max(0.5, g.duration_weight) for g in grp) or 1.0)
                   for seg, grp in by_seg.items()}

    shots: list[Shot] = []
    for i, s in enumerate(specs):
        seg_dur = segments[min(s.seg, len(segments) - 1)][1]
        dur = max(1.0, seg_dur * max(0.5, s.duration_weight) / wsum_by_seg[s.seg])
        # resolve + build TRONG try → mọi lỗi cứng (makedirs/import) chỉ BỎ 1 shot, không vỡ cả beat
        try:
            content_asset = asset_resolver.resolve_content_asset(
                s.content, beat, asset_dir, idx=i, source_urls=source_urls, used=used)
            shot = build_shot(s, dur, content_asset=content_asset, bg_asset=None, beat=beat, used=used)
            # Stage 4: transition_in=glitch (trừ shot đầu) → FLASH glitch 0.12s mở đầu shot (z-top, tự tắt).
            if i > 0 and s.transition_in == "glitch":
                gpath = asset_resolver.make_glitch(asset_dir)
                if gpath:
                    shot.layers.append(Layer(kind="fx", asset=gpath, fullbleed=True, end=0.12, fade_out=0.06,
                                             keyframes=motion_keyframes("static", "center", dur)))
            shots.append(shot)
        except Exception as exc:  # noqa: BLE001 — 1 shot lỗi → bỏ shot đó, giữ phần còn lại
            logger.warning(f"[builder] shot {i} lỗi → bỏ: {str(exc)[:120]}")
    return shots
