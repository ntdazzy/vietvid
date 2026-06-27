"""scene_schema.py — mô hình SCENE đa-lớp cho engine auto-edit kiểu Vui Vẻ (Stage 0).

Khác hẳn 'compose_beat_scene' (nung mọi thứ vào 1 PNG tĩnh): ở đây 1 Shot = nhiều Layer độc lập,
mỗi Layer có chuỗi Keyframe (vị-trí + scale theo thời gian) → compositor.py ghép LIVE bằng
CompositeVideoClip, từng cut-out di chuyển/pop/zoom riêng (slide-in ngựa, pop-in lính...).

KHÔNG đụng script_schema.py (Beat/Block giữ nguyên). Shot-plan sinh runtime (Stage 2: shot_planner).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

W, H = 1920, 1080

# anchor → tâm (cx, cy) theo fraction của W/H. Vai trò scale: chủ thể ~0.7 / phản ứng ~0.4 / điểm xuyết ~0.2.
ANCHORS: dict[str, tuple[float, float]] = {
    "center": (0.50, 0.46),
    "under_content": (0.50, 0.72),
    "corner_bl": (0.15, 0.80),
    "corner_br": (0.85, 0.80),
    "beside_left": (0.27, 0.50),
    "beside_right": (0.73, 0.50),
    "top": (0.50, 0.12),
}


@dataclass
class Keyframe:
    t: float                 # giây trong shot
    cx: float                # tâm X (fraction 0-1 của W)
    cy: float                # tâm Y (fraction 0-1 của H)
    scale: float = 1.0       # nhân base size
    ease: str = "ease_out"   # linear | ease_out


@dataclass
class Layer:
    kind: str                                  # bg | content | presenter | text | fx
    asset: str = ""                            # path PNG (RGBA cho cut-out); rỗng + kind=bg → nền màu kem
    text: str = ""                             # cho kind=text
    text_style: str = "doodle"                 # doodle | tech (preset font, dùng từ Stage 4)
    base_h: float = 0.5                        # chiều cao base = fraction của H (vai trò)
    keyframes: list[Keyframe] = field(default_factory=list)
    start: float = 0.0                         # xuất hiện sau `start` giây (cho pop_sequence)
    end: float = 0.0                           # 0 = tới hết shot; >0 = TẮT sau `end` giây (glitch-flash transition)
    fade_in: float = 0.0                       # CrossFadeIn (giây)
    fade_out: float = 0.0                      # CrossFadeOut (giây)
    shake: float = 0.0                         # biên lắc ngang (px), 0 = tắt
    fullbleed: bool = False                    # phủ kín khung (bg/fx)
    mirror: bool = False                       # lật ngang (np.fliplr) — người dẫn quay mặt đối diện nội dung


@dataclass
class Shot:
    duration: float
    transition_in: str = "cut"                 # cut | fade | glitch (glitch dùng từ Stage 5)
    layers: list[Layer] = field(default_factory=list)


# ── easing ───────────────────────────────────────────────────────────────
def _ease(name: str, p: float) -> float:
    p = max(0.0, min(1.0, p))
    if name == "linear":
        return p
    return 1.0 - (1.0 - p) * (1.0 - p)   # ease_out (mặc định) — chậm dần, tự nhiên


def sample(layer: Layer, t: float) -> tuple[float, float, float]:
    """Nội suy (cx, cy, scale) của layer tại thời điểm t (giây trong shot)."""
    kfs = layer.keyframes
    if not kfs:
        return (0.5, 0.5, 1.0)
    if t <= kfs[0].t:
        k = kfs[0]
        return (k.cx, k.cy, k.scale)
    if t >= kfs[-1].t:
        k = kfs[-1]
        return (k.cx, k.cy, k.scale)
    for i in range(len(kfs) - 1):
        a, b = kfs[i], kfs[i + 1]
        if a.t <= t <= b.t:
            p = (t - a.t) / (b.t - a.t) if b.t > a.t else 1.0
            e = _ease(b.ease, p)
            return (a.cx + (b.cx - a.cx) * e, a.cy + (b.cy - a.cy) * e, a.scale + (b.scale - a.scale) * e)
    k = kfs[-1]
    return (k.cx, k.cy, k.scale)


# ── MOTION presets: sinh sẵn keyframes cho 1 anchor (tránh AI phải tự nghĩ toạ độ) ──
def motion_keyframes(name: str, anchor: str, dur: float) -> list[Keyframe]:
    cx, cy = ANCHORS.get(anchor, ANCHORS["center"])
    if name == "slide_in_right":
        return [Keyframe(0, 1.30, cy, 1.0), Keyframe(0.45, cx, cy, 1.0), Keyframe(dur, cx, cy, 1.0)]
    if name == "slide_in_left":
        return [Keyframe(0, -0.30, cy, 1.0), Keyframe(0.45, cx, cy, 1.0), Keyframe(dur, cx, cy, 1.0)]
    if name == "slide_out":
        return [Keyframe(0, cx, cy, 1.0), Keyframe(max(0.4, dur - 0.4), cx, cy, 1.0), Keyframe(dur, 1.30, cy, 1.0)]
    if name == "pop_in":
        return [Keyframe(0, cx, cy, 0.01), Keyframe(0.16, cx, cy, 1.10), Keyframe(0.26, cx, cy, 1.0),
                Keyframe(dur, cx, cy, 1.0)]
    if name == "zoom_in":
        return [Keyframe(0, cx, cy, 1.0), Keyframe(dur, cx, cy, 1.07, "linear")]
    if name == "zoom_out":
        return [Keyframe(0, cx, cy, 1.07), Keyframe(dur, cx, cy, 1.0, "linear")]
    # static (mặc định)
    return [Keyframe(0, cx, cy, 1.0), Keyframe(dur, cx, cy, 1.0)]


def shake_offset(amp: float, t: float) -> tuple[float, float]:
    """Lắc nhẹ (cut-out 'rung' lúc nhấn). amp=0 → (0,0)."""
    if amp <= 0:
        return (0.0, 0.0)
    return (amp * math.sin(2 * math.pi * 3.0 * t), 0.5 * amp * math.sin(2 * math.pi * 2.3 * t))
