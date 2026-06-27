"""Công tắc tự động toàn phần + kill-switch runtime."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, fields
from datetime import datetime, timedelta, timezone
from tempfile import NamedTemporaryFile

from config.registry import hot_keys
from config.settings import settings
from core.logger import logger

_CONFIG_NAME = "automation.json"
_CATEGORY_ALIASES = {
    "health_care": "health",
    "healthcare": "health",
    "medical": "health",
    "weight_loss": "health",
    "personal_care": "beauty",
    "electronics": "tech",
    "pc": "tech",
    "decor": "home",
    "household": "home",
    "home_living": "home",
    "home_kitchen": "home",
}


@dataclass(frozen=True)
class AutomationConfig:
    auto_approve_script: bool
    auto_approve_video: bool
    auto_dispatch: bool
    auto_sensitive_categories: list[str]
    auto_dispatch_privacy: str
    auto_dispatch_max_per_hour: int
    # V8.2 Phase 5: autopilot tự tạo video từ SP tier A — toggle runtime (không cần restart).
    autopilot_enabled: bool = False

    def model_dump(self) -> dict:
        return asdict(self)


# V8.3-W2.3c: whitelist hot-reload = registry hot=True. Drift với AutomationConfig
# (thêm field quên đánh hot / ngược lại) → cảnh báo ngay khi import, fail-open.
_drift = hot_keys() ^ {f.name for f in fields(AutomationConfig)}
if _drift:
    logger.warning(f"[automation] hot-keys registry lệch AutomationConfig: {sorted(_drift)}")


@dataclass(frozen=True)
class AutomationPatch:
    auto_approve_script: bool | None = None
    auto_approve_video: bool | None = None
    auto_dispatch: bool | None = None
    auto_sensitive_categories: list[str] | None = None
    auto_dispatch_privacy: str | None = None
    auto_dispatch_max_per_hour: int | None = None
    autopilot_enabled: bool | None = None


def automation_path() -> str:
    return os.path.join(settings.storage_dir, "config", _CONFIG_NAME)


def load_automation_config() -> AutomationConfig:
    config = _defaults()
    path = automation_path()
    if not os.path.exists(path):
        return config
    try:
        with open(path, encoding="utf-8") as fh:
            raw = json.load(fh)
    except Exception as exc:  # noqa: BLE001
        logger.error(f"[automation] không đọc được {path}: {exc}")
        return config
    return _coerce_config({**config.model_dump(), **(raw if isinstance(raw, dict) else {})})


def save_automation_config(patch: AutomationPatch) -> AutomationConfig:
    current = load_automation_config().model_dump()
    patch_data = {key: value for key, value in asdict(patch).items() if value is not None}
    updated = _coerce_config({**current, **patch_data})
    path = automation_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", dir=os.path.dirname(path), delete=False) as fh:
        json.dump(updated.model_dump(), fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")
        tmp_path = fh.name
    os.replace(tmp_path, path)
    logger.info(f"[automation] đã cập nhật runtime config: {path}")
    return updated


def is_sensitive_category(category: str | None, config: AutomationConfig | None = None) -> bool:
    if not category:
        return False
    cfg = config or load_automation_config()
    normalized = _normalize_category(category)
    return normalized in {_normalize_category(item) for item in cfg.auto_sensitive_categories}


def should_auto_approve_script(category: str | None = None) -> bool:
    cfg = load_automation_config()
    return cfg.auto_approve_script and not is_sensitive_category(category, cfg)


def should_auto_approve_video(category: str | None = None) -> bool:
    cfg = load_automation_config()
    return cfg.auto_approve_video and not is_sensitive_category(category, cfg)


def should_auto_dispatch(category: str | None = None) -> bool:
    cfg = load_automation_config()
    return cfg.auto_dispatch and not is_sensitive_category(category, cfg)


def dispatch_window_start(now: datetime | None = None) -> datetime:
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    return current - timedelta(hours=1)


def _defaults() -> AutomationConfig:
    return _coerce_config(
        {
            "auto_approve_script": settings.auto_approve_script,
            "auto_approve_video": settings.auto_approve_video,
            "auto_dispatch": settings.auto_dispatch,
            "auto_sensitive_categories": settings.auto_sensitive_categories_list,
            "auto_dispatch_privacy": settings.auto_dispatch_privacy,
            "auto_dispatch_max_per_hour": settings.auto_dispatch_max_per_hour,
            "autopilot_enabled": settings.autopilot_enabled,
        }
    )


def _coerce_config(raw: dict) -> AutomationConfig:
    privacy = str(raw.get("auto_dispatch_privacy") or "private").strip().lower()
    if privacy not in {"private", "unlisted", "public"}:
        privacy = "private"
    return AutomationConfig(
        auto_approve_script=bool(raw.get("auto_approve_script")),
        auto_approve_video=bool(raw.get("auto_approve_video")),
        auto_dispatch=bool(raw.get("auto_dispatch")),
        auto_sensitive_categories=_category_list(raw.get("auto_sensitive_categories")),
        auto_dispatch_privacy=privacy,
        auto_dispatch_max_per_hour=max(0, int(raw.get("auto_dispatch_max_per_hour") or 0)),
        autopilot_enabled=bool(raw.get("autopilot_enabled")),
    )


def _category_list(value) -> list[str]:  # noqa: ANN001
    if isinstance(value, str):
        items = value.split(",")
    elif isinstance(value, list):
        items = value
    else:
        items = []
    normalized = [_normalize_category(str(item)) for item in items]
    seen: set[str] = set()
    # dedupe giữ thứ tự: alias (medical/weight_loss→health) gộp về 1, tránh list phình mỗi lần lưu.
    return [item for item in normalized if item and not (item in seen or seen.add(item))]


def _normalize_category(value: str) -> str:
    normalized = value.strip().lower().replace(" ", "_").replace("-", "_")
    return _CATEGORY_ALIASES.get(normalized, normalized)
