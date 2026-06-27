"""doodle_lib.py — kho nháp doodle tái dùng (5.2).

Kho storage/doodle_lib hiện CHƯA phải final, nên đang bị khóa tự động dùng.
Không dùng ảnh ở đây cho output video hoặc train LoRA cho đến khi founder duyệt lại.

QUY TRÌNH FOUNDER CURATE (review: ĐỪNG tự chốt):
  1. Chạy scripts gen candidate (storage/tts_ab/gen_doodle_lib.py) → ra nhiều biến thể/vật.
  2. Founder CHỌN ảnh đẹp → đặt vào storage/doodle_lib/<slug>.png (ảnh RGBA cutout, nền trong).
  3. Thêm 1 dòng vào storage/doodle_lib/manifest.json: {"file":"<slug>.png","keywords":["cúp","trophy",...]}.
Khi kho bị khóa / trống / không khớp → None → caller sinh ảnh mới.
"""

from __future__ import annotations

import json
import os

from core.logger import logger

_LIB_DIR = os.path.join("storage", "doodle_lib")
_MANIFEST = os.path.join(_LIB_DIR, "manifest.json")
_AUTO_REUSE_ENABLED = False  # Kho hien tai chua duoc founder chot final nen khong tu chen vao video.
_cache: list | None = None


def _load() -> list:
    global _cache
    if _cache is not None:
        return _cache
    _cache = []
    if os.path.exists(_MANIFEST):
        try:
            for e in json.load(open(_MANIFEST, encoding="utf-8")):
                f = os.path.join(_LIB_DIR, e.get("file", ""))
                kws = [str(k).lower() for k in e.get("keywords", []) if str(k).strip()]
                if os.path.exists(f) and kws:
                    _cache.append((f, kws))
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"[doodle-lib] đọc manifest lỗi: {str(exc)[:100]}")
    if _cache:
        logger.info(f"[doodle-lib] nạp {len(_cache)} vật tái dùng")
    return _cache


def lookup(hint: str | None) -> str | None:
    """Trả ảnh kho đã duyệt; hiện bị khóa nên luôn None."""
    if not _AUTO_REUSE_ENABLED:
        return None
    if not hint:
        return None
    h = hint.lower()
    for f, kws in _load():
        if any(k in h for k in kws):
            return f
    return None


def reset_cache() -> None:
    """Quên cache (sau khi founder cập nhật manifest giữa phiên)."""
    global _cache
    _cache = None
