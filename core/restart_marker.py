"""Restart marker for config changes that child processes cannot hot-reload."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from config.settings import settings
from core.redaction import redact_secret_text

MARKER_FILE = "need_restart.json"
DEFAULT_AFFECTED_PROCESSES = ("dashboard", "orchestrator", "worker")


@dataclass(frozen=True)
class RestartMarker:
    changed_at: str
    changed_keys_redacted: list[str]
    affected_processes: list[str]
    reason: str
    resolved_at: str = ""

    def model_dump(self) -> dict:
        return asdict(self)


def restart_marker_path() -> Path:
    return Path(settings.storage_dir).resolve() / "config" / MARKER_FILE


def write_restart_marker(
    changed_keys: list[str],
    *,
    affected_processes: list[str] | None = None,
    reason: str = "Credential .env updated",
) -> RestartMarker:
    marker = RestartMarker(
        changed_at=datetime.now(timezone.utc).isoformat(),
        changed_keys_redacted=_redacted_keys(changed_keys),
        affected_processes=affected_processes or list(DEFAULT_AFFECTED_PROCESSES),
        reason=redact_secret_text(reason, limit=240),
    )
    path = restart_marker_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as fh:
        json.dump(marker.model_dump(), fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")
        tmp_path = fh.name
    os.replace(tmp_path, path)
    return marker


def resolve_restart_marker() -> None:
    """Đánh dấu marker đã xử lý (gọi khi orchestrator boot — restart đã diễn ra)."""
    path = restart_marker_path()
    if not path.exists():
        return
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    if not isinstance(raw, dict) or raw.get("resolved_at"):
        return
    raw["resolved_at"] = datetime.now(timezone.utc).isoformat()
    with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as fh:
        json.dump(raw, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")
        tmp_path = fh.name
    os.replace(tmp_path, path)


def load_restart_marker() -> RestartMarker | None:
    path = restart_marker_path()
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(raw, dict) or raw.get("resolved_at"):
        return None
    return RestartMarker(
        changed_at=str(raw.get("changed_at") or ""),
        changed_keys_redacted=[str(item) for item in raw.get("changed_keys_redacted") or []],
        affected_processes=[str(item) for item in raw.get("affected_processes") or []],
        reason=str(raw.get("reason") or ""),
        resolved_at=str(raw.get("resolved_at") or ""),
    )


def _redacted_keys(keys: list[str]) -> list[str]:
    return sorted({redact_secret_text(str(key), limit=120) for key in keys if str(key).strip()})
