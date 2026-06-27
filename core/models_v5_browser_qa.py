"""V5 Browser QA, Test Profile, and Network Diagnostics models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.models import Base
from core.models_v5_common import TimestampMixin


class NetworkProxyStatus:
    UNKNOWN = "UNKNOWN"
    READY = "READY"
    FAILED = "FAILED"
    DISABLED = "DISABLED"


class NetworkProxyType:
    STATIC = "static"
    ROTATING = "rotating"
    DCOM = "dcom"


class BrowserTestProfileStatus:
    NEEDS_SETUP = "NEEDS_SETUP"
    READY = "READY"
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    DISABLED = "DISABLED"


class BrowserQaRunStatus:
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    NEEDS_OPERATOR = "NEEDS_OPERATOR"
    CANCELLED = "CANCELLED"


class BrowserQaScenario:
    QUICK_CHECK = "quick_check"
    FULL_SMOKE = "full_smoke"
    READ_ONLY = "read_only"
    OFFLINE_CHECK = "offline_check"


class BrowserQaAssetBlockingMode:
    OFF = "off"
    MEDIA_ONLY = "media_only"
    HEAVY = "heavy"


class NetworkProxy(TimestampMixin, Base):
    __tablename__ = "proxies"
    __table_args__ = (
        UniqueConstraint(
            "protocol",
            "host",
            "port",
            "username",
            name="uq_proxies_endpoint_user",
        ),
        Index("ix_proxies_status", "status"),
        Index("ix_proxies_proxy_type", "proxy_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    protocol: Mapped[str] = mapped_column(String(16))
    host: Mapped[str] = mapped_column(String(255))
    port: Mapped[int] = mapped_column(Integer)
    proxy_type: Mapped[str] = mapped_column(String(32), default=NetworkProxyType.STATIC)
    username: Mapped[str] = mapped_column(String(255), default="")
    password_encrypted: Mapped[str] = mapped_column(Text, default="")
    refresh_url_encrypted: Mapped[str] = mapped_column(Text, default="")
    diagnostic_url: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default=NetworkProxyStatus.UNKNOWN)
    last_ip: Mapped[str] = mapped_column(String(64), default="")
    last_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_error_redacted: Mapped[str] = mapped_column(Text, default="")
    fail_count: Mapped[int] = mapped_column(Integer, default=0)
    checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    browser_profiles: Mapped[list["BrowserTestProfile"]] = relationship(back_populates="proxy")


class BrowserTestProfile(TimestampMixin, Base):
    __tablename__ = "browser_test_profiles"
    __table_args__ = (
        UniqueConstraint("profile_key", name="uq_browser_test_profiles_profile_key"),
        Index("ix_browser_test_profiles_platform", "platform"),
        Index("ix_browser_test_profiles_status", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    owner_label: Mapped[str] = mapped_column(String(128), default="")
    platform: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default=BrowserTestProfileStatus.NEEDS_SETUP)
    profile_key: Mapped[str] = mapped_column(String(128))
    user_data_dir: Mapped[str] = mapped_column(Text)
    proxy_id: Mapped[int | None] = mapped_column(ForeignKey("proxies.id"), nullable=True)
    viewport_width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    viewport_height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    user_agent: Mapped[str] = mapped_column(Text, default="")
    device_profile_json: Mapped[str] = mapped_column(Text, default="{}")
    credential_ref: Mapped[str] = mapped_column(String(255), default="")
    cookie_encrypted: Mapped[str] = mapped_column(Text, default="")
    password_encrypted: Mapped[str] = mapped_column(Text, default="")
    mfa_secret_encrypted: Mapped[str] = mapped_column(Text, default="")
    scenario_profile: Mapped[str] = mapped_column(String(32), default=BrowserQaScenario.QUICK_CHECK)
    asset_blocking_mode: Mapped[str] = mapped_column(
        String(32), default=BrowserQaAssetBlockingMode.MEDIA_ONLY
    )
    last_run_status: Mapped[str] = mapped_column(String(32), default="")
    last_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    last_error_redacted: Mapped[str] = mapped_column(Text, default="")
    tags_json: Mapped[str] = mapped_column(Text, default="[]")

    proxy: Mapped["NetworkProxy | None"] = relationship(back_populates="browser_profiles")
    qa_runs: Mapped[list["BrowserQaRun"]] = relationship(back_populates="profile")


class BrowserQaRun(TimestampMixin, Base):
    __tablename__ = "browser_qa_runs"
    __table_args__ = (
        Index("ix_browser_qa_runs_profile_id", "profile_id"),
        Index("ix_browser_qa_runs_status", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("browser_test_profiles.id"))
    scenario: Mapped[str] = mapped_column(String(64))
    target_url: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default=BrowserQaRunStatus.QUEUED)
    confirm_side_effect: Mapped[bool] = mapped_column(default=False)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    screenshot_path: Mapped[str] = mapped_column(Text, default="")
    trace_path: Mapped[str] = mapped_column(Text, default="")
    log_json: Mapped[str] = mapped_column(Text, default="{}")
    metrics_json: Mapped[str] = mapped_column(Text, default="{}")
    error_message_redacted: Mapped[str] = mapped_column(Text, default="")

    profile: Mapped["BrowserTestProfile"] = relationship(back_populates="qa_runs")
