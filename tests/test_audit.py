"""Audit log — admin action ghi nhật ký bất biến; chỉ admin xem được."""

from __future__ import annotations


import pytest
from sqlalchemy import text

from app_api.db import session_scope


def test_admin_actions_are_audited(client, admin, user):
    # suspend → audit "user.status"; credit-adjust → audit "credit.adjust"
    client.post(f"/v1/admin/users/{user['uid']}/status", headers=admin["headers"],
                json={"status": "SUSPENDED"})
    client.post(f"/v1/admin/users/{user['uid']}/status", headers=admin["headers"],
                json={"status": "ACTIVE"})
    client.post(f"/v1/admin/orgs/{user['org_id']}/credit-adjust", headers=admin["headers"],
                json={"amount": 10, "note": "test"})
    client.post(f"/v1/admin/orgs/{user['org_id']}/credit-adjust", headers=admin["headers"],
                json={"amount": -10, "note": "revert"})

    rows = client.get("/v1/admin/audit", headers=admin["headers"]).json()
    actions = {r["action"] for r in rows}
    assert "user.status" in actions
    assert "credit.adjust" in actions
    # actor_email = email admin
    assert any(r["actor_email"] == admin["email"] for r in rows)


def test_non_admin_cannot_view_audit(client, user):
    assert client.get("/v1/admin/audit", headers=user["headers"]).status_code == 403


def test_audit_log_is_append_only():
    """Trigger DB chặn UPDATE/DELETE trên audit_log (bất biến như ledger)."""
    with session_scope() as s:
        rid = s.execute(text(
            "INSERT INTO audit_log (action, detail) VALUES ('test.append', '{}'::jsonb) RETURNING id"
        )).scalar()
    with pytest.raises(Exception):  # noqa: B017
        with session_scope() as s:
            s.execute(text("UPDATE audit_log SET action='hack' WHERE id=:id"), {"id": rid})
    with pytest.raises(Exception):  # noqa: B017
        with session_scope() as s:
            s.execute(text("DELETE FROM audit_log WHERE id=:id"), {"id": rid})
