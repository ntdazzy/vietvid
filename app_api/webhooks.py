"""Giao webhook B2B — khi job tới trạng thái CUỐI, POST payload có CHỮ KÝ HMAC tới URL đã đăng ký.

Best-effort fire-and-forget: lỗi mạng/URL chết KHÔNG được làm vỡ worker. Chữ ký để bên nhận
xác minh payload thật từ VietVid (chống giả mạo): header `X-VietVid-Signature: sha256=<hex>`.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import uuid

from sqlalchemy import select

from app_api.db import tenant_session
from app_api.models import JobStatus, VvWebhook

_EVENT = {
    JobStatus.READY: "video.ready",
    JobStatus.FAILED: "video.failed",
    JobStatus.QA_FAIL: "video.failed",
    JobStatus.REFUNDED: "video.failed",
    JobStatus.CANCELLED: "video.cancelled",
}


def sign(secret: str, body: bytes) -> str:
    """HMAC-SHA256 hex của body bằng secret webhook."""
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


def build_payload(org_id: str, job_id, status: str) -> dict:
    return {
        "event": _EVENT.get(status, "video.updated"),
        "org_id": str(org_id),
        "job_id": str(job_id),
        "status": status,
    }


def notify_terminal(org_id: str, job_id, status: str) -> int:
    """Đọc webhook active của org → POST payload đã ký. Trả số endpoint đã gửi. Nuốt mọi lỗi."""
    payload = build_payload(org_id, job_id, status)
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    try:
        with tenant_session(org_id) as s:
            hooks = s.execute(
                select(VvWebhook).where(
                    VvWebhook.org_id == uuid.UUID(org_id), VvWebhook.active.is_(True)
                )
            ).scalars().all()
            targets = [(h.url, h.secret) for h in hooks]
    except Exception:  # noqa: BLE001 — đọc webhook lỗi không được làm vỡ worker
        return 0
    if not targets:
        return 0

    import httpx

    sent = 0
    for url, secret in targets:
        headers = {
            "content-type": "application/json",
            "X-Vyra-Signature": f"sha256={sign(secret, body)}",
            "X-Vyra-Event": payload["event"],
        }
        try:
            httpx.post(url, content=body, headers=headers, timeout=4.0)
            sent += 1
        except Exception:  # noqa: BLE001 — best-effort: URL chết/timeout bỏ qua
            pass
    return sent
