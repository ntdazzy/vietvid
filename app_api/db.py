"""Engine + session cho app_api. Fork-safe lazy engine (mượn pattern core/database.py).

`tenant_session(org_id)` = transaction NGẮN có set GUC RLS ngay đầu (mục 6.1 + R4 plan):
KHÔNG bọc cả request trong 1 transaction (giữ lock lúc gọi API chậm) → mở/đóng quanh cụm query.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app_api.config import DATABASE_URL, RLS_GUC


class Base:
    """Khai báo qua DeclarativeBase ở models.py — re-export để alembic/env.py import 1 chỗ."""


# ── Fork-safe lazy engine (1 engine / PID) ───────────────────────────────
_engine = None
_engine_pid: int | None = None
_Session: sessionmaker | None = None


def _get_engine():
    global _engine, _engine_pid, _Session
    pid = os.getpid()
    if _engine is None or _engine_pid != pid:
        # fork → bỏ engine cũ (không đóng socket cha), tạo mới cho PID này.
        _engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            future=True,
        )
        _engine_pid = pid
        _Session = sessionmaker(bind=_engine, expire_on_commit=False, future=True)
    return _engine


def get_sessionmaker() -> sessionmaker:
    _get_engine()
    assert _Session is not None
    return _Session


@contextmanager
def session_scope() -> Iterator[Session]:
    """Transaction thường (không tenant scope) — dùng cho bảng global (users/plans)."""
    session = get_sessionmaker()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def tenant_session(org_id: str) -> Iterator[Session]:
    """Transaction NGẮN cho dữ liệu tenant: set `vietvid.current_org` ngay đầu → RLS lọc.

    `SET LOCAL` chỉ sống trong transaction này (an toàn với PgBouncer transaction-mode).
    KHÔNG giữ transaction qua call mạng dài — mở/đóng quanh cụm query.
    """
    session = get_sessionmaker()()
    try:
        # bind tham số an toàn (org_id là uuid string từ JWT đã xác thực).
        session.execute(text(f"SET LOCAL {RLS_GUC} = :org"), {"org": str(org_id)})
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
