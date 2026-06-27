"""B2B API — vv_api_keys (global) + vv_webhooks (tenant RLS).

Revision ID: 20260628_0010
Revises: 20260627_0009
Create Date: 2026-06-28
"""
from __future__ import annotations

from alembic import op

from app_api.models import RLS_USING_PREDICATE, VvApiKey, VvWebhook

revision = "20260628_0010"
down_revision = "20260627_0009"
branch_labels = None
depends_on = None

_P = f"({RLS_USING_PREDICATE})"


def upgrade() -> None:
    # api_keys: GLOBAL (tra theo hash trước khi biết org) → KHÔNG RLS.
    VvApiKey.__table__.create(op.get_bind(), checkfirst=True)
    # webhooks: tenant, RLS org_isolation chuẩn.
    VvWebhook.__table__.create(op.get_bind(), checkfirst=True)
    op.execute("ALTER TABLE vv_webhooks ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE vv_webhooks FORCE ROW LEVEL SECURITY")
    op.execute(f"CREATE POLICY org_isolation ON vv_webhooks USING {_P} WITH CHECK {_P}")


def downgrade() -> None:
    VvWebhook.__table__.drop(op.get_bind(), checkfirst=True)
    VvApiKey.__table__.drop(op.get_bind(), checkfirst=True)
