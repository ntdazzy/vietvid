"""Vòng đời auth — đăng ký/đăng nhập, refresh rotate, đổi mật khẩu, kill-switch tài khoản."""

from __future__ import annotations

import uuid

from sqlalchemy import text

from app_api.db import session_scope


def test_register_duplicate_email_409(client):
    email = f"dup-{uuid.uuid4().hex[:8]}@test.local"
    assert client.post("/v1/auth/register", json={"email": email, "password": "matkhau123"}).status_code == 201
    assert client.post("/v1/auth/register", json={"email": email, "password": "matkhau123"}).status_code == 409


def test_login_wrong_password_401(client, user):
    r = client.post("/v1/auth/login", json={"email": user["email"], "password": "saimatkhau"})
    assert r.status_code == 401


def test_refresh_rotation_invalidates_old(client, user):
    r1 = client.post("/v1/auth/refresh", json={"refresh_token": user["refresh"]})
    assert r1.status_code == 200
    new_refresh = r1.json()["refresh_token"]
    assert new_refresh != user["refresh"]
    # refresh cũ (đã rotate) → 401
    assert client.post("/v1/auth/refresh", json={"refresh_token": user["refresh"]}).status_code == 401
    # refresh mới còn dùng được
    assert client.post("/v1/auth/refresh", json={"refresh_token": new_refresh}).status_code == 200


def test_change_password_then_old_fails(client, user):
    r = client.post("/v1/auth/change-password",
                    headers=user["headers"],
                    json={"current_password": "matkhau123", "new_password": "matkhaumoi999"})
    assert r.status_code == 200
    assert client.post("/v1/auth/login", json={"email": user["email"], "password": "matkhau123"}).status_code == 401
    assert client.post("/v1/auth/login", json={"email": user["email"], "password": "matkhaumoi999"}).status_code == 200


def test_suspended_account_blocked(client, user):
    # /auth/me ok khi ACTIVE
    assert client.get("/v1/auth/me", headers=user["headers"]).status_code == 200
    with session_scope() as s:
        s.execute(text("UPDATE users SET status='SUSPENDED' WHERE id=:id"), {"id": user["uid"]})
    try:
        assert client.get("/v1/auth/me", headers=user["headers"]).status_code == 403
        assert client.post("/v1/auth/login",
                           json={"email": user["email"], "password": "matkhau123"}).status_code == 403
    finally:
        with session_scope() as s:
            s.execute(text("UPDATE users SET status='ACTIVE' WHERE id=:id"), {"id": user["uid"]})
