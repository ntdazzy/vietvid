"""Router orgs — quản lý thành viên + lời mời (Sóng 1C).

Bảng global (memberships/org_invitations/users/orgs) → session_scope + lọc org_id tường minh.
Owner-only cho mời/xoá/thu hồi (require_owner). Mọi member xem được danh sách.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from app_api import email as email_mod
from app_api.auth import Principal
from app_api.db import session_scope
from app_api.deps import Tenant, get_principal, get_tenant, require_owner
from app_api.models import Membership, Org, OrgInvitation, User

router = APIRouter(prefix="/v1/orgs", tags=["orgs"])

_INVITE_TTL = 60 * 60 * 24 * 7  # 7 ngày
_INVITE_ROLES = {"member", "admin"}


def _now() -> _dt.datetime:
    return _dt.datetime.now(tz=_dt.timezone.utc)


def _hash(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# ── Models ───────────────────────────────────────────────────────────────
class MemberOut(BaseModel):
    user_id: str
    email: str
    full_name: str
    role: str
    status: str
    is_owner: bool


class InviteReq(BaseModel):
    email: str = Field(min_length=3, max_length=200)
    role: str = Field(default="member")


class InviteOut(BaseModel):
    id: str
    email: str
    role: str
    status: str
    expires_at: _dt.datetime


class AcceptReq(BaseModel):
    token: str = Field(min_length=10, max_length=200)


class OkResponse(BaseModel):
    ok: bool = True
    detail: str = ""


# ── Thành viên ──────────────────────────────────────────────────────────
@router.get("/members", response_model=list[MemberOut])
def list_members(tenant: Tenant = Depends(get_tenant)) -> list[MemberOut]:
    org_uuid = uuid.UUID(tenant.org_id)
    with session_scope() as s:
        org = s.get(Org, org_uuid)
        owner_id = org.owner_user_id if org else None
        rows = s.execute(
            select(Membership, User)
            .join(User, User.id == Membership.user_id)
            .where(Membership.org_id == org_uuid)
            .order_by(Membership.created_at.asc())
        ).all()
        return [
            MemberOut(
                user_id=str(m.user_id), email=u.email, full_name=u.full_name or "",
                role=m.role, status=m.status, is_owner=(m.user_id == owner_id),
            )
            for m, u in rows
        ]


@router.delete("/members/{user_id}", response_model=OkResponse)
def remove_member(user_id: uuid.UUID, tenant: Tenant = Depends(require_owner)) -> OkResponse:
    org_uuid = uuid.UUID(tenant.org_id)
    with session_scope() as s:
        org = s.get(Org, org_uuid)
        if org and org.owner_user_id == user_id:
            raise HTTPException(400, "Không thể xoá chủ workspace")
        if user_id == tenant.uid:
            raise HTTPException(400, "Không thể tự xoá mình")
        m = s.execute(
            select(Membership).where(
                Membership.org_id == org_uuid, Membership.user_id == user_id
            )
        ).scalar_one_or_none()
        if m is None:
            raise HTTPException(404, "Không phải thành viên")
        s.delete(m)
    return OkResponse(detail="Đã xoá thành viên")


# ── Lời mời ─────────────────────────────────────────────────────────────
@router.get("/invites", response_model=list[InviteOut])
def list_invites(tenant: Tenant = Depends(require_owner)) -> list[InviteOut]:
    org_uuid = uuid.UUID(tenant.org_id)
    with session_scope() as s:
        rows = s.execute(
            select(OrgInvitation)
            .where(OrgInvitation.org_id == org_uuid, OrgInvitation.status == "PENDING")
            .order_by(OrgInvitation.created_at.desc())
        ).scalars().all()
        return [
            InviteOut(id=str(i.id), email=i.email, role=i.role, status=i.status,
                      expires_at=i.expires_at)
            for i in rows
        ]


@router.post("/invite", response_model=InviteOut, status_code=201)
def create_invite(req: InviteReq, tenant: Tenant = Depends(require_owner)) -> InviteOut:
    email = str(req.email).strip().lower()
    role = req.role if req.role in _INVITE_ROLES else "member"
    org_uuid = uuid.UUID(tenant.org_id)
    raw = secrets.token_urlsafe(32)
    with session_scope() as s:
        org = s.get(Org, org_uuid)
        # đã là thành viên?
        existing_user = s.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if existing_user:
            m = s.execute(
                select(Membership).where(
                    Membership.org_id == org_uuid, Membership.user_id == existing_user.id
                )
            ).scalar_one_or_none()
            if m is not None:
                raise HTTPException(409, "Người này đã là thành viên")
        # thu hồi lời mời PENDING cũ cùng email (tránh trùng)
        for old in s.execute(
            select(OrgInvitation).where(
                OrgInvitation.org_id == org_uuid, OrgInvitation.email == email,
                OrgInvitation.status == "PENDING",
            )
        ).scalars().all():
            old.status = "REVOKED"
        inv = OrgInvitation(
            org_id=org_uuid, email=email, role=role, token_hash=_hash(raw),
            invited_by=tenant.uid, expires_at=_now() + _dt.timedelta(seconds=_INVITE_TTL),
        )
        s.add(inv)
        s.flush()
        out = InviteOut(id=str(inv.id), email=email, role=role, status="PENDING",
                        expires_at=inv.expires_at)
        org_name = org.name if org else "workspace"
    email_mod.send_invite(email, raw, org_name)
    return out


@router.delete("/invites/{invite_id}", response_model=OkResponse)
def revoke_invite(invite_id: uuid.UUID, tenant: Tenant = Depends(require_owner)) -> OkResponse:
    org_uuid = uuid.UUID(tenant.org_id)
    with session_scope() as s:
        inv = s.execute(
            select(OrgInvitation).where(
                OrgInvitation.id == invite_id, OrgInvitation.org_id == org_uuid
            )
        ).scalar_one_or_none()
        if inv is None:
            raise HTTPException(404, "Không tìm thấy lời mời")
        inv.status = "REVOKED"
    return OkResponse(detail="Đã thu hồi lời mời")


@router.post("/accept-invite", response_model=OkResponse)
def accept_invite(req: AcceptReq, principal: Principal = Depends(get_principal)) -> OkResponse:
    """Chấp nhận lời mời (đang đăng nhập). Phải đúng email được mời."""
    from app_api import tenancy

    uid = tenancy.principal_uuid(principal.user_id)
    with session_scope() as s:
        inv = s.execute(
            select(OrgInvitation).where(OrgInvitation.token_hash == _hash(req.token))
        ).scalar_one_or_none()
        if inv is None or inv.status != "PENDING" or inv.expires_at <= _now():
            raise HTTPException(400, "Lời mời không hợp lệ hoặc đã hết hạn")
        u = s.get(User, uid)
        if u is None:
            raise HTTPException(404, "Cần đăng ký tài khoản trước")
        if u.email.lower() != inv.email.lower():
            raise HTTPException(403, "Lời mời này dành cho email khác")
        # đã là thành viên?
        m = s.execute(
            select(Membership).where(
                Membership.org_id == inv.org_id, Membership.user_id == uid
            )
        ).scalar_one_or_none()
        if m is None:
            s.add(Membership(org_id=inv.org_id, user_id=uid, role=inv.role,
                             invited_by=inv.invited_by))
        inv.status = "ACCEPTED"
        inv.accepted_user_id = uid
    return OkResponse(detail="Đã tham gia workspace. Dùng X-Org-Id để chuyển vào.")
