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
    # VNPay: nhúng org vào ext_ref để IPN (không-auth) resolve được tenant; dev = uuid ngẫu nhiên.
    ext_ref = (
        uuid.UUID(str(org_id)).hex + uuid.uuid4().hex[:8]
        if provider == "vnpay"
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
