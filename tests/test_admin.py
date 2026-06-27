"""Admin — gating (chỉ super-admin), khoá user, cộng/trừ credit, duyệt KOL mặt thật."""

from __future__ import annotations


def test_non_admin_forbidden(client, user):
    # user thường KHÔNG vào được admin
    assert client.get("/v1/admin/stats", headers=user["headers"]).status_code == 403
    assert client.get("/v1/admin/users", headers=user["headers"]).status_code == 403


def test_admin_stats_and_users(client, admin, user):
    st = client.get("/v1/admin/stats", headers=admin["headers"])
    assert st.status_code == 200
    assert st.json()["users"] >= 1
    rows = client.get(f"/v1/admin/users?q={user['email']}", headers=admin["headers"])
    assert rows.status_code == 200
    assert any(u["email"] == user["email"] for u in rows.json())


def test_admin_suspend_unsuspend(client, admin, user):
    # khoá user → /auth/me của họ 403
    s1 = client.post(f"/v1/admin/users/{user['uid']}/status", headers=admin["headers"],
                     json={"status": "SUSPENDED"})
    assert s1.status_code == 200
    assert client.get("/v1/auth/me", headers=user["headers"]).status_code == 403
    # mở lại
    client.post(f"/v1/admin/users/{user['uid']}/status", headers=admin["headers"],
                json={"status": "ACTIVE"})
    assert client.get("/v1/auth/me", headers=user["headers"]).status_code == 200


def test_admin_credit_adjust(client, admin, user):
    before = client.get("/v1/auth/me", headers=user["headers"]).json()["balance_credits"]
    r = client.post(f"/v1/admin/orgs/{user['org_id']}/credit-adjust", headers=admin["headers"],
                    json={"amount": 500, "note": "test bonus"})
    assert r.status_code == 200
    after = client.get("/v1/auth/me", headers=user["headers"]).json()["balance_credits"]
    assert after == before + 500
    # trừ lại
    client.post(f"/v1/admin/orgs/{user['org_id']}/credit-adjust", headers=admin["headers"],
                json={"amount": -500, "note": "revert"})
    assert client.get("/v1/auth/me", headers=user["headers"]).json()["balance_credits"] == before


def test_admin_moderation_flow(client, admin, user):
    # user tạo KOL mặt thật → PENDING
    k = client.post("/v1/kol-personas", headers=user["headers"],
                    json={"name": "Mặt thật QA", "source": "upload",
                          "avatar_url": "http://x/a.jpg", "consent_confirmed": True}).json()
    assert k["moderation_status"] == "PENDING"
    # xuất hiện trong hàng kiểm duyệt admin
    queue = client.get("/v1/admin/moderation", headers=admin["headers"]).json()
    assert any(m["id"] == k["id"] for m in queue)
    # admin duyệt
    d = client.post(f"/v1/admin/moderation/{k['id']}/decision", headers=admin["headers"],
                    json={"org_id": user["org_id"], "approve": True})
    assert d.status_code == 200 and d.json()["status"] == "APPROVED"
    # giờ KOL dùng được (không còn PENDING)
    rows = client.get("/v1/kol-personas", headers=user["headers"]).json()
    assert next(x for x in rows if x["id"] == k["id"])["moderation_status"] == "APPROVED"
