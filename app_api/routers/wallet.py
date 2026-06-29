"""Router wallet — số dư + ví đang giữ + sổ cái (minh bạch giá, mục 8.3 plan)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select

from app_api import wallet as wallet_svc
from app_api.db import tenant_session
from app_api.deps import Tenant, get_tenant
from app_api.models import LedgerEntry
from app_api.schemas import LedgerEntryOut, WalletResponse

router = APIRouter(prefix="/v1/wallet", tags=["wallet"])


@router.get("", response_model=WalletResponse)
def get_wallet(tenant: Tenant = Depends(get_tenant)) -> WalletResponse:
    with tenant_session(tenant.org_id) as s:
        wallet_svc.ensure_wallet(s, tenant.org_id)
        st = wallet_svc.wallet_state(s, tenant.org_id)  # lazy-expire xu gói + 2 loại xu
        return WalletResponse(
            org_id=tenant.org_id,
            balance_credits=st["balance_credits"],
            held_credits=st["held_credits"],
            plan_credits=st["plan_credits"],
            plan_expires_at=st["plan_expires_at"],
            available_credits=st["available_credits"],
        )


@router.get("/ledger", response_model=list[LedgerEntryOut])
def get_ledger(
    tenant: Tenant = Depends(get_tenant),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[LedgerEntryOut]:
    with tenant_session(tenant.org_id) as s:
        rows = s.execute(
            select(LedgerEntry)
            .where(LedgerEntry.org_id == tenant.org_id)
            .order_by(LedgerEntry.id.desc())
            .limit(limit)
        ).scalars().all()
        return [
            LedgerEntryOut(
                id=int(e.id),
                entry_type=e.entry_type,
                delta_credits=int(e.delta_credits),
                balance_after=int(e.balance_after),
                job_id=str(e.job_id) if e.job_id else None,
                payment_id=str(e.payment_id) if e.payment_id else None,
                note=e.note or "",
                created_at=e.created_at,
            )
            for e in rows
        ]
