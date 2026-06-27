"""Money core — bất biến TIỀN (audit chấm ZERO test là P0 lớn nhất).

Ví ACID HOLD/REFUND · sổ cái APPEND-ONLY (trigger DB) · idempotency tạo job.
Chạy thật trên Postgres (trigger + RLS là hành vi Postgres-specific, SQLite/mock không tái hiện).
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import text

from app_api import jobs as jobs_svc
from app_api.db import tenant_session
from tests.conftest import JOB_SPEC


def _make_job(org_id: str, uid: str):
    with tenant_session(org_id) as s:
        job, hold, dup = jobs_svc.create_job(
            s, uuid.UUID(org_id), uuid.UUID(uid),
            idempotency_key=f"k-{uuid.uuid4().hex[:10]}", spec_input=JOB_SPEC,
        )
        return str(job.id), hold, dup


def test_signup_grants_free_credits(user, client):
    me = client.get("/v1/auth/me", headers=user["headers"]).json()
    assert me["balance_credits"] == 300
    assert me["held_credits"] == 0


def test_hold_then_refund_restores_balance(user, client):
    job_id, hold, _ = _make_job(user["org_id"], user["uid"])
    assert hold > 0
    me = client.get("/v1/auth/me", headers=user["headers"]).json()
    assert me["held_credits"] == hold
    assert me["balance_credits"] == 300 - hold

    # release_hold = hoàn 100% HOLD + CANCELLED (idempotent qua _terminal_done)
    with tenant_session(user["org_id"]) as s:
        jobs_svc.release_hold(s, uuid.UUID(user["org_id"]), uuid.UUID(job_id), note="test")
    me2 = client.get("/v1/auth/me", headers=user["headers"]).json()
    assert me2["held_credits"] == 0
    assert me2["balance_credits"] == 300


def test_ledger_is_append_only(user):
    """Trigger DB chặn UPDATE/DELETE trên ledger_entries — sổ cái bất biến."""
    _make_job(user["org_id"], user["uid"])  # sinh ít nhất 1 ledger row (HOLD)
    with tenant_session(user["org_id"]) as s:
        row_id = s.execute(
            text("SELECT id FROM ledger_entries WHERE org_id = :o ORDER BY id DESC LIMIT 1"),
            {"o": user["org_id"]},
        ).scalar()
        assert row_id is not None

    with pytest.raises(Exception):  # noqa: B017 — trigger raise, đúng là phải nổ
        with tenant_session(user["org_id"]) as s:
            s.execute(text("UPDATE ledger_entries SET note='hack' WHERE id = :id"), {"id": row_id})

    with pytest.raises(Exception):  # noqa: B017
        with tenant_session(user["org_id"]) as s:
            s.execute(text("DELETE FROM ledger_entries WHERE id = :id"), {"id": row_id})


def test_job_creation_is_idempotent(user):
    """Cùng (org, idempotency_key) → CÙNG job, KHÔNG HOLD lần 2."""
    key = f"k-{uuid.uuid4().hex[:10]}"
    with tenant_session(user["org_id"]) as s:
        j1, h1, dup1 = jobs_svc.create_job(
            s, uuid.UUID(user["org_id"]), uuid.UUID(user["uid"]),
            idempotency_key=key, spec_input=JOB_SPEC,
        )
        id1 = str(j1.id)
    with tenant_session(user["org_id"]) as s:
        j2, h2, dup2 = jobs_svc.create_job(
            s, uuid.UUID(user["org_id"]), uuid.UUID(user["uid"]),
            idempotency_key=key, spec_input=JOB_SPEC,
        )
        id2 = str(j2.id)
    assert id1 == id2
    assert dup2 is True
    # held chỉ bằng 1 lần hold (không nhân đôi)
    with tenant_session(user["org_id"]) as s:
        held = s.execute(
            text("SELECT held_credits FROM wallets WHERE org_id = :o"), {"o": user["org_id"]}
        ).scalar()
    assert held == h1
