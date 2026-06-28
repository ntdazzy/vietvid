"""Cấu hình nền tảng runtime + quota API (admin sửa không cần deploy). Vận hành thật."""

from __future__ import annotations

import uuid


def test_config_defaults_and_update(client, admin):
    cfg = client.get("/v1/admin/config", headers=admin["headers"]).json()
    for k in ("video_provider_chain", "max_api_jobs_per_day", "feature_flags"):
        assert k in cfg
    # cập nhật 1 key → phản ánh ngay
    r = client.put("/v1/admin/config", headers=admin["headers"],
                   json={"video_provider_chain": "fal,kling"})
    assert r.status_code == 200 and r.json()["video_provider_chain"] == "fal,kling"
    # khôi phục
    client.put("/v1/admin/config", headers=admin["headers"], json={"video_provider_chain": ""})


def test_config_requires_admin(client, user):
    assert client.put("/v1/admin/config", headers=user["headers"],
                      json={"max_api_jobs_per_day": 5}).status_code == 403


def _api_create(client, key, n):
    return client.post("/api/v1/videos", headers={"X-API-Key": key}, json={
        "idempotency_key": f"q-{uuid.uuid4().hex[:10]}-{n}",
        "purpose": "draft", "seconds": 5, "resolution": "480p",
        "product": {"name": "Quota test", "image_path": "a.png"},
    })


def test_api_quota_enforced_then_reset(client, admin, user):
    # phát khoá API cho org của user
    raw = client.post("/v1/api-keys", headers=user["headers"], json={"name": "q"}).json()["key"]
    # đặt quota = 2/ngày
    client.put("/v1/admin/config", headers=admin["headers"], json={"max_api_jobs_per_day": 2})
    try:
        assert _api_create(client, raw, 1).status_code == 201
        assert _api_create(client, raw, 2).status_code == 201
        # video thứ 3 trong ngày → 429
        assert _api_create(client, raw, 3).status_code == 429
    finally:
        # khôi phục quota để không ảnh hưởng test khác (config là global 1 hàng)
        client.put("/v1/admin/config", headers=admin["headers"], json={"max_api_jobs_per_day": 200})


def test_feature_flag_blocks_api_when_disabled(client, admin, user):
    raw = client.post("/v1/api-keys", headers=user["headers"], json={"name": "ff"}).json()["key"]
    # tắt api_access cho gói free
    client.put("/v1/admin/config", headers=admin["headers"],
               json={"feature_flags": {"free": {"api_access": False}}})
    try:
        assert _api_create(client, raw, 9).status_code == 403
    finally:
        client.put("/v1/admin/config", headers=admin["headers"],
                   json={"feature_flags": {"free": {"api_access": True}}})
