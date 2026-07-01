"""Batch — N sản phẩm KHÁC nhau → N job (mỗi SP 1 clip), atomic credit.

Nhân y hệt test_series (money-core dùng chung khuôn): đủ credit cho CẢ loạt → 201
(HOLD cả loạt trong 1 transaction), thiếu → 402 rollback (KHÔNG tạo nửa vời).
Khác series ở chỗ mỗi item là 1 SẢN PHẨM khác nhau; gom chung series_group =
batch_group để tái dùng màn theo dõi.
"""

from __future__ import annotations

import uuid

from sqlalchemy import text

from app_api.db import tenant_session


def test_batch_creates_job_per_product(client, user):
    r = client.post("/v1/batch", headers=user["headers"], json={
        "idempotency_key": f"b-{uuid.uuid4().hex[:10]}",
        "mode": "product_ad", "seconds": 3, "resolution": "480p",
        "brief": "Giới thiệu sản phẩm",
        "items": [
            {"product": {"name": "Áo thun", "image_path": "ao.png"}},
            {"product": {"name": "Quần jean", "image_path": "quan.png"}},
        ],
    })
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["count"] == 2 and len(data["job_ids"]) == 2
    assert data["total_hold_credits"] > 0
    # org mới, chưa hold gì trước → held (snapshot trong CÙNG transaction hold) = tổng hold loạt
    assert data["held_credits"] == data["total_hold_credits"]
    # mỗi job = 1 SẢN PHẨM khác nhau, cùng 1 batch_group (=series_group) để gom theo dõi
    with tenant_session(user["org_id"]) as s:
        rows = [
            s.execute(
                text("SELECT params->'product'->>'name', series_group::text "
                     "FROM jobs WHERE id=:id"),
                {"id": uuid.UUID(j)},
            ).one()
            for j in data["job_ids"]
        ]
    names = {row[0] for row in rows}
    groups = {row[1] for row in rows}
    assert names == {"Áo thun", "Quần jean"}       # 2 SP khác nhau, không trùng
    assert groups == {data["batch_group"]}          # cùng 1 batch_group
    # dọn (job có thể đã chạy nền & fail/kẹt hold — best-effort)
    for j in data["job_ids"]:
        with tenant_session(user["org_id"]) as s:
            try:
                from app_api import jobs as jobs_svc
                jobs_svc.release_hold(s, uuid.UUID(user["org_id"]), uuid.UUID(j), note="cleanup")
            except Exception:
                pass


def test_batch_insufficient_credit_402_atomic(client, user):
    # 5 SP × 15s → vượt 300 credit free → 402, KHÔNG tạo nửa vời (rollback cả loạt)
    before = client.get("/v1/jobs", headers=user["headers"]).json()["count"]
    items = [{"product": {"name": f"SP {i}", "image_path": f"{i}.png"}} for i in range(5)]
    r = client.post("/v1/batch", headers=user["headers"], json={
        "idempotency_key": f"b-{uuid.uuid4().hex[:10]}",
        "seconds": 15, "resolution": "720p", "brief": "x", "items": items,
    })
    assert r.status_code == 402, r.text
    after = client.get("/v1/jobs", headers=user["headers"]).json()["count"]
    assert after == before  # rollback: không job nào được tạo
    # ví KHÔNG kẹt credit nào sau rollback
    with tenant_session(user["org_id"]) as s:
        held = s.execute(
            text("SELECT held_credits FROM wallets WHERE org_id=:o"),
            {"o": uuid.UUID(user["org_id"])},
        ).scalar()
    assert held == 0
