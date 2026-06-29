"""Billing — nạp credit đa cổng (mục 7.3). Adapter: dev (nạp tức thì, local) + VNPay (URL + IPN).

apply_topup IDEMPOTENT (SELECT ... FOR UPDATE trên payment + check status) = chống IPN replay (R3):
mỗi payment cộng credit ĐÚNG MỘT lần dù IPN gọi nhiều lần. ext_ref UNIQUE(provider) là lưới cuối.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import hmac
import re
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


_MEMO_RE = re.compile(r"VYRA[0-9A-F]{8}")


def credits_for_amount(amount_vnd: int) -> int:
    """Quy đổi VND → credit theo giá gốc (1 credit = CREDIT_PRICE_VND đ)."""
    return max(1, round(int(amount_vnd) / config.CREDIT_PRICE_VND))


def _bank_memo() -> str:
    """Nội dung chuyển khoản duy nhất để đối soát — ngắn, không dấu, dễ gõ."""
    return "VYRA" + uuid.uuid4().hex[:8].upper()


def _ext_ref_for(provider: str, org_id) -> str:
    # bank_qr: ext_ref = memo (ngắn, hiện trên QR). VNPay/MoMo: nhúng org để IPN không-auth resolve.
    if provider == "bank_qr":
        return _bank_memo()
    if provider in ("vnpay", "momo"):
        return uuid.UUID(str(org_id)).hex + uuid.uuid4().hex[:8]
    return uuid.uuid4().hex  # dev


def create_payment(
    session: Session, org_id, user_id, *,
    provider: str, amount_vnd: int, credits: int, credit_pack_id=None, raw_payload=None,
) -> Payment:
    """Tạo Payment PENDING (gói lẻ / tuỳ ý / gói tháng). ext_ref theo provider.
    raw_payload có {"plan_code": ...} → apply_topup cấp XU GÓI (hết hạn) thay vì xu mua."""
    p = Payment(
        org_id=org_id, user_id=user_id, provider=provider, ext_ref=_ext_ref_for(provider, org_id),
        amount_vnd=int(amount_vnd), credits_granted=int(credits),
        credit_pack_id=credit_pack_id, status=PaymentStatus.PENDING,
        raw_payload=raw_payload or {},
    )
    session.add(p)
    session.flush()
    return p


def get_plans(session: Session) -> list[dict]:
    """Catalog gói tháng (subscription) đang bật, từ DB."""
    from app_api.models import Plan

    rows = session.execute(
        select(Plan).where(Plan.is_active.is_(True)).order_by(Plan.sort_order)
    ).scalars().all()
    return [{
        "code": p.code, "name": p.name, "name_vi": p.name_vi,
        "monthly_price_vnd": int(p.monthly_price_vnd), "credits": int(p.monthly_credit_grant),
        "max_resolution": p.max_resolution, "max_seconds": int(p.max_seconds),
        "watermark_free": bool(p.watermark_free),
    } for p in rows if p.monthly_price_vnd > 0]


def create_plan_purchase(session: Session, org_id, user_id, *, plan_code: str, provider: str) -> Payment:
    """Tạo payment MUA GÓI THÁNG: giá + xu lấy từ Plan; raw_payload gắn plan_code → apply_topup
    cấp xu gói (hết hạn 30n) + set org.plan_code khi thanh toán xong."""
    from app_api.models import Plan

    plan = session.get(Plan, plan_code)
    if plan is None or not plan.is_active or plan.monthly_price_vnd <= 0:
        raise BillingError(f"Gói không hợp lệ: {plan_code}")
    return create_payment(
        session, org_id, user_id, provider=provider,
        amount_vnd=int(plan.monthly_price_vnd), credits=int(plan.monthly_credit_grant),
        raw_payload={"plan_code": plan.code},
    )


def create_topup(session: Session, org_id, user_id, *, pack_id: str, provider: str) -> Payment:
    pack = _pack_by_code(session, pack_id)
    if pack is None:
        raise BillingError(f"Gói không hợp lệ: {pack_id}")
    return create_payment(
        session, org_id, user_id, provider=provider,
        amount_vnd=int(pack.amount_vnd), credits=int(pack.credits), credit_pack_id=pack.id,
    )


# ── VietQR (chuyển khoản ngân hàng) — keyless, quét bằng app bank bất kỳ ───
def vietqr_image_url(amount_vnd: int, memo: str, *, bank_bin: str, account: str, account_name: str) -> str:
    """Ảnh VietQR (napas247) sinh từ thông tin tài khoản nhận — không cần API key.
    Bank info truyền vào (từ payment_config động) thay vì đọc env tĩnh."""
    base = f"https://img.vietqr.io/image/{bank_bin}-{account}-{config.BANK_QR_TEMPLATE}.png"
    return (
        f"{base}?amount={int(amount_vnd)}"
        f"&addInfo={quote(memo, safe='')}"
        f"&accountName={quote(account_name, safe='')}"
    )


def parse_sepay_memo(content: str) -> str | None:
    """Bóc mã VYRAxxxxxxxx khỏi nội dung chuyển khoản SePay gửi về."""
    if not content:
        return None
    m = _MEMO_RE.search(content.upper())
    return m.group(0) if m else None


def resolve_bank_payment_org(memo: str) -> str | None:
    """Tìm org của 1 payment bank_qr theo memo (ext_ref unique toàn cục per-provider).

    Khớp cả PENDING lẫn SUCCEEDED: thông báo-trùng (SePay/poller gửi lại sau khi đã cộng)
    cần resolve được org để credit_bank_transfer trả 'already' (idempotent rõ ràng) thay vì
    'no_pending' giả — tránh cảnh báo "memo không khớp" sai trên log. Cộng-đôi vẫn bị chặn
    bởi FOR UPDATE + check status SUCCEEDED trong credit_bank_transfer.

    TODO(scale): thay vòng lặp org bằng bảng GLOBAL memo→org (mẫu webhook_events trong
    SYSTEM_DESIGN) trước khi mở bán — O(orgs) chỉ chấp nhận được khi webhook tần suất thấp."""
    from app_api.db import session_scope, tenant_session
    from app_api.models import Org

    with session_scope() as s:
        org_ids = [str(x) for x in s.execute(select(Org.id)).scalars().all()]
    for org_id in org_ids:
        with tenant_session(org_id) as s:
            hit = s.execute(
                select(Payment.id).where(
                    Payment.provider == "bank_qr",
                    Payment.ext_ref == memo,
                    Payment.status.in_([PaymentStatus.PENDING, PaymentStatus.SUCCEEDED]),
                )
            ).scalar_one_or_none()
            if hit is not None:
                return org_id
    return None


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
        return p  # đã cộng → bỏ qua (replay) — bonus cũng KHÔNG chạy lại
    from app_api.models import LedgerEntry, LedgerKind

    # Khuyến mãi nạp lần đầu: lần nạp THÀNH CÔNG đầu tiên của org (0 TOPUP trước đó) → tặng cố định.
    # Đếm trước khi cộng (wallet.topup sắp thêm 1 TOPUP). Replay không tới đây nên chỉ tặng 1 lần/org.
    prior_topups = session.execute(
        select(func.count()).select_from(LedgerEntry).where(
            LedgerEntry.org_id == p.org_id, LedgerEntry.entry_type == LedgerKind.TOPUP
        )
    ).scalar_one()
    plan_code = (p.raw_payload or {}).get("plan_code")
    if plan_code:  # MUA GÓI THÁNG → cấp XU GÓI (hết hạn 30n, reset gói cũ) + gắn nhãn gói cho org
        wallet.grant_plan_credits(
            session, p.org_id, int(p.credits_granted), days=30, payment_id=p.id,
            note=f"gói {plan_code} +{int(p.credits_granted)} ({int(p.amount_vnd):,}đ)",
        )
        from app_api.models import Org

        org = session.get(Org, p.org_id)
        if org is not None:
            org.plan_code = plan_code
    else:  # NẠP LẺ / PACK → xu mua (không hết hạn)
        wallet.topup(
            session, p.org_id, int(p.credits_granted), payment_id=p.id,
            note=f"nạp {int(p.amount_vnd):,}đ ({p.provider})",
        )
    bonus = config.FIRST_TOPUP_BONUS_CREDITS if (prior_topups == 0 and config.FIRST_TOPUP_BONUS_CREDITS > 0) else 0
    if bonus:
        wallet.topup(
            session, p.org_id, bonus, payment_id=p.id, kind=LedgerKind.BONUS,
            note=f"khuyến mãi nạp lần đầu +{bonus}",
        )
    p.status = PaymentStatus.SUCCEEDED
    p.settled_at = func.now()
    session.flush()
    from app_api import notify

    _bonus_txt = f" +{bonus} thưởng nạp lần đầu 🎁" if bonus else ""
    notify.create(
        session, p.org_id, type="payment", title="Đã nạp credit thành công 💳",
        body=f"+{int(p.credits_granted):,} credit ({int(p.amount_vnd):,}đ qua {p.provider}).{_bonus_txt}",
        ref_type="payment", ref_id=p.id, user_id=p.user_id,
    )
    return p


# ── Đối soát 1 giao dịch chuyển khoản đến (dùng chung webhook SePay + poller email) ──
def credit_bank_transfer(content: str, amount_vnd: int) -> dict:
    """Đối soát MỘT giao dịch tiền-vào: bóc memo VYRA → tìm đơn PENDING → check ĐỦ tiền
    (trả >= số cần) → cộng credit. Idempotent (FOR UPDATE + status). Nguồn nào gọi cũng được
    (SePay webhook hay poller email MB). Trả {status, memo?, need?, got?}:
      no_memo · no_pending · already · insufficient · credited
    """
    from sqlalchemy import select as _select

    from app_api.db import tenant_session

    memo = parse_sepay_memo(content)
    if not memo:
        return {"status": "no_memo"}
    org_id = resolve_bank_payment_org(memo)
    if org_id is None:
        return {"status": "no_pending", "memo": memo}
    with tenant_session(org_id) as s:
        p = s.execute(
            _select(Payment)
            .where(Payment.provider == "bank_qr", Payment.ext_ref == memo)
            .with_for_update()
        ).scalar_one_or_none()
        if p is None or p.status == PaymentStatus.SUCCEEDED:
            return {"status": "already", "memo": memo}
        if int(amount_vnd) < int(p.amount_vnd):
            # Trả THIẾU → không cộng (để admin xử). Trả ĐỦ/DƯ → cộng (nhận đúng gói đã đặt).
            return {"status": "insufficient", "memo": memo, "need": int(p.amount_vnd), "got": int(amount_vnd)}
        apply_topup(s, provider="bank_qr", ext_ref=memo)
        pid, credits = str(p.id), int(p.credits_granted)
    return {"status": "credited", "memo": memo, "payment_id": pid, "credits": credits}


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
