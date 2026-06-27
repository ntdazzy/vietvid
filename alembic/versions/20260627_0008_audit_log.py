"""Sóng 4 — audit_log (GLOBAL, append-only). Nhật ký hành động admin/bảo mật.

Tái dùng function ledger_immutable() (tạo ở 0001) cho trigger chặn UPDATE/DELETE.

Revision ID: 20260627_0008
Revises: 20260627_0007
Create Date: 2026-06-27
"""
from __future__ import annotations

from alembic import op

from app_api.models import AuditLog

revision = "20260627_0008"
down_revision = "20260627_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    AuditLog.__table__.create(op.get_bind(), checkfirst=True)
    # append-only: tái dùng ledger_immutable() đã có từ baseline.
    op.execute("DROP TRIGGER IF EXISTS trg_audit_no_update ON audit_log")
    op.execute(
        "CREATE TRIGGER trg_audit_no_update BEFORE UPDATE ON audit_log "
        "FOR EACH ROW EXECUTE FUNCTION ledger_immutable()"
    )
    op.execute("DROP TRIGGER IF EXISTS trg_audit_no_delete ON audit_log")
    op.execute(
        "CREATE TRIGGER trg_audit_no_delete BEFORE DELETE ON audit_log "
        "FOR EACH ROW EXECUTE FUNCTION ledger_immutable()"
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_audit_no_update ON audit_log")
    op.execute("DROP TRIGGER IF EXISTS trg_audit_no_delete ON audit_log")
    AuditLog.__table__.drop(op.get_bind(), checkfirst=True)
