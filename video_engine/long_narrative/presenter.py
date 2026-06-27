"""presenter.py — dàn LỚP NGƯỜI DẪN cho engine đa-lớp (Stage 1).

Tái tạo cách kênh Vui Vẻ/Lóng đặt nhân vật dẫn (phân tích từ scene_all_*.jpg):
  - ĐỔI biểu cảm theo context beat (pick_pose: 30 pose có sẵn).
  - CO GIÃN theo VAI: chủ thể (to, giữa) / phản ứng (vừa, góc) / điểm xuyết (nhỏ, góc).
  - LUÔN ĐỨNG CHẠM ĐÁY khung (ground chân) — KHÔNG lơ lửng giữa khung (lỗi bố cục Stage 0).
  - Đứng LỆCH một bên (side) để đối diện nội dung; vào mềm (static/rise/pop).

shot_planner (Stage 2) chỉ cần xin (role, side); module này lo pose + scale + VỊ TRÍ HỢP LÝ.
Fail-soft → None (caller bỏ lớp người dẫn, shot vẫn dựng được).
"""

from __future__ import annotations

from core.logger import logger
from video_engine.long_narrative.images import character_library as clib
from video_engine.long_narrative.scene_schema import Keyframe, Layer

# Vai → chiều cao base (fraction H). Chủ thể chiếm sân; phản ứng vừa ở góc; điểm xuyết nhỏ.
# Người dẫn NHỎ lại (founder 2026-06-21 'chiếm nhiều quá'): mặt-meme bán-thân, đa số ghép cạnh B-roll.
_ROLE_BASE_H = {"subject": 0.42, "reaction": 0.32, "accent": 0.22}
# cx theo (role, side): chủ thể giữa; phản ứng/điểm xuyết lệch về góc trái/phải (đối diện nội dung).
_ROLE_CX = {
    "subject": {"left": 0.42, "right": 0.58, "center": 0.50},
    "reaction": {"left": 0.20, "right": 0.80, "center": 0.50},
    "accent": {"left": 0.12, "right": 0.88, "center": 0.50},
}
_BOTTOM = 0.06   # DÍ SÁT đáy (founder 2026-06-21 'hết khoảng trống dưới'); người dẫn nhỏ+lệch góc nên ít đụng phụ đề


def _ground_cy(base_h: float) -> float:
    """cy (tâm) để ĐÁY cut-out (chân) chạm gần đáy khung: cy = 1 - bottom - base_h/2.

    Vị trí tính TỪ chiều cao pose (không dùng anchor cy cố định) → mọi vai đều ground chân chuẩn,
    không lơ lửng. (Anchor cy tĩnh không ground được vì chiều cao đổi theo vai.)"""
    return 1.0 - _BOTTOM - base_h / 2.0


def _motion_kf(motion: str, cx: float, cy: float, dur: float) -> list[Keyframe]:
    """Keyframe tại vị trí GROUND (cx,cy). Không qua motion_keyframes(anchor) vì cy phụ thuộc base_h."""
    if motion == "pop_in":
        return [Keyframe(0, cx, cy, 0.01), Keyframe(0.16, cx, cy, 1.10),
                Keyframe(0.26, cx, cy, 1.0), Keyframe(dur, cx, cy, 1.0)]
    if motion == "rise_in":   # trồi lên từ dưới — vào mềm, hợp người dẫn
        return [Keyframe(0, cx, cy + 0.10, 1.0), Keyframe(0.35, cx, cy, 1.0, "ease_out"),
                Keyframe(dur, cx, cy, 1.0)]
    return [Keyframe(0, cx, cy, 1.0), Keyframe(dur, cx, cy, 1.0)]   # static (mặc định)


def presenter_layer(beat, role: str, shot_dur: float, *, side: str = "right",
                    used: set | None = None, motion: str = "static",
                    fade_in: float = 0.2, pose_hint: str | None = None) -> Layer | None:
    """1 Layer người dẫn: pose theo context(beat) + scale theo role + GROUND chân + entrance mềm.

    role: subject (chủ thể, to, giữa) | reaction (phản ứng, vừa, góc) | accent (điểm xuyết, nhỏ, góc).
    side: left|right|center — đứng bên nào (shot_planner đặt đối diện nội dung).
    beat: duck-typed (cần .context, .beat_id) — pick_pose chọn biểu cảm + chống lặp qua `used`.
    """
    name = clib.pick_pose(beat, used=used, pose_hint=pose_hint)
    if not name:
        return None
    asset = clib.pose_asset(name)   # kho meme (cut-out sẵn) hoặc bust kho cũ — đúng nét kênh
    if not asset:
        return None
    base_h = _ROLE_BASE_H.get(role, _ROLE_BASE_H["reaction"])
    cx = _ROLE_CX.get(role, _ROLE_CX["reaction"]).get(side, 0.50)
    cy = _ground_cy(base_h)
    logger.info(f"[presenter] pose={name} role={role} side={side} base_h={base_h} pos=({cx:.2f},{cy:.2f})")
    return Layer(kind="presenter", asset=asset, base_h=base_h, fade_in=fade_in,
                 keyframes=_motion_kf(motion, cx, cy, shot_dur))
