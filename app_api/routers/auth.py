"""Router auth/tenancy — bootstrap (idempotent), me, dev-token (chỉ dev-mode)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app_api import config, tenancy, wallet
from app_api.auth import Principal, mint_dev_token
from app_api.db import tenant_session
from app_api.deps import Tenant, get_principal, get_tenant
from app_api.schemas import (
    BootstrapResponse,
    DevTokenRequest,
    DevTokenResponse,
    MeResponse,
)

router = APIRouter(prefix="/v1", tags=["auth"])


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
