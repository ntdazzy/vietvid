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

from app_api import audit, config, notify, wallet
from app_api.auth import Principal
from app_api.db import session_scope, tenant_session
from app_api.deps import require_admin
from app_api.models import (
    AuditLog, Job, JobStatus, LedgerEntry, LedgerKind, Membership, Org, Payment,
    PaymentStatus, User, VvKolPersona, Video,
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


# ── Economics: doanh thu vs chi phí provider → biên lợi nhuận ──────────────
@router.get("/economics")
def economics() -> dict:
    issued = consumed = revenue_vnd = 0
    cost_usd = 0.0
    by_status: dict[str, int] = {}
    for org_id in _org_ids():
        with tenant_session(org_id) as s:
            issued += int(s.execute(
                select(func.coalesce(func.sum(LedgerEntry.delta_credits), 0))
                .where(LedgerEntry.entry_type.in_([LedgerKind.TOPUP, LedgerKind.BONUS]))
            ).scalar_one())
            consumed += int(-s.execute(
                select(func.coalesce(func.sum(LedgerEntry.delta_credits), 0))
                .where(LedgerEntry.entry_type == LedgerKind.SETTLE)
            ).scalar_one())
            cost_usd += float(s.execute(
                select(func.coalesce(func.sum(Job.actual_cost_usd), 0))
            ).scalar_one() or 0)
            revenue_vnd += int(s.execute(
                select(func.coalesce(func.sum(Payment.amount_vnd), 0))
                .where(Payment.status == PaymentStatus.SUCCEEDED)
            ).scalar_one())
            for st, c in s.execute(select(Job.status, func.count()).group_by(Job.status)).all():
                by_status[st] = by_status.get(st, 0) + int(c)
    cost_vnd = int(cost_usd * config.USD_TO_VND)
    total = sum(by_status.values()) or 1
    return {
        "credits_issued": issued, "credits_consumed": consumed,
        "provider_cost_usd": round(cost_usd, 2), "provider_cost_vnd": cost_vnd,
        "revenue_vnd": revenue_vnd, "margin_vnd": revenue_vnd - cost_vnd,
        "jobs_total": sum(by_status.values()), "jobs_by_status": by_status,
        "success_rate": round(by_status.get(JobStatus.READY, 0) / total * 100, 1),
    }


# ── Broadcast: gửi 1 thông báo tới mọi workspace ───────────────────────────
class BroadcastReq(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    body: str = Field(default="", max_length=500)


@router.post("/broadcast")
def broadcast(req: BroadcastReq, admin: Principal = Depends(require_admin)) -> dict:
    sent = 0
    for org_id in _org_ids():
        try:
            with tenant_session(org_id) as s:
                notify.create(s, org_id, type="system", title=req.title, body=req.body)
            sent += 1
        except Exception:  # noqa: BLE001
            pass
    with session_scope() as s:
        audit.record(s, action="broadcast", actor_email=admin.email,
                     actor_user_id=admin.user_id, detail={"title": req.title, "sent": sent})
    return {"ok": True, "sent": sent}


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
        audit.record(s, action="user.status", actor_email=admin.email,
                     actor_user_id=admin.user_id,
                     detail={"user_id": str(user_id), "status": req.status})
    return {"ok": True, "user_id": str(user_id), "status": req.status}


# ── Credit adjust (cộng/trừ tay, ghi ADJUST ledger) ───────────────────────
class CreditAdjustReq(BaseModel):
    amount: int  # >0 cộng, <0 trừ
    note: str = Field(default="", max_length=200)


@router.post("/orgs/{org_id}/credit-adjust")
def credit_adjust(org_id: uuid.UUID, req: CreditAdjustReq,
                  admin: Principal = Depends(require_admin)) -> dict:
    if req.amount == 0:
        raise HTTPException(422, "amount phải khác 0")
    try:
        with tenant_session(str(org_id)) as s:
            wallet.ensure_wallet(s, org_id)
            bal = wallet.topup(
                s, org_id, req.amount, kind=LedgerKind.ADJUST,
                note=req.note or f"admin adjust {req.amount:+d}",
            )
            audit.record(s, action="credit.adjust", actor_email=admin.email,
                         actor_user_id=admin.user_id, org_id=str(org_id),
                         detail={"amount": req.amount, "note": req.note})
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
def moderate(kol_id: uuid.UUID, req: ModDecision, admin: Principal = Depends(require_admin)) -> dict:
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
        audit.record(s, action="kol.moderate", actor_email=admin.email,
                     actor_user_id=admin.user_id, org_id=req.org_id,
                     detail={"kol_id": str(kol_id), "status": new_status})
    return {"ok": True, "kol_id": str(kol_id), "status": new_status}


# ── Audit log viewer ──────────────────────────────────────────────────────
class AuditRow(BaseModel):
    id: int
    action: str
    actor_email: str
    org_id: str | None
    detail: dict
    created_at: str | None


@router.get("/audit", response_model=list[AuditRow])
def list_audit(limit: int = 50) -> list[AuditRow]:
    limit = max(1, min(limit, 200))
    with session_scope() as s:
        rows = s.execute(
            select(AuditLog).order_by(AuditLog.id.desc()).limit(limit)
        ).scalars().all()
        return [
            AuditRow(id=r.id, action=r.action, actor_email=r.actor_email or "",
                     org_id=str(r.org_id) if r.org_id else None, detail=dict(r.detail or {}),
                     created_at=r.created_at.isoformat() if r.created_at else None)
            for r in rows
        ]
