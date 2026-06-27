"""Router auth/tenancy — bootstrap (idempotent), me, dev-token (chỉ dev-mode)."""

from __future__ import annotations

import hashlib
import uuid

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from app_api import config, tenancy, wallet
from app_api.auth import Principal, mint_dev_token
from app_api.db import session_scope, tenant_session
from app_api.deps import Tenant, get_principal, get_tenant
from app_api.models import User
from app_api.schemas import (
    BootstrapResponse,
    DevTokenRequest,
    DevTokenResponse,
    MeResponse,
)

router = APIRouter(prefix="/v1", tags=["auth"])


# ── Đăng ký / Đăng nhập THẬT bằng email+mật khẩu (khi KHÔNG dùng Supabase) ──
class RegisterReq(BaseModel):
    email: str = Field(min_length=3, max_length=200)
    password: str = Field(min_length=6, max_length=128)
    full_name: str = ""


class LoginReq(BaseModel):
    email: str = Field(min_length=3, max_length=200)
    password: str = Field(min_length=1, max_length=128)


def _valid_email(e: str) -> bool:
    return "@" in e and "." in e.split("@")[-1] and len(e) <= 200


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str


def _hash_pw(pw: str) -> str:
    # sha256 trước → tránh giới hạn 72 byte của bcrypt với mật khẩu/ký tự Việt dài.
    d = hashlib.sha256(pw.encode("utf-8")).hexdigest().encode("utf-8")
    return bcrypt.hashpw(d, bcrypt.gensalt()).decode("utf-8")


def _verify_pw(pw: str, hashed: str) -> bool:
    d = hashlib.sha256(pw.encode("utf-8")).hexdigest().encode("utf-8")
    try:
        return bcrypt.checkpw(d, hashed.encode("utf-8"))
    except ValueError:
        return False


def _local_auth_allowed() -> None:
    if config.auth_mode() == "supabase":
        raise HTTPException(404, "Dùng đăng nhập Supabase (Google/Email)")


@router.post("/auth/register", response_model=AuthTokenResponse, status_code=201)
def register(req: RegisterReq) -> AuthTokenResponse:
    _local_auth_allowed()
    email = str(req.email).strip().lower()
    if not _valid_email(email):
        raise HTTPException(422, "Email không hợp lệ")
    uid = uuid.uuid4()
    with session_scope() as s:
        if s.execute(select(User).where(User.email == email)).scalar_one_or_none():
            raise HTTPException(409, "Email đã được đăng ký")
        s.add(User(
            id=uid, email=email, password_hash=_hash_pw(req.password),
            auth_provider="local", full_name=req.full_name.strip(), email_verified=False,
        ))
    # tạo workspace + ví + tặng credit (idempotent)
    tenancy.bootstrap_tenant(Principal(user_id=str(uid), email=email, claims={}))
    return AuthTokenResponse(access_token=mint_dev_token(str(uid), email), user_id=str(uid), email=email)


@router.post("/auth/login", response_model=AuthTokenResponse)
def login(req: LoginReq) -> AuthTokenResponse:
    _local_auth_allowed()
    email = str(req.email).strip().lower()
    with session_scope() as s:
        u = s.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if not u or not u.password_hash or not _verify_pw(req.password, u.password_hash):
            raise HTTPException(401, "Sai email hoặc mật khẩu")
        uid, em = str(u.id), u.email
    return AuthTokenResponse(access_token=mint_dev_token(uid, em), user_id=uid, email=em)


@router.post("/tenants/bootstrap", response_model=BootstrapResponse)
def bootstrap(response: Response, principal: Principal = Depends(get_principal)) -> BootstrapResponse:
    """Tạo workspace + ví + free credit lần đầu (idempotent). Gọi sau khi đăng nhập.

    201 khi tạo workspace mới, 200 khi gọi lại (idempotent) — đúng REST, đồng bộ với POST /jobs.
    """
    out = tenancy.bootstrap_tenant(principal)
    response.status_code = status.HTTP_201_CREATED if out.get("created") else status.HTTP_200_OK
    return BootstrapResponse(**out)


@router.get("/auth/me", response_model=MeResponse)
def me(tenant: Tenant = Depends(get_tenant)) -> MeResponse:
    with tenant_session(tenant.org_id) as s:
        w = wallet.ensure_wallet(s, tenant.org_id)
        bal, held = int(w.balance_credits), int(w.held_credits)
    return MeResponse(
        user_id=str(tenant.uid),
        email=tenant.principal.email,
        org_id=tenant.org_id,
        role=tenant.role,
        auth_mode=config.auth_mode(),
        balance_credits=bal,
        held_credits=held,
    )


@router.post("/dev/token", response_model=DevTokenResponse)
def dev_token(req: DevTokenRequest) -> DevTokenResponse:
    """Phát dev JWT (HS256) để verify lớp HTTP không cần Supabase. 404 nếu KHÔNG ở dev-mode."""
    if config.auth_mode() != "dev" or not config.DEV_AUTH_ENABLED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="dev token tắt")
    user_id = req.user_id or str(uuid.uuid4())
    email = (req.email or f"dev-{user_id[:8]}@vietvid.local").strip().lower()
    token = mint_dev_token(user_id, email, ttl_seconds=req.ttl_seconds)
    return DevTokenResponse(
        access_token=token, user_id=user_id, email=email, expires_in=req.ttl_seconds
    )
