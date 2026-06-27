"""V5 campaign, creative variant, and scene models."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.models import Base
from core.models_v5_common import TimestampMixin

if TYPE_CHECKING:
    from core.models import Product, Script
    from core.models_v5_experiment import Experiment, ExperimentAllocation, HookExperiment
    from core.models_v5_ops import LeadSignal
    from core.models_v5_publish import PublishJob
    from core.models_v5_tracking import LandingPage, TrackingToken


class CampaignStatus:
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    DONE = "DONE"
    ARCHIVED = "ARCHIVED"


class CreativeVariantStatus:
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    RENDERED = "RENDERED"
    PUBLISHED = "PUBLISHED"
    WINNER = "WINNER"
    LOSER = "LOSER"


class ComplianceStatus:
    PENDING = "PENDING"
    SAFE = "SAFE"
    UNSAFE = "UNSAFE"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class Campaign(TimestampMixin, Base):
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    status: Mapped[str] = mapped_column(String(32), default=CampaignStatus.DRAFT, index=True)
    category: Mapped[str] = mapped_column(String(64), default="", index=True)
    goal: Mapped[str] = mapped_column(String(64), default="sales")
    budget_note: Mapped[str] = mapped_column(Text, default="")
    target_channels_json: Mapped[str] = mapped_column(Text, default="[]")
    variants: Mapped[list["CreativeVariant"]] = relationship(back_populates="campaign")
    scenes: Mapped[list["VariantScene"]] = relationship(back_populates="campaign")
    tracking_tokens: Mapped[list["TrackingToken"]] = relationship(back_populates="campaign")
    landing_pages: Mapped[list["LandingPage"]] = relationship(back_populates="campaign")
    experiments: Mapped[list["Experiment"]] = relationship(back_populates="campaign")
    experiment_allocations: Mapped[list["ExperimentAllocation"]] = relationship(
        back_populates="campaign"
    )
    hook_experiments: Mapped[list["HookExperiment"]] = relationship(back_populates="campaign")
    publish_jobs: Mapped[list["PublishJob"]] = relationship(back_populates="campaign")
    lead_signals: Mapped[list["LeadSignal"]] = relationship(back_populates="campaign")


class CreativeVariant(TimestampMixin, Base):
    __tablename__ = "creative_variants"

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id"), index=True)
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id"), nullable=True, index=True
    )
    script_id: Mapped[int | None] = mapped_column(
        ForeignKey("scripts.id"), nullable=True, index=True
    )
    variant_code: Mapped[str] = mapped_column(String(32), default="", index=True)
    style: Mapped[str] = mapped_column(String(64), default="", index=True)
    hook_text: Mapped[str] = mapped_column(Text, default="")
    caption_text: Mapped[str] = mapped_column(Text, default="")
    cta_text: Mapped[str] = mapped_column(Text, default="")
    render_plan_json: Mapped[str] = mapped_column(Text, default="{}")
    prompt_snapshot_json: Mapped[str] = mapped_column(Text, default="{}")
    critic_score: Mapped[float] = mapped_column(Float, default=0.0)
    compliance_status: Mapped[str] = mapped_column(
        String(32), default=ComplianceStatus.PENDING, index=True
    )
    status: Mapped[str] = mapped_column(String(32), default=CreativeVariantStatus.DRAFT, index=True)
    campaign: Mapped["Campaign"] = relationship(back_populates="variants")
    product: Mapped["Product | None"] = relationship(back_populates="creative_variants")
    script: Mapped["Script | None"] = relationship(back_populates="creative_variants")
    scenes: Mapped[list["VariantScene"]] = relationship(back_populates="variant")
    tracking_tokens: Mapped[list["TrackingToken"]] = relationship(back_populates="variant")
    landing_pages: Mapped[list["LandingPage"]] = relationship(back_populates="variant")
    experiment_allocations: Mapped[list["ExperimentAllocation"]] = relationship(
        back_populates="variant"
    )
    hook_experiments: Mapped[list["HookExperiment"]] = relationship(back_populates="variant")
    publish_jobs: Mapped[list["PublishJob"]] = relationship(back_populates="variant")
    lead_signals: Mapped[list["LeadSignal"]] = relationship(back_populates="variant")


class VariantScene(TimestampMixin, Base):
    __tablename__ = "variant_scenes"
    __table_args__ = (
        UniqueConstraint("variant_id", "scene_index", name="uq_variant_scenes_variant_index"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id"), index=True)
    variant_id: Mapped[int] = mapped_column(ForeignKey("creative_variants.id"), index=True)
    scene_index: Mapped[int] = mapped_column(Integer)
    scene_type: Mapped[str] = mapped_column(String(64), default="", index=True)
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    voiceover_text: Mapped[str] = mapped_column(Text, default="")
    visual_goal: Mapped[str] = mapped_column(Text, default="")
    broll_keywords_json: Mapped[str] = mapped_column(Text, default="[]")
    cut_pace: Mapped[str] = mapped_column(String(32), default="medium")
    must_show_json: Mapped[str] = mapped_column(Text, default="[]")
    must_avoid_json: Mapped[str] = mapped_column(Text, default="[]")
    campaign: Mapped["Campaign"] = relationship(back_populates="scenes")
    variant: Mapped["CreativeVariant"] = relationship(back_populates="scenes")
