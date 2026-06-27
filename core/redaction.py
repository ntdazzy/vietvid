"""Helpers to keep secrets out of logs and audit payloads."""

from __future__ import annotations

import json
import re
from typing import Any

SENSITIVE_KEY_PARTS = (
    "authorization",
    "cookie",
    "csrf",
    "password",
    "secret",
    "token",
)

_TEXT_PATTERNS = (
    r"(?i)(authorization\s*[:=]\s*)([^;\n]+)",
    r"(?i)(cookie\s*[:=]\s*)([^;\n]+)",
    r"(?i)(csrf[-_ ]?token\s*[:=]\s*)([^\s;,]+)",
    r"(?i)(access[-_ ]?token\s*[:=]\s*)([^\s;,]+)",
    r"(?i)(refresh[-_ ]?token\s*[:=]\s*)([^\s;,]+)",
    r"(?i)(password\s*[:=]\s*)([^\s;,]+)",
    r"(?i)(token\s*[:=]\s*)([^\s;,]+)",
    r"(?i)(secret\s*[:=]\s*)([^\s;,]+)",
    r"(?i)(api[-_ ]?key\s*[:=]\s*)([^\s;,]+)",
    r"(?i)(bot[-_ ]?token\s*[:=]\s*)([^\s;,]+)",
    r"\b([A-Za-z0-9_-]{24,}\.[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_-]{6,})\b",
    r"\b(?![0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b)([A-Za-z0-9_:-]{32,})\b",
)


def redact_secret_text(value: Any, *, limit: int | None = 500) -> str:
    text = str(value or "")
    for pattern in _TEXT_PATTERNS:
        text = re.sub(pattern, _redact_match, text)
    if limit is None:
        return text
    return text[: max(0, int(limit))]


def safe_error_detail(value: Any, *, limit: int = 500) -> str:
    return redact_secret_text(value, limit=limit)


def safe_event_message(value: Any, *, limit: int = 500) -> str:
    return redact_secret_text(value, limit=limit)


def redact_secret_payload(payload: Any) -> Any:
    if isinstance(payload, dict):
        return {
            str(key): "[redacted]" if _sensitive_key(str(key)) else redact_secret_payload(value)
            for key, value in payload.items()
        }
    if isinstance(payload, list):
        return [redact_secret_payload(value) for value in payload]
    if isinstance(payload, tuple):
        return [redact_secret_payload(value) for value in payload]
    if isinstance(payload, str):
        return redact_secret_text(payload, limit=None)
    return payload


def redacted_json(payload: Any) -> str:
    return json.dumps(redact_secret_payload(payload), ensure_ascii=False, sort_keys=True)


def _sensitive_key(value: str) -> bool:
    lowered = value.strip().lower()
    return any(part in lowered for part in SENSITIVE_KEY_PARTS)


def _redact_match(match: re.Match) -> str:
    if len(match.groups()) >= 2:
        return f"{match.group(1)}[redacted]"
    return "[redacted]"


__all__ = [
    "SENSITIVE_KEY_PARTS",
    "redact_secret_payload",
    "redact_secret_text",
    "redacted_json",
    "safe_error_detail",
    "safe_event_message",
]
