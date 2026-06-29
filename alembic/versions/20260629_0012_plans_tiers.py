"""Cập nhật catalog `plans` thành 4 gói tháng rẻ hơn Autovis ~6-12% (model A: tự nạp lại).

Giá user chốt: 179k/469k/969k/1.319k; số xu khớp tier Autovis (1.500/3.700/7.500/11.200).
free=0 xu (đồng bộ FREE_GRANT_CREDITS=0 chống farm). Tắt pro/business seed cũ (199k/599k).
CHỈ là DATA — hành vi mua gói/cấp credit/enforce giới hạn wire ở bước sau.

Revision ID: 20260629_0012
Revises: 20260628_0011
Create Date: 2026-06-29
"""
from __future__ import annotations

from alembic import op

revision = "20260629_0012"
down_revision = "20260628_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # free: 0 xu (khớp anti-farm). Giữ làm plan_code mặc định của org.
    op.execute("UPDATE plans SET monthly_credit_grant=0, max_resolution='480p', max_seconds=8, "
               "watermark_free=false, name_vi='Miễn phí' WHERE code='free'")
    # Tắt seed cũ (giá không khớp).
    op.execute("UPDATE plans SET is_active=false WHERE code IN ('pro','business')")
    # 4 gói tháng mới — rẻ hơn Autovis (199k/499k/999k/1499k).
    op.execute(
        "INSERT INTO plans (code,name,name_vi,monthly_price_vnd,yearly_price_vnd,"
        "monthly_credit_grant,max_concurrent_jobs,max_resolution,max_seconds,watermark_free,sort_order) VALUES "
        "('khoi_dau','Starter','Khởi đầu',179000,1790000,1500,2,'720p',30,true,1),"
        "('pho_thong','Pro','Phổ thông',469000,4690000,3700,3,'1080p',60,true,2),"
        "('premier','Premier','Cao cấp',969000,9690000,7500,4,'1080p',120,true,3),"
        "('super','Super','Doanh nghiệp',1319000,13190000,11200,6,'1080p',180,true,4) "
        "ON CONFLICT (code) DO UPDATE SET "
        "name=EXCLUDED.name, name_vi=EXCLUDED.name_vi, monthly_price_vnd=EXCLUDED.monthly_price_vnd, "
        "yearly_price_vnd=EXCLUDED.yearly_price_vnd, monthly_credit_grant=EXCLUDED.monthly_credit_grant, "
        "max_concurrent_jobs=EXCLUDED.max_concurrent_jobs, max_resolution=EXCLUDED.max_resolution, "
        "max_seconds=EXCLUDED.max_seconds, watermark_free=EXCLUDED.watermark_free, "
        "sort_order=EXCLUDED.sort_order, is_active=true"
    )


def downgrade() -> None:
    op.execute("UPDATE plans SET is_active=false WHERE code IN ('khoi_dau','pho_thong','premier','super')")
    op.execute("UPDATE plans SET is_active=true WHERE code IN ('pro','business')")
    op.execute("UPDATE plans SET monthly_credit_grant=300, max_resolution='720p', max_seconds=30 WHERE code='free'")
