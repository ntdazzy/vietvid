"""Router billing — gói credit, tạo nạp (dev/VNPay), IPN VNPay idempotent (R3)."""

from __future__ import annotations

import asyncio
import hmac
import json
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select

from app_api import billing, config, events, payment_config, wallet
from app_api.db import session_scope, tenant_session
from app_api.deps import Tenant, get_tenant
from app_api.models import Payment

router = APIRouter(prefix="/v1/billing", tags=["billing"])
log = logging.getLogger("vietvid")


class TopupRequest(BaseModel):
    pack_id: str | None = None         # gói có sẵn
    amount_vnd: int | None = None      # hoặc số tiền tuỳ ý
    provider: str = "dev"  # dev | vnpay | momo | bank_qr


@router.get("/packs")
def list_packs() -> list[dict]:
    # credit_packs là bảng GLOBAL (không RLS) → session_scope.
    with session_scope() as s:
        return billing.get_packs(s)


@router.post("/topup")
def create_topup(req: TopupRequest, tenant: Tenant = Depends(get_tenant)) -> dict:
    org_uuid = uuid.UUID(tenant.org_id)
    provider = req.provider
    if provider == "dev" and not config.BILLING_DEV_ENABLED:
        raise HTTPException(status_code=404, detail="Cổng dev đã tắt")
    if provider not in ("dev", "vnpay", "momo", "bank_qr"):
        raise HTTPException(status_code=422, detail="Cổng không hỗ trợ")
    # Cấu hình thanh toán GLOBAL (admin sửa ở UI) — DB ⊕ env fallback.
    with session_scope() as gs:
        pcfg = payment_config.resolve(gs)
    if not pcfg["enabled"].get(provider, provider == "dev"):
        raise HTTPException(status_code=400, detail="Phương thức này đang tắt")
    if provider == "bank_qr" and not payment_config.bank_ready(pcfg):
        raise HTTPException(status_code=400, detail="Chuyển khoản ngân hàng chưa được cấu hình")

    # Số tiền tuỳ ý (khi không chọn gói): chặn dưới/trên.
    custom_amount = None
    if not req.pack_id:
        if req.amount_vnd is None:
            raise HTTPException(status_code=422, detail="Thiếu pack_id hoặc amount_vnd")
        custom_amount = int(req.amount_vnd)
        if custom_amount < config.TOPUP_MIN_VND or custom_amount > config.TOPUP_MAX_VND:
            raise HTTPException(
                status_code=422,
                detail=f"Số tiền nạp từ {config.TOPUP_MIN_VND:,}đ đến {config.TOPUP_MAX_VND:,}đ",
            )

    pay_url = None
    balance = None
    try:
        with tenant_session(tenant.org_id) as s:
            if custom_amount is not None:
                p = billing.create_payment(
                    s, org_uuid, tenant.uid, provider=provider,
                    amount_vnd=custom_amount, credits=billing.credits_for_amount(custom_amount),
                )
            else:
                p = billing.create_topup(s, org_uuid, tenant.uid, pack_id=req.pack_id, provider=provider)
            payment_id, ext_ref, credits, amount = str(p.id), p.ext_ref, int(p.credits_granted), int(p.amount_vnd)
            if provider == "dev":
                # nạp tức thì (local) — cộng credit ngay trong cùng txn.
                billing.apply_topup(s, provider="dev", ext_ref=ext_ref)
                balance = int(wallet.ensure_wallet(s, org_uuid).balance_credits)
            elif provider == "vnpay":
                pay_url = billing.build_vnpay_url(p)
            elif provider == "momo":
                pay_url = billing.build_momo_payment(p)
    except billing.BillingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if provider == "dev":
        return {"payment_id": payment_id, "provider": "dev", "status": "succeeded",
                "credits": credits, "amount_vnd": amount, "balance_credits": balance}
    if provider == "bank_qr":
        # ext_ref CHÍNH LÀ nội dung chuyển khoản (memo) hiện trên QR. Bank info từ config động.
        return {
            "payment_id": payment_id, "provider": "bank_qr", "status": "pending",
            "credits": credits, "amount_vnd": amount,
            "qr_image_url": billing.vietqr_image_url(
                amount, ext_ref,
                bank_bin=pcfg["bank_bin"], account=pcfg["bank_account"], account_name=pcfg["bank_account_name"],
            ),
            "memo": ext_ref,
            "bank": {
                "name": pcfg["bank_name"], "bin": pcfg["bank_bin"],
                "account_number": pcfg["bank_account"], "account_name": pcfg["bank_account_name"],
            },
        }
    return {"payment_id": payment_id, "provider": provider, "status": "pending",
            "credits": credits, "amount_vnd": amount, "pay_url": pay_url}


@router.get("/payment/{payment_id}")
def get_payment(payment_id: str, tenant: Tenant = Depends(get_tenant)) -> dict:
    """Poll trạng thái 1 payment (UI QR chờ tự cộng). RLS đã giới hạn theo org."""
    try:
        pid = uuid.UUID(payment_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="payment_id không hợp lệ") from exc
    with tenant_session(tenant.org_id) as s:
        p = s.get(Payment, pid)
        if p is None:
            raise HTTPException(status_code=404, detail="Không tìm thấy")
        return {"id": str(p.id), "status": p.status, "provider": p.provider,
                "credits": int(p.credits_granted), "amount_vnd": int(p.amount_vnd)}


@router.get("/payment/{payment_id}/stream")
async def payment_stream(payment_id: str, request: Request) -> StreamingResponse:
    """SSE: đẩy 'đã thanh toán' tức thì khi credit được cộng (thay vì poll 3s).

    Không cần Bearer: payment_id là UUID không-đoán-được (capability), event chỉ chứa
    status + credits (không nhạy cảm) — EventSource không gắn được header Authorization."""

    async def gen():
        q = events.subscribe(payment_id)
        try:
            yield ": connected\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    data = await asyncio.wait_for(q.get(), timeout=15)
                    yield f"data: {json.dumps(data)}\n\n"
                except asyncio.TimeoutError:
                    yield ": ping\n\n"  # heartbeat giữ kết nối sống
        finally:
            events.unsubscribe(payment_id, q)

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"},
    )


@router.post("/payment/{payment_id}/dev-confirm")
def dev_confirm(payment_id: str, tenant: Tenant = Depends(get_tenant)) -> dict:
    """Giả lập 'đã nhận tiền' để thử luồng QR khi chưa nối SePay. Chỉ bật ở chế độ dev."""
    if not config.BILLING_DEV_ENABLED:
        raise HTTPException(status_code=404, detail="Đã tắt")
    try:
        pid = uuid.UUID(payment_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="payment_id không hợp lệ") from exc
    credited = 0
    with tenant_session(tenant.org_id) as s:
        p = s.get(Payment, pid)
        if p is None:
            raise HTTPException(status_code=404, detail="Không tìm thấy")
        if p.status == "PENDING":
            billing.apply_topup(s, provider=p.provider, ext_ref=p.ext_ref)
            credited = int(p.credits_granted)
        balance = int(wallet.ensure_wallet(s, uuid.UUID(tenant.org_id)).balance_credits)
    if credited:  # post-commit → đẩy SSE cho QR panel lật success tức thì
        events.publish(payment_id, {"status": "SUCCEEDED", "credits": credited})
    return {"status": "succeeded", "balance_credits": balance}


@router.post("/ipn/sepay")
async def sepay_webhook(request: Request) -> dict:
    """SePay đọc biến động số dư bank → POST về đây. Auth bằng Apikey token; đối soát memo + SỐ TIỀN.

    apply_topup idempotent (FOR UPDATE) → không cộng 2 lần dù SePay gửi lại."""
    with session_scope() as gs:
        token = payment_config.resolve(gs)["webhook_token"]
    if not token:
        raise HTTPException(status_code=503, detail="Webhook chưa cấu hình token")
    auth = request.headers.get("authorization", "")
    if not hmac.compare_digest(auth, f"Apikey {token}"):
        raise HTTPException(status_code=401, detail="Token không hợp lệ")
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        return {"success": False, "message": "Bad payload"}

    if str(body.get("transferType")) != "in":
        return {"success": True}  # tiền ra — bỏ qua
    content = str(body.get("content") or body.get("description") or "")
    try:
        amount = int(float(body.get("transferAmount") or 0))
    except (TypeError, ValueError):
        return {"success": True, "message": "Số tiền không đọc được"}

    # Đối soát + cộng credit dùng CHUNG với poller email (billing.credit_bank_transfer):
    # bóc memo → tìm đơn PENDING → check đủ tiền (>=) → cộng (idempotent).
    result = billing.credit_bank_transfer(content, amount)
    if result["status"] == "credited":  # đẩy SSE → trình duyệt lật success tức thì
        events.publish(result["payment_id"], {"status": "SUCCEEDED", "credits": result["credits"]})
    elif result["status"] == "insufficient":
        log.warning("bank: memo %s thiếu tiền — nhận %s, cần %s",
                    result.get("memo"), result.get("got"), result.get("need"))
    elif result["status"] == "no_pending":
        log.warning("bank: memo %s không khớp payment PENDING nào", result.get("memo"))
    return {"success": True, "message": result["status"]}


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
        # Đối soát số tiền: VNPay gửi vnp_Amount = số tiền × 100.
        if str(params.get("vnp_Amount")) != str(int(existing.amount_vnd) * 100):
            existing.status = "FAILED"
            return {"RspCode": "04", "Message": "Invalid amount"}
        billing.apply_topup(s, provider="vnpay", ext_ref=txn_ref)
    return {"RspCode": "00", "Message": "Confirm Success"}


@router.post("/ipn/momo")
async def momo_ipn(request: Request) -> dict:
    """MoMo gọi server-to-server (JSON). Verify chữ ký → đối soát SỐ TIỀN → apply idempotent."""
    if not config.momo_configured():
        return {"resultCode": 99, "message": "Gateway not configured"}
    try:
        params = await request.json()
    except Exception:  # noqa: BLE001
        return {"resultCode": 99, "message": "Bad payload"}

    ok, order_id = billing.verify_momo_ipn(params)
    if not order_id:
        return {"resultCode": 99, "message": "Order not found"}
    if not ok:
        return {"resultCode": 99, "message": "Invalid signature or unpaid"}

    org_id = billing.org_from_momo_orderid(order_id)
    if org_id is None:
        return {"resultCode": 99, "message": "Order not found"}

    with tenant_session(org_id) as s:
        existing = s.execute(
            select(Payment).where(Payment.provider == "momo", Payment.ext_ref == order_id)
        ).scalar_one_or_none()
        if existing is None:
            return {"resultCode": 99, "message": "Order not found"}
        if existing.status == "SUCCEEDED":
            return {"resultCode": 0, "message": "Already confirmed"}
        # Đối soát số tiền (fix lỗ hổng audit: IPN phải khớp amount đã tạo).
        if str(params.get("amount")) != str(int(existing.amount_vnd)):
            existing.status = "FAILED"
            return {"resultCode": 99, "message": "Amount mismatch"}
        billing.apply_topup(s, provider="momo", ext_ref=order_id)
    return {"resultCode": 0, "message": "Confirm Success"}
