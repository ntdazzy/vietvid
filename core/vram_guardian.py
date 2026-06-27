"""VRAM pressure guard for render GPU tasks."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from config.settings import settings
from core.database import db
from core.exceptions import RenderError
from core.logger import logger
from core.models import AuditActorType, AuditLog, Incident, IncidentStatus
from core.redaction import redacted_json

INCIDENT_TYPE = "gpu_vram_pressure"


@dataclass(frozen=True)
class GPUSnapshot:
    name: str
    memory_total_mib: int
    memory_used_mib: int
    utilization_gpu_pct: int
    temperature_c: int
    process_count: int = 0

    @property
    def memory_free_mib(self) -> int:
        return max(0, self.memory_total_mib - self.memory_used_mib)

    @property
    def memory_used_pct(self) -> float:
        if self.memory_total_mib <= 0:
            return 0.0
        return round((self.memory_used_mib / self.memory_total_mib) * 100, 2)


@dataclass(frozen=True)
class VRAMGuardDecision:
    ok: bool
    reason: str
    snapshot: GPUSnapshot | None
    threshold_used_pct: float
    min_free_mib: int

    def payload(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "reason": self.reason,
            "snapshot": asdict(self.snapshot) if self.snapshot else None,
            "threshold_used_pct": self.threshold_used_pct,
            "min_free_mib": self.min_free_mib,
        }


def ensure_vram_available(*, task_name: str = "render_gpu_task") -> VRAMGuardDecision:
    decision = evaluate_vram_pressure()
    if decision.ok:
        return decision
    _record_gpu_incident(decision, task_name=task_name)
    raise RenderError(
        "GPU VRAM đang bị chiếm hoặc còn quá thấp; "
        f"tạm dừng {task_name} để tránh OOM ({decision.reason})."
    )


def record_vram_pressure_incident(
    decision: VRAMGuardDecision,
    *,
    task_name: str = "vram_guardian_daemon",
) -> bool:
    """Record an incident for a known-bad decision without re-reading nvidia-smi."""
    if decision.ok:
        return False
    return _record_gpu_incident(decision, task_name=task_name)


def evaluate_vram_pressure(snapshot: GPUSnapshot | None = None) -> VRAMGuardDecision:
    threshold = float(settings.render_vram_guard_max_used_pct or 85.0)
    min_free = int(settings.render_vram_guard_min_free_mb or 0)
    if not bool(settings.render_vram_guard_enabled):
        return VRAMGuardDecision(True, "disabled", snapshot, threshold, min_free)
    snapshot = snapshot or read_gpu_snapshot()
    if snapshot is None:
        return VRAMGuardDecision(True, "gpu_snapshot_unavailable", None, threshold, min_free)
    reasons: list[str] = []
    if snapshot.memory_used_pct >= threshold:
        reasons.append(f"memory_used_pct={snapshot.memory_used_pct:.2f}>={threshold:.2f}")
    if min_free > 0 and snapshot.memory_free_mib < min_free:
        reasons.append(f"memory_free_mib={snapshot.memory_free_mib}<{min_free}")
    if reasons:
        return VRAMGuardDecision(False, "; ".join(reasons), snapshot, threshold, min_free)
    return VRAMGuardDecision(True, "ok", snapshot, threshold, min_free)


def read_gpu_snapshot() -> GPUSnapshot | None:
    if shutil.which("nvidia-smi") is None:
        return None
    proc = subprocess.run(
        [
            "nvidia-smi",
            "--query-gpu=name,memory.total,memory.used,utilization.gpu,temperature.gpu",
            "--format=csv,noheader,nounits",
        ],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    if proc.returncode != 0:
        logger.warning("nvidia-smi snapshot lỗi: " + (proc.stderr or proc.stdout)[-300:])
        return None
    for line in proc.stdout.splitlines():
        snapshot = _parse_gpu_snapshot(line)
        if snapshot is not None:
            return snapshot
    return None


def _parse_gpu_snapshot(line: str) -> GPUSnapshot | None:
    parts = [part.strip() for part in line.split(",")]
    if len(parts) != 5:
        return None
    name, total, used, util, temp = parts
    try:
        return GPUSnapshot(
            name=name,
            memory_total_mib=int(total),
            memory_used_mib=int(used),
            utilization_gpu_pct=int(util),
            temperature_c=int(temp),
        )
    except ValueError:
        return None


def _record_gpu_incident(decision: VRAMGuardDecision, *, task_name: str) -> bool:
    now = datetime.now(timezone.utc)
    payload = {"task_name": task_name, **decision.payload()}
    detail = f"{task_name}: {decision.reason}"
    try:
        with db.transaction() as session:
            if _recent_open_incident(session, now):
                return False
            incident = Incident(
                level="ERROR",
                module="video_engine",
                incident_type=INCIDENT_TYPE,
                status=IncidentStatus.OPEN,
                title="GPU VRAM pressure blocks render",
                detail_redacted=detail[:500],
                opened_at=now,
                payload_redacted_json=redacted_json(payload),
            )
            session.add(incident)
            session.flush()
            session.add(
                AuditLog(
                    actor_type=AuditActorType.SYSTEM,
                    actor_ref="vram_guardian",
                    action="gpu_vram_guard_block",
                    resource_type="gpu",
                    status="BLOCKED",
                    occurred_at=now,
                    message_redacted=detail[:500],
                    payload_redacted_json=redacted_json(payload),
                    incident_id=incident.id,
                )
            )
            return True
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Không ghi được GPU incident: {exc}")
        return False


def _recent_open_incident(session, now: datetime) -> bool:  # noqa: ANN001
    cooldown = max(0, int(settings.render_vram_guard_incident_cooldown_minutes or 0))
    cutoff = now - timedelta(minutes=cooldown)
    incident = (
        session.query(Incident)
        .filter(
            Incident.incident_type == INCIDENT_TYPE,
            Incident.status == IncidentStatus.OPEN,
            Incident.opened_at >= cutoff,
        )
        .order_by(Incident.opened_at.desc())
        .first()
    )
    return incident is not None


__all__ = [
    "GPUSnapshot",
    "VRAMGuardDecision",
    "ensure_vram_available",
    "evaluate_vram_pressure",
    "record_vram_pressure_incident",
    "read_gpu_snapshot",
]
