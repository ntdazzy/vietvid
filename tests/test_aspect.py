"""Multi-aspect export — params.aspect chảy vào job + clamp giá trị sai (vận hành thật)."""

from __future__ import annotations

import uuid


def _create(client, user, aspect: str):
    body = {
        "idempotency_key": f"k-{uuid.uuid4().hex[:10]}",
        "purpose": "draft", "seconds": 5, "resolution": "480p",
        "product": {"name": "Bình giữ nhiệt", "image_path": "a.png"},
        "params": {"aspect": aspect, "voice_gender": "female"},
    }
    return client.post("/v1/jobs", headers=user["headers"], json=body)


def test_square_aspect_persists_on_job(client, user):
    r = _create(client, user, "1:1")
    assert r.status_code in (200, 201), r.text
    job_id = r.json()["job_id"]
    detail = client.get(f"/v1/jobs/{job_id}", headers=user["headers"]).json()
    assert detail["aspect"] == "1:1"


def test_landscape_aspect_persists(client, user):
    r = _create(client, user, "16:9")
    job_id = r.json()["job_id"]
    assert client.get(f"/v1/jobs/{job_id}", headers=user["headers"]).json()["aspect"] == "16:9"


def test_bad_aspect_clamped_to_vertical(client, user):
    r = _create(client, user, "banana")
    job_id = r.json()["job_id"]
    assert client.get(f"/v1/jobs/{job_id}", headers=user["headers"]).json()["aspect"] == "9:16"


def test_default_aspect_is_vertical(client, user):
    body = {
        "idempotency_key": f"k-{uuid.uuid4().hex[:10]}",
        "purpose": "draft", "seconds": 5, "resolution": "480p",
        "product": {"name": "X", "image_path": "a.png"},
    }
    r = client.post("/v1/jobs", headers=user["headers"], json=body)
    job_id = r.json()["job_id"]
    assert client.get(f"/v1/jobs/{job_id}", headers=user["headers"]).json()["aspect"] == "9:16"
