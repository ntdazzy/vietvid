"""V5 lead, incident, and audit models."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.models import Base
from core.models_v5_common import TimestampMixin

if TYPE_CHECKING:
    from core.models_v5_campaign import Campaign, CreativeVariant
    from core.models_v5_publish import PostPublication, PublishJob
    from core.models_v5_sessions import ChannelAccount, ChannelSession
    from core.models_v5_tracking import TrackingToken


class LeadSignalStatus:
    NEW = "NEW"
    QUALIFIED = "QUALIFIED"
    IGNORED = "IGNORED"
    ACTIONED = "ACTIONED"
    ARCHIVED = "ARCHIVED"


class LeadActionStatus:
    SUGGESTED = "SUGGESTED"
    NEEDS_APPROVAL = "NEEDS_APPROVAL"
    APPROVED = "APPROVED"
    SENT = "SENT"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


class IncidentStatus:
    OPEN = "OPEN"
    ACKED = "ACKED"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class AuditActorType:
    SYSTEM = "SYSTEM"
    WEB = "WEB"
    MOBILE = "MOBILE"
    TELEGRAM = "TELEGRAM"
    BOT = "BOT"


class LeadSignal(TimestampMixin, Base):
    __tablename__ = "lead_signals"

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(64), index=True)
    channel: Mapped[str] = mapped_column(String(32), default="", index=True)
    external_id: Mapped[str] = mapped_column(String(255), default="", index=True)
    campaign_id: Mapped[int | None] = mapped_column(
        ForeignKey("campaigns.id"), nullable=True, index=True
    )
    variant_id: Mapped[int | None] = mapped_column(
        ForeignKey("creative_variants.id"), nullable=True, index=True
    )
    post_publication_id: Mapped[int | None] = mapped_column(
        ForeignKey("post_publications.id"), nullable=True, index=True
    )
    tracking_token_id: Mapped[int | None] = mapped_column(
        ForeignKey("tracking_tokens.id"), nullable=True, index=True
    )
    author_ref_hash: Mapped[str] = mapped_column(String(128), default="", index=True)
    text_redacted: Mapped[str] = mapped_column(Text, default="")
    intent: Mapped[str] = mapped_column(String(64), default="", index=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    # P1c: phân tích sâu bằng LLM (fallback regex để mặc định 0/"").
    heat: Mapped[float] = mapped_column(Float, default=0.0)
    interested_product: Mapped[str] = mapped_column(String(255), default="")
    source_policy: Mapped[str] = mapped_column(String(64), default="", index=True)
    received_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(32), default=LeadSignalStatus.NEW, index=True)
    campaign: Mapped["Campaign | None"] = relationship(back_populates="lead_signals")
    variant: Mapped["CreativeVariant | None"] = relationship(back_populates="lead_signals")
    post_publication: Mapped["PostPublication | None"] = relationship(back_populates="lead_signals")
    tracking_token: Mapped["TrackingToken | None"] = relationship(back_populates="lead_signals")
    actions: Mapped[list["LeadAction"]] = relationship(back_populates="lead_signal")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="lead_signal")


class LeadAction(TimestampMixin, Base):
    __tablename__ = "lead_actions"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_signal_id: Mapped[int] = mapped_column(ForeignKey("lead_signals.id"), index=True)
    action_type: Mapped[str] = mapped_column(String(64), index=True)
    suggested_reply: Mapped[str] = mapped_column(Text, default="")
    approved_reply: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default=LeadActionStatus.SUGGESTED, index=True)
    actor: Mapped[str] = mapped_column(String(128), default="", index=True)
    policy_snapshot_json: Mapped[str] = mapped_column(Text, default="{}")
    executed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    error_message_redacted: Mapped[str] = mapped_column(Text, default="")
    lead_signal: Mapped["LeadSignal"] = relationship(back_populates="actions")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="lead_action")


class Incident(TimestampMixin, Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(primary_key=True)
    level: Mapped[str] = mapped_column(String(16), default="WARNING", index=True)
    module: Mapped[str] = mapped_column(String(64), default="", index=True)
    incident_type: Mapped[str] = mapped_column(String(64), default="", index=True)
    status: Mapped[str] = mapped_column(String(32), default=IncidentStatus.OPEN, index=True)
    title: Mapped[str] = mapped_column(String(255), default="")
    detail_redacted: Mapped[str] = mapped_column(Text, default="")
    channel_account_id: Mapped[int | None] = mapped_column(
        ForeignKey("channel_accounts.id"), nullable=True, index=True
    )
    channel_session_id: Mapped[int | None] = mapped_column(
        ForeignKey("channel_sessions.id"), nullable=True, index=True
    )
    publish_job_id: Mapped[int | None] = mapped_column(
        ForeignKey("publish_jobs.id"), nullable=True, index=True
    )
    lead_signal_id: Mapped[int | None] = mapped_column(
        ForeignKey("lead_signals.id"), nullable=True, index=True
    )
    opened_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    screenshot_path: Mapped[str] = mapped_column(Text, default="")
    payload_redacted_json: Mapped[str] = mapped_column(Text, default="{}")
    channel_account: Mapped["ChannelAccount | None"] = relationship(back_populates="incidents")
    channel_session: Mapped["ChannelSession | None"] = relationship(back_populates="incidents")
    publish_job: Mapped["PublishJob | None"] = relationship(back_populates="incidents")
    lead_signal: Mapped["LeadSignal | None"] = relationship()
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="incident")


class AuditLog(TimestampMixin, Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    actor_type: Mapped[str] = mapped_column(String(32), default=AuditActorType.SYSTEM, index=True)
    actor_ref: Mapped[str] = mapped_column(String(128), default="", index=True)
    action: Mapped[str] = mapped_column(String(128), index=True)
    resource_type: Mapped[str] = mapped_column(String(64), default="", index=True)
    resource_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default="OK", index=True)
    occurred_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    message_redacted: Mapped[str] = mapped_column(Text, default="")
    payload_redacted_json: Mapped[str] = mapped_column(Text, default="{}")
    incident_id: Mapped[int | None] = mapped_column(
        ForeignKey("incidents.id"), nullable=True, index=True
    )
    lead_signal_id: Mapped[int | None] = mapped_column(
        ForeignKey("lead_signals.id"), nullable=True, index=True
    )
    lead_action_id: Mapped[int | None] = mapped_column(
        ForeignKey("lead_actions.id"), nullable=True, index=True
    )
    publish_job_id: Mapped[int | None] = mapped_column(
        ForeignKey("publish_jobs.id"), nullable=True, index=True
    )
    incident: Mapped["Incident | None"] = relationship(back_populates="audit_logs")
    lead_signal: Mapped["LeadSignal | None"] = relationship(back_populates="audit_logs")
    lead_action: Mapped["LeadAction | None"] = relationship(back_populates="audit_logs")
    publish_job: Mapped["PublishJob | None"] = relationship(back_populates="audit_logs")
