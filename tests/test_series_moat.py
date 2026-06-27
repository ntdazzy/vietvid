"""MOAT — vòng lặp hiệu suất: loạt có target_url → short-link/biến thể → click → xếp hạng bản thắng.

Đây là thứ autovis KHÔNG có (không attribution). Test chứng minh loop chạy thật.
"""

from __future__ import annotations

import uuid

import httpx


def test_series_tracks_clicks_and_ranks_winner(client, user, server):
    target = f"https://shopee.vn/sp-{uuid.uuid4().hex[:8]}"
    r = client.post("/v1/series", headers=user["headers"], json={
        "idempotency_key": f"s-{uuid.uuid4().hex[:10]}", "count": 2,
        "seconds": 3, "resolution": "480p", "brief": "Giới thiệu",
        "product": {"name": "Áo", "image_path": "x.png"}, "target_url": target,
    })
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["tracked"] is True
    group = data["series_group"]

    # 2 short-link cho loạt này (lọc theo target_url vừa tạo)
    links = [x for x in client.get("/v1/affiliate/links", headers=user["headers"]).json()
             if x["target_url"] == target]
    assert len(links) == 2

    # click biến thể đầu 3 lần qua /r/{code} (public)
    raw = httpx.Client(base_url=server, follow_redirects=False, timeout=30)
    for _ in range(3):
        assert raw.get(f"/r/{links[0]['code']}").status_code == 302

    # performance: 1 biến thể có 3 click + is_winner; tổng click = 3
    perf = client.get(f"/v1/series/{group}/performance", headers=user["headers"]).json()
    assert len(perf) == 2
    assert sum(v["clicks"] for v in perf) == 3
    winners = [v for v in perf if v["is_winner"]]
    assert len(winners) == 1 and winners[0]["clicks"] == 3

    # dọn
    from app_api import jobs as jobs_svc
    from app_api.db import tenant_session
    for jid in data["job_ids"]:
        with tenant_session(user["org_id"]) as s:
            try:
                jobs_svc.release_hold(s, uuid.UUID(user["org_id"]), uuid.UUID(jid), note="cleanup")
            except Exception:
                pass


def test_performance_unknown_group_404(client, user):
    assert client.get(f"/v1/series/{uuid.uuid4()}/performance", headers=user["headers"]).status_code == 404
