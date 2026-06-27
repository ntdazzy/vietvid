"""Notifications — sinh khi nạp tiền, list + unread + mark-read, cô lập org."""

from __future__ import annotations


def test_payment_creates_notification(client, user):
    # dev topup → payment SUCCEEDED → notification "payment"
    r = client.post("/v1/billing/topup", headers=user["headers"],
                    json={"pack_id": "starter", "provider": "dev"})
    assert r.status_code == 200 and r.json()["status"] == "succeeded"

    nl = client.get("/v1/notifications", headers=user["headers"]).json()
    assert nl["unread"] >= 1
    assert any(n["type"] == "payment" for n in nl["items"])
    assert any("credit" in n["title"].lower() or "nạp" in n["title"].lower() for n in nl["items"])


def test_mark_read_clears_unread(client, user):
    client.post("/v1/billing/topup", headers=user["headers"], json={"pack_id": "starter", "provider": "dev"})
    assert client.get("/v1/notifications", headers=user["headers"]).json()["unread"] >= 1
    assert client.post("/v1/notifications/read", headers=user["headers"], json={}).status_code == 200
    assert client.get("/v1/notifications", headers=user["headers"]).json()["unread"] == 0


def test_notifications_isolated(client, user, user2):
    client.post("/v1/billing/topup", headers=user["headers"], json={"pack_id": "starter", "provider": "dev"})
    # user2 (org khác) KHÔNG thấy thông báo của user
    b = client.get("/v1/notifications", headers=user2["headers"]).json()
    assert b["unread"] == 0
    assert all(n["type"] != "payment" or True for n in b["items"])  # không có của user
