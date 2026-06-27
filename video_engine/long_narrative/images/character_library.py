"""character_library.py — thư viện NHÂN VẬT DẪN cut-out cho visual_mode 'doodle_cutout'.

Đọc thư viện PNG gen-sẵn-1-lần (LONGFORM_CHARACTER_DIR/library) + chọn pose theo beat.context,
tách nền trắng → RGBA (scipy border-flood: bỏ trắng NỐI MÉP, GIỮ trắng TRONG như mắt/kính/răng;
rembg fallback). Tái dùng PNG — KHÔNG gen runtime mỗi video. Fail-soft → None (caller quay doodle).
"""

from __future__ import annotations

import os

from config.settings import settings
from core.logger import logger

_WHITE_THR = 236  # ngưỡng "gần trắng" để coi là nền

# context beat → MẶT-MEME ưu tiên (kho library_meme; lọc theo mặt CÓ THẬT). Founder 2026-06-21.
_CTX_POSES = {
    "normal":  ["point_content", "think_chin"],
    "hype":    ["hype_fistup", "laugh_tears", "point_content"],
    "joke":    ["troll_grin", "laugh_tears", "sideeye_suspect", "deadpan_bruh"],
    "climax":  ["shock_jawdrop", "hype_fistup", "galaxy_brain"],
    "whisper": ["sideeye_suspect", "think_chin", "rollsafe_temple"],
    "drama":   ["facepalm", "exhausted_soul", "shock_jawdrop", "this_is_fine"],
}
_FALLBACK = ["point_content", "think_chin"]
_EDGE_CLIPPED_POSES = {
    "explain_palm",
    "galaxy_brain",
    "hype_fistup",
    "rollsafe_temple",
    "shock_jawdrop",
    "think_chin",
}
_SAFE_LIBRARY_POSE = {
    "deadpan_bruh": "binh_thuong_dung_thang",
    "facepalm": "facepalm_1tay",
    "point_content": "gio_mot_ngon_tay",
    "sideeye_suspect": "nghi_ngo_nhuong_may",
    "explain_palm": "tay_ngua_giai_thich",
    "troll_grin": "nhech_mep_smug",
}
_NO_BUST_CROP_POSES = {
    "chi_camera_ban",
}

# 6.1 GỢI Ý POSE từ đạo diễn (khớp HÀNH ĐỘNG shot) → tên mặt-meme ưu tiên (any(k in tên)).
_POSE_HINT_KEYWORDS = {
    "point":     ["point_content", "cta_subscribe"],
    "celebrate": ["hype_fistup", "laugh_tears"],
    "shock":     ["shock_jawdrop"],
    "laugh":     ["laugh_tears", "troll_grin"],
    "think":     ["think_chin", "galaxy_brain"],
    "explain":   ["point_content", "think_chin"],
    "smug":      ["troll_grin", "sideeye_suspect"],
    "worry":     ["facepalm", "exhausted_soul", "this_is_fine", "sideeye_suspect"],
}

_MEME_SUBDIR = "library_meme"   # kho mặt-meme cut-out SẴN (RGBA, bán-thân) — ưu tiên hơn library/ raw.


def _char_root() -> str:
    return (settings.longform_character_dir or "storage/characters").strip()


def _lib_dir() -> str:
    return os.path.join(_char_root(), "library")


def _meme_dir() -> str:
    return os.path.join(_char_root(), _MEME_SUBDIR)


def _use_meme() -> bool:
    """Có kho meme cut-out sẵn (≥1 PNG) → dùng nó thay kho pose cũ."""
    d = _meme_dir()
    return os.path.isdir(d) and any(
        f.lower().endswith(".png") and not f.startswith("_") for f in os.listdir(d))


def _active_dir() -> str:
    return _meme_dir() if _use_meme() else _lib_dir()


def available_poses() -> set[str]:
    d = _active_dir()
    if not os.path.isdir(d):
        return set()
    return {f[:-4] for f in os.listdir(d) if f.lower().endswith(".png") and not f.startswith("_")}


def pose_asset(name: str) -> str | None:
    """PNG người dẫn dùng được NGAY: kho meme (RGBA cut-out sẵn) trả thẳng; kho cũ → cutout_pose_bust."""
    safe_name = _SAFE_LIBRARY_POSE.get(name)
    if safe_name:
        safe = cutout_pose_bust(safe_name)
        if safe:
            return safe
    if _use_meme():
        p = os.path.join(_meme_dir(), f"{name}.png")
        return p if os.path.exists(p) else None
    return cutout_pose_bust(name)


def pick_pose(beat, used: set | None = None, pose_hint: str | None = None) -> str | None:
    """Chọn 1 pose cho beat theo context (+ beat_id biến thiên, chống lặp qua `used`).
    pose_hint (6.1): gợi ý HÀNH ĐỘNG từ đạo diễn (point/celebrate/shock/laugh/think/explain...) → ưu tiên
    pose khớp tên trước context. FALLBACK an toàn về pose CÓ THẬT — KHÔNG bao giờ trả tên không tồn tại."""
    avail = available_poses()
    if not avail:
        return None
    cands = []
    if pose_hint:   # 6.1: ưu tiên pose khớp gợi ý hành động (vd 'point' → chi_tay_man_hinh)
        kws = _POSE_HINT_KEYWORDS.get(pose_hint.strip().lower(), [])
        cands = [p for p in sorted(avail) if any(k in p for k in kws)]
    if not cands:
        ctx = (getattr(beat, "context", "normal") or "normal").strip().lower()
        cands = [p for p in _CTX_POSES.get(ctx, []) if p in avail]
    cands = cands or [p for p in _FALLBACK if p in avail] or sorted(avail)
    clean = [p for p in cands if p not in _EDGE_CLIPPED_POSES]
    cands = clean or [p for p in _SAFE_LIBRARY_POSE if p in avail]
    used = used if used is not None else set()
    fresh = [p for p in cands if p not in used]
    pool = fresh or cands
    pick = pool[(getattr(beat, "beat_id", 0) or 0) % len(pool)]
    used.add(pick)
    return pick


def cutout_pose(name: str) -> str | None:
    """Tách nền pose `name` → RGBA PNG (cache theo mtime nguồn). None nếu không có/đều lỗi."""
    src = os.path.join(_lib_dir(), f"{name}.png")
    if not os.path.exists(src):
        return None
    cdir = os.path.join(_lib_dir(), "_cutout")
    os.makedirs(cdir, exist_ok=True)
    out = os.path.join(cdir, f"{name}.png")
    if os.path.exists(out) and os.path.getmtime(out) >= os.path.getmtime(src):
        return out
    from PIL import Image
    try:
        _cutout_white(Image.open(src).convert("RGBA")).save(out)
        return out
    except Exception as exc:  # noqa: BLE001 — fallback rembg
        logger.warning(f"[char-lib] flood cutout '{name}' lỗi → rembg: {str(exc)[:120]}")
        try:
            from rembg import remove
            remove(Image.open(src).convert("RGBA")).save(out)
            return out
        except Exception as exc2:  # noqa: BLE001
            logger.warning(f"[char-lib] rembg '{name}' lỗi: {str(exc2)[:120]}")
            return None


def cutout_pose_tight(name: str, pad: int = 10) -> str | None:
    """cutout_pose(name) RỒI crop về bbox alpha (+pad) → PNG KHÍT (cache _cutout/{name}_tight.png).

    Tách RIÊNG cutout_pose (KHÔNG đổi output cũ mà cutout_compose/doodle_cutout đang dùng). Khung khít
    để base_h map đúng CHIỀU CAO NHÂN VẬT → presenter.py ground chân vào đáy khung chuẩn (không lơ lửng
    do biên trong suốt thừa của ảnh thô 1408×768). Fail-soft → cut-out chưa-crop (vẫn dùng được)."""
    import numpy as np
    from PIL import Image

    src = cutout_pose(name)
    if not src:
        return None
    out = os.path.join(_lib_dir(), "_cutout", f"{name}_tight.png")
    if os.path.exists(out) and os.path.getmtime(out) >= os.path.getmtime(src):
        return out
    try:
        arr = np.array(Image.open(src).convert("RGBA"))
        ys, xs = np.where(arr[:, :, 3] > 10)
        if not len(xs):
            return src
        x0, y0 = max(0, int(xs.min()) - pad), max(0, int(ys.min()) - pad)
        x1, y1 = min(arr.shape[1], int(xs.max()) + pad), min(arr.shape[0], int(ys.max()) + pad)
        Image.fromarray(arr[y0:y1, x0:x1]).save(out)
        return out
    except Exception as exc:  # noqa: BLE001 — fail-soft: dùng cut-out thường
        logger.warning(f"[char-lib] tight-crop '{name}' lỗi → cut-out thường: {str(exc)[:100]}")
        return src


def cutout_pose_bust(name: str, frac: float = 0.82) -> str | None:
    """cutout_pose_tight rồi CROP còn BÁN THÂN (top `frac` chiều cao bbox = đầu→bụng, BỎ chân) — đúng nét
    kênh (nhân vật chỉ vẽ tới bụng). Cache _cutout/{name}_bust.png. Fail-soft → cut-out đầy đủ."""
    import numpy as np
    from PIL import Image

    src = cutout_pose_tight(name)
    if not src:
        return None
    out = os.path.join(_lib_dir(), "_cutout", f"{name}_bust.png")
    try:
        arr = np.array(Image.open(src).convert("RGBA"))
        h = arr.shape[0]
        crop_h = h if name in _NO_BUST_CROP_POSES else max(1, int(h * frac))
        bust = Image.fromarray(arr[:crop_h])
        bottom_pad = max(18, int(bust.height * 0.08))
        framed = Image.new("RGBA", (bust.width, bust.height + bottom_pad), (0, 0, 0, 0))
        framed.alpha_composite(bust, (0, 0))
        framed.save(out)
        return out
    except Exception as exc:  # noqa: BLE001 — fail-soft: dùng cut-out đầy đủ
        logger.warning(f"[char-lib] bust-crop '{name}' lỗi → cut-out đầy đủ: {str(exc)[:100]}")
        return src


def cutout_subject(src: str, out: str) -> str | None:
    """Tách nền ảnh SUBJECT doodle_cutout (gen với nền trắng) → RGBA. White-flood trước; nếu nền
    KHÔNG trắng (flood bỏ <4% pixel) → rembg (segment foreground). None nếu cả hai lỗi."""
    if not src or not os.path.exists(src):
        return None
    from PIL import Image
    import numpy as np
    try:
        r = _tight_rgba(_drop_border_strokes(_cutout_white(Image.open(src).convert("RGBA"))))
        if (np.array(r)[:, :, 3] == 0).mean() < 0.04:   # flood bỏ quá ít = nền không trắng
            raise ValueError("flood không bắt được nền (không trắng)")
        r.save(out)
        return out
    except Exception as exc:  # noqa: BLE001 — fallback rembg cho nền lạ
        logger.warning(f"[char-lib] subject white-flood fail → rembg: {str(exc)[:100]}")
        try:
            from rembg import remove
            _tight_rgba(_drop_border_strokes(remove(Image.open(src).convert("RGBA")))).save(out)
            return out
        except Exception as exc2:  # noqa: BLE001
            logger.warning(f"[char-lib] subject rembg lỗi: {str(exc2)[:100]}")
    return None


def _drop_border_strokes(img):
    """Drop long frame/grid strokes while keeping the central subject."""
    try:
        import numpy as np
        from PIL import Image

        arr = np.array(img.convert("RGBA"))
        alpha = arr[:, :, 3]
        ys, xs = np.where(alpha > 10)
        if not len(xs):
            return img
        h, w = alpha.shape
        x0, x1 = int(xs.min()), int(xs.max())
        y0, y1 = int(ys.min()), int(ys.max())
        bw, bh = max(1, x1 - x0 + 1), max(1, y1 - y0 + 1)
        dark = (arr[:, :, :3].max(axis=2) < 80) & (alpha > 10)
        rm = np.zeros_like(alpha, dtype=bool)
        long_x = max(80, int(w * 0.35))
        long_y = max(80, int(h * 0.35))
        for y in range(y0, y1 + 1):
            cols = np.where(dark[y])[0]
            if len(cols) and (cols.max() - cols.min() + 1) >= long_x:
                rm[y] = True
        for x in range(x0, x1 + 1):
            rows = np.where(dark[:, x])[0]
            if len(rows) and (rows.max() - rows.min() + 1) >= long_y:
                rm[:, x] = True
        yy, xx = np.indices(alpha.shape)
        edge = (
            (xx < x0 + int(bw * 0.18)) |
            (xx > x1 - int(bw * 0.18)) |
            (yy < y0 + int(bh * 0.18)) |
            (yy > y1 - int(bh * 0.18))
        )
        arr[:, :, 3] = np.where(rm & edge, 0, alpha).astype(arr.dtype)
        return Image.fromarray(arr, "RGBA")
    except Exception:
        return img


def _tight_rgba(img, pad: int = 12):
    try:
        import numpy as np
        from PIL import Image

        arr = np.array(img.convert("RGBA"))
        ys, xs = np.where(arr[:, :, 3] > 10)
        if not len(xs):
            return img
        x0, y0 = max(0, int(xs.min()) - pad), max(0, int(ys.min()) - pad)
        x1, y1 = min(arr.shape[1], int(xs.max()) + pad), min(arr.shape[0], int(ys.max()) + pad)
        return Image.fromarray(arr[y0:y1, x0:x1], "RGBA")
    except Exception:
        return img


def _cutout_white(img):
    """Bỏ nền trắng NỐI MÉP (giữ trắng trong) bằng connected-components (scipy)."""
    import numpy as np
    from scipy import ndimage

    arr = np.array(img)
    near_white = (arr[:, :, :3] >= _WHITE_THR).all(axis=2)
    lbl, _ = ndimage.label(near_white)
    border = set(lbl[0, :].tolist()) | set(lbl[-1, :].tolist()) | set(lbl[:, 0].tolist()) | set(lbl[:, -1].tolist())
    border.discard(0)
    if border:
        bg = np.isin(lbl, list(border))
        arr[:, :, 3] = np.where(bg, 0, 255).astype(arr.dtype)
    from PIL import Image
    return Image.fromarray(arr, "RGBA")
