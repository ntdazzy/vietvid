"""Router admin (Sóng 4) — super-admin vận hành nền tảng. Gated bởi require_admin.

Cross-org KHÔNG dùng BYPASSRLS: bảng global (users/orgs) query thẳng; dữ liệu RLS (ví/job/KOL)
thao tác qua tenant_session(org_id) cho TỪNG org (admin chỉ định org → GUC set → policy cho qua).
Duyệt/thống kê quét theo từng org (số org nhỏ).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from app_api import wallet
from app_api.auth import Principal
from app_api.db import session_scope, tenant_session
from app_api.deps import require_admin
from app_api.models import (
    Job, LedgerEntry, LedgerKind, Membership, Org, User, VvKolPersona, Video,
)

router = APIRouter(prefix="/v1/admin", tags=["admin"], dependencies=[Depends(require_admin)])


def _org_ids() -> list[str]:
    with session_scope() as s:
        return [str(x) for x in s.execute(select(Org.id)).scalars().all()]


# ── Stats ────────────────────────────────────────────────────────────────
@router.get("/stats")
def stats() -> dict:
    with session_scope() as s:
        users = s.execute(select(func.count()).select_from(User)).scalar_one()
        orgs = s.execute(select(func.count()).select_from(Org)).scalar_one()
    jobs = videos = credits_issued = 0
    for org_id in _org_ids():
        with tenant_session(org_id) as s:
            jobs += s.execute(select(func.count()).select_from(Job)).scalar_one()
            videos += s.execute(select(func.count()).select_from(Video)).scalar_one()
            credits_issued += int(s.execute(
                select(func.coalesce(func.sum(LedgerEntry.delta_credits), 0))
                .where(LedgerEntry.entry_type.in_([LedgerKind.TOPUP, LedgerKind.BONUS]))
            ).scalar_one())
    return {"users": users, "orgs": orgs, "jobs": jobs, "videos": videos,
            "credits_issued": credits_issued}


# ── Users ────────────────────────────────────────────────────────────────
class UserRow(BaseModel):
    id: str
    email: str
    full_name: str
    status: str
    org_id: str | None
    plan_code: str | None
    created_at: str | None


@router.get("/users", response_model=list[UserRow])
def list_users(q: str = "", limit: int = 50) -> list[UserRow]:
    limit = max(1, min(limit, 200))
    with session_scope() as s:
        stmt = select(User).order_by(User.created_at.desc()).limit(limit)
        if q.strip():
            stmt = select(User).where(User.email.ilike(f"%{q.strip()}%")).limit(limit)
        users = s.execute(stmt).scalars().all()
        out = []
        for u in users:
            org = s.execute(
                select(Org).join(Membership, Membership.org_id == Org.id)
                .where(Membership.user_id == u.id, Membership.role == "owner")
                .order_by(Org.created_at.asc()).limit(1)
            ).scalar_one_or_none()
            out.append(UserRow(
                id=str(u.id), email=u.email, full_name=u.full_name or "", status=u.status,
                org_id=str(org.id) if org else None, plan_code=org.plan_code if org else None,
                created_at=u.created_at.isoformat() if u.created_at else None,
            ))
        return out


class StatusReq(BaseModel):
    status: str = Field(pattern="^(ACTIVE|SUSPENDED|DELETED)$")


@router.post("/users/{user_id}/status")
def set_user_status(user_id: uuid.UUID, req: StatusReq, admin: Principal = Depends(require_admin)) -> dict:
    with session_scope() as s:
        u = s.get(User, user_id)
        if u is None:
            raise HTTPException(404, "Không tìm thấy user")
        u.status = req.status
    return {"ok": True, "user_id": str(user_id), "status": req.status}


# ── Credit adjust (cộng/trừ tay, ghi ADJUST ledger) ───────────────────────
class CreditAdjustReq(BaseModel):
    amount: int  # >0 cộng, <0 trừ
    note: str = Field(default="", max_length=200)


@router.post("/orgs/{org_id}/credit-adjust")
def credit_adjust(org_id: uuid.UUID, req: CreditAdjustReq) -> dict:
    if req.amount == 0:
        raise HTTPException(422, "amount phải khác 0")
    try:
        with tenant_session(str(org_id)) as s:
            wallet.ensure_wallet(s, org_id)
            bal = wallet.topup(
                s, org_id, req.amount, kind=LedgerKind.ADJUST,
                note=req.note or f"admin adjust {req.amount:+d}",
            )
    except wallet.WalletError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"ok": True, "org_id": str(org_id), "balance_credits": bal}


# ── Moderation queue KOL mặt thật (PENDING) ───────────────────────────────
class ModRow(BaseModel):
    id: str
    org_id: str
    name: str
    avatar_url: str
    description: str


@router.get("/moderation", response_model=list[ModRow])
def moderation_queue() -> list[ModRow]:
    rows: list[ModRow] = []
    for org_id in _org_ids():
        with tenant_session(org_id) as s:
            pend = s.execute(
                select(VvKolPersona).where(
                    VvKolPersona.org_id == uuid.UUID(org_id),
                    VvKolPersona.moderation_status == "PENDING",
                )
            ).scalars().all()
            for k in pend:
                rows.append(ModRow(id=str(k.id), org_id=org_id, name=k.name,
                                   avatar_url=k.avatar_url or "", description=k.description or ""))
    return rows


class ModDecision(BaseModel):
    org_id: str
    approve: bool


@router.post("/moderation/{kol_id}/decision")
def moderate(kol_id: uuid.UUID, req: ModDecision) -> dict:
    new_status = "APPROVED" if req.approve else "BLOCKED"
    with tenant_session(req.org_id) as s:
        k = s.execute(
            select(VvKolPersona).where(
                VvKolPersona.id == kol_id, VvKolPersona.org_id == uuid.UUID(req.org_id)
            )
        ).scalar_one_or_none()
        if k is None:
            raise HTTPException(404, "Không tìm thấy KOL")
        k.moderation_status = new_status
    return {"ok": True, "kol_id": str(kol_id), "status": new_status}
