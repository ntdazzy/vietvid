"""Ví: thêm xu GÓI hết hạn (plan_credits + plan_expires_at) — tách khỏi balance_credits (mua/thưởng,
không hết hạn). Invariant mới: SUM(ledger.delta) == balance_credits + plan_credits.

Revision ID: 20260629_0013
Revises: 20260629_0012
Create Date: 2026-06-29
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260629_0013"
down_revision = "20260629_0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("wallets", sa.Column("plan_credits", sa.BigInteger(), server_default="0", nullable=False))
    op.add_column("wallets", sa.Column("plan_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.create_check_constraint("ck_wallet_plan_nonneg", "wallets", "plan_credits >= 0")


def downgrade() -> None:
    op.drop_constraint("ck_wallet_plan_nonneg", "wallets", type_="check")
    op.drop_column("wallets", "plan_expires_at")
    op.drop_column("wallets", "plan_credits")
