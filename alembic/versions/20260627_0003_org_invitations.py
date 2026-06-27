"""Sóng 1C — bảng org_invitations (mời thành viên vào org).

Global table (không RLS, giống memberships). Tạo từ model.

Revision ID: 20260627_0003
Revises: 20260627_0002
Create Date: 2026-06-27
"""
from __future__ import annotations

from alembic import op

from app_api.models import OrgInvitation

revision = "20260627_0003"
down_revision = "20260627_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    OrgInvitation.__table__.create(op.get_bind(), checkfirst=True)


def downgrade() -> None:
    OrgInvitation.__table__.drop(op.get_bind(), checkfirst=True)
