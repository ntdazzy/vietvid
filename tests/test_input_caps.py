"""Giới hạn độ dài field tự do (audit P2) — chặn payload khổng lồ vào JSONB."""

from __future__ import annotations

import uuid


def test_oversized_product_name_rejected(client, user):
    body = {
        "idempotency_key": f"k-{uuid.uuid4().hex[:8]}",
        "product": {"name": "x" * 5000, "image_path": "a.png"},
    }
    r = client.post("/v1/jobs", headers=user["headers"], json=body)
    assert r.status_code == 422  # vượt max_length=200


def test_oversized_scene_prompt_rejected(client, user):
    body = {
        "idempotency_key": f"k-{uuid.uuid4().hex[:8]}",
        "scene_prompt": "y" * 9000,
        "product": {"name": "OK", "image_path": "a.png"},
    }
    r = client.post("/v1/jobs", headers=user["headers"], json=body)
    assert r.status_code == 422  # vượt max_length=4000
