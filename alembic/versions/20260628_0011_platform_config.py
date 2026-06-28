"""Cấu hình nền tảng runtime (admin sửa không cần deploy) — vv_platform_config global 1 hàng.

Revision ID: 20260628_0011
Revises: 20260628_0010
Create Date: 2026-06-28
"""
from __future__ import annotations

from alembic import op

from app_api.models import VvPlatformConfig

revision = "20260628_0011"
down_revision = "20260628_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    VvPlatformConfig.__table__.create(op.get_bind(), checkfirst=True)
    # seed hàng id=1 rỗng (get_config merge default lên trên).
    op.execute("INSERT INTO vv_platform_config (id, data) VALUES (1, '{}'::jsonb) "
               "ON CONFLICT (id) DO NOTHING")


def downgrade() -> None:
    VvPlatformConfig.__table__.drop(op.get_bind(), checkfirst=True)
