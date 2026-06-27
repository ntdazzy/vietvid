"""V5 experiment, learned pattern, hook score, and trend signal models."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.models import Base
from core.models_v5_common import CreatedAtMixin, TimestampMixin

if TYPE_CHECKING:
    from core.models import VideoAsset
    from core.models_v5_campaign import Campaign, CreativeVariant


class ExperimentStatus:
    DRAFT = "DRAFT"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    DONE = "DONE"
    ARCHIVED = "ARCHIVED"


class ScriptPatternStatus:
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    ARCHIVED = "ARCHIVED"


class HookExperimentStatus:
    DRAFT = "DRAFT"
    RUNNING = "RUNNING"
    DONE = "DONE"
    ARCHIVED = "ARCHIVED"


class TrendSignalStatus:
    ACTIVE = "ACTIVE"
    STALE = "STALE"
    DISMISSED = "DISMISSED"


class Experiment(TimestampMixin, Base):
    __tablename__ = "experiments"

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id"), index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    status: Mapped[str] = mapped_column(String(32), default=ExperimentStatus.DRAFT, index=True)
    start_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    end_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    primary_metric: Mapped[str] = mapped_column(String(64), default="net_commission")
    min_sample: Mapped[int] = mapped_column(Integer, default=0)
    exploration_rate: Mapped[float] = mapped_column(Float, default=0.0)
    campaign: Mapped["Campaign"] = relationship(back_populates="experiments")
    allocations: Mapped[list["ExperimentAllocation"]] = relationship(back_populates="experiment")
    hook_experiments: Mapped[list["HookExperiment"]] = relationship(back_populates="experiment")


class ExperimentAllocation(CreatedAtMixin, Base):
    __tablename__ = "experiment_allocations"

    id: Mapped[int] = mapped_column(primary_key=True)
    experiment_id: Mapped[int] = mapped_column(ForeignKey("experiments.id"), index=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id"), index=True)
    variant_id: Mapped[int] = mapped_column(ForeignKey("creative_variants.id"), index=True)
    video_asset_id: Mapped[int | None] = mapped_column(
        ForeignKey("video_assets.id"), nullable=True, index=True
    )
    publish_job_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    channel: Mapped[str] = mapped_column(String(32), default="", index=True)
    sub_id: Mapped[str] = mapped_column(String(64), default="", index=True)
    allocated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    metrics_snapshot_json: Mapped[str] = mapped_column(Text, default="{}")
    experiment: Mapped["Experiment"] = relationship(back_populates="allocations")
    campaign: Mapped["Campaign"] = relationship(back_populates="experiment_allocations")
    variant: Mapped["CreativeVariant"] = relationship(back_populates="experiment_allocations")
    video_asset: Mapped["VideoAsset | None"] = relationship()


class ScriptPattern(TimestampMixin, Base):
    __tablename__ = "script_patterns"

    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(String(64), default="", index=True)
    pattern_name: Mapped[str] = mapped_column(String(255), default="", index=True)
    hook_structure: Mapped[str] = mapped_column(Text, default="")
    body_structure: Mapped[str] = mapped_column(Text, default="")
    cta_style: Mapped[str] = mapped_column(Text, default="")
    source_policy: Mapped[str] = mapped_column(String(64), default="", index=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    sample_size: Mapped[int] = mapped_column(Integer, default=0)
    metrics_json: Mapped[str] = mapped_column(Text, default="{}")
    status: Mapped[str] = mapped_column(String(32), default=ScriptPatternStatus.ACTIVE, index=True)


class HookExperiment(TimestampMixin, Base):
    __tablename__ = "hook_experiments"

    id: Mapped[int] = mapped_column(primary_key=True)
    experiment_id: Mapped[int] = mapped_column(ForeignKey("experiments.id"), index=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id"), index=True)
    variant_id: Mapped[int | None] = mapped_column(
        ForeignKey("creative_variants.id"), nullable=True, index=True
    )
    hook_style: Mapped[str] = mapped_column(String(64), default="", index=True)
    hook_text: Mapped[str] = mapped_column(Text, default="")
    opening_scene_goal: Mapped[str] = mapped_column(Text, default="")
    retention_3s_rate: Mapped[float] = mapped_column(Float, default=0.0)
    click_rate: Mapped[float] = mapped_column(Float, default=0.0)
    revenue_score: Mapped[float] = mapped_column(Float, default=0.0)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    metrics_json: Mapped[str] = mapped_column(Text, default="{}")
    status: Mapped[str] = mapped_column(String(32), default=HookExperimentStatus.DRAFT, index=True)
    experiment: Mapped["Experiment"] = relationship(back_populates="hook_experiments")
    campaign: Mapped["Campaign"] = relationship(back_populates="hook_experiments")
    variant: Mapped["CreativeVariant | None"] = relationship(back_populates="hook_experiments")


class TrendSignal(TimestampMixin, Base):
    __tablename__ = "trend_signals"

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(64), default="", index=True)
    source_policy: Mapped[str] = mapped_column(String(64), default="", index=True)
    keyword: Mapped[str] = mapped_column(String(255), default="", index=True)
    category: Mapped[str] = mapped_column(String(64), default="", index=True)
    signal_strength: Mapped[float] = mapped_column(Float, default=0.0)
    growth_rate: Mapped[float] = mapped_column(Float, default=0.0)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    observed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    status: Mapped[str] = mapped_column(String(32), default=TrendSignalStatus.ACTIVE, index=True)
