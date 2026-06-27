"""V5 channel account, session, and lease models.

These tables store safe session state only. Secrets stay outside API/log output by design:
raw token/cookie/header values should live in a local vault or encrypted store, referenced here
by path or key name.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.models import Base
from core.models_v5_common import TimestampMixin

if TYPE_CHECKING:
    from core.models_v5_campaign import Campaign
    from core.models_v5_ops import Incident
    from core.models_v5_publish import PostPublication, PublishJob


class ChannelAccountStatus:
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    ARCHIVED = "ARCHIVED"


class ChannelSessionStatus:
    READY = "READY"
    NEED_LOGIN = "NEED_LOGIN"
    NEED_CONFIG = "NEED_CONFIG"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    CAPTCHA_REQUIRED = "CAPTCHA_REQUIRED"
    LOCKED = "LOCKED"
    DISABLED = "DISABLED"


class SessionLeaseStatus:
    ACTIVE = "ACTIVE"
    RELEASED = "RELEASED"
    EXPIRED = "EXPIRED"


class ChannelAccount(TimestampMixin, Base):
    __tablename__ = "channel_accounts"
    __table_args__ = (
        UniqueConstraint("platform", "account_key", name="uq_channel_accounts_platform_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    platform: Mapped[str] = mapped_column(String(32), index=True)
    account_key: Mapped[str] = mapped_column(String(128), index=True)
    display_name: Mapped[str] = mapped_column(String(255), default="")
    status: Mapped[str] = mapped_column(String(32), default=ChannelAccountStatus.ACTIVE, index=True)
    profile_path: Mapped[str] = mapped_column(Text, default="")
    console_url: Mapped[str] = mapped_column(Text, default="")
    safe_note: Mapped[str] = mapped_column(Text, default="")
    last_health_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    sessions: Mapped[list["ChannelSession"]] = relationship(back_populates="account")
    publish_jobs: Mapped[list["PublishJob"]] = relationship(back_populates="channel_account")
    publications: Mapped[list["PostPublication"]] = relationship(back_populates="channel_account")
    incidents: Mapped[list["Incident"]] = relationship(back_populates="channel_account")


class ChannelSession(TimestampMixin, Base):
    __tablename__ = "channel_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("channel_accounts.id"), index=True)
    session_key: Mapped[str] = mapped_column(String(128), index=True)
    mode: Mapped[str] = mapped_column(String(32), default="", index=True)
    status: Mapped[str] = mapped_column(
        String(32), default=ChannelSessionStatus.NEED_LOGIN, index=True
    )
    profile_path: Mapped[str] = mapped_column(Text, default="")
    secret_ref: Mapped[str] = mapped_column(String(255), default="")
    secret_kind: Mapped[str] = mapped_column(String(32), default="", index=True)
    health_json: Mapped[str] = mapped_column(Text, default="{}")
    error_code: Mapped[str] = mapped_column(String(64), default="")
    error_message_redacted: Mapped[str] = mapped_column(Text, default="")
    checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    account: Mapped["ChannelAccount"] = relationship(back_populates="sessions")
    leases: Mapped[list["SessionLease"]] = relationship(back_populates="session")
    publish_jobs: Mapped[list["PublishJob"]] = relationship(back_populates="channel_session")
    publications: Mapped[list["PostPublication"]] = relationship(back_populates="channel_session")
    incidents: Mapped[list["Incident"]] = relationship(back_populates="channel_session")

    def __repr__(self) -> str:
        return (
            "ChannelSession("
            f"id={self.id!r}, account_id={self.account_id!r}, session_key={self.session_key!r}, "
            f"mode={self.mode!r}, status={self.status!r})"
        )


class SessionLease(TimestampMixin, Base):
    __tablename__ = "session_leases"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("channel_sessions.id"), index=True)
    holder: Mapped[str] = mapped_column(String(128), index=True)
    purpose: Mapped[str] = mapped_column(String(128), default="", index=True)
    status: Mapped[str] = mapped_column(String(32), default=SessionLeaseStatus.ACTIVE, index=True)
    acquired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    released_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    campaign_id: Mapped[int | None] = mapped_column(
        ForeignKey("campaigns.id"), nullable=True, index=True
    )
    session: Mapped["ChannelSession"] = relationship(back_populates="leases")
    campaign: Mapped["Campaign | None"] = relationship()
