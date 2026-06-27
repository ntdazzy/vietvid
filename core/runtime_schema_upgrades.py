"""Runtime schema patches for old DBs created before Alembic.

These patches keep early SQLite/Postgres installs running while migrations are
introduced gradually. New schema changes should still live in Alembic first.
"""

from __future__ import annotations


V5_LEGACY_LINK_TABLES = (
    "scripts",
    "render_jobs",
    "video_assets",
    "dispatch_jobs",
    "link_request_queue",
    "product_performance",
)


def schema_upgrade_statements(inspector) -> list[str]:  # noqa: ANN001
    if not inspector.has_table("products"):
        return []

    statements: list[str] = []
    statements.extend(_product_statements(inspector))
    statements.extend(_script_statements(inspector))
    statements.extend(_asset_statements(inspector))
    statements.extend(_render_job_statements(inspector))
    statements.extend(_dispatch_job_statements(inspector))
    statements.extend(_publish_job_statements(inspector))
    statements.extend(_system_event_statements(inspector))
    statements.extend(_performance_statements(inspector))
    statements.extend(_lead_signal_statements(inspector))
    statements.extend(_affiliate_link_statements(inspector))
    statements.extend(_v5_legacy_link_statements(inspector))
    statements.extend(_browser_qa_statements(inspector))
    return statements


def _columns(inspector, table_name: str) -> set[str]:  # noqa: ANN001
    return {col["name"] for col in inspector.get_columns(table_name)}


def _indexes(inspector, table_name: str) -> set[str]:  # noqa: ANN001
    return {idx["name"] for idx in inspector.get_indexes(table_name)}


def _product_statements(inspector) -> list[str]:  # noqa: ANN001
    existing = _columns(inspector, "products")
    statements: list[str] = []
    if "brain_retry_count" not in existing:
        statements.append("ALTER TABLE products ADD COLUMN brain_retry_count INTEGER DEFAULT 0")
    if "brain_last_attempt_at" not in existing:
        statements.append("ALTER TABLE products ADD COLUMN brain_last_attempt_at TIMESTAMP")
    if "last_error" not in existing:
        statements.append("ALTER TABLE products ADD COLUMN last_error TEXT DEFAULT ''")
    if "trace_id" not in existing:
        statements.append("ALTER TABLE products ADD COLUMN trace_id VARCHAR(36) DEFAULT ''")
    if "category" not in existing:
        statements.append("ALTER TABLE products ADD COLUMN category VARCHAR(64) DEFAULT ''")
    if "category_confidence" not in existing:
        statements.append("ALTER TABLE products ADD COLUMN category_confidence FLOAT DEFAULT 0.0")
    if "tiktok_shop_product_id" not in existing:
        statements.append(
            "ALTER TABLE products ADD COLUMN tiktok_shop_product_id VARCHAR(255) DEFAULT ''"
        )
    if "tiktok_shop_url" not in existing:
        statements.append("ALTER TABLE products ADD COLUMN tiktok_shop_url TEXT DEFAULT ''")
    if "image_url" not in existing:
        statements.append("ALTER TABLE products ADD COLUMN image_url TEXT DEFAULT ''")
    if "image_path" not in existing:
        statements.append("ALTER TABLE products ADD COLUMN image_path TEXT DEFAULT ''")
    if "description" not in existing:
        statements.append("ALTER TABLE products ADD COLUMN description TEXT DEFAULT ''")
    if "price" not in existing:
        statements.append("ALTER TABLE products ADD COLUMN price FLOAT DEFAULT 0.0")
    if "currency" not in existing:
        statements.append("ALTER TABLE products ADD COLUMN currency VARCHAR(8) DEFAULT ''")
    if "rating" not in existing:
        statements.append("ALTER TABLE products ADD COLUMN rating FLOAT DEFAULT 0.0")
    if "rating_count" not in existing:
        statements.append("ALTER TABLE products ADD COLUMN rating_count INTEGER DEFAULT 0")
    if "specs_json" not in existing:
        statements.append("ALTER TABLE products ADD COLUMN specs_json TEXT DEFAULT '{}'")
    # V7-B1: gallery nhiều ảnh thật + cổng input cứng.
    if "image_paths_json" not in existing:
        statements.append("ALTER TABLE products ADD COLUMN image_paths_json TEXT DEFAULT '[]'")
    if "input_status" not in existing:
        statements.append("ALTER TABLE products ADD COLUMN input_status VARCHAR(32) DEFAULT ''")
    if "input_missing_json" not in existing:
        statements.append("ALTER TABLE products ADD COLUMN input_missing_json TEXT DEFAULT '{}'")
    return statements


def _script_statements(inspector) -> list[str]:  # noqa: ANN001
    if not inspector.has_table("scripts"):
        return []

    existing = _columns(inspector, "scripts")
    statements: list[str] = []
    if "safety_passed" not in existing:
        statements.append("ALTER TABLE scripts ADD COLUMN safety_passed BOOLEAN DEFAULT FALSE")
    if "safety_feedback" not in existing:
        statements.append("ALTER TABLE scripts ADD COLUMN safety_feedback TEXT DEFAULT ''")
    return statements


def _asset_statements(inspector) -> list[str]:  # noqa: ANN001
    if not inspector.has_table("video_assets"):
        return []

    existing = _columns(inspector, "video_assets")
    statements: list[str] = []
    if "sub_id" not in existing:
        statements.append("ALTER TABLE video_assets ADD COLUMN sub_id VARCHAR(64) DEFAULT ''")
    if "affiliate_url" not in existing:
        statements.append("ALTER TABLE video_assets ADD COLUMN affiliate_url TEXT DEFAULT ''")
    if "tiktok_shop_affiliate_url" not in existing:
        statements.append(
            "ALTER TABLE video_assets ADD COLUMN tiktok_shop_affiliate_url TEXT DEFAULT ''"
        )
    if "source_asset_json" not in existing:
        statements.append("ALTER TABLE video_assets ADD COLUMN source_asset_json TEXT DEFAULT '{}'")
    if "license_status" not in existing:
        statements.append(
            "ALTER TABLE video_assets ADD COLUMN license_status VARCHAR(32) DEFAULT 'UNKNOWN'"
        )
    if "qa_status" not in existing:
        statements.append(
            "ALTER TABLE video_assets ADD COLUMN qa_status VARCHAR(32) DEFAULT 'PENDING'"
        )
    if "qa_report_json" not in existing:
        statements.append("ALTER TABLE video_assets ADD COLUMN qa_report_json TEXT DEFAULT '{}'")
    if _needs_video_asset_fmt_unique_index(inspector, existing):
        statements.append(
            "DELETE FROM video_assets WHERE id IN ("
            "SELECT id FROM ("
            "SELECT id, ROW_NUMBER() OVER ("
            "PARTITION BY render_job_id, fmt ORDER BY id DESC"
            ") AS rn FROM video_assets "
            "WHERE render_job_id IS NOT NULL AND fmt IS NOT NULL"
            ") ranked WHERE rn > 1"
            ")"
        )
        statements.append(
            "CREATE UNIQUE INDEX uq_video_assets_render_job_fmt "
            "ON video_assets (render_job_id, fmt)"
        )
    return statements


def _needs_video_asset_fmt_unique_index(inspector, existing: set[str]) -> bool:  # noqa: ANN001
    indexes = _indexes(inspector, "video_assets")
    unique_indexes = {
        idx["name"] for idx in inspector.get_indexes("video_assets") if idx.get("unique")
    }
    constraints = {
        constraint["name"]
        for constraint in inspector.get_unique_constraints("video_assets")
        if constraint.get("name")
    }
    return (
        "uq_video_assets_render_job_fmt" not in indexes
        and "uq_video_assets_render_job_fmt" not in unique_indexes
        and "uq_video_assets_render_job_fmt" not in constraints
        and {"id", "render_job_id", "fmt"}.issubset(existing)
    )


def _render_job_statements(inspector) -> list[str]:  # noqa: ANN001
    if not inspector.has_table("render_jobs"):
        return []

    existing = _columns(inspector, "render_jobs")
    indexes = _indexes(inspector, "render_jobs")
    if "uq_render_jobs_active_script" in indexes or not {
        "id",
        "script_id",
        "status",
    }.issubset(existing):
        return []

    return [
        "UPDATE render_jobs SET status = 'FAILED' WHERE id IN ("
        "SELECT id FROM ("
        "SELECT id, ROW_NUMBER() OVER ("
        "PARTITION BY script_id ORDER BY id DESC"
        ") AS rn FROM render_jobs "
        "WHERE script_id IS NOT NULL AND status IN ('PENDING', 'RENDERING')"
        ") ranked WHERE rn > 1"
        ")",
        "CREATE UNIQUE INDEX uq_render_jobs_active_script "
        "ON render_jobs (script_id) WHERE status IN ('PENDING', 'RENDERING')",
    ]


def _dispatch_job_statements(inspector) -> list[str]:  # noqa: ANN001
    if not inspector.has_table("dispatch_jobs"):
        return []

    existing = _columns(inspector, "dispatch_jobs")
    statements: list[str] = []
    if "post_title" not in existing:
        statements.append("ALTER TABLE dispatch_jobs ADD COLUMN post_title VARCHAR(255) DEFAULT ''")
    if "post_description" not in existing:
        statements.append("ALTER TABLE dispatch_jobs ADD COLUMN post_description TEXT DEFAULT ''")
    if "cta_text" not in existing:
        statements.append("ALTER TABLE dispatch_jobs ADD COLUMN cta_text TEXT DEFAULT ''")
    if "followup_comment" not in existing:
        statements.append("ALTER TABLE dispatch_jobs ADD COLUMN followup_comment TEXT DEFAULT ''")
    if "platform_action" not in existing:
        statements.append(
            "ALTER TABLE dispatch_jobs ADD COLUMN platform_action VARCHAR(128) DEFAULT ''"
        )
    return statements


def _publish_job_statements(inspector) -> list[str]:  # noqa: ANN001
    if not inspector.has_table("publish_jobs"):
        return []
    existing = _columns(inspector, "publish_jobs")
    statements: list[str] = []
    if "external_post_id" not in existing:
        statements.append(
            "ALTER TABLE publish_jobs ADD COLUMN external_post_id VARCHAR(255) DEFAULT ''"
        )
    return statements


def _system_event_statements(inspector) -> list[str]:  # noqa: ANN001
    if not inspector.has_table("system_events"):
        return []

    existing = _columns(inspector, "system_events")
    statements: list[str] = []
    if "read_at" not in existing:
        statements.append("ALTER TABLE system_events ADD COLUMN read_at TIMESTAMP")
    if "dismissed_at" not in existing:
        statements.append("ALTER TABLE system_events ADD COLUMN dismissed_at TIMESTAMP")
    return statements


def _affiliate_link_statements(inspector) -> list[str]:  # noqa: ANN001
    if not inspector.has_table("affiliate_links"):
        return []

    existing = _columns(inspector, "affiliate_links")
    statements: list[str] = []
    if "commission_expires_at" not in existing:
        statements.append("ALTER TABLE affiliate_links ADD COLUMN commission_expires_at TIMESTAMP")
    if "last_checked_at" not in existing:
        statements.append("ALTER TABLE affiliate_links ADD COLUMN last_checked_at TIMESTAMP")
    indexes = _indexes(inspector, "affiliate_links")
    if "ix_affiliate_links_commission_expires_at" not in indexes:
        statements.append(
            "CREATE INDEX ix_affiliate_links_commission_expires_at "
            "ON affiliate_links (commission_expires_at)"
        )
    if "ix_affiliate_links_last_checked_at" not in indexes:
        statements.append(
            "CREATE INDEX ix_affiliate_links_last_checked_at ON affiliate_links (last_checked_at)"
        )
    return statements


def _performance_statements(inspector) -> list[str]:  # noqa: ANN001
    if not inspector.has_table("product_performance"):
        return []

    existing = _columns(inspector, "product_performance")
    statements: list[str] = []
    if "refund_amount" not in existing:
        statements.append(
            "ALTER TABLE product_performance ADD COLUMN refund_amount FLOAT DEFAULT 0.0"
        )
    if "net_commission" not in existing:
        statements.append(
            "ALTER TABLE product_performance ADD COLUMN net_commission FLOAT DEFAULT 0.0"
        )
    if "video_asset_id" not in existing:
        statements.append("ALTER TABLE product_performance ADD COLUMN video_asset_id INTEGER")
    if "platform" not in existing:  # E1: khớp Alembic 0020 cho DB cũ boot không qua alembic
        statements.append(
            "ALTER TABLE product_performance ADD COLUMN platform VARCHAR(32) DEFAULT ''"
        )
    indexes = _indexes(inspector, "product_performance")
    if "ix_product_performance_video_asset_id" not in indexes:
        statements.append(
            "CREATE INDEX ix_product_performance_video_asset_id "
            "ON product_performance (video_asset_id)"
        )
    if "ix_product_performance_platform" not in indexes:
        statements.append(
            "CREATE INDEX ix_product_performance_platform ON product_performance (platform)"
        )
    if (
        inspector.has_table("video_assets")
        and "sub_id" in existing
        and "video_asset_id" in (existing | {"video_asset_id"})
    ):
        asset_columns = _columns(inspector, "video_assets")
        if "sub_id" in asset_columns:
            statements.append(
                "UPDATE product_performance SET video_asset_id = ("
                "SELECT MAX(a.id) FROM video_assets a "
                "WHERE a.sub_id = product_performance.sub_id AND a.sub_id <> ''"
                ") "
                "WHERE video_asset_id IS NULL "
                "AND sub_id IS NOT NULL AND sub_id <> '' "
                "AND ("
                "SELECT COUNT(*) FROM video_assets a "
                "WHERE a.sub_id = product_performance.sub_id AND a.sub_id <> ''"
                ") = 1"
            )
    return statements


def _lead_signal_statements(inspector) -> list[str]:  # noqa: ANN001
    # P1c: khớp Alembic 0021 cho DB cũ boot không qua alembic (heat + interested_product).
    if not inspector.has_table("lead_signals"):
        return []
    existing = _columns(inspector, "lead_signals")
    statements: list[str] = []
    if "heat" not in existing:
        statements.append("ALTER TABLE lead_signals ADD COLUMN heat FLOAT DEFAULT 0.0")
    if "interested_product" not in existing:
        statements.append(
            "ALTER TABLE lead_signals ADD COLUMN interested_product VARCHAR(255) DEFAULT ''"
        )
    return statements


def _v5_legacy_link_statements(inspector) -> list[str]:  # noqa: ANN001
    statements: list[str] = []
    for table_name in V5_LEGACY_LINK_TABLES:
        if not inspector.has_table(table_name):
            continue

        existing = _columns(inspector, table_name)
        indexes = _indexes(inspector, table_name)
        if "campaign_id" not in existing:
            statements.append(f"ALTER TABLE {table_name} ADD COLUMN campaign_id INTEGER")
        if "variant_id" not in existing:
            statements.append(f"ALTER TABLE {table_name} ADD COLUMN variant_id INTEGER")
        if f"ix_{table_name}_campaign_id" not in indexes:
            statements.append(
                f"CREATE INDEX ix_{table_name}_campaign_id ON {table_name} (campaign_id)"
            )
        if f"ix_{table_name}_variant_id" not in indexes:
            statements.append(
                f"CREATE INDEX ix_{table_name}_variant_id ON {table_name} (variant_id)"
            )
    return statements


def _browser_qa_statements(inspector) -> list[str]:  # noqa: ANN001
    statements: list[str] = []
    if inspector.has_table("proxies"):
        proxy_indexes = _indexes(inspector, "proxies")
        if "ix_proxies_status" not in proxy_indexes:
            statements.append("CREATE INDEX ix_proxies_status ON proxies (status)")
        if "ix_proxies_proxy_type" not in proxy_indexes:
            statements.append("CREATE INDEX ix_proxies_proxy_type ON proxies (proxy_type)")
    if inspector.has_table("browser_test_profiles"):
        profile_indexes = _indexes(inspector, "browser_test_profiles")
        if "ix_browser_test_profiles_platform" not in profile_indexes:
            statements.append(
                "CREATE INDEX ix_browser_test_profiles_platform ON browser_test_profiles (platform)"
            )
        if "ix_browser_test_profiles_status" not in profile_indexes:
            statements.append(
                "CREATE INDEX ix_browser_test_profiles_status ON browser_test_profiles (status)"
            )
    if inspector.has_table("browser_qa_runs"):
        run_indexes = _indexes(inspector, "browser_qa_runs")
        if "ix_browser_qa_runs_profile_id" not in run_indexes:
            statements.append(
                "CREATE INDEX ix_browser_qa_runs_profile_id ON browser_qa_runs (profile_id)"
            )
        if "ix_browser_qa_runs_status" not in run_indexes:
            statements.append("CREATE INDEX ix_browser_qa_runs_status ON browser_qa_runs (status)")
        if "ix_browser_qa_runs_created_at" not in run_indexes:
            statements.append(
                "CREATE INDEX ix_browser_qa_runs_created_at ON browser_qa_runs (created_at)"
            )
    return statements
