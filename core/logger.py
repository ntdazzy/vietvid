"""Central Loguru setup with split module logs and secret redaction."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable

from loguru import logger as _raw_logger

from config.settings import settings
from core.redaction import redact_secret_payload, redact_secret_text, redacted_json

_configured = False
_DEFAULT_LEVEL = "INFO"
_FILE_LEVEL = "DEBUG"
_ROTATION = "20 MB"
_MODULE_DOMAINS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("db", ("core.database", "core.models", "core.runtime_schema_upgrades", "scripts.init_db")),
    ("telegram", ("dashboard.telegram",)),
    ("web", ("dashboard.routers.client_logs",)),
    ("api", ("dashboard.api", "dashboard.routers", "dashboard.health", "dashboard.security")),
    ("scraper", ("module1_scraper",)),
    ("brain", ("module2_brain",)),
    ("video_engine", ("video_engine",)),
    ("dispatch", ("module4_dispatch",)),
    ("revenue", ("module5_revenue",)),
    ("leads", ("module6_leads",)),
    ("scripts", ("scripts.",)),
    ("core", ("core.", "orchestrator")),
    ("system", ("__main__",)),
)
_LOG_DOMAINS = tuple(domain for domain, _prefixes in _MODULE_DOMAINS)


def _patch_record(record: dict[str, Any]) -> None:
    record["message"] = redact_secret_text(record.get("message", ""), limit=None)
    if record.get("extra"):
        record["extra"].update(redact_secret_payload(record["extra"]))


logger = _raw_logger.patch(_patch_record)


def _log_root() -> Path:
    raw = (settings.log_dir or "logs").strip() or "logs"
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return path


def _retention() -> str:
    days = max(1, int(settings.log_retention_days or 10))
    return f"{days} days"


def _domain_filter(domain: str) -> Callable[[dict[str, Any]], bool]:
    def _matches(record: dict[str, Any]) -> bool:
        if record["extra"].get("log_domain") == domain:
            return True
        module_name = str(record.get("name") or "")
        return _domain_for_module(module_name) == domain

    return _matches


def _domain_for_module(module_name: str) -> str | None:
    for domain, prefixes in _MODULE_DOMAINS:
        if any(module_name.startswith(prefix) for prefix in prefixes):
            return domain
    return None


def _add_file_sink(
    path: Path,
    *,
    level: str,
    filter_fn: Callable[[dict[str, Any]], bool] | None = None,
):
    path.parent.mkdir(parents=True, exist_ok=True)
    return logger.add(
        str(path),
        level=level,
        rotation=_ROTATION,
        retention=_retention(),
        enqueue=True,
        encoding="utf-8",
        filter=filter_fn,
    )


def setup_logging(level: str | None = None) -> "logger":
    """Configure stderr, aggregate log, and per-domain files.

    Safe to call many times and from child processes.
    """
    global _configured
    if _configured:
        return logger
    effective_level = (level or settings.log_level or _DEFAULT_LEVEL).upper()
    log_root = _log_root()
    logger.remove()
    logger.add(
        sys.stderr,
        level=effective_level,
        format=(
            "<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | "
            "<cyan>pid={process}</cyan> | <cyan>{name}</cyan> - <level>{message}</level>"
        ),
        enqueue=True,  # an toàn đa tiến trình
    )
    _add_file_sink(log_root / "affiliatebot_{time:YYYY-MM-DD}.log", level=_FILE_LEVEL)
    for domain in sorted(_LOG_DOMAINS):
        _add_file_sink(
            log_root / domain / f"{domain}_{{time:YYYY-MM-DD}}.log",
            level=_FILE_LEVEL,
            filter_fn=_domain_filter(domain),
        )
    _configured = True
    logger.bind(log_domain="system").info(
        f"logging configured level={effective_level} log_dir={log_root}"
    )
    return logger


def log_event(
    domain: str,
    event_name: str,
    *,
    status: str = "OK",
    level: str = "INFO",
    message: str = "",
    **fields: Any,
) -> None:
    """Write a small structured event to the correct log file."""
    payload = {
        "action": event_name,
        "status": status,
        **{key: value for key, value in fields.items() if value is not None},
    }
    text = f"{event_name} status={status}"
    if message:
        text += f" message={redact_secret_text(message, limit=300)}"
    if fields:
        text += f" data={redacted_json(payload)}"
    bound = logger.bind(log_domain=domain)
    getattr(bound, level.lower(), bound.info)(text)


def reset_logging_for_tests() -> None:
    global _configured
    logger.remove()
    _configured = False


__all__ = ["log_event", "logger", "reset_logging_for_tests", "setup_logging"]
