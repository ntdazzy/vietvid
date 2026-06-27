"""Cấu hình tập trung — field SINH TỪ `config/registry.py` (V8.3-W2, Registry mức B).

KHÔNG thêm field tay vào đây. Thêm key mới = thêm 1 dòng vào REGISTRY (config/registry.py)
rồi chạy `python -m scripts.gen_settings_stub` (cập nhật settings.pyi cho IDE).
Call-site `settings.xyz` giữ nguyên — đọc từ biến môi trường / file .env như cũ.
"""

from __future__ import annotations

import json
import os

from pydantic import create_model
from pydantic_settings import BaseSettings, SettingsConfigDict

from config.registry import REGISTRY


class _SettingsBase(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False
    )

    @property
    def cors_origins(self) -> list[str]:
        raw = self.dashboard_cors_origins.strip()
        if not raw:
            return ["capacitor://localhost", "http://localhost"]
        return [origin.strip() for origin in raw.split(",") if origin.strip()]

    @property
    def auto_sensitive_categories_list(self) -> list[str]:
        return [
            item.strip().lower().replace(" ", "_").replace("-", "_")
            for item in self.auto_sensitive_categories.split(",")
            if item.strip()
        ]

    # ── Tiện ích đường dẫn ────────────────────────────────────────────
    @property
    def scripts_dir(self) -> str:
        return os.path.join(self.storage_dir, "scripts")

    @property
    def audio_dir(self) -> str:
        return os.path.join(self.storage_dir, "audio")

    @property
    def broll_dir(self) -> str:
        return os.path.join(self.storage_dir, "broll")

    @property
    def music_dir(self) -> str:
        return os.path.join(self.storage_dir, "music")

    @property
    def output_dir(self) -> str:
        return os.path.join(self.storage_dir, "output")

    @property
    def score_weights(self) -> dict[str, float]:
        return {
            "trend": self.weight_trend,
            "sales": self.weight_sales,
            "intent": self.weight_intent,
            "commission": self.weight_commission,
        }

    def render_format_specs(self) -> list[tuple[str, int, int]]:
        """V6-P4: parse `render_formats` (CSV) → [(tỉ lệ, rộng, cao)]. Rỗng/sai → 9:16."""
        dims = {"9:16": (1080, 1920), "16:9": (1920, 1080), "1:1": (1080, 1080)}
        specs = [
            (key, *dims[key])
            for token in (self.render_formats or "").split(",")
            if (key := token.strip()) in dims
        ]
        return specs or [("9:16", 1080, 1920)]

    @property
    def category_weights_map(self) -> dict[str, dict[str, float]]:
        try:
            raw = json.loads(self.category_weights or "{}")
        except json.JSONDecodeError:
            raw = {}
        if not isinstance(raw, dict):
            raw = {}
        default = raw.get("default") if isinstance(raw.get("default"), dict) else self.score_weights
        parsed: dict[str, dict[str, float]] = {
            "default": _coerce_weights(default, self.score_weights)
        }
        for category, weights in raw.items():
            if category == "default" or not isinstance(weights, dict):
                continue
            key = str(category).strip().lower().replace(" ", "_").replace("-", "_")
            if key:
                parsed[key] = _coerce_weights(weights, parsed["default"])
        return parsed

    def score_weights_for_category(self, category: str | None) -> dict[str, float]:
        key = (category or "default").strip().lower().replace(" ", "_").replace("-", "_")
        weights = self.category_weights_map
        return weights.get(key, weights["default"])


def _coerce_weights(raw: dict, fallback: dict[str, float]) -> dict[str, float]:
    required = {"trend", "sales", "intent", "commission"}
    if set(raw) != required:
        return dict(fallback)
    try:
        return {key: float(raw[key]) for key in required}
    except (TypeError, ValueError):
        return dict(fallback)


_fields = {k.name: (k.type, k.default) for k in REGISTRY if not k.env_only}
Settings = create_model("Settings", __base__=_SettingsBase, **_fields)

settings = Settings()
