"""M1 baseline — tất cả bảng M1 + extensions + RLS + ledger immutable trigger + partial indexes.

Revision ID: 20260627_0001
Revises:
Create Date: 2026-06-27
"""
from __future__ import annotations

from alembic import op

from app_api.models import Base, TENANT_TABLES

revision = "20260627_0001"
down_revision = None
branch_labels = None
depends_on = None

_RLS_USING = "org_id = nullif(current_setting('vietvid.current_org', true), '')::uuid"


def upgrade() -> None:
    bind = op.get_bind()
    # Extensions cần TRƯỚC create_all (gen_random_uuid, CITEXT).
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE EXTENSION IF NOT EXISTS citext")

    # Tạo mọi bảng/constraint/index khai báo trong models.
    Base.metadata.create_all(bind)

    # Partial indexes (alembic autogen không sinh — viết tay).
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_ledger_hold_job "
        "ON ledger_entries (job_id) WHERE entry_type = 'HOLD'"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_jobs_queued "
        "ON jobs (created_at) WHERE status = 'QUEUED'"
    )

    # ledger_entries APPEND-ONLY: trigger chặn UPDATE/DELETE.
    op.execute(
        "CREATE OR REPLACE FUNCTION ledger_immutable() RETURNS trigger AS $$ "
        "BEGIN RAISE EXCEPTION 'ledger_entries is append-only (% blocked on id %)', TG_OP, OLD.id; "
        "END; $$ LANGUAGE plpgsql;"
    )
    op.execute("DROP TRIGGER IF EXISTS trg_ledger_no_update ON ledger_entries")
    op.execute(
        "CREATE TRIGGER trg_ledger_no_update BEFORE UPDATE ON ledger_entries "
        "FOR EACH ROW EXECUTE FUNCTION ledger_immutable()"
    )
    op.execute("DROP TRIGGER IF EXISTS trg_ledger_no_delete ON ledger_entries")
    op.execute(
        "CREATE TRIGGER trg_ledger_no_delete BEFORE DELETE ON ledger_entries "
        "FOR EACH ROW EXECUTE FUNCTION ledger_immutable()"
    )

    # RLS trên bảng tenant-owned (fail-closed qua nullif; FORCE áp cả owner).
    for t in TENANT_TABLES:
        op.execute(f"ALTER TABLE {t} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {t} FORCE ROW LEVEL SECURITY")
        op.execute(f"DROP POLICY IF EXISTS org_isolation ON {t}")
        op.execute(
            f"CREATE POLICY org_isolation ON {t} "
            f"USING ({_RLS_USING}) WITH CHECK ({_RLS_USING})"
        )


def downgrade() -> None:
    bind = op.get_bind()
    for t in TENANT_TABLES:
        op.execute(f"DROP POLICY IF EXISTS org_isolation ON {t}")
        op.execute(f"ALTER TABLE {t} DISABLE ROW LEVEL SECURITY")
    op.execute("DROP TRIGGER IF EXISTS trg_ledger_no_update ON ledger_entries")
    op.execute("DROP TRIGGER IF EXISTS trg_ledger_no_delete ON ledger_entries")
    op.execute("DROP FUNCTION IF EXISTS ledger_immutable()")
    Base.metadata.drop_all(bind)
