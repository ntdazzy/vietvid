"""Lightweight runtime process registry for the dashboard.

The orchestrator owns worker processes, while the dashboard is only a child
process/API surface. A tiny JSON snapshot lets the dashboard show real process
state without shelling out or keeping cross-process handles.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config.settings import settings
from core.redaction import redacted_json


@dataclass(frozen=True)
class ProcessSnapshot:
    name: str
    status: str
    pid: int = 0
    note: str = ""
    restarts: int = 0
    disabled: bool = False
    updated_at: str = ""


def process_registry_path() -> Path:
    return Path(settings.storage_dir) / "runtime" / "processes.json"


def write_process_snapshots(rows: list[ProcessSnapshot]) -> None:
    path = process_registry_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "monotonic": time.monotonic(),
        "processes": [asdict(row) for row in rows],
    }
    tmp = path.with_suffix(".tmp")
    tmp.write_text(redacted_json(payload), encoding="utf-8")
    os.replace(tmp, path)


def read_process_snapshots(max_age_seconds: int = 180) -> tuple[list[dict[str, Any]], str]:
    path = process_registry_path()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return [], "missing"

    updated_at = str(payload.get("updated_at") or "")
    try:
        age = time.monotonic() - float(payload.get("monotonic") or 0.0)
    except (TypeError, ValueError):
        age = max_age_seconds + 1
    if age > max_age_seconds:
        return list(payload.get("processes") or []), "stale"
    return list(payload.get("processes") or []), updated_at
