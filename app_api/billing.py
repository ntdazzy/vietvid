"""Billing — nạp credit đa cổng (mục 7.3). Adapter: dev (nạp tức thì, local) + VNPay (URL + IPN).

apply_topup IDEMPOTENT (SELECT ... FOR UPDATE trên payment + check status) = chống IPN replay (R3):
mỗi payment cộng credit ĐÚNG MỘT lần dù IPN gọi nhiều lần. ext_ref UNIQUE(provider) là lưới cuối.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import hmac
import uuid
from urllib.parse import quote

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app_api import config, wallet
from app_api.models import CreditPack, Payment, PaymentStatus


class BillingError(Exception):
    pass


def get_packs(session: Session) -> list[dict]:
    """Catalog gói credit từ DB (data-driven). id = code (ổn định cho frontend)."""
    rows = session.execute(
        select(CreditPack).where(CreditPack.is_active.is_(True)).order_by(CreditPack.sort_order)
    ).scalars().all()
    return [
        {"id": p.code, "code": p.code, "name": p.name,
         "amount_vnd": int(p.amount_vnd), "credits": int(p.credits)}
        for p in rows
    ]


def _pack_by_code(session: Session, code: str) -> CreditPack | None:
    return session.execute(
        select(CreditPack).where(CreditPack.code == code, CreditPack.is_active.is_(True))
    ).scalar_one_or_none()


def create_topup(session: Session, org_id, user_id, *, pack_id: str, provider: str) -> Payment:
    pack = _pack_by_code(session, pack_id)
    if pack is None:
        raise BillingError(f"Gói không hợp lệ: {pack_id}")
    # VNPay/MoMo: nhúng org vào ext_ref để IPN (không-auth) resolve được tenant; dev = uuid ngẫu nhiên.
    ext_ref = (
        uuid.UUID(str(org_id)).hex + uuid.uuid4().hex[:8]
        if provider in ("vnpay", "momo")
        else uuid.uuid4().hex
    )
    p = Payment(
        org_id=org_id, user_id=user_id, provider=provider, ext_ref=ext_ref,
        amount_vnd=int(pack.amount_vnd), credits_granted=int(pack.credits),
        credit_pack_id=pack.id, status=PaymentStatus.PENDING,
    )
    session.add(p)
    session.flush()
    return p


def apply_topup(session: Session, *, provider: str, ext_ref: str) -> Payment | None:
    """Cộng credit cho payment ĐÚNG MỘT lần. FOR UPDATE + check SUCCEEDED = idempotent (R3)."""
    p = session.execute(
        select(Payment)
        .where(Payment.provider == provider, Payment.ext_ref == ext_ref)
        .with_for_update()
    ).scalar_one_or_none()
    if p is None:
        return None
    if p.status == PaymentStatus.SUCCEEDED:
        return p  # đã cộng → bỏ qua (replay)
    wallet.topup(
        session, p.org_id, int(p.credits_granted), payment_id=p.id,
        note=f"nạp {int(p.amount_vnd):,}đ ({p.provider})",
    )
    p.status = PaymentStatus.SUCCEEDED
    p.settled_at = func.now()
    session.flush()
    return p


# ── VNPay adapter ────────────────────────────────────────────────────────
def _sign(query: str) -> str:
    return hmac.new(config.VNPAY_HASH_SECRET.encode(), query.encode(), hashlib.sha512).hexdigest()


def _query(params: dict) -> str:
    return "&".join(f"{k}={quote(str(v), safe='')}" for k, v in sorted(params.items()))


def build_vnpay_url(payment: Payment, client_ip: str = "127.0.0.1") -> str:
    if not config.vnpay_configured():
        raise BillingError("VNPay chưa cấu hình (thiếu TMN_CODE / HASH_SECRET)")
    params = {
        "vnp_Version": "2.1.0", "vnp_Command": "pay", "vnp_TmnCode": config.VNPAY_TMN_CODE,
        "vnp_Amount": str(int(payment.amount_vnd) * 100), "vnp_CurrCode": "VND",
        "vnp_TxnRef": payment.ext_ref, "vnp_OrderInfo": f"Nap {payment.credits_granted} credit VietVid",
        "vnp_OrderType": "other", "vnp_Locale": "vn", "vnp_ReturnUrl": config.VNPAY_RETURN_URL,
        "vnp_IpAddr": client_ip, "vnp_CreateDate": _dt.datetime.now().strftime("%Y%m%d%H%M%S"),
    }
    q = _query(params)
    return f"{config.VNPAY_URL}?{q}&vnp_SecureHash={_sign(q)}"


def verify_vnpay_ipn(params: dict) -> tuple[bool, str]:
    """(chữ ký hợp lệ VÀ giao dịch thành công, vnp_TxnRef)."""
    recv = params.get("vnp_SecureHash", "")
    data = {k: v for k, v in params.items() if k not in ("vnp_SecureHash", "vnp_SecureHashType")}
    sig_ok = hmac.compare_digest(_sign(_query(data)), recv)
    paid = params.get("vnp_ResponseCode") == "00" and params.get("vnp_TransactionStatus") == "00"
    return (sig_ok and paid), params.get("vnp_TxnRef", "")


def org_from_vnpay_txnref(ext_ref: str) -> str | None:
    """org_id nhúng ở 32 hex đầu của vnp_TxnRef (đã được HMAC ký nên tin được sau verify)."""
    try:
        return str(uuid.UUID(ext_ref[:32]))
    except (ValueError, IndexError):
        return None


# ── MoMo adapter (cổng chính) ─────────────────────────────────────────────
def _momo_sign(raw: str) -> str:
    return hmac.new(config.MOMO_SECRET_KEY.encode(), raw.encode(), hashlib.sha256).hexdigest()


def build_momo_payment(payment: Payment) -> str:
    """Gọi MoMo createPayment (server-to-server) → trả payUrl. ext_ref = orderId (nhúng org)."""
    if not config.momo_configured():
        raise BillingError("MoMo chưa cấu hình (thiếu PARTNER_CODE / ACCESS_KEY / SECRET_KEY)")
    import json

    import httpx

    order_id = payment.ext_ref
    request_id = uuid.uuid4().hex
    amount = str(int(payment.amount_vnd))
    order_info = f"Nap {int(payment.credits_granted)} credit VietVid"
    extra_data = ""
    request_type = "captureWallet"
    raw = (
        f"accessKey={config.MOMO_ACCESS_KEY}&amount={amount}&extraData={extra_data}"
        f"&ipnUrl={config.MOMO_IPN_URL}&orderId={order_id}&orderInfo={order_info}"
        f"&partnerCode={config.MOMO_PARTNER_CODE}&redirectUrl={config.MOMO_RETURN_URL}"
        f"&requestId={request_id}&requestType={request_type}"
    )
    body = {
        "partnerCode": config.MOMO_PARTNER_CODE, "accessKey": config.MOMO_ACCESS_KEY,
        "requestId": request_id, "amount": amount, "orderId": order_id,
        "orderInfo": order_info, "redirectUrl": config.MOMO_RETURN_URL,
        "ipnUrl": config.MOMO_IPN_URL, "extraData": extra_data, "requestType": request_type,
        "signature": _momo_sign(raw), "lang": "vi",
    }
    try:
        resp = httpx.post(config.MOMO_ENDPOINT, json=body, timeout=20)
        data = resp.json()
    except (httpx.HTTPError, json.JSONDecodeError) as exc:
        raise BillingError(f"MoMo lỗi kết nối: {exc}") from exc
    pay_url = data.get("payUrl")
    if not pay_url:
        raise BillingError(f"MoMo từ chối: {data.get('message', data)}")
    return pay_url


def verify_momo_ipn(params: dict) -> tuple[bool, str]:
    """(chữ ký hợp lệ VÀ resultCode==0, orderId). MoMo IPN ký theo thứ tự field cố định."""
    if not config.momo_configured():
        return False, params.get("orderId", "")
    recv = params.get("signature", "")
    raw = (
        f"accessKey={config.MOMO_ACCESS_KEY}&amount={params.get('amount','')}"
        f"&extraData={params.get('extraData','')}&message={params.get('message','')}"
        f"&orderId={params.get('orderId','')}&orderInfo={params.get('orderInfo','')}"
        f"&orderType={params.get('orderType','')}&partnerCode={params.get('partnerCode','')}"
        f"&payType={params.get('payType','')}&requestId={params.get('requestId','')}"
        f"&responseTime={params.get('responseTime','')}&resultCode={params.get('resultCode','')}"
        f"&transId={params.get('transId','')}"
    )
    sig_ok = hmac.compare_digest(_momo_sign(raw), recv)
    paid = str(params.get("resultCode")) == "0"
    return (sig_ok and paid), params.get("orderId", "")


def org_from_momo_orderid(order_id: str) -> str | None:
    """org_id nhúng 32 hex đầu của orderId (giống VNPay ext_ref)."""
    try:
        return str(uuid.UUID(order_id[:32]))
    except (ValueError, IndexError):
        return None
