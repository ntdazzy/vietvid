"""FastAPI dependencies — auth + tenancy (mục 7 plan, R4).

get_principal: tách Bearer JWT → Principal (401 nếu thiếu/sai).
get_tenant:    Principal → org_id (header X-Org-Id override, mặc định = org sở hữu). 409 nếu
               user chưa có org (cần gọi /v1/tenants/bootstrap). KHÔNG mở DB transaction ở đây —
               chỉ tra membership (bảng global). Handler tự mở tenant_session NGẮN quanh cụm query
               (R4: không giữ lock DB qua call mạng dài).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, status

from app_api import tenancy
from app_api.auth import AuthError, Principal, verify_token


def get_principal(authorization: str | None = Header(default=None)) -> Principal:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Thiếu Authorization: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization[7:].strip()
    try:
        principal = verify_token(token)
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    # Kill-switch: tài khoản bị khoá/xoá không qua được dù token còn hạn.
    # (None = user chưa tồn tại trong DB, vd Supabase JIT → để bootstrap tạo.)
    st = tenancy.user_account_status(tenancy.principal_uuid(principal.user_id))
    if st in ("SUSPENDED", "DELETED"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tài khoản đã bị khoá")
    return principal


@dataclass(frozen=True)
class Tenant:
    org_id: str
    uid: uuid.UUID
    role: str
    principal: Principal


def get_tenant(
    principal: Principal = Depends(get_principal),
    x_org_id: str | None = Header(default=None, alias="X-Org-Id"),
) -> Tenant:
    uid = tenancy.principal_uuid(principal.user_id)
    if x_org_id:
        try:
            uuid.UUID(x_org_id)
        except (ValueError, TypeError) as exc:
            raise HTTPException(status_code=422, detail="X-Org-Id không phải uuid") from exc
        role = tenancy.role_in_org(uid, x_org_id)
        if role is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Không thuộc org này")
        return Tenant(org_id=str(x_org_id), uid=uid, role=role, principal=principal)

    org_id = tenancy.get_default_org_id(uid)
    if org_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Chưa có workspace — gọi POST /v1/tenants/bootstrap trước.",
        )
    role = tenancy.role_in_org(uid, org_id) or "owner"
    return Tenant(org_id=org_id, uid=uid, role=role, principal=principal)


# ── RBAC: chặn theo role (Sóng 1B) ──────────────────────────────────────
def require_role(*roles: str):
    """Dependency factory: chỉ cho qua nếu tenant.role thuộc `roles`. 403 nếu không."""

    def _dep(tenant: Tenant = Depends(get_tenant)) -> Tenant:
        if tenant.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Cần quyền: {', '.join(roles)}",
            )
        return tenant

    return _dep


require_owner = require_role("owner")
