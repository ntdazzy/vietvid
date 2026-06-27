"""M1 data model (SQLAlchemy 2.0, Postgres-only). Theo plan mục 6.2.

Bảng M1 tối thiểu bán được: users, orgs, memberships, wallets, ledger_entries,
payments, jobs, job_events, videos. RLS + trigger immutable thêm ở migration 0001.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import CITEXT, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


_PK = lambda: mapped_column(  # noqa: E731
    UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
)
_TS = lambda: mapped_column(DateTime(timezone=True), server_default=func.now())  # noqa: E731


# ── status constants (String, không native Enum — thêm trạng thái không cần ALTER) ──
class OrgStatus:
    ACTIVE, SUSPENDED, DELETED = "ACTIVE", "SUSPENDED", "DELETED"


class LedgerKind:
    TOPUP, HOLD, SETTLE, REFUND, ADJUST, EXPIRE, BONUS = (
        "TOPUP", "HOLD", "SETTLE", "REFUND", "ADJUST", "EXPIRE", "BONUS",
    )


class PaymentStatus:
    PENDING, SUCCEEDED, FAILED, REFUNDED = "PENDING", "SUCCEEDED", "FAILED", "REFUNDED"


class JobStatus:
    WAITING_CONFIG, QUEUED, HELD, RUNNING, QA_FAIL, READY, FAILED, REFUNDED, CANCELLED = (
        "WAITING_CONFIG", "QUEUED", "HELD", "RUNNING", "QA_FAIL", "READY",
        "FAILED", "REFUNDED", "CANCELLED",
    )


class ModerationStatus:
    PENDING, APPROVED, FLAGGED, BLOCKED = "PENDING", "APPROVED", "FLAGGED", "BLOCKED"


# ── [M1] global (no org_id, no RLS) ──────────────────────────────────────
class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = _PK()
    email: Mapped[str] = mapped_column(CITEXT, nullable=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    password_hash: Mapped[str | None] = mapped_column(Text)
    auth_provider: Mapped[str] = mapped_column(Text, server_default=text("'password'"))
    full_name: Mapped[str] = mapped_column(Text, server_default=text("''"))
    avatar_url: Mapped[str] = mapped_column(Text, server_default=text("''"))
    locale: Mapped[str] = mapped_column(Text, server_default=text("'vi'"))
    status: Mapped[str] = mapped_column(Text, server_default=text("'ACTIVE'"))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = _TS()
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    __table_args__ = (UniqueConstraint("email", name="uq_users_email"),)


class Org(Base):
    __tablename__ = "orgs"
    id: Mapped[uuid.UUID] = _PK()
    name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(CITEXT, nullable=False)
    owner_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    plan_code: Mapped[str] = mapped_column(Text, server_default=text("'free'"))
    status: Mapped[str] = mapped_column(Text, server_default=text("'ACTIVE'"))
    settings: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    created_at: Mapped[datetime] = _TS()
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    __table_args__ = (UniqueConstraint("slug", name="uq_orgs_slug"),)


class Membership(Base):
    __tablename__ = "memberships"
    id: Mapped[uuid.UUID] = _PK()
    org_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(Text, server_default=text("'member'"))
    status: Mapped[str] = mapped_column(Text, server_default=text("'ACTIVE'"))
    invited_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = _TS()
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    __table_args__ = (
        UniqueConstraint("org_id", "user_id", name="uq_membership_org_user"),
        Index("ix_memberships_user", "user_id"),
        Index("ix_memberships_org", "org_id"),
    )


# ── [M1] tenant-owned (org_id + RLS ở migration) ─────────────────────────
class Wallet(Base):
    __tablename__ = "wallets"
    org_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orgs.id", ondelete="CASCADE"), primary_key=True
    )
    balance_credits: Mapped[int] = mapped_column(BigInteger, server_default=text("0"))
    held_credits: Mapped[int] = mapped_column(BigInteger, server_default=text("0"))
    version: Mapped[int] = mapped_column(BigInteger, server_default=text("0"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    __table_args__ = (
        CheckConstraint("balance_credits >= 0", name="ck_wallet_balance_nonneg"),
        CheckConstraint("held_credits >= 0", name="ck_wallet_held_nonneg"),
    )


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"
    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    org_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orgs.id", ondelete="RESTRICT"), nullable=False
    )
    entry_type: Mapped[str] = mapped_column(Text, nullable=False)
    delta_credits: Mapped[int] = mapped_column(BigInteger, nullable=False)
    balance_after: Mapped[int] = mapped_column(BigInteger, nullable=False)
    job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    payment_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    ref_group: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    usd_cost: Mapped[float | None] = mapped_column(Numeric(12, 6))
    credit_price_vnd: Mapped[int | None] = mapped_column(BigInteger)
    fx_usd_vnd: Mapped[float | None] = mapped_column(Numeric(12, 4))
    note: Mapped[str] = mapped_column(Text, server_default=text("''"))
    extra: Mapped[dict] = mapped_column("metadata", JSONB, server_default=text("'{}'::jsonb"))
    created_at: Mapped[datetime] = _TS()
    __table_args__ = (
        CheckConstraint(
            "entry_type IN ('TOPUP','HOLD','SETTLE','REFUND','ADJUST','EXPIRE','BONUS')",
            name="ck_ledger_type",
        ),
        CheckConstraint("balance_after >= 0", name="ck_ledger_balance_after_nonneg"),
        Index("ix_ledger_org_created", "org_id", "created_at"),
        Index("ix_ledger_ref_group", "ref_group"),
        # 1 HOLD / job (chống double-click): partial unique ở migration (WHERE entry_type='HOLD').
    )


class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[uuid.UUID] = _PK()
    org_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orgs.id", ondelete="RESTRICT"), nullable=False
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    provider: Mapped[str] = mapped_column(Text, nullable=False)  # vnpay|momo|bank_qr|usdt
    ext_ref: Mapped[str] = mapped_column(Text, nullable=False)
    amount_vnd: Mapped[int] = mapped_column(BigInteger, nullable=False)
    credits_granted: Mapped[int] = mapped_column(BigInteger, nullable=False)
    credit_pack_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))  # M2 FK
    status: Mapped[str] = mapped_column(Text, server_default=text("'PENDING'"))
    crypto_asset: Mapped[str | None] = mapped_column(Text)
    crypto_network: Mapped[str | None] = mapped_column(Text)
    crypto_amount: Mapped[float | None] = mapped_column(Numeric(24, 8))
    rate_snapshot: Mapped[dict | None] = mapped_column(JSONB)
    confirmations: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    ledger_entry_id: Mapped[int | None] = mapped_column(BigInteger)
    raw_payload: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    created_at: Mapped[datetime] = _TS()
    settled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        UniqueConstraint("provider", "ext_ref", name="uq_payment_provider_extref"),
        CheckConstraint("amount_vnd > 0", name="ck_payment_amount_pos"),
        CheckConstraint(
            "status IN ('PENDING','SUCCEEDED','FAILED','REFUNDED')", name="ck_payment_status"
        ),
        Index("ix_payments_org_created", "org_id", "created_at"),
    )


class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[uuid.UUID] = _PK()
    org_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    idempotency_key: Mapped[str] = mapped_column(Text, nullable=False)
    kind: Mapped[str] = mapped_column(Text, server_default=text("'product_ad'"))
    status: Mapped[str] = mapped_column(Text, server_default=text("'QUEUED'"))
    # M2 (nullable, FK thêm sau): template_id/kol_persona_id/brand_kit_id
    template_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    kol_persona_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    brand_kit_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    params: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    aspect: Mapped[str] = mapped_column(Text, server_default=text("'9:16'"))
    resolution: Mapped[str] = mapped_column(Text, server_default=text("'720p'"))
    seconds: Mapped[int] = mapped_column(Integer, server_default=text("15"))
    speed_tier: Mapped[str] = mapped_column(Text, server_default=text("'fast'"))
    provider_image: Mapped[str] = mapped_column(Text, server_default=text("''"))
    provider_video: Mapped[str] = mapped_column(Text, server_default=text("''"))
    model_id: Mapped[str] = mapped_column(Text, server_default=text("''"))
    est_cost_usd: Mapped[float] = mapped_column(Numeric(12, 6), server_default=text("0"))
    actual_cost_usd: Mapped[float] = mapped_column(Numeric(12, 6), server_default=text("0"))
    est_credits: Mapped[int] = mapped_column(BigInteger, server_default=text("0"))
    credit_ref_group: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    stage_timings: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    error: Mapped[str] = mapped_column(Text, server_default=text("''"))
    created_at: Mapped[datetime] = _TS()
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        UniqueConstraint("org_id", "idempotency_key", name="uq_jobs_org_idem"),
        CheckConstraint(
            "status IN ('WAITING_CONFIG','QUEUED','HELD','RUNNING','QA_FAIL','READY',"
            "'FAILED','REFUNDED','CANCELLED')",
            name="ck_jobs_status",
        ),
        Index("ix_jobs_org_created", "org_id", "created_at"),
        Index("ix_jobs_org_status", "org_id", "status"),
        # partial index worker poll (WHERE status='QUEUED') ở migration.
    )


class JobEvent(Base):
    __tablename__ = "job_events"
    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    org_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False
    )
    stage: Mapped[str] = mapped_column(Text, nullable=False)
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    provider: Mapped[str] = mapped_column(Text, server_default=text("''"))
    cost_usd: Mapped[float] = mapped_column(Numeric(12, 6), server_default=text("0"))
    asset_url: Mapped[str] = mapped_column(Text, server_default=text("''"))
    detail: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    created_at: Mapped[datetime] = _TS()
    __table_args__ = (Index("ix_job_events_job", "job_id", "id"),)


class Video(Base):
    __tablename__ = "videos"
    id: Mapped[uuid.UUID] = _PK()
    org_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False
    )
    storage_url: Mapped[str] = mapped_column(Text, server_default=text("''"))
    thumbnail_url: Mapped[str] = mapped_column(Text, server_default=text("''"))
    poster_url: Mapped[str] = mapped_column(Text, server_default=text("''"))
    duration_s: Mapped[float] = mapped_column(Numeric(8, 3), server_default=text("0"))
    width: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    height: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    aspect: Mapped[str] = mapped_column(Text, server_default=text("'9:16'"))
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, server_default=text("0"))
    has_watermark: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    watermark_removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    moderation_status: Mapped[str] = mapped_column(Text, server_default=text("'PENDING'"))
    moderation_detail: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    visibility: Mapped[str] = mapped_column(Text, server_default=text("'private'"))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = _TS()
    __table_args__ = (
        UniqueConstraint("job_id", name="uq_videos_job"),
        CheckConstraint(
            "moderation_status IN ('PENDING','APPROVED','FLAGGED','BLOCKED')",
            name="ck_videos_moderation",
        ),
        Index("ix_videos_org_created", "org_id", "created_at"),
    )


# Bảng tenant-owned cần RLS (migration bật ENABLE+FORCE + policy org_isolation).
TENANT_TABLES = (
    "wallets", "ledger_entries", "payments", "jobs", "job_events", "videos",
)
