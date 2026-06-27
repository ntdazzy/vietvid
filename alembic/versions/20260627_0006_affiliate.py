"""Sóng 4 — affiliate loop (vượt autovis): vv_affiliate_links + vv_link_clicks.

GLOBAL (không RLS): redirect /r/{code} & ghi click chạy PRE-AUTH (không GUC). Endpoint quản lý
lọc org_id tường minh (như org_invitations). Xem GLOBAL_ORG_TABLES.

Revision ID: 20260627_0006
Revises: 20260627_0005
Create Date: 2026-06-27
"""
from __future__ import annotations

from alembic import op

from app_api.models import VvAffiliateLink, VvLinkClick

revision = "20260627_0006"
down_revision = "20260627_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    VvAffiliateLink.__table__.create(bind, checkfirst=True)
    VvLinkClick.__table__.create(bind, checkfirst=True)


def downgrade() -> None:
    bind = op.get_bind()
    VvLinkClick.__table__.drop(bind, checkfirst=True)
    VvAffiliateLink.__table__.drop(bind, checkfirst=True)
