"""Nội dung — templates/KOL/brand-kit: RLS nới (system + own), cô lập org, gate upload mặt thật."""

from __future__ import annotations


def test_templates_list_includes_system(client, user):
    rows = client.get("/v1/templates", headers=user["headers"]).json()
    systems = [t for t in rows if t["is_system"]]
    names = {t["name"] for t in systems}
    assert len(systems) >= 4
    assert "Review sản phẩm" in names
    # preset có feature để wizard dùng
    review = next(t for t in systems if t["name"] == "Review sản phẩm")
    assert review["preset"].get("feature") == "review"


def test_create_then_delete_own_template(client, user):
    r = client.post("/v1/templates", headers=user["headers"],
                    json={"name": "Mẫu của tôi", "category": "review", "preset": {"feature": "review"}})
    assert r.status_code == 201 and r.json()["is_system"] is False
    tid = r.json()["id"]
    rows = client.get("/v1/templates", headers=user["headers"]).json()
    assert any(t["id"] == tid for t in rows)
    assert client.delete(f"/v1/templates/{tid}", headers=user["headers"]).status_code == 204
    rows2 = client.get("/v1/templates", headers=user["headers"]).json()
    assert not any(t["id"] == tid for t in rows2)


def test_cannot_delete_system_template(client, user):
    rows = client.get("/v1/templates", headers=user["headers"]).json()
    sys_id = next(t["id"] for t in rows if t["is_system"])
    # row hệ thống (org_id NULL) — endpoint lọc org_id nên KHÔNG xoá được → 404
    assert client.delete(f"/v1/templates/{sys_id}", headers=user["headers"]).status_code == 404
    # vẫn còn đó
    rows2 = client.get("/v1/templates", headers=user["headers"]).json()
    assert any(t["id"] == sys_id for t in rows2)


def test_template_isolated_between_orgs(client, user, user2):
    r = client.post("/v1/templates", headers=user["headers"],
                    json={"name": "Bí mật của A", "preset": {}})
    tid = r.json()["id"]
    # B thấy system nhưng KHÔNG thấy template riêng của A
    b_rows = client.get("/v1/templates", headers=user2["headers"]).json()
    assert not any(t["id"] == tid for t in b_rows)
    assert any(t["is_system"] for t in b_rows)  # nhưng vẫn thấy system


def test_kol_upload_requires_consent(client, user):
    # upload mặt thật thiếu đồng ý → 400
    r1 = client.post("/v1/kol-personas", headers=user["headers"],
                     json={"name": "Mặt thật", "source": "upload", "avatar_url": "http://x/a.jpg"})
    assert r1.status_code == 400
    # đủ đồng ý + ảnh → 201, vào kiểm duyệt PENDING
    r2 = client.post("/v1/kol-personas", headers=user["headers"],
                     json={"name": "Mặt thật", "source": "upload",
                           "avatar_url": "http://x/a.jpg", "consent_confirmed": True})
    assert r2.status_code == 201
    assert r2.json()["moderation_status"] == "PENDING"
    assert r2.json()["source"] == "upload"


def test_kol_list_includes_system_personas(client, user):
    rows = client.get("/v1/kol-personas", headers=user["headers"]).json()
    names = {k["name"] for k in rows if k["is_system"]}
    assert {"Linh", "Minh", "Hà"} <= names


def test_brand_kit_crud(client, user):
    r = client.post("/v1/brand-kits", headers=user["headers"],
                    json={"name": "Shop ABC", "primary_color": "#FF0000", "is_default": True})
    assert r.status_code == 201
    kid = r.json()["id"]
    assert r.json()["is_default"] is True
    # update
    up = client.patch(f"/v1/brand-kits/{kid}", headers=user["headers"],
                      json={"name": "Shop ABC v2", "watermark_text": "@shopabc"})
    assert up.status_code == 200 and up.json()["watermark_text"] == "@shopabc"
    # list shows it
    assert any(k["id"] == kid for k in client.get("/v1/brand-kits", headers=user["headers"]).json())
    # delete
    assert client.delete(f"/v1/brand-kits/{kid}", headers=user["headers"]).status_code == 204


def test_brand_kit_isolated(client, user, user2):
    r = client.post("/v1/brand-kits", headers=user["headers"], json={"name": "Kit A"})
    kid = r.json()["id"]
    b_rows = client.get("/v1/brand-kits", headers=user2["headers"]).json()
    assert not any(k["id"] == kid for k in b_rows)
