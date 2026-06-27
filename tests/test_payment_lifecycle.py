"""Vòng đời payment — reaper đánh dấu PENDING quá hạn (>24h) thành FAILED; recent giữ nguyên."""

from __future__ import annotations

import uuid

from sqlalchemy import text

from app_api import billing
from app_api.db import tenant_session
from app_api.reaper import reap_stuck_jobs


def _pending_payment(org, uid) -> uuid.UUID:
    with tenant_session(org) as s:
        p = billing.create_topup(s, uuid.UUID(org), uuid.UUID(uid),
                                 pack_id="starter", provider="vnpay")
        return p.id


def test_reaper_expires_stale_pending_payment(user):
    org, uid = user["org_id"], user["uid"]
    stale = _pending_payment(org, uid)
    fresh = _pending_payment(org, uid)
    # backdate cái stale > 24h
    with tenant_session(org) as s:
        s.execute(text("UPDATE payments SET created_at = now() - interval '30 hours' WHERE id=:id"),
                  {"id": stale})

    out = reap_stuck_jobs()
    assert out["expired_payments"] >= 1

    with tenant_session(org) as s:
        st_stale = s.execute(text("SELECT status FROM payments WHERE id=:id"), {"id": stale}).scalar()
        st_fresh = s.execute(text("SELECT status FROM payments WHERE id=:id"), {"id": fresh}).scalar()
    assert st_stale == "FAILED"      # quá hạn → FAILED
    assert st_fresh == "PENDING"     # recent → giữ nguyên
