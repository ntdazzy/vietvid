"""Ví credit ACID (mục 6.3 plan). Mọi thao tác tiền:
- SELECT ... FOR UPDATE khóa hàng wallet → serialize hold song song (hết race over-draw).
- ledger_entries append-only = nguồn chân lý; wallets.balance là CACHE ghi CÙNG transaction.
- CHECK(balance>=0) là lưới chặn cuối ở DB; pre-check sau FOR UPDATE cho lỗi sạch (không abort txn).
- HOLD rồi ĐÚNG MỘT trong {SETTLE, REFUND} mỗi job (idempotent).

Hàm chạy TRONG transaction của caller (tenant_session(org_id) đã set GUC RLS). Caller commit.
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app_api.config import CREDIT_PRICE_VND, USD_TO_VND
from app_api.models import LedgerEntry, LedgerKind, Wallet
from app_api.pricing import usd_to_credits


class WalletError(Exception):
    pass


class WalletNotFound(WalletError):
    pass


class InsufficientCredits(WalletError):
    def __init__(self, need: int, have: int) -> None:
        super().__init__(f"Không đủ credit: cần {need}, có {have}")
        self.need, self.have = need, have


def ensure_wallet(session: Session, org_id) -> Wallet:
    """Tạo ví nếu chưa có. Idempotent + AN TOÀN ĐỒNG THỜI (ON CONFLICT DO NOTHING) — 2 bootstrap
    cùng org chạy song song KHÔNG còn đua INSERT (trước đây lỗi PK abort txn của request thua)."""
    session.execute(
        pg_insert(Wallet)
        .values(org_id=org_id, balance_credits=0, held_credits=0, version=0)
        .on_conflict_do_nothing(index_elements=[Wallet.org_id])
    )
    return session.execute(select(Wallet).where(Wallet.org_id == org_id)).scalar_one()


def _lock(session: Session, org_id) -> Wallet:
    w = session.execute(
        select(Wallet).where(Wallet.org_id == org_id).with_for_update()
    ).scalar_one_or_none()
    if w is None:
        raise WalletNotFound(str(org_id))
    return w


def _terminal_done(session: Session, org_id, job_id) -> bool:
    """Job đã SETTLE/REFUND chưa (idempotent guard). Lọc org_id tường minh (defense-in-depth,
    KHÔNG chỉ dựa RLS) — khớp pattern lọc org_id mọi nơi khác."""
    return bool(
        session.execute(
            select(func.count())
            .select_from(LedgerEntry)
            .where(
                LedgerEntry.org_id == org_id,
                LedgerEntry.job_id == job_id,
                LedgerEntry.entry_type.in_((LedgerKind.SETTLE, LedgerKind.REFUND)),
            )
        ).scalar_one()
    )


def hold(session: Session, org_id, job_id, credits: int, *, ref_group, note: str = "") -> int:
    """Giữ `credits` cho job. FOR UPDATE → pre-check → trừ balance + tăng held + ghi HOLD(-credits)."""
    w = _lock(session, org_id)
    if w.balance_credits < credits:
        raise InsufficientCredits(credits, w.balance_credits)
    w.balance_credits -= credits
    w.held_credits += credits
    w.version += 1
    session.add(LedgerEntry(
        org_id=org_id, entry_type=LedgerKind.HOLD, delta_credits=-credits,
        balance_after=w.balance_credits, job_id=job_id, ref_group=ref_group,
        credit_price_vnd=CREDIT_PRICE_VND, fx_usd_vnd=USD_TO_VND, note=note or "hold for job",
    ))
    session.flush()
    return w.balance_credits


def settle(session: Session, org_id, job_id, *, ref_group, hold_credits: int, actual_usd: float) -> int:
    """Quyết toán: final = min(usd→credit, hold) (KHÔNG quá báo giá); hoàn phần thừa; held -= hold."""
    if _terminal_done(session, org_id, job_id):
        return _balance(session, org_id)
    final = min(usd_to_credits(actual_usd), hold_credits)
    refund_back = hold_credits - final
    w = _lock(session, org_id)
    w.held_credits -= hold_credits
    w.balance_credits += refund_back
    w.version += 1
    session.add(LedgerEntry(
        org_id=org_id, entry_type=LedgerKind.SETTLE, delta_credits=refund_back,
        balance_after=w.balance_credits, job_id=job_id, ref_group=ref_group,
        usd_cost=actual_usd, credit_price_vnd=CREDIT_PRICE_VND, fx_usd_vnd=USD_TO_VND,
        note=f"settle: final={final} hoàn={refund_back}",
    ))
    session.flush()
    return w.balance_credits


def refund(session: Session, org_id, job_id, *, ref_group, hold_credits: int, note: str = "") -> int:
    """Hoàn 100% hold (lỗi hệ thống): balance += hold; held -= hold. Idempotent."""
    if _terminal_done(session, org_id, job_id):
        return _balance(session, org_id)
    w = _lock(session, org_id)
    w.held_credits -= hold_credits
    w.balance_credits += hold_credits
    w.version += 1
    session.add(LedgerEntry(
        org_id=org_id, entry_type=LedgerKind.REFUND, delta_credits=hold_credits,
        balance_after=w.balance_credits, job_id=job_id, ref_group=ref_group,
        note=note or "refund: lỗi hệ thống",
    ))
    session.flush()
    return w.balance_credits


def topup(
    session: Session, org_id, credits: int, *,
    payment_id=None, ref_group=None, note: str = "", kind: str = LedgerKind.TOPUP,
) -> int:
    """Cộng credit. balance += credits; ghi ledger `kind` (TOPUP nạp tiền | BONUS tặng/grant)."""
    if kind not in (LedgerKind.TOPUP, LedgerKind.BONUS, LedgerKind.ADJUST):
        raise WalletError(f"kind không hợp lệ cho topup: {kind}")
    w = _lock(session, org_id)
    w.balance_credits += credits
    w.version += 1
    session.add(LedgerEntry(
        org_id=org_id, entry_type=kind, delta_credits=credits,
        balance_after=w.balance_credits, payment_id=payment_id,
        ref_group=ref_group or uuid.uuid4(), note=note or kind.lower(),
    ))
    session.flush()
    return w.balance_credits


def has_entry_of_kind(session: Session, org_id, kind: str) -> bool:
    """Đã có ledger entry loại `kind` cho org chưa (guard idempotent grant). Chạy trong tenant_session."""
    return bool(
        session.execute(
            select(func.count())
            .select_from(LedgerEntry)
            .where(LedgerEntry.org_id == org_id, LedgerEntry.entry_type == kind)
        ).scalar_one()
    )


def grant_once(session: Session, org_id, credits: int, *, kind: str = LedgerKind.BONUS, note: str = "") -> int:
    """Cộng credit ĐÚNG MỘT lần cho mỗi loại (vd signup BONUS). Trả số đã cộng (0 nếu đã có).

    AN TOÀN ĐUA ĐỒNG THỜI: khóa ví FOR UPDATE TRƯỚC khi check `has_entry_of_kind` → 2 bootstrap
    song song bị serialize trên hàng ví; request thua chờ lock, khi vào thấy entry đã commit → bỏ
    qua. (Trước đây check-rồi-mới-lock có khe hở → cấp BONUS 2 lần.)

    Lưu ý M2 (reset free credit hàng tháng): grant theo CHU KỲ phải dùng key/period riêng — guard
    `kind` đơn thuần ở đây chỉ đúng cho grant-một-lần-đời (signup)."""
    if credits <= 0:
        return 0
    w = _lock(session, org_id)                       # serialize đua grant
    if has_entry_of_kind(session, org_id, kind):
        return 0
    w.balance_credits += credits
    w.version += 1
    session.add(LedgerEntry(
        org_id=org_id, entry_type=kind, delta_credits=credits,
        balance_after=w.balance_credits, ref_group=uuid.uuid4(), note=note or kind.lower(),
    ))
    session.flush()
    return credits


def _balance(session: Session, org_id) -> int:
    w = session.get(Wallet, org_id)
    return int(w.balance_credits) if w else 0


def audit_org(session: Session, org_id) -> dict:
    """Kiểm toán 1 org: cache balance phải == SUM(ledger.delta). Chạy trong tenant_session."""
    cached = _balance(session, org_id)
    ledger_sum = int(
        session.execute(
            select(func.coalesce(func.sum(LedgerEntry.delta_credits), 0))
            .where(LedgerEntry.org_id == org_id)
        ).scalar_one()
    )
    return {"org_id": str(org_id), "cached": cached, "ledger_sum": ledger_sum, "drift": cached - ledger_sum}


def audit_all(session: Session) -> list[dict]:
    """Cron: mọi org lệch cache vs ledger → báo động. Cần role BYPASSRLS/owner (RLS lọc 0 dòng nếu chưa)."""
    rows = session.execute(text(
        "SELECT w.org_id, w.balance_credits AS cached, "
        "COALESCE(SUM(l.delta_credits),0) AS ledger_sum "
        "FROM wallets w LEFT JOIN ledger_entries l ON l.org_id = w.org_id "
        "GROUP BY w.org_id, w.balance_credits "
        "HAVING w.balance_credits <> COALESCE(SUM(l.delta_credits),0)"
    ))
    return [{"org_id": str(r.org_id), "cached": int(r.cached), "ledger_sum": int(r.ledger_sum)} for r in rows]
