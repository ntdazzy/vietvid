"""Sóng 4 — notifications (tenant, RLS chuẩn org_isolation).

Revision ID: 20260627_0007
Revises: 20260627_0006
Create Date: 2026-06-27
"""
from __future__ import annotations

from alembic import op

from app_api.models import RLS_USING_PREDICATE, Notification

revision = "20260627_0007"
down_revision = "20260627_0006"
branch_labels = None
depends_on = None

_P = f"({RLS_USING_PREDICATE})"


def upgrade() -> None:
    Notification.__table__.create(op.get_bind(), checkfirst=True)
    op.execute("ALTER TABLE notifications ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE notifications FORCE ROW LEVEL SECURITY")
    op.execute(f"CREATE POLICY org_isolation ON notifications USING {_P} WITH CHECK {_P}")


def downgrade() -> None:
    Notification.__table__.drop(op.get_bind(), checkfirst=True)
