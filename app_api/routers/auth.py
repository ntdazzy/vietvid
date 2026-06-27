"""Router auth/tenancy — đăng ký/đăng nhập, vòng đời (reset/verify/refresh/logout/đổi mật khẩu),
bootstrap (idempotent), me, dev-token (chỉ dev-mode).

Các endpoint local-auth (email+mật khẩu, refresh, reset...) tự 404 khi dùng Supabase
(Supabase tự lo các luồng này). Token chỉ lưu HASH (xem app_api/tokens.py).
"""

from __future__ import annotations

import hashlib
import uuid

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from app_api import config, email as email_mod, tenancy, tokens, wallet
from app_api.auth import Principal, mint_dev_token
from app_api.db import session_scope, tenant_session
from app_api.deps import Tenant, get_principal, get_tenant
from app_api.models import TokenPurpose, User
from app_api.schemas import (
    BootstrapResponse,
    DevTokenRequest,
    DevTokenResponse,
    MeResponse,
)

router = APIRouter(prefix="/v1", tags=["auth"])


# ── Models ───────────────────────────────────────────────────────────────
class RegisterReq(BaseModel):
    email: str = Field(min_length=3, max_length=200)
    password: str = Field(min_length=6, max_length=128)
    full_name: str = ""


class LoginReq(BaseModel):
    email: str = Field(min_length=3, max_length=200)
    password: str = Field(min_length=1, max_length=128)


class ForgotReq(BaseModel):
    email: str = Field(min_length=3, max_length=200)


class ResetReq(BaseModel):
    token: str = Field(min_length=10, max_length=200)
    new_password: str = Field(min_length=6, max_length=128)


class VerifyReq(BaseModel):
    token: str = Field(min_length=10, max_length=200)


class ChangePasswordReq(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=6, max_length=128)


class RefreshReq(BaseModel):
    refresh_token: str = Field(min_length=10, max_length=400)


class AuthTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = config.ACCESS_TOKEN_TTL
    user_id: str
    email: str


class OkResponse(BaseModel):
    ok: bool = True
    detail: str = ""


class ProfileUpdateReq(BaseModel):
    full_name: str | None = Field(default=None, max_length=120)
    avatar_url: str | None = Field(default=None, max_length=500)
    locale: str | None = Field(default=None, max_length=10)


class ProfileResponse(BaseModel):
    user_id: str
    email: str
    full_name: str
    avatar_url: str
    locale: str
    email_verified: bool


def _valid_email(e: str) -> bool:
    return "@" in e and "." in e.split("@")[-1] and len(e) <= 200


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


def _issue_session(uid: str, email: str) -> AuthTokenResponse:
    """Phát access (HS256) + refresh (DB, rotate được) cho 1 phiên đăng nhập."""
    with session_scope() as s:
        refresh = tokens.issue(s, uid, TokenPurpose.REFRESH, config.REFRESH_TOKEN_TTL)
    access = mint_dev_token(uid, email, ttl_seconds=config.ACCESS_TOKEN_TTL)
    return AuthTokenResponse(access_token=access, refresh_token=refresh, user_id=uid, email=email)


# ── Đăng ký / Đăng nhập ────────────────────────────────────────────────
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
    # workspace + ví + tặng credit (idempotent)
    tenancy.bootstrap_tenant(Principal(user_id=str(uid), email=email, claims={}))
    # gửi email xác minh (dev: ghi link ra log)
    with session_scope() as s:
        raw_verify = tokens.issue(s, uid, TokenPurpose.EMAIL_VERIFY, config.VERIFY_TOKEN_TTL)
    email_mod.send_verify(email, raw_verify)
    return _issue_session(str(uid), email)


@router.post("/auth/login", response_model=AuthTokenResponse)
def login(req: LoginReq) -> AuthTokenResponse:
    _local_auth_allowed()
    email = str(req.email).strip().lower()
    with session_scope() as s:
        u = s.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if not u or not u.password_hash or not _verify_pw(req.password, u.password_hash):
            raise HTTPException(401, "Sai email hoặc mật khẩu")
        if u.status in ("SUSPENDED", "DELETED"):
            raise HTTPException(403, "Tài khoản đã bị khoá")
        uid, em = str(u.id), u.email
    tenancy.touch_last_login(uuid.UUID(uid))
    return _issue_session(uid, em)


# ── Quên / đặt lại mật khẩu ────────────────────────────────────────────
@router.post("/auth/forgot", response_model=OkResponse)
def forgot(req: ForgotReq) -> OkResponse:
    _local_auth_allowed()
    email = str(req.email).strip().lower()
    # Luôn trả 200 (không tiết lộ email có tồn tại hay không).
    with session_scope() as s:
        u = s.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if u and u.password_hash:
            raw = tokens.issue(s, u.id, TokenPurpose.PASSWORD_RESET, config.RESET_TOKEN_TTL)
        else:
            raw = None
    if raw:
        email_mod.send_reset(email, raw)
    return OkResponse(detail="Nếu email tồn tại, link đặt lại đã được gửi.")


@router.post("/auth/reset", response_model=OkResponse)
def reset(req: ResetReq) -> OkResponse:
    _local_auth_allowed()
    with session_scope() as s:
        uid = tokens.consume(s, req.token, TokenPurpose.PASSWORD_RESET)
        if uid is None:
            raise HTTPException(400, "Token đặt lại không hợp lệ hoặc đã hết hạn")
        u = s.get(User, uid)
        u.password_hash = _hash_pw(req.new_password)
        # đổi mật khẩu = thu hồi mọi phiên cũ (bắt đăng nhập lại).
        tokens.revoke_all(s, uid, TokenPurpose.REFRESH)
    return OkResponse(detail="Đặt lại mật khẩu thành công. Hãy đăng nhập lại.")


# ── Xác minh email ─────────────────────────────────────────────────────
@router.post("/auth/verify", response_model=OkResponse)
def verify_email(req: VerifyReq) -> OkResponse:
    _local_auth_allowed()
    with session_scope() as s:
        uid = tokens.consume(s, req.token, TokenPurpose.EMAIL_VERIFY)
        if uid is None:
            raise HTTPException(400, "Token xác minh không hợp lệ hoặc đã hết hạn")
        u = s.get(User, uid)
        u.email_verified = True
    return OkResponse(detail="Email đã được xác minh.")


@router.post("/auth/resend-verify", response_model=OkResponse)
def resend_verify(principal: Principal = Depends(get_principal)) -> OkResponse:
    _local_auth_allowed()
    uid = tenancy.principal_uuid(principal.user_id)
    with session_scope() as s:
        u = s.get(User, uid)
        if u is None:
            raise HTTPException(404, "Không tìm thấy tài khoản")
        if u.email_verified:
            return OkResponse(detail="Email đã xác minh.")
        tokens.revoke_all(s, uid, TokenPurpose.EMAIL_VERIFY)
        raw = tokens.issue(s, uid, TokenPurpose.EMAIL_VERIFY, config.VERIFY_TOKEN_TTL)
        em = u.email
    email_mod.send_verify(em, raw)
    return OkResponse(detail="Đã gửi lại email xác minh.")


# ── Đổi mật khẩu (đang đăng nhập) ──────────────────────────────────────
@router.post("/auth/change-password", response_model=OkResponse)
def change_password(
    req: ChangePasswordReq, principal: Principal = Depends(get_principal)
) -> OkResponse:
    _local_auth_allowed()
    uid = tenancy.principal_uuid(principal.user_id)
    with session_scope() as s:
        u = s.get(User, uid)
        if u is None or not u.password_hash or not _verify_pw(req.current_password, u.password_hash):
            raise HTTPException(400, "Mật khẩu hiện tại không đúng")
        u.password_hash = _hash_pw(req.new_password)
        tokens.revoke_all(s, uid, TokenPurpose.REFRESH)
    return OkResponse(detail="Đổi mật khẩu thành công. Các phiên khác đã bị đăng xuất.")


# ── Refresh / Logout ───────────────────────────────────────────────────
@router.post("/auth/refresh", response_model=AuthTokenResponse)
def refresh(req: RefreshReq) -> AuthTokenResponse:
    _local_auth_allowed()
    with session_scope() as s:
        tok = tokens.verify_refresh(s, req.refresh_token)
        if tok is None:
            raise HTTPException(401, "Refresh token không hợp lệ hoặc đã hết hạn")
        u = s.get(User, tok.user_id)
        if u is None or u.status in ("SUSPENDED", "DELETED"):
            raise HTTPException(403, "Tài khoản không khả dụng")
        # rotate: thu hồi token cũ + phát token mới.
        tokens.revoke(s, tok)
        new_refresh = tokens.issue(s, u.id, TokenPurpose.REFRESH, config.REFRESH_TOKEN_TTL)
        uid, em = str(u.id), u.email
    access = mint_dev_token(uid, em, ttl_seconds=config.ACCESS_TOKEN_TTL)
    return AuthTokenResponse(access_token=access, refresh_token=new_refresh, user_id=uid, email=em)


@router.post("/auth/logout", response_model=OkResponse)
def logout(req: RefreshReq) -> OkResponse:
    _local_auth_allowed()
    with session_scope() as s:
        tok = tokens.verify_refresh(s, req.refresh_token)
        if tok is not None:
            tokens.revoke(s, tok)
    return OkResponse(detail="Đã đăng xuất.")


# ── Tenancy / identity ─────────────────────────────────────────────────
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
        is_admin=config.is_admin_email(tenant.principal.email),
    )


@router.patch("/auth/me", response_model=ProfileResponse)
def update_profile(
    req: ProfileUpdateReq, principal: Principal = Depends(get_principal)
) -> ProfileResponse:
    """Sửa hồ sơ (tên / avatar / ngôn ngữ). Chỉ cập nhật field được gửi."""
    uid = tenancy.principal_uuid(principal.user_id)
    with session_scope() as s:
        u = s.get(User, uid)
        if u is None:
            raise HTTPException(404, "Không tìm thấy tài khoản")
        if req.full_name is not None:
            u.full_name = req.full_name.strip()
        if req.avatar_url is not None:
            u.avatar_url = req.avatar_url.strip()
        if req.locale is not None:
            u.locale = req.locale.strip() or "vi"
        s.flush()
        return ProfileResponse(
            user_id=str(u.id), email=u.email, full_name=u.full_name or "",
            avatar_url=u.avatar_url or "", locale=u.locale or "vi",
            email_verified=bool(u.email_verified),
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
