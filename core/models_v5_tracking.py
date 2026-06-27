"""V5 tracking token, affiliate link, landing page, and click models."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.models import Base
from core.models_v5_common import CreatedAtMixin, TimestampMixin

if TYPE_CHECKING:
    from core.models import Product, VideoAsset
    from core.models_v5_campaign import Campaign, CreativeVariant
    from core.models_v5_ops import LeadSignal
    from core.models_v5_publish import PostPublication, PublishJob


class TrackingTokenStatus:
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    EXPIRED = "EXPIRED"


class AffiliateLinkStatus:
    PENDING = "PENDING"
    READY = "READY"
    FAILED = "FAILED"
    LOCKED = "LOCKED"
    EXPIRED = "EXPIRED"


class LandingPageStatus:
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    ARCHIVED = "ARCHIVED"


class TrackingToken(CreatedAtMixin, Base):
    __tablename__ = "tracking_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    provider: Mapped[str] = mapped_column(String(32), default="", index=True)
    campaign_id: Mapped[int | None] = mapped_column(
        ForeignKey("campaigns.id"), nullable=True, index=True
    )
    variant_id: Mapped[int | None] = mapped_column(
        ForeignKey("creative_variants.id"), nullable=True, index=True
    )
    video_asset_id: Mapped[int | None] = mapped_column(
        ForeignKey("video_assets.id"), nullable=True, index=True
    )
    publish_job_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    landing_page_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default=TrackingTokenStatus.ACTIVE, index=True)
    campaign: Mapped["Campaign | None"] = relationship(back_populates="tracking_tokens")
    variant: Mapped["CreativeVariant | None"] = relationship(back_populates="tracking_tokens")
    video_asset: Mapped["VideoAsset | None"] = relationship(back_populates="tracking_tokens")
    affiliate_links: Mapped[list["AffiliateLink"]] = relationship(back_populates="tracking_token")
    landing_pages: Mapped[list["LandingPage"]] = relationship(back_populates="tracking_token")
    click_rollups: Mapped[list["ClickRollup"]] = relationship(back_populates="tracking_token")
    publish_jobs: Mapped[list["PublishJob"]] = relationship(back_populates="tracking_token")
    publications: Mapped[list["PostPublication"]] = relationship(back_populates="tracking_token")
    lead_signals: Mapped[list["LeadSignal"]] = relationship(back_populates="tracking_token")


class AffiliateLink(TimestampMixin, Base):
    __tablename__ = "affiliate_links"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(32), default="", index=True)
    tracking_token_id: Mapped[int | None] = mapped_column(
        ForeignKey("tracking_tokens.id"), nullable=True, index=True
    )
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id"), nullable=True, index=True
    )
    video_asset_id: Mapped[int | None] = mapped_column(
        ForeignKey("video_assets.id"), nullable=True, index=True
    )
    url: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default=AffiliateLinkStatus.PENDING, index=True)
    commission_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    last_checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    error_code: Mapped[str] = mapped_column(String(64), default="")
    error_message_redacted: Mapped[str] = mapped_column(Text, default="")
    tracking_token: Mapped["TrackingToken | None"] = relationship(back_populates="affiliate_links")
    product: Mapped["Product | None"] = relationship(back_populates="affiliate_links")
    video_asset: Mapped["VideoAsset | None"] = relationship(back_populates="affiliate_links")
    publish_jobs: Mapped[list["PublishJob"]] = relationship(back_populates="affiliate_link")


class LandingPage(TimestampMixin, Base):
    __tablename__ = "landing_pages"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    campaign_id: Mapped[int | None] = mapped_column(
        ForeignKey("campaigns.id"), nullable=True, index=True
    )
    variant_id: Mapped[int | None] = mapped_column(
        ForeignKey("creative_variants.id"), nullable=True, index=True
    )
    tracking_token_id: Mapped[int | None] = mapped_column(
        ForeignKey("tracking_tokens.id"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), default="")
    disclosure_text: Mapped[str] = mapped_column(Text, default="")
    destination_url: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default=LandingPageStatus.DRAFT, index=True)
    campaign: Mapped["Campaign | None"] = relationship(back_populates="landing_pages")
    variant: Mapped["CreativeVariant | None"] = relationship(back_populates="landing_pages")
    tracking_token: Mapped["TrackingToken | None"] = relationship(back_populates="landing_pages")
    variants: Mapped[list["LandingPageVariant"]] = relationship(back_populates="landing_page")
    click_rollups: Mapped[list["ClickRollup"]] = relationship(back_populates="landing_page")
    publish_jobs: Mapped[list["PublishJob"]] = relationship(back_populates="landing_page")


class LandingPageVariant(TimestampMixin, Base):
    __tablename__ = "landing_page_variants"

    id: Mapped[int] = mapped_column(primary_key=True)
    landing_page_id: Mapped[int] = mapped_column(ForeignKey("landing_pages.id"), index=True)
    variant_code: Mapped[str] = mapped_column(String(32), default="", index=True)
    layout: Mapped[str] = mapped_column(String(64), default="default")
    cta_text: Mapped[str] = mapped_column(Text, default="")
    content_json: Mapped[str] = mapped_column(Text, default="{}")
    status: Mapped[str] = mapped_column(String(32), default=LandingPageStatus.DRAFT, index=True)
    landing_page: Mapped["LandingPage"] = relationship(back_populates="variants")


class ClickRollup(TimestampMixin, Base):
    __tablename__ = "click_rollups"
    __table_args__ = (
        UniqueConstraint(
            "rollup_date",
            "platform",
            "campaign_id",
            "variant_id",
            "tracking_token_id",
            name="uq_click_rollups_daily_scope",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    rollup_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    platform: Mapped[str] = mapped_column(String(32), default="", index=True)
    category: Mapped[str] = mapped_column(String(64), default="", index=True)
    campaign_id: Mapped[int | None] = mapped_column(
        ForeignKey("campaigns.id"), nullable=True, index=True
    )
    variant_id: Mapped[int | None] = mapped_column(
        ForeignKey("creative_variants.id"), nullable=True, index=True
    )
    tracking_token_id: Mapped[int | None] = mapped_column(
        ForeignKey("tracking_tokens.id"), nullable=True, index=True
    )
    landing_page_id: Mapped[int | None] = mapped_column(
        ForeignKey("landing_pages.id"), nullable=True, index=True
    )
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    campaign: Mapped["Campaign | None"] = relationship()
    variant: Mapped["CreativeVariant | None"] = relationship()
    tracking_token: Mapped["TrackingToken | None"] = relationship(back_populates="click_rollups")
    landing_page: Mapped["LandingPage | None"] = relationship(back_populates="click_rollups")
