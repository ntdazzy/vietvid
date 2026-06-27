"""Sóng 1B — bảng auth_tokens (password reset / email verify / refresh).

Global table (không RLS, giống users/orgs). Tạo từ model để khỏi lặp định nghĩa.

Revision ID: 20260627_0002
Revises: 20260627_0001
Create Date: 2026-06-27
"""
from __future__ import annotations

from alembic import op

from app_api.models import AuthToken

revision = "20260627_0002"
down_revision = "20260627_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    AuthToken.__table__.create(op.get_bind(), checkfirst=True)


def downgrade() -> None:
    AuthToken.__table__.drop(op.get_bind(), checkfirst=True)
