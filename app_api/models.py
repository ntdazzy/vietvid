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


class TokenPurpose:
    PASSWORD_RESET, EMAIL_VERIFY, REFRESH = "PASSWORD_RESET", "EMAIL_VERIFY", "REFRESH"


# Predicate RLS fail-closed (GUC chưa set → NULL → 0 dòng). Dùng LẠI nguyên văn ở mọi migration
# tenant (D7) — tránh gõ lại literal sai lệch phá cô lập.
RLS_USING_PREDICATE = "org_id = nullif(current_setting('vietvid.current_org', true), '')::uuid"


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


class AuthToken(Base):
    """Token vòng đời auth (global, KHÔNG RLS) — dùng chung cho:
    PASSWORD_RESET, EMAIL_VERIFY, REFRESH. Chỉ lưu HASH (sha256) của token, KHÔNG lưu raw.
    Hết hiệu lực khi: quá expires_at, đã used_at (one-time), hoặc revoked_at (logout/rotate).
    """

    __tablename__ = "auth_tokens"
    id: Mapped[uuid.UUID] = _PK()
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    token_hash: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    meta: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    created_at: Mapped[datetime] = _TS()
    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_auth_tokens_hash"),
        CheckConstraint(
            "purpose IN ('PASSWORD_RESET','EMAIL_VERIFY','REFRESH')", name="ck_auth_token_purpose"
        ),
        Index("ix_auth_tokens_user_purpose", "user_id", "purpose"),
    )


class AuditLog(Base):
    """Nhật ký hành động nhạy cảm (admin suspend/credit-adjust/moderation). GLOBAL + append-only
    (sống sót cả khi org/user bị xoá — phục vụ điều tra/pháp lý, D5). Trigger chặn UPDATE/DELETE."""

    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    org_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))  # plain (không FK/CASCADE)
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    actor_email: Mapped[str] = mapped_column(Text, server_default=text("''"))
    action: Mapped[str] = mapped_column(Text, nullable=False)
    detail: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    created_at: Mapped[datetime] = _TS()
    __table_args__ = (Index("ix_audit_created", "created_at"),)


class OrgInvitation(Base):
    """Lời mời thành viên vào org (global, KHÔNG RLS — invitee chưa là member nên không qua RLS).
    Tra cứu bằng token (secret) khi accept; liệt kê theo org_id tường minh (như memberships).
    """

    __tablename__ = "org_invitations"
    id: Mapped[uuid.UUID] = _PK()
    org_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False
    )
    email: Mapped[str] = mapped_column(CITEXT, nullable=False)
    role: Mapped[str] = mapped_column(Text, server_default=text("'member'"))
    token_hash: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, server_default=text("'PENDING'"))
    invited_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    accepted_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = _TS()
    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_org_invite_hash"),
        CheckConstraint(
            "status IN ('PENDING','ACCEPTED','REVOKED')", name="ck_org_invite_status"
        ),
        Index("ix_org_invite_org", "org_id"),
        Index("ix_org_invite_email", "email"),
    )


# ── [M2] billing catalog (GLOBAL — không RLS) ────────────────────────────
class Plan(Base):
    """Catalog gói thuê bao. Backs orgs.plan_code (cache denormalized)."""

    __tablename__ = "plans"
    code: Mapped[str] = mapped_column(Text, primary_key=True)  # free/pro/business
    name: Mapped[str] = mapped_column(Text, nullable=False)
    name_vi: Mapped[str] = mapped_column(Text, server_default=text("''"))
    monthly_price_vnd: Mapped[int] = mapped_column(BigInteger, server_default=text("0"))
    yearly_price_vnd: Mapped[int] = mapped_column(BigInteger, server_default=text("0"))
    monthly_credit_grant: Mapped[int] = mapped_column(BigInteger, server_default=text("0"))
    max_concurrent_jobs: Mapped[int] = mapped_column(Integer, server_default=text("1"))
    max_resolution: Mapped[str] = mapped_column(Text, server_default=text("'720p'"))
    max_seconds: Mapped[int] = mapped_column(Integer, server_default=text("15"))
    watermark_free: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    features: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    sort_order: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    created_at: Mapped[datetime] = _TS()
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class CreditPack(Base):
    """Catalog gói credit mua lẻ (top-up). Backs payments.credit_pack_id."""

    __tablename__ = "credit_packs"
    id: Mapped[uuid.UUID] = _PK()
    code: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    amount_vnd: Mapped[int] = mapped_column(BigInteger, nullable=False)
    credits: Mapped[int] = mapped_column(BigInteger, nullable=False)
    bonus_credits: Mapped[int] = mapped_column(BigInteger, server_default=text("0"))
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    sort_order: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    created_at: Mapped[datetime] = _TS()
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    __table_args__ = (
        UniqueConstraint("code", name="uq_credit_pack_code"),
        CheckConstraint("amount_vnd > 0", name="ck_credit_pack_amount_pos"),
        CheckConstraint("credits > 0", name="ck_credit_pack_credits_pos"),
    )


# ── [M2] affiliate loop (vượt autovis: video → click → doanh thu) ────────
class VvPlatformConfig(Base):
    """Cấu hình nền tảng SỬA ĐƯỢC LÚC CHẠY (admin, không cần deploy). GLOBAL, 1 hàng id=1.

    data JSONB giữ: video_provider_chain (override), quota (max_api_jobs_per_day),
    feature_flags theo gói. Đọc qua platform.get_config() (merge default). Chỉ admin ghi."""

    __tablename__ = "vv_platform_config"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    data: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class VvAffiliateLink(Base):
    """Short-link gắn vào đuôi CTA video. /r/{code} → redirect target_url + ghi click."""

    __tablename__ = "vv_affiliate_links"
    id: Mapped[uuid.UUID] = _PK()
    org_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    code: Mapped[str] = mapped_column(Text, nullable=False)            # mã ngắn (global-unique)
    target_url: Mapped[str] = mapped_column(Text, nullable=False)
    label: Mapped[str] = mapped_column(Text, server_default=text("''"))
    network: Mapped[str] = mapped_column(Text, server_default=text("''"))  # shopee/lazada/tiktok
    job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))    # video gắn link
    clicks: Mapped[int] = mapped_column(BigInteger, server_default=text("0"))  # cache đếm
    created_at: Mapped[datetime] = _TS()
    __table_args__ = (
        UniqueConstraint("code", name="uq_affiliate_code"),
        Index("ix_affiliate_org", "org_id"),
    )


class VvLinkClick(Base):
    """Click append-only trên short-link (nguồn chân lý cho attribution)."""

    __tablename__ = "vv_link_clicks"
    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    org_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False
    )
    link_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("vv_affiliate_links.id", ondelete="CASCADE"), nullable=False
    )
    referer: Mapped[str] = mapped_column(Text, server_default=text("''"))
    ua_hash: Mapped[str] = mapped_column(Text, server_default=text("''"))  # sha256 UA (không lưu PII)
    created_at: Mapped[datetime] = _TS()
    __table_args__ = (Index("ix_link_click_link", "link_id", "id"),)


class VvApiKey(Base):
    """Khoá API B2B — cho phép gọi /api/v1 thay người dùng (agency/dev tích hợp).

    GLOBAL (tra cứu theo hash TRƯỚC khi biết org → không RLS), nhưng có org_id để định danh
    workspace. Chỉ lưu sha256(key); raw chỉ hiện 1 lần lúc tạo. prefix lưu để hiển thị
    'vv_live_ab…' trong danh sách. Hết hiệu lực khi revoked_at đặt."""

    __tablename__ = "vv_api_keys"
    id: Mapped[uuid.UUID] = _PK()
    org_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(Text, server_default=text("''"))
    key_hash: Mapped[str] = mapped_column(Text, nullable=False)
    prefix: Mapped[str] = mapped_column(Text, server_default=text("''"))  # hiển thị, không bí mật
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = _TS()
    __table_args__ = (
        UniqueConstraint("key_hash", name="uq_api_key_hash"),
        Index("ix_api_key_org", "org_id"),
    )


class VvWebhook(Base):
    """Webhook B2B — URL nhận sự kiện job (READY/FAILED) kèm chữ ký HMAC. RLS tenant chuẩn."""

    __tablename__ = "vv_webhooks"
    id: Mapped[uuid.UUID] = _PK()
    org_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    url: Mapped[str] = mapped_column(Text, nullable=False)
    secret: Mapped[str] = mapped_column(Text, nullable=False)  # ký HMAC payload
    active: Mapped[bool] = mapped_column(server_default=text("true"))
    created_at: Mapped[datetime] = _TS()
    __table_args__ = (Index("ix_webhook_org", "org_id"),)


# ── [M2] nội dung tenant (org_id NULLABLE = system seed dùng chung; RLS NỚI) ──
class VvTemplate(Base):
    """Template/preset wizard. org_id NULL = mẫu hệ thống (mọi org thấy); có org_id = của riêng org."""

    __tablename__ = "vv_templates"
    id: Mapped[uuid.UUID] = _PK()
    org_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("orgs.id", ondelete="CASCADE"))
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, server_default=text("''"))
    category: Mapped[str] = mapped_column(Text, server_default=text("'product_ad'"))
    preset: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    thumbnail_url: Mapped[str] = mapped_column(Text, server_default=text("''"))
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    sort_order: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    created_at: Mapped[datetime] = _TS()
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    __table_args__ = (Index("ix_vv_templates_org", "org_id"),)


class VvKolPersona(Base):
    """Người mẫu/KOL. source='ai' (persona AI sinh) hoặc 'upload' (mặt thật user tải — cần đồng ý
    + kiểm duyệt). org_id NULL = persona hệ thống."""

    __tablename__ = "vv_kol_personas"
    id: Mapped[uuid.UUID] = _PK()
    org_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("orgs.id", ondelete="CASCADE"))
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, server_default=text("''"))  # character sheet
    gender: Mapped[str] = mapped_column(Text, server_default=text("'female'"))
    voice_gender: Mapped[str] = mapped_column(Text, server_default=text("'female'"))
    avatar_url: Mapped[str] = mapped_column(Text, server_default=text("''"))  # ảnh tham chiếu (i2v)
    source: Mapped[str] = mapped_column(Text, server_default=text("'ai'"))
    consent_confirmed: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    moderation_status: Mapped[str] = mapped_column(Text, server_default=text("'APPROVED'"))
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    sort_order: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    created_at: Mapped[datetime] = _TS()
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    __table_args__ = (
        CheckConstraint("source IN ('ai','upload')", name="ck_kol_source"),
        CheckConstraint(
            "moderation_status IN ('PENDING','APPROVED','FLAGGED','BLOCKED')",
            name="ck_kol_moderation",
        ),
        Index("ix_vv_kol_org", "org_id"),
    )


class VvBrandKit(Base):
    """Bộ nhận diện thương hiệu (logo/màu/watermark/disclosure). Luôn thuộc 1 org (RLS chuẩn)."""

    __tablename__ = "vv_brand_kits"
    id: Mapped[uuid.UUID] = _PK()
    org_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(Text, nullable=False)
    logo_url: Mapped[str] = mapped_column(Text, server_default=text("''"))
    primary_color: Mapped[str] = mapped_column(Text, server_default=text("'#7C3AED'"))
    secondary_color: Mapped[str] = mapped_column(Text, server_default=text("'#2563EB'"))
    font: Mapped[str] = mapped_column(Text, server_default=text("''"))
    watermark_text: Mapped[str] = mapped_column(Text, server_default=text("''"))
    disclosure_text: Mapped[str] = mapped_column(Text, server_default=text("''"))
    is_default: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    created_at: Mapped[datetime] = _TS()
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    __table_args__ = (Index("ix_vv_brand_kits_org", "org_id"),)


class VvCharacter(Base):
    """Nhân vật AI tái dùng — diễn viên nhất quán "bring into future images & videos" (clone openart
    /suite/character). 3 lối tạo (source): 'image' (từ ảnh upload), 'describe' (prompt text),
    'build' (thuộc tính: look vibe/gender/ethnicity/age). avatar_url = ảnh đại diện;
    images = mảng ảnh tham chiếu (đa pose). org_id NULL = nhân vật hệ thống (mọi org thấy).
    RLS NỚI (system + own) như personas/templates."""

    __tablename__ = "vv_characters"
    id: Mapped[uuid.UUID] = _PK()
    org_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("orgs.id", ondelete="CASCADE"))
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, server_default=text("''"))  # prompt / character sheet
    avatar_url: Mapped[str] = mapped_column(Text, server_default=text("''"))  # ảnh đại diện
    images: Mapped[list] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))  # ref đa pose
    source: Mapped[str] = mapped_column(Text, server_default=text("'build'"))  # image|describe|build
    gender: Mapped[str] = mapped_column(Text, server_default=text("''"))  # thuộc tính build
    ethnicity: Mapped[str] = mapped_column(Text, server_default=text("''"))
    age_range: Mapped[str] = mapped_column(Text, server_default=text("''"))
    vibe: Mapped[str] = mapped_column(Text, server_default=text("''"))  # look vibe
    voice_gender: Mapped[str] = mapped_column(Text, server_default=text("'female'"))  # dùng khi vào video
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    sort_order: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    created_at: Mapped[datetime] = _TS()
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    __table_args__ = (
        CheckConstraint("source IN ('image','describe','build')", name="ck_character_source"),
        Index("ix_vv_characters_org", "org_id"),
    )


# ── [M2] notifications (tenant, RLS chuẩn) ────────────────────────────────
class Notification(Base):
    """Thông báo in-app: video sẵn sàng / lỗi, đã nạp tiền, hệ thống."""

    __tablename__ = "notifications"
    id: Mapped[uuid.UUID] = _PK()
    org_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    type: Mapped[str] = mapped_column(Text, nullable=False)  # job_ready/job_failed/payment/system
    title: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, server_default=text("''"))
    ref_type: Mapped[str] = mapped_column(Text, server_default=text("''"))  # job/payment
    ref_id: Mapped[str] = mapped_column(Text, server_default=text("''"))
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = _TS()
    __table_args__ = (
        Index("ix_notifications_org_created", "org_id", "created_at"),
        Index("ix_notifications_unread", "org_id", "read_at"),
    )


# ── [M1] tenant-owned (org_id + RLS ở migration) ─────────────────────────
class Wallet(Base):
    __tablename__ = "wallets"
    org_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orgs.id", ondelete="CASCADE"), primary_key=True
    )
    balance_credits: Mapped[int] = mapped_column(BigInteger, server_default=text("0"))  # xu mua/thưởng — KHÔNG hết hạn
    held_credits: Mapped[int] = mapped_column(BigInteger, server_default=text("0"))
    # Xu GÓI tháng — HẾT HẠN (breakage). Tiêu trừ xu này TRƯỚC. Mua gói mới = reset (xoá cũ chưa xài).
    plan_credits: Mapped[int] = mapped_column(BigInteger, server_default=text("0"))
    plan_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(BigInteger, server_default=text("0"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    __table_args__ = (
        CheckConstraint("balance_credits >= 0", name="ck_wallet_balance_nonneg"),
        CheckConstraint("held_credits >= 0", name="ck_wallet_held_nonneg"),
        CheckConstraint("plan_credits >= 0", name="ck_wallet_plan_nonneg"),
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
    # nhóm biến thể auto-series (vòng lặp hiệu suất: rank biến thể theo click thật).
    series_group: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
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
    "notifications", "vv_webhooks",
)

# Bảng CÓ cột org_id nhưng CỐ Ý global (không RLS): lớp join/identity/pre-auth — truy cập
# trước khi set GUC tenant (vd IPN, accept-invite bằng token). Mỗi mục là quyết định có chủ đích
# (SYSTEM_DESIGN D4/D5). Test RLS-coverage loại trừ danh sách này; thêm bảng global-org mới vào đây.
GLOBAL_ORG_TABLES = (
    "memberships", "org_invitations",
    # affiliate: redirect /r/{code} & ghi click chạy PRE-AUTH (không GUC) → phải global,
    # lọc org_id tường minh ở endpoint quản lý/analytics.
    "vv_affiliate_links", "vv_link_clicks",
    # audit_log: phải SỐNG SÓT cả khi org bị xoá (điều tra/pháp lý, D5) → global, không RLS.
    "audit_log",
    # vv_api_keys: tra cứu theo hash TRƯỚC khi biết org (auth /api/v1) → global, lọc org_id ở quản lý.
    "vv_api_keys",
)
