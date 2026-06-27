"""Pytest fixtures — VẬN HÀNH THẬT (server uvicorn thật + httpx + Postgres thật).

Không TestClient, không mock: boot 1 server con (reaper/rate-limit tắt) trên cổng test, chờ
/health, rồi gọi qua HTTP. Test money-core thao tác DB trực tiếp qua jobs_svc/tenant_session
(cùng DB) để dựng trạng thái — đúng tinh thần "kiểm thử bằng vận hành thật".

Cần env VIETVID_DATABASE_URL trỏ Postgres (CI: service container; local: DB dev).
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import uuid

import httpx
import pytest

ADMIN_EMAIL = "vietvid-pytest-admin@test.local"


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_health(url: str, timeout: float = 40) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        try:
            if httpx.get(url, timeout=2).status_code == 200:
                return True
        except httpx.HTTPError:
            pass
        time.sleep(0.5)
    return False


@pytest.fixture(scope="session")
def server() -> str:
    """Boot server con MỚI trên cổng trống (không tái dùng → tránh server cũ leak).
    Reaper + rate-limit TẮT để test xác định."""
    port = _free_port()
    base = f"http://127.0.0.1:{port}"
    env = dict(os.environ)
    env.update(
        VIETVID_REAPER="0", VIETVID_RATE_LIMIT="0", PYTHONUTF8="1",
        VIETVID_ADMIN_EMAILS=ADMIN_EMAIL,
    )
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app_api.main:app",
         "--port", str(port), "--log-level", "warning"],
        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    assert _wait_health(f"{base}/health"), "server test không lên được"
    yield base
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()


@pytest.fixture
def client(server: str):
    with httpx.Client(base_url=server, timeout=30) as c:
        yield c


def _register(client) -> dict:
    email = f"pytest-{uuid.uuid4().hex[:10]}@test.local"
    r = client.post("/v1/auth/register", json={"email": email, "password": "matkhau123"})
    assert r.status_code == 201, r.text
    tok = r.json()["access_token"]
    me = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {tok}"}).json()
    return {
        "email": email, "token": tok, "refresh": r.json().get("refresh_token"),
        "org_id": me["org_id"], "uid": me["user_id"],
        "headers": {"Authorization": f"Bearer {tok}"},
    }


@pytest.fixture
def user(client) -> dict:
    return _register(client)


@pytest.fixture
def user2(client) -> dict:
    return _register(client)


@pytest.fixture
def admin(client) -> dict:
    """User có email trong VIETVID_ADMIN_EMAILS (đăng ký, hoặc login nếu đã tồn tại từ run trước)."""
    r = client.post("/v1/auth/register", json={"email": ADMIN_EMAIL, "password": "matkhau123"})
    if r.status_code == 409:
        r = client.post("/v1/auth/login", json={"email": ADMIN_EMAIL, "password": "matkhau123"})
    tok = r.json()["access_token"]
    return {"email": ADMIN_EMAIL, "token": tok, "headers": {"Authorization": f"Bearer {tok}"}}


# spec tối thiểu hợp lệ để create_job dựng HOLD (KHÔNG gọi engine).
JOB_SPEC = {
    "mode": "product_ad", "purpose": "final", "seconds": 5, "resolution": "480p",
    "kind": "product_ad", "params": {"aspect": "9:16"},
}
