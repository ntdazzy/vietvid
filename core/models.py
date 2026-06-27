"""Schema cơ sở dữ liệu (SQLAlchemy 2.0). Dùng kiểu dữ liệu tương thích cả Postgres lẫn SQLite."""

from __future__ import annotations

import os
import threading
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    inspect,
    text,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from core.logger import log_event
from core.models_v4_mixins import V5LegacyLinkMixin
from core.runtime_schema_upgrades import schema_upgrade_statements


class Base(DeclarativeBase):
    pass


_SCHEMA_LOCK = threading.RLock()
_POSTGRES_SCHEMA_LOCK_ID = 78630041
_ALLOW_NON_SQLITE_RESET_ENV = "AFFILIATEBOT_ALLOW_NON_SQLITE_SCHEMA_RESET"


# ── Hằng trạng thái (dùng String thay Enum để tương thích đa DB) ──────────
class ProductStatus:
    NEW = "NEW"
    QUALIFIED = "QUALIFIED"
    REJECTED = "REJECTED"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"


class ScriptStatus:
    DRAFT = "DRAFT"
    APPROVED_AI = "APPROVED_AI"  # Critic chấm >= ngưỡng
    REJECTED = "REJECTED"  # quá số vòng lặp mà chưa đạt
    REJECTED_UNSAFE = "REJECTED_UNSAFE"  # không đạt cổng an toàn nội dung


class RenderStatus:
    PENDING = "PENDING"
    RENDERING = "RENDERING"
    DONE = "DONE"
    FAILED = "FAILED"


class AssetStatus:
    READY = "READY"  # nằm trong hàng đợi dispatch (Module 4 tương lai)
    APPROVED = "APPROVED"  # admin đã duyệt qua dashboard/Telegram
    DISPATCHING = "DISPATCHING"  # đang upload qua provider, chặn bấm/gọi trùng
    REJECTED = "REJECTED"  # admin từ chối
    DISPATCHED = "DISPATCHED"  # đã gửi qua Module 4


class DispatchStatus:
    PENDING = "PENDING"
    DONE = "DONE"
    FAILED = "FAILED"


class LinkRequestStatus:
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COOLDOWN = "COOLDOWN"
    DONE = "DONE"
    FAILED = "FAILED"
    LOCKED = "LOCKED"


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(64))
    external_id: Mapped[str] = mapped_column(String(255), index=True)
    name: Mapped[str] = mapped_column(String(512))
    url: Mapped[str] = mapped_column(Text, default="")
    image_url: Mapped[str] = mapped_column(Text, default="")
    image_path: Mapped[str] = mapped_column(Text, default="")
    # V7-B1: nhiều ảnh thật local (gallery 5-9 ảnh) — JSON list các path; image_path giữ làm ảnh bìa.
    image_paths_json: Mapped[str] = mapped_column(Text, default="[]")
    tiktok_shop_product_id: Mapped[str] = mapped_column(String(255), default="", index=True)
    tiktok_shop_url: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(64), default="", index=True)
    category_confidence: Mapped[float] = mapped_column(Float, default=0.0)

    # Chi tiết sản phẩm (enrichment V6-P1.5) — nguồn/enrich_product_detail populate khi có quyền;
    # trống → bộ não viết theo tên (fail-open). Bộ não V5 đọc các field này vào prompt copywriter.
    description: Mapped[str] = mapped_column(Text, default="")
    price: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(8), default="")
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)
    specs_json: Mapped[str] = mapped_column(Text, default="{}")

    # Giá trị thô
    trend_rate: Mapped[float] = mapped_column(Float, default=0.0)
    sales_volume: Mapped[float] = mapped_column(Float, default=0.0)
    intent_count: Mapped[float] = mapped_column(Float, default=0.0)
    commission_total: Mapped[float] = mapped_column(Float, default=0.0)

    # Giá trị đã chuẩn hóa [0,1]
    n_trend: Mapped[float] = mapped_column(Float, default=0.0)
    n_sales: Mapped[float] = mapped_column(Float, default=0.0)
    n_intent: Mapped[float] = mapped_column(Float, default=0.0)
    n_commission: Mapped[float] = mapped_column(Float, default=0.0)

    profit_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    # V8.2: tier A/B/C theo scoring_xtra (A=autopilot lấy, B=tạo tay, C=loại) + breakdown audit.
    tier: Mapped[str] = mapped_column(String(2), default="", index=True)
    score_breakdown_json: Mapped[str] = mapped_column(Text, default="{}")
    product_hash: Mapped[str] = mapped_column(String(64), index=True)
    trace_id: Mapped[str] = mapped_column(String(36), default="", index=True)
    status: Mapped[str] = mapped_column(String(32), default=ProductStatus.NEW, index=True)
    # V7-B1: cổng input cứng — "" (chưa xét) / READY / BLOCKED_INPUT + thiếu gì (hiện trên web).
    input_status: Mapped[str] = mapped_column(String(32), default="", index=True)
    input_missing_json: Mapped[str] = mapped_column(Text, default="{}")
    brain_retry_count: Mapped[int] = mapped_column(Integer, default=0)
    brain_last_attempt_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    last_error: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    scripts: Mapped[list["Script"]] = relationship(back_populates="product")
    creative_variants: Mapped[list["CreativeVariant"]] = relationship(back_populates="product")
    affiliate_links: Mapped[list["AffiliateLink"]] = relationship(back_populates="product")


class MetricHistory(Base):
    """Lưu biên percentile của từng chỉ số theo nguồn để chuẩn hóa ổn định."""

    __tablename__ = "metric_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    metric_name: Mapped[str] = mapped_column(String(64), index=True)
    source: Mapped[str] = mapped_column(String(64), index=True, default="global")
    min_value: Mapped[float] = mapped_column(Float, default=0.0)
    max_value: Mapped[float] = mapped_column(Float, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Script(V5LegacyLinkMixin, Base):
    __tablename__ = "scripts"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(32), default=ScriptStatus.DRAFT, index=True)
    draft_text: Mapped[str] = mapped_column(Text, default="")
    critic_score: Mapped[float] = mapped_column(Float, default=0.0)
    critic_feedback: Mapped[str] = mapped_column(Text, default="")
    iterations: Mapped[int] = mapped_column(Integer, default=0)
    final_json_path: Mapped[str] = mapped_column(Text, default="")
    disclosure_text: Mapped[str] = mapped_column(
        String(255), default="Nội dung có hỗ trợ AI · Tiếp thị liên kết"
    )
    safety_passed: Mapped[bool] = mapped_column(default=False)
    safety_feedback: Mapped[str] = mapped_column(Text, default="")
    approved: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    product: Mapped["Product"] = relationship(back_populates="scripts")
    render_jobs: Mapped[list["RenderJob"]] = relationship(back_populates="script")
    creative_variants: Mapped[list["CreativeVariant"]] = relationship(back_populates="script")


class RenderJob(V5LegacyLinkMixin, Base):
    __tablename__ = "render_jobs"
    __table_args__ = (
        Index(
            "uq_render_jobs_active_script",
            "script_id",
            unique=True,
            sqlite_where=text("status IN ('PENDING', 'RENDERING')"),
            postgresql_where=text("status IN ('PENDING', 'RENDERING')"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    script_id: Mapped[int] = mapped_column(ForeignKey("scripts.id"), index=True)
    status: Mapped[str] = mapped_column(String(32), default=RenderStatus.PENDING, index=True)
    worker_pid: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str] = mapped_column(Text, default="")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    script: Mapped["Script"] = relationship(back_populates="render_jobs")
    assets: Mapped[list["VideoAsset"]] = relationship(back_populates="render_job")


class VideoAsset(V5LegacyLinkMixin, Base):
    __tablename__ = "video_assets"
    __table_args__ = (
        UniqueConstraint("render_job_id", "fmt", name="uq_video_assets_render_job_fmt"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    render_job_id: Mapped[int] = mapped_column(ForeignKey("render_jobs.id"), index=True)
    # V8: truy vết ngược về video_jobs khi asset do video_engine bridge tạo (stub RenderJob)
    video_job_id: Mapped[int | None] = mapped_column(
        ForeignKey("video_jobs.id"), nullable=True, index=True
    )
    fmt: Mapped[str] = mapped_column(String(16))  # "9:16" | "16:9"
    file_path: Mapped[str] = mapped_column(Text)
    sub_id: Mapped[str] = mapped_column(String(64), default="", index=True)
    affiliate_url: Mapped[str] = mapped_column(Text, default="")
    tiktok_shop_affiliate_url: Mapped[str] = mapped_column(Text, default="")
    duration_s: Mapped[float] = mapped_column(Float, default=0.0)
    has_captions: Mapped[bool] = mapped_column(default=False)
    status: Mapped[str] = mapped_column(String(32), default=AssetStatus.READY, index=True)
    source_asset_json: Mapped[str] = mapped_column(Text, default="{}")
    license_status: Mapped[str] = mapped_column(String(32), default="UNKNOWN", index=True)
    qa_status: Mapped[str] = mapped_column(String(32), default="PENDING", index=True)
    qa_report_json: Mapped[str] = mapped_column(Text, default="{}")
    # V8.2 Phase 6: giờ vàng — auto-dispatch CHỈ đăng khi scheduled_at <= now (NULL = đăng ngay).
    scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    render_job: Mapped["RenderJob"] = relationship(back_populates="assets")
    dispatch_jobs: Mapped[list["DispatchJob"]] = relationship(back_populates="asset")
    tracking_tokens: Mapped[list["TrackingToken"]] = relationship(back_populates="video_asset")
    affiliate_links: Mapped[list["AffiliateLink"]] = relationship(back_populates="video_asset")


class DispatchJob(V5LegacyLinkMixin, Base):
    """Lịch sử gửi video qua API đăng bài chính thức hoặc mock provider."""

    __tablename__ = "dispatch_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    video_asset_id: Mapped[int] = mapped_column(ForeignKey("video_assets.id"), index=True)
    provider: Mapped[str] = mapped_column(String(32), default="mock", index=True)
    status: Mapped[str] = mapped_column(String(32), default=DispatchStatus.PENDING, index=True)
    external_post_id: Mapped[str] = mapped_column(String(255), default="")
    post_title: Mapped[str] = mapped_column(String(255), default="")
    post_description: Mapped[str] = mapped_column(Text, default="")
    cta_text: Mapped[str] = mapped_column(Text, default="")
    followup_comment: Mapped[str] = mapped_column(Text, default="")
    platform_action: Mapped[str] = mapped_column(String(128), default="")
    error: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    asset: Mapped["VideoAsset"] = relationship(back_populates="dispatch_jobs")


class LinkRequestQueue(V5LegacyLinkMixin, Base):
    """Hàng đợi tạo affiliate link; tách khỏi render để không gọi Shopee dồn dập."""

    __tablename__ = "link_request_queue"
    __table_args__ = (
        UniqueConstraint("video_asset_id", "provider", name="uq_link_request_asset_provider"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    video_asset_id: Mapped[int] = mapped_column(ForeignKey("video_assets.id"), index=True)
    provider: Mapped[str] = mapped_column(String(32), default="shopee_cdp", index=True)
    status: Mapped[str] = mapped_column(String(32), default=LinkRequestStatus.PENDING, index=True)
    product_url: Mapped[str] = mapped_column(Text, default="")
    sub_id: Mapped[str] = mapped_column(String(64), default="", index=True)
    short_link: Mapped[str] = mapped_column(Text, default="")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str] = mapped_column(Text, default="")
    locked_reason: Mapped[str] = mapped_column(Text, default="")
    available_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    asset: Mapped["VideoAsset"] = relationship()


class ProductPerformance(V5LegacyLinkMixin, Base):
    """Dữ liệu doanh thu/click thật để hệ thống học sản phẩm nào ra tiền."""

    __tablename__ = "product_performance"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    video_asset_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    sub_id: Mapped[str] = mapped_column(String(64), index=True, default="")
    # E1: kênh đăng suy từ sub_id → token → PublishJob.platform (1 sub_id = 1 platform).
    # Chỉ để báo cáo doanh thu per-kênh; KHÔNG thêm vào khóa idempotency (sub_id đã xác định kênh).
    platform: Mapped[str] = mapped_column(String(32), index=True, default="")
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    orders: Mapped[int] = mapped_column(Integer, default=0)
    conversion_rate: Mapped[float] = mapped_column(Float, default=0.0)
    commission_earned: Mapped[float] = mapped_column(Float, default=0.0)
    refunds: Mapped[int] = mapped_column(Integer, default=0)
    refund_amount: Mapped[float] = mapped_column(Float, default=0.0)
    net_commission: Mapped[float] = mapped_column(Float, default=0.0)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    product: Mapped["Product"] = relationship()


class CategoryStat(Base):
    """Tín hiệu doanh thu theo ngành để điều chỉnh ranking Module 1."""

    __tablename__ = "category_stats"

    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    videos: Mapped[int] = mapped_column(Integer, default=0)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    orders: Mapped[int] = mapped_column(Integer, default=0)
    refunds: Mapped[int] = mapped_column(Integer, default=0)
    gross_commission: Mapped[float] = mapped_column(Float, default=0.0)
    refund_amount: Mapped[float] = mapped_column(Float, default=0.0)
    net_commission: Mapped[float] = mapped_column(Float, default=0.0)
    conversion_rate: Mapped[float] = mapped_column(Float, default=0.0)
    return_rate: Mapped[float] = mapped_column(Float, default=0.0)
    weight: Mapped[float] = mapped_column(Float, default=1.0, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ChannelStat(Base):
    """Doanh thu theo (ngành × kênh) — đo kênh nào in tiền cho từng ngách (E1).

    Mirror CategoryStat nhưng tách thêm chiều `platform` (youtube/meta/instagram/tiktok).
    Dùng cho báo cáo per-kênh; `weight` để P2 phân bổ autopilot theo kênh thắng.
    """

    __tablename__ = "channel_stats"
    __table_args__ = (
        UniqueConstraint("category", "platform", name="uq_channel_stats_category_platform"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(String(64), index=True)
    platform: Mapped[str] = mapped_column(String(32), index=True)
    videos: Mapped[int] = mapped_column(Integer, default=0)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    orders: Mapped[int] = mapped_column(Integer, default=0)
    refunds: Mapped[int] = mapped_column(Integer, default=0)
    gross_commission: Mapped[float] = mapped_column(Float, default=0.0)
    refund_amount: Mapped[float] = mapped_column(Float, default=0.0)
    net_commission: Mapped[float] = mapped_column(Float, default=0.0)
    conversion_rate: Mapped[float] = mapped_column(Float, default=0.0)
    return_rate: Mapped[float] = mapped_column(Float, default=0.0)
    weight: Mapped[float] = mapped_column(Float, default=1.0, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class SystemEvent(Base):
    """Nhật ký sự kiện hệ thống — phục vụ dashboard & cảnh báo Telegram."""

    __tablename__ = "system_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    level: Mapped[str] = mapped_column(String(16), default="INFO", index=True)
    module: Mapped[str] = mapped_column(String(64), default="")
    message: Mapped[str] = mapped_column(Text, default="")
    screenshot_path: Mapped[str] = mapped_column(Text, default="")
    resolved: Mapped[bool] = mapped_column(default=False, index=True)
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    dismissed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )


# ── V8 Video Engine (Plan C: Gemini Image + Seedance PiAPI) ────────────────
class KolStatus:
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"


class VideoJobStatus:
    """Máy trạng thái video_jobs — UI đọc trực tiếp các giá trị này."""

    WAITING_CONFIG = "WAITING_CONFIG"  # thiếu key/budget config → không chạy giả
    QUEUED = "QUEUED"  # chờ worker nhặt
    QUEUED_BUDGET = "QUEUED_BUDGET"  # hết ngân sách ngày → xếp hàng mai
    RUNNING = "RUNNING"  # đang chạy (stage chi tiết trong stage_timings)
    QA_FAIL = "QA_FAIL"  # không qua cổng fidelity → không cho duyệt
    READY = "READY"  # video xong, chờ founder duyệt
    APPROVED = "APPROVED"  # đã duyệt → bridge sang VideoAsset
    REJECTED = "REJECTED"  # founder từ chối
    FAILED = "FAILED"  # lỗi kỹ thuật (provider/timeout/…)


class KolCharacter(Base):
    """Hồ sơ KOL ảo dùng lại cho nhiều video (ảnh + giọng + character sheet)."""

    __tablename__ = "kol_characters"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    gender: Mapped[str] = mapped_column(String(16), default="")
    persona: Mapped[str] = mapped_column(Text, default="")
    style: Mapped[str] = mapped_column(String(64), default="")
    image_path: Mapped[str] = mapped_column(Text, default="")
    ref_image_paths: Mapped[str] = mapped_column(Text, default="[]")  # JSON list path
    image_source: Mapped[str] = mapped_column(String(16), default="generated")  # uploaded|generated
    consent_status: Mapped[str] = mapped_column(String(16), default="")  # bắt buộc với uploaded
    consent_note: Mapped[str] = mapped_column(Text, default="")
    voice_provider: Mapped[str] = mapped_column(String(32), default="vbee")
    voice_id: Mapped[str] = mapped_column(String(64), default="")
    character_sheet: Mapped[str] = mapped_column(Text, default="")
    tags: Mapped[str] = mapped_column(Text, default="[]")  # JSON list ngách
    status: Mapped[str] = mapped_column(String(16), default=KolStatus.DRAFT, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    video_jobs: Mapped[list["VideoJob"]] = relationship(back_populates="kol")


class AdFormat(Base):
    """Template format quảng cáo — mỗi format = 1 system prompt cho Director."""

    __tablename__ = "ad_formats"

    key: Mapped[str] = mapped_column(String(32), primary_key=True)
    label: Mapped[str] = mapped_column(String(128))
    icon: Mapped[str] = mapped_column(String(32), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    director_system_prompt: Mapped[str] = mapped_column(Text, default="")
    default_duration: Mapped[int] = mapped_column(Integer, default=10)
    shot_pattern: Mapped[str] = mapped_column(Text, default="[]")  # JSON list shot
    requires_kol: Mapped[bool] = mapped_column(default=False)
    supports_product_only: Mapped[bool] = mapped_column(default=True)
    # V8.2 Phase 3: chính sách chữ trên video (Seedance vẽ): require | allow | forbid.
    overlay_policy: Mapped[str] = mapped_column(String(8), default="allow")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="ACTIVE")


class ScenePreset(Base):
    """Bối cảnh KOL (học từ autovis koc-context) — prompt nền sinh ảnh/video nhân vật."""

    __tablename__ = "scene_presets"

    key: Mapped[str] = mapped_column(String(48), primary_key=True)
    label: Mapped[str] = mapped_column(String(128))
    category: Mapped[str] = mapped_column(String(32), default="chung")  # ngách: thời trang/beauty…
    gender_hint: Mapped[str] = mapped_column(String(16), default="")  # nam|nữ|"" (gợi ý)
    image_prompt: Mapped[str] = mapped_column(Text, default="")  # prompt nền (EN) tả nhân vật+bối cảnh
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="ACTIVE")


class PromptTemplate(Base):
    """Template prompt video autovis (36 mẫu) — gallery #/product-ads, import từ dump."""

    __tablename__ = "prompt_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(48), default="")  # slug autovis (quang-cao…)
    category_label: Mapped[str] = mapped_column(String(128), default="")
    title_vi: Mapped[str] = mapped_column(String(256), default="")
    title_en: Mapped[str] = mapped_column(String(256), default="")
    prompt_vi: Mapped[str] = mapped_column(Text, default="")
    prompt_en: Mapped[str] = mapped_column(Text, default="")
    aspect: Mapped[str] = mapped_column(String(8), default="9:16")
    duration: Mapped[int] = mapped_column(Integer, default=15)
    resolution: Mapped[str] = mapped_column(String(8), default="480p")
    model: Mapped[str] = mapped_column(String(64), default="")
    format_key: Mapped[str] = mapped_column(String(32), default="")  # map sang ad_formats
    thumb_path: Mapped[str] = mapped_column(Text, default="")
    poster_path: Mapped[str] = mapped_column(Text, default="")
    source_thumb_url: Mapped[str] = mapped_column(Text, default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="ACTIVE")


class ScenePrompt(Base):
    """Prompt mẫu từng bối cảnh (80 prompt FULL từ autovis) — thư viện ảnh KOL #/kol-ai."""

    __tablename__ = "scene_prompts"

    id: Mapped[int] = mapped_column(primary_key=True)
    scene_key: Mapped[str] = mapped_column(String(48), index=True)  # khớp scene_presets.key
    ord: Mapped[int] = mapped_column(Integer, default=0)
    prompt: Mapped[str] = mapped_column(Text, default="")  # prompt FULL không cắt
    source_image_url: Mapped[str] = mapped_column(Text, default="")
    thumb_path: Mapped[str] = mapped_column(Text, default="")  # ảnh tự sinh Gemini (Phase 7)
    status: Mapped[str] = mapped_column(String(16), default="ACTIVE")


class VideoJob(Base):
    """1 yêu cầu tạo video AI — máy trạng thái + chi phí + asset từng stage."""

    __tablename__ = "video_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    idempotency_key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id"), nullable=True, index=True
    )
    kol_id: Mapped[int | None] = mapped_column(
        ForeignKey("kol_characters.id"), nullable=True, index=True
    )
    format_key: Mapped[str] = mapped_column(String(32), default="")
    mode: Mapped[str] = mapped_column(String(16), default="product_only")  # kol_full|product_only|premium
    purpose: Mapped[str] = mapped_column(String(8), default="final")  # draft|final
    speed_tier: Mapped[str] = mapped_column(String(8), default="fast")  # fast|pro
    moderation_policy: Mapped[str] = mapped_column(String(20), default="strict")  # strict|less_restriction
    resolution: Mapped[str] = mapped_column(String(8), default="720p")  # 480p|720p|1080p
    seconds: Mapped[int] = mapped_column(Integer, default=10)
    status: Mapped[str] = mapped_column(String(20), default=VideoJobStatus.QUEUED, index=True)
    params: Mapped[str] = mapped_column(Text, default="{}")  # JSON: prompt người dùng, voice, aspect…
    provider_image: Mapped[str] = mapped_column(String(32), default="")
    provider_video: Mapped[str] = mapped_column(String(32), default="")
    model_id: Mapped[str] = mapped_column(String(64), default="")
    estimated_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    max_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    actual_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    final_path: Mapped[str] = mapped_column(Text, default="")
    stage_timings: Mapped[str] = mapped_column(Text, default="{}")  # JSON: stage → {status,start,end}
    error: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    product: Mapped["Product | None"] = relationship()
    kol: Mapped["KolCharacter | None"] = relationship(back_populates="video_jobs")
    shot_plans: Mapped[list["ShotPlan"]] = relationship(back_populates="job")
    stage_assets: Mapped[list["VideoStageAsset"]] = relationship(back_populates="job")


class ShotPlan(Base):
    """Storyboard + narration + prompt do Director sinh cho 1 job."""

    __tablename__ = "shot_plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("video_jobs.id"), index=True)
    storyboard: Mapped[str] = mapped_column(Text, default="[]")  # JSON list shot theo timecode
    narration: Mapped[str] = mapped_column(Text, default="")
    image_prompts: Mapped[str] = mapped_column(Text, default="[]")  # JSON list prompt ảnh
    video_prompt: Mapped[str] = mapped_column(Text, default="")
    cta: Mapped[str] = mapped_column(Text, default="")
    # V8.3-Q1: chữ vẽ LOCAL [{t,text,pos,kind,sent}] — từ product_facts, không bịa số.
    text_overlays: Mapped[str] = mapped_column(Text, default="[]")
    # V8.3-Q4: Script Critic chấm trước render — score 0-10 (NULL = critic lỗi/fail-open).
    critic_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    critic_notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    job: Mapped["VideoJob"] = relationship(back_populates="shot_plans")


class ScriptFormula(Base):
    """Công thức viral chưng cất (36 template autovis + viral bóc tay) — few-shot cho Director."""

    __tablename__ = "script_formulas"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    source: Mapped[str] = mapped_column(String(32), default="autovis")  # autovis|viral_video
    autovis_category: Mapped[str] = mapped_column(String(48), default="")
    format_key: Mapped[str] = mapped_column(String(32), default="", index=True)
    title: Mapped[str] = mapped_column(String(256), default="")
    prompt_en: Mapped[str] = mapped_column(Text, default="")
    prompt_vi: Mapped[str] = mapped_column(Text, default="")
    product_keywords: Mapped[str] = mapped_column(Text, default="")  # CSV keyword ngách/SP
    duration: Mapped[int] = mapped_column(Integer, default=15)
    status: Mapped[str] = mapped_column(String(16), default="ACTIVE")
    uses: Mapped[int] = mapped_column(Integer, default=0)
    # V8.3-Q7: learning — formula THẮNG (doanh thu thật) được pick_formulas ưu tiên.
    wins: Mapped[int] = mapped_column(Integer, default=0)
    revenue_usd: Mapped[float] = mapped_column(Float, default=0.0)


class VideoStageAsset(Base):
    """Asset trung gian từng stage (ảnh/video/voice/compose) + cost + QA report."""

    __tablename__ = "video_stage_assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("video_jobs.id"), index=True)
    stage: Mapped[str] = mapped_column(String(16))  # image|video|voice|compose
    path: Mapped[str] = mapped_column(Text, default="")
    provider: Mapped[str] = mapped_column(String(32), default="")
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    qa_report: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    job: Mapped["VideoJob"] = relationship(back_populates="stage_assets")


class ProviderLedger(Base):
    """Sổ chi tiêu ngày/provider — NGUỒN ngân sách duy nhất (reserve qua row-lock)."""

    __tablename__ = "provider_ledger"
    __table_args__ = (
        UniqueConstraint("date", "provider", name="uq_provider_ledger_date_provider"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[str] = mapped_column(String(10), index=True)  # YYYY-MM-DD (UTC)
    provider: Mapped[str] = mapped_column(String(32))
    spent_usd: Mapped[float] = mapped_column(Float, default=0.0)
    budget_usd: Mapped[float] = mapped_column(Float, default=0.0)
    jobs_count: Mapped[int] = mapped_column(Integer, default=0)


def ensure_runtime_schema(engine: Engine) -> None:
    """Bổ sung cột mới khi chạy trên DB đã tạo từ scaffold cũ.

    create_all() không tự ALTER bảng đã tồn tại; helper này giữ compatibility cho
    SQLite/Postgres trong giai đoạn chưa dùng Alembic.
    """
    log_event("db", "runtime_schema_check_start", dialect=engine.dialect.name)
    if engine.dialect.name == "postgresql":
        with engine.begin() as conn:
            conn.execute(text(f"SELECT pg_advisory_xact_lock({_POSTGRES_SCHEMA_LOCK_ID})"))
            _ensure_runtime_schema_locked(conn)
        log_event("db", "runtime_schema_check_done", dialect=engine.dialect.name)
        return
    with _SCHEMA_LOCK:
        with engine.begin() as conn:
            _ensure_runtime_schema_locked(conn)
    log_event("db", "runtime_schema_check_done", dialect=engine.dialect.name)


def initialize_schema(engine: Engine, reset: bool = False) -> None:
    """Tạo/nâng cấp schema có khóa để tránh race DDL khi nhiều script chạy song song."""
    if reset and engine.dialect.name != "sqlite" and not _non_sqlite_reset_confirmed():
        raise RuntimeError(
            "Schema reset trên DB không phải SQLite bị chặn. "
            f"Chỉ bật {_ALLOW_NON_SQLITE_RESET_ENV}=I_UNDERSTAND_THIS_DROPS_DATA "
            "khi đã backup và thật sự muốn xóa dữ liệu."
        )
    log_event("db", "schema_init_start", dialect=engine.dialect.name, reset=reset)
    if engine.dialect.name == "postgresql":
        with engine.begin() as conn:
            conn.execute(text(f"SELECT pg_advisory_xact_lock({_POSTGRES_SCHEMA_LOCK_ID})"))
            if reset:
                Base.metadata.drop_all(conn)
            Base.metadata.create_all(conn)
            _ensure_runtime_schema_locked(conn)
        log_event("db", "schema_init_done", dialect=engine.dialect.name, reset=reset)
        return
    with _SCHEMA_LOCK:
        if reset:
            Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        ensure_runtime_schema(engine)
    log_event("db", "schema_init_done", dialect=engine.dialect.name, reset=reset)


def _non_sqlite_reset_confirmed() -> bool:
    return os.getenv(_ALLOW_NON_SQLITE_RESET_ENV) == "I_UNDERSTAND_THIS_DROPS_DATA"


def _ensure_runtime_schema_locked(conn) -> None:  # noqa: ANN001
    inspector = inspect(conn)
    statements = schema_upgrade_statements(inspector)
    log_event("db", "runtime_schema_patch_plan", statement_count=len(statements))
    for stmt in statements:
        conn.execute(text(stmt))


# Import sau khi model V4 đã khai báo để V5 dùng chung Base nhưng không làm file này phình dài.
from core.models_v5 import (  # noqa: E402
    AffiliateLink,
    AffiliateLinkStatus,
    AuditActorType,
    AuditLog,
    BrowserQaAssetBlockingMode,
    BrowserQaRun,
    BrowserQaRunStatus,
    BrowserQaScenario,
    BrowserTestProfile,
    BrowserTestProfileStatus,
    Campaign,
    CampaignStatus,
    ChannelAccount,
    ChannelAccountStatus,
    ChannelSession,
    ChannelSessionStatus,
    ClickRollup,
    ComplianceStatus,
    CreativeVariant,
    CreativeVariantStatus,
    Experiment,
    ExperimentAllocation,
    ExperimentStatus,
    HookExperiment,
    HookExperimentStatus,
    Incident,
    IncidentStatus,
    LandingPage,
    LandingPageStatus,
    LandingPageVariant,
    LeadAction,
    LeadActionStatus,
    LeadSignal,
    LeadSignalStatus,
    NetworkProxy,
    NetworkProxyStatus,
    NetworkProxyType,
    PostPublication,
    PostPublicationStatus,
    PublishJob,
    PublishJobStatus,
    ScriptPattern,
    ScriptPatternStatus,
    SessionLease,
    SessionLeaseStatus,
    TrackingToken,
    TrackingTokenStatus,
    TrendSignal,
    TrendSignalStatus,
    VariantScene,
)
