"""B2B API — khoá API (phát/dùng/thu hồi) + public /api/v1 + webhook (vận hành thật)."""

from __future__ import annotations

import uuid


def _new_key(client, user, name="CI key") -> str:
    r = client.post("/v1/api-keys", headers=user["headers"], json={"name": name})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["key"].startswith("vv_live_")  # raw chỉ trả lần này
    return body["key"]


def test_apikey_create_list_masks_raw(client, user):
    raw = _new_key(client, user)
    rows = client.get("/v1/api-keys", headers=user["headers"]).json()
    assert any(r["prefix"] == raw[:14] for r in rows)
    # danh sách KHÔNG bao giờ chứa raw key
    assert all("key" not in r for r in rows)


def test_public_api_requires_key(client):
    r = client.post("/api/v1/videos", json={"idempotency_key": "x", "product": {"name": "X"}})
    assert r.status_code == 401


def test_public_api_rejects_bad_key(client):
    r = client.post("/api/v1/videos", headers={"X-API-Key": "vv_live_khongtondtai"},
                    json={"idempotency_key": "x", "product": {"name": "X"}})
    assert r.status_code == 401


def test_public_api_create_then_status(client, user):
    raw = _new_key(client, user)
    hdr = {"X-API-Key": raw}
    body = {
        "idempotency_key": f"api-{uuid.uuid4().hex[:10]}",
        "product": {"name": "Tai nghe API", "image_path": "a.png"},
        "seconds": 5, "purpose": "draft", "resolution": "480p", "aspect": "1:1",
    }
    r = client.post("/api/v1/videos", headers=hdr, json=body)
    assert r.status_code == 201, r.text
    job_id = r.json()["id"]
    # status qua API
    st = client.get(f"/api/v1/videos/{job_id}", headers=hdr)
    assert st.status_code == 200
    assert st.json()["aspect"] == "1:1"
    # list qua API
    lst = client.get("/api/v1/videos", headers=hdr).json()
    assert any(j["id"] == job_id for j in lst["items"])


def test_apikey_revoke_blocks_use(client, user):
    raw = _new_key(client, user)
    rows = client.get("/v1/api-keys", headers=user["headers"]).json()
    key_id = next(r["id"] for r in rows if r["prefix"] == raw[:14])
    assert client.delete(f"/v1/api-keys/{key_id}", headers=user["headers"]).status_code == 200
    # khoá thu hồi → 401
    r = client.post("/api/v1/videos", headers={"X-API-Key": raw},
                    json={"idempotency_key": "y", "product": {"name": "X"}})
    assert r.status_code == 401


def test_webhook_crud(client, user):
    c = client.post("/v1/webhooks", headers=user["headers"], json={"url": "https://hook.example/vv"})
    assert c.status_code == 200
    body = c.json()
    assert body["secret"].startswith("whsec_")  # secret chỉ trả lần này
    hid = body["id"]
    rows = client.get("/v1/webhooks", headers=user["headers"]).json()
    assert any(r["id"] == hid for r in rows)
    assert all("secret" not in r for r in rows)  # list không lộ secret
    assert client.delete(f"/v1/webhooks/{hid}", headers=user["headers"]).status_code == 200


def test_webhook_rejects_non_http(client, user):
    r = client.post("/v1/webhooks", headers=user["headers"], json={"url": "ftp://bad/x"})
    assert r.status_code == 422


def test_webhook_signature_is_deterministic_hmac():
    from app_api import webhooks

    body = b'{"event":"video.ready"}'
    sig = webhooks.sign("whsec_abc", body)
    # ổn định + khác secret → khác chữ ký (chống giả mạo)
    assert sig == webhooks.sign("whsec_abc", body)
    assert sig != webhooks.sign("whsec_xyz", body)
    assert len(sig) == 64  # sha256 hex


def test_webhook_payload_event_mapping():
    from app_api import webhooks
    from app_api.models import JobStatus

    assert webhooks.build_payload("o", "j", JobStatus.READY)["event"] == "video.ready"
    assert webhooks.build_payload("o", "j", JobStatus.FAILED)["event"] == "video.failed"
