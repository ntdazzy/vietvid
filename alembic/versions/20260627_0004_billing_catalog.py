"""Sóng 4 — catalog billing: plans + credit_packs (GLOBAL) + back FK payments.credit_pack_id.

Theo SYSTEM_DESIGN D1 (migration tường minh, không autogen), D2 (FK NOT VALID→VALIDATE,
ON DELETE SET NULL — không xoá lịch sử payment khi pack bị xoá), D3 (orgs.plan_code = soft ref
tới plans.code; seed 'free' để khớp dữ liệu hiện có).

Revision ID: 20260627_0004
Revises: 20260627_0003
Create Date: 2026-06-27
"""
from __future__ import annotations

from alembic import op

from app_api.models import CreditPack, Plan

revision = "20260627_0004"
down_revision = "20260627_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Plan.__table__.create(bind, checkfirst=True)
    CreditPack.__table__.create(bind, checkfirst=True)

    # Seed plans (giá VND mặc định — chỉnh được sau). 'free' phải tồn tại vì orgs.plan_code='free'.
    op.execute(
        "INSERT INTO plans (code,name,name_vi,monthly_price_vnd,yearly_price_vnd,"
        "monthly_credit_grant,max_concurrent_jobs,max_resolution,max_seconds,watermark_free,sort_order) VALUES "
        "('free','Free','Miễn phí',0,0,300,1,'720p',30,false,0),"
        "('pro','Pro','Chuyên nghiệp',199000,1990000,3000,3,'1080p',60,true,1),"
        "('business','Business','Doanh nghiệp',599000,5990000,10000,6,'1080p',120,true,2) "
        "ON CONFLICT (code) DO NOTHING"
    )

    # Seed credit packs (khớp dict billing.PACKS cũ → payment.credit_pack_id resolve được).
    op.execute(
        "INSERT INTO credit_packs (code,name,amount_vnd,credits,sort_order) VALUES "
        "('starter','Khởi đầu',100000,700,0),"
        "('popular','Phổ biến',300000,2000,1),"
        "('pro','Chuyên nghiệp',900000,7000,2) "
        "ON CONFLICT (code) DO NOTHING"
    )

    # Back cột đặt-chỗ payments.credit_pack_id bằng FK thật (online, không khoá quét bảng).
    op.execute(
        "ALTER TABLE payments ADD CONSTRAINT fk_payments_credit_pack "
        "FOREIGN KEY (credit_pack_id) REFERENCES credit_packs(id) ON DELETE SET NULL NOT VALID"
    )
    op.execute("ALTER TABLE payments VALIDATE CONSTRAINT fk_payments_credit_pack")


def downgrade() -> None:
    op.execute("ALTER TABLE payments DROP CONSTRAINT IF EXISTS fk_payments_credit_pack")
    CreditPack.__table__.drop(op.get_bind(), checkfirst=True)
    Plan.__table__.drop(op.get_bind(), checkfirst=True)
