"""Router billing — gói credit, tạo nạp (dev/VNPay), IPN VNPay idempotent (R3)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select

from app_api import billing, config, wallet
from app_api.db import tenant_session
from app_api.deps import Tenant, get_tenant
from app_api.models import Payment

router = APIRouter(prefix="/v1/billing", tags=["billing"])


class TopupRequest(BaseModel):
    pack_id: str
    provider: str = "dev"  # dev | vnpay


@router.get("/packs")
def list_packs() -> list[dict]:
    return billing.get_packs()


@router.post("/topup")
def create_topup(req: TopupRequest, tenant: Tenant = Depends(get_tenant)) -> dict:
    org_uuid = uuid.UUID(tenant.org_id)
    if req.provider == "dev" and not config.BILLING_DEV_ENABLED:
        raise HTTPException(status_code=404, detail="Cổng dev đã tắt")
    if req.provider not in ("dev", "vnpay"):
        raise HTTPException(status_code=422, detail="Cổng không hỗ trợ")

    try:
        with tenant_session(tenant.org_id) as s:
            p = billing.create_topup(s, org_uuid, tenant.uid, pack_id=req.pack_id, provider=req.provider)
            payment_id, ext_ref, credits, amount = str(p.id), p.ext_ref, int(p.credits_granted), int(p.amount_vnd)
            if req.provider == "dev":
                # nạp tức thì (local) — cộng credit ngay trong cùng txn.
                billing.apply_topup(s, provider="dev", ext_ref=ext_ref)
                w = wallet.ensure_wallet(s, org_uuid)
                balance = int(w.balance_credits)
            else:
                pay_url = billing.build_vnpay_url(p)
    except billing.BillingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if req.provider == "dev":
        return {"payment_id": payment_id, "provider": "dev", "status": "succeeded",
                "credits": credits, "amount_vnd": amount, "balance_credits": balance}
    return {"payment_id": payment_id, "provider": "vnpay", "status": "pending",
            "credits": credits, "amount_vnd": amount, "pay_url": pay_url}


@router.get("/payments")
def list_payments(tenant: Tenant = Depends(get_tenant)) -> list[dict]:
    with tenant_session(tenant.org_id) as s:
        rows = s.execute(
            select(Payment).where(Payment.org_id == tenant.org_id)
            .order_by(Payment.created_at.desc()).limit(50)
        ).scalars().all()
        return [
            {"id": str(p.id), "provider": p.provider, "amount_vnd": int(p.amount_vnd),
             "credits": int(p.credits_granted), "status": p.status, "created_at": p.created_at}
            for p in rows
        ]


@router.api_route("/ipn/vnpay", methods=["GET", "POST"])
async def vnpay_ipn(request: Request) -> dict:
    """VNPay gọi server-to-server. R3: verify chữ ký → resolve org → apply_topup idempotent."""
    # Chưa cấu hình VNPay → KHÔNG verify bằng secret rỗng (kẻ gian sẽ giả chữ ký được) → từ chối.
    if not config.vnpay_configured():
        return {"RspCode": "97", "Message": "Gateway not configured"}

    params = dict(request.query_params)
    if not params:
        try:
            form = await request.form()
            params = {k: str(v) for k, v in form.items()}
        except Exception:  # noqa: BLE001
            params = {}

    ok, txn_ref = billing.verify_vnpay_ipn(params)
    if not txn_ref:
        return {"RspCode": "01", "Message": "Order not found"}
    if not ok:
        return {"RspCode": "97", "Message": "Invalid signature or unpaid"}

    org_id = billing.org_from_vnpay_txnref(txn_ref)
    if org_id is None:
        return {"RspCode": "01", "Message": "Order not found"}

    with tenant_session(org_id) as s:
        # apply_topup tự idempotent: payment đã SUCCEEDED → trả nguyên (không cộng lần 2).
        existing = s.execute(
            select(Payment).where(Payment.provider == "vnpay", Payment.ext_ref == txn_ref)
        ).scalar_one_or_none()
        if existing is None:
            return {"RspCode": "01", "Message": "Order not found"}
        if existing.status == "SUCCEEDED":
            return {"RspCode": "02", "Message": "Order already confirmed"}
        billing.apply_topup(s, provider="vnpay", ext_ref=txn_ref)
    return {"RspCode": "00", "Message": "Confirm Success"}
