"""Bối cảnh KOL (scene presets) — nguồn chuẩn ở presets.py (trích từ autovis),
``ensure_default_scenes()`` upsert vào DB để màn KOL-AI Studio đọc + founder chỉnh sau."""

from __future__ import annotations

from sqlalchemy import select

from core.database import db
from core.logger import logger
from core.models import ScenePreset
from video_engine.scenes.presets import SCENE_PRESETS


def ensure_default_scenes() -> None:
    """Upsert bối cảnh mặc định (chỉ thêm khi thiếu — không ghi đè chỉnh sửa)."""
    with db.transaction() as session:
        existing = set(session.scalars(select(ScenePreset.key)).all())
        added = 0
        for spec in SCENE_PRESETS:
            if spec["key"] in existing:
                continue
            session.add(ScenePreset(**spec))
            added += 1
        if added:
            logger.info(f"[scenes] seed {added} bối cảnh vào scene_presets")


def list_scenes(gender: str = "") -> list[dict]:
    """Trả danh sách bối cảnh (lọc gợi ý giới tính nếu có)."""
    with db.transaction() as session:
        q = select(ScenePreset).where(ScenePreset.status == "ACTIVE").order_by(ScenePreset.sort_order)
        rows = session.scalars(q).all()
        out = []
        for r in rows:
            if gender and r.gender_hint and r.gender_hint != gender:
                continue
            out.append({"key": r.key, "label": r.label, "category": r.category,
                        "gender_hint": r.gender_hint})
        return out
