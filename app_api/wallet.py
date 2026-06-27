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
    """Tạo ví nếu chưa có (lúc tạo org). Idempotent."""
    w = session.get(Wallet, org_id)
    if w is None:
        w = Wallet(org_id=org_id, balance_credits=0, held_credits=0, version=0)
        session.add(w)
        session.flush()
    return w


def _lock(session: Session, org_id) -> Wallet:
    w = session.execute(
        select(Wallet).where(Wallet.org_id == org_id).with_for_update()
    ).scalar_one_or_none()
    if w is None:
        raise WalletNotFound(str(org_id))
    return w


def _terminal_done(session: Session, job_id) -> bool:
    """Job đã SETTLE/REFUND chưa (idempotent guard)."""
    return bool(
        session.execute(
            select(func.count())
            .select_from(LedgerEntry)
            .where(
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
    if _terminal_done(session, job_id):
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
    if _terminal_done(session, job_id):
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


def topup(session: Session, org_id, credits: int, *, payment_id=None, ref_group=None, note: str = "") -> int:
    """Nạp credit (billing) hoặc tặng (grant/bonus). balance += credits; ghi TOPUP."""
    w = _lock(session, org_id)
    w.balance_credits += credits
    w.version += 1
    session.add(LedgerEntry(
        org_id=org_id, entry_type=LedgerKind.TOPUP, delta_credits=credits,
        balance_after=w.balance_credits, payment_id=payment_id,
        ref_group=ref_group or uuid.uuid4(), note=note or "topup",
    ))
    session.flush()
    return w.balance_credits


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
