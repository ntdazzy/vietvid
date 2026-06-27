"""V5 publish job and post proof models."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.models import Base
from core.models_v5_common import TimestampMixin

if TYPE_CHECKING:
    from core.models import VideoAsset
    from core.models_v5_campaign import Campaign, CreativeVariant
    from core.models_v5_ops import AuditLog, Incident, LeadSignal
    from core.models_v5_sessions import ChannelAccount, ChannelSession
    from core.models_v5_tracking import AffiliateLink, LandingPage, TrackingToken


class PublishJobStatus:
    PENDING = "PENDING"
    READY = "READY"
    PUBLISHING = "PUBLISHING"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class PostPublicationStatus:
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"
    REMOVED = "REMOVED"


class PublishJob(TimestampMixin, Base):
    __tablename__ = "publish_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int | None] = mapped_column(
        ForeignKey("campaigns.id"), nullable=True, index=True
    )
    variant_id: Mapped[int | None] = mapped_column(
        ForeignKey("creative_variants.id"), nullable=True, index=True
    )
    video_asset_id: Mapped[int] = mapped_column(ForeignKey("video_assets.id"), index=True)
    channel_account_id: Mapped[int] = mapped_column(ForeignKey("channel_accounts.id"), index=True)
    channel_session_id: Mapped[int | None] = mapped_column(
        ForeignKey("channel_sessions.id"), nullable=True, index=True
    )
    tracking_token_id: Mapped[int | None] = mapped_column(
        ForeignKey("tracking_tokens.id"), nullable=True, index=True
    )
    affiliate_link_id: Mapped[int | None] = mapped_column(
        ForeignKey("affiliate_links.id"), nullable=True, index=True
    )
    landing_page_id: Mapped[int | None] = mapped_column(
        ForeignKey("landing_pages.id"), nullable=True, index=True
    )
    platform: Mapped[str] = mapped_column(String(32), default="", index=True)
    status: Mapped[str] = mapped_column(String(32), default=PublishJobStatus.PENDING, index=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    caption_text: Mapped[str] = mapped_column(Text, default="")
    title_text: Mapped[str] = mapped_column(String(255), default="")
    cta_text: Mapped[str] = mapped_column(Text, default="")
    link_url: Mapped[str] = mapped_column(Text, default="")
    policy_snapshot_json: Mapped[str] = mapped_column(Text, default="{}")
    approval_status: Mapped[str] = mapped_column(String(32), default="PENDING", index=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    last_error_code: Mapped[str] = mapped_column(String(64), default="")
    last_error_message_redacted: Mapped[str] = mapped_column(Text, default="")
    # Stamp NGAY sau provider.publish() (trước khi ghi PostPublication): nếu process chết giữa
    # chừng, reclaim phân biệt "đã đăng nhưng chưa ghi" (có id) vs "chưa đăng" (rỗng).
    external_post_id: Mapped[str] = mapped_column(String(255), default="")
    campaign: Mapped["Campaign | None"] = relationship(back_populates="publish_jobs")
    variant: Mapped["CreativeVariant | None"] = relationship(back_populates="publish_jobs")
    video_asset: Mapped["VideoAsset"] = relationship()
    channel_account: Mapped["ChannelAccount"] = relationship(back_populates="publish_jobs")
    channel_session: Mapped["ChannelSession | None"] = relationship(back_populates="publish_jobs")
    tracking_token: Mapped["TrackingToken | None"] = relationship(back_populates="publish_jobs")
    affiliate_link: Mapped["AffiliateLink | None"] = relationship(back_populates="publish_jobs")
    landing_page: Mapped["LandingPage | None"] = relationship(back_populates="publish_jobs")
    publications: Mapped[list["PostPublication"]] = relationship(back_populates="publish_job")
    incidents: Mapped[list["Incident"]] = relationship(back_populates="publish_job")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="publish_job")


class PostPublication(TimestampMixin, Base):
    __tablename__ = "post_publications"
    __table_args__ = (
        UniqueConstraint("platform", "external_post_id", name="uq_post_publications_platform_post"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    publish_job_id: Mapped[int] = mapped_column(ForeignKey("publish_jobs.id"), index=True)
    channel_account_id: Mapped[int] = mapped_column(ForeignKey("channel_accounts.id"), index=True)
    channel_session_id: Mapped[int | None] = mapped_column(
        ForeignKey("channel_sessions.id"), nullable=True, index=True
    )
    tracking_token_id: Mapped[int | None] = mapped_column(
        ForeignKey("tracking_tokens.id"), nullable=True, index=True
    )
    platform: Mapped[str] = mapped_column(String(32), default="", index=True)
    external_post_id: Mapped[str] = mapped_column(String(255), default="", index=True)
    post_url: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(
        String(32), default=PostPublicationStatus.PUBLISHED, index=True
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    proof_path: Mapped[str] = mapped_column(Text, default="")
    response_redacted_json: Mapped[str] = mapped_column(Text, default="{}")
    revenue_at_publish: Mapped[float] = mapped_column(Float, default=0.0)
    publish_job: Mapped["PublishJob"] = relationship(back_populates="publications")
    channel_account: Mapped["ChannelAccount"] = relationship(back_populates="publications")
    channel_session: Mapped["ChannelSession | None"] = relationship(back_populates="publications")
    tracking_token: Mapped["TrackingToken | None"] = relationship(back_populates="publications")
    lead_signals: Mapped[list["LeadSignal"]] = relationship(back_populates="post_publication")
