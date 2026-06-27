"""Moat — cột jobs.series_group nhóm biến thể auto-series (vòng lặp hiệu suất).

Revision ID: 20260627_0009
Revises: 20260627_0008
Create Date: 2026-06-27
"""
from __future__ import annotations

from alembic import op

revision = "20260627_0009"
down_revision = "20260627_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS series_group uuid")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_jobs_series_group ON jobs (series_group) "
        "WHERE series_group IS NOT NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_jobs_series_group")
    op.execute("ALTER TABLE jobs DROP COLUMN IF EXISTS series_group")
