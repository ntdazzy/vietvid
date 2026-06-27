"""Auto-series — 1 brief → N job biến thể, atomic (đủ credit cho cả loạt hoặc 402)."""

from __future__ import annotations

import uuid

from sqlalchemy import text

from app_api.db import tenant_session


def test_series_creates_n_variant_jobs(client, user):
    r = client.post("/v1/series", headers=user["headers"], json={
        "idempotency_key": f"s-{uuid.uuid4().hex[:10]}", "count": 2,
        "mode": "product_ad", "seconds": 3, "resolution": "480p",
        "brief": "Giới thiệu sản phẩm", "product": {"name": "Áo thun", "image_path": "x.png"},
    })
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["count"] == 2 and len(data["job_ids"]) == 2
    assert data["total_hold_credits"] > 0
    # 2 job khác nhau, mỗi job có brief biến thể (góc nhìn) khác nhau
    with tenant_session(user["org_id"]) as s:
        briefs = [
            s.execute(text("SELECT params->'params'->>'brief' FROM jobs WHERE id=:id"),
                      {"id": uuid.UUID(j)}).scalar()
            for j in data["job_ids"]
        ]
    assert briefs[0] != briefs[1]
    assert all("góc nhìn" in (b or "") for b in briefs)
    # dọn (job có thể đã chạy nền & fail+refund — best-effort)
    for j in data["job_ids"]:
        with tenant_session(user["org_id"]) as s:
            try:
                from app_api import jobs as jobs_svc
                jobs_svc.release_hold(s, uuid.UUID(user["org_id"]), uuid.UUID(j), note="cleanup")
            except Exception:
                pass


def test_series_insufficient_credit_402_atomic(client, user):
    # 5 video 15s/720p → vượt 300 credit free → 402, KHÔNG tạo nửa vời
    before = client.get("/v1/jobs", headers=user["headers"]).json()["count"]
    r = client.post("/v1/series", headers=user["headers"], json={
        "idempotency_key": f"s-{uuid.uuid4().hex[:10]}", "count": 5,
        "seconds": 15, "resolution": "720p", "brief": "x",
        "product": {"name": "P", "image_path": "x.png"},
    })
    assert r.status_code == 402
    after = client.get("/v1/jobs", headers=user["headers"]).json()["count"]
    assert after == before  # rollback: không job nào được tạo
