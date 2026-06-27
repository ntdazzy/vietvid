"""RLS — cô lập tenant. Org A KHÔNG được thấy/đụng dữ liệu org B.

Đây là bất biến bảo mật quan trọng nhất của hệ đa-tenant (FORCE RLS + GUC vietvid.current_org).
"""

from __future__ import annotations

import uuid

from sqlalchemy import select, text

from app_api.db import tenant_session
from app_api.models import Job
from tests.conftest import JOB_SPEC
from app_api import jobs as jobs_svc


def _make_job(org_id: str, uid: str) -> str:
    with tenant_session(org_id) as s:
        job, _, _ = jobs_svc.create_job(
            s, uuid.UUID(org_id), uuid.UUID(uid),
            idempotency_key=f"k-{uuid.uuid4().hex[:10]}", spec_input=JOB_SPEC,
        )
        return str(job.id)


def test_tenant_session_hides_other_org_rows(user, user2):
    """Job của A KHÔNG xuất hiện trong tenant_session của B (RLS lọc theo GUC)."""
    job_a = _make_job(user["org_id"], user["uid"])
    with tenant_session(user2["org_id"]) as s:
        # B query toàn bộ jobs (không lọc org) → RLS chỉ cho thấy của B → KHÔNG có job_a.
        ids = [str(j.id) for j in s.execute(select(Job)).scalars().all()]
    assert job_a not in ids


def test_unset_guc_sees_nothing_fail_closed(user):
    """GUC chưa set → policy nullif()->NULL → fail-closed → 0 dòng (kể cả role app)."""
    _make_job(user["org_id"], user["uid"])
    from app_api.db import get_sessionmaker

    s = get_sessionmaker()()
    try:
        # KHÔNG set vietvid.current_org → phải thấy 0 job.
        n = s.execute(text("SELECT count(*) FROM jobs")).scalar()
        assert n == 0
    finally:
        s.close()


def test_other_org_cannot_read_job_over_http(user, user2, client):
    """GET /v1/jobs/{A} với token B → 404 (không lộ tồn tại)."""
    job_a = _make_job(user["org_id"], user["uid"])
    r = client.get(f"/v1/jobs/{job_a}", headers=user2["headers"])
    assert r.status_code == 404
    # chủ thật vẫn xem được
    assert client.get(f"/v1/jobs/{job_a}", headers=user["headers"]).status_code == 200


def test_other_org_cannot_delete_job(user, user2, client):
    job_a = _make_job(user["org_id"], user["uid"])
    r = client.delete(f"/v1/jobs/{job_a}", headers=user2["headers"])
    assert r.status_code in (403, 404)  # không xoá được của org khác
