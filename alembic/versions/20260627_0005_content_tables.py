"""Sóng 4 — nội dung tenant: vv_templates / vv_kol_personas (RLS NỚI: system row org_id NULL
dùng chung) + vv_brand_kits (RLS chuẩn) + back 3 FK đặt-chỗ trên jobs.

Theo SYSTEM_DESIGN D6 (org_id nullable + policy nới: USING org_id IS NULL OR =GUC; WITH CHECK
=GUC; seed globals TRƯỚC khi bật RLS) và D2 (FK NOT VALID→VALIDATE, ON DELETE SET NULL).

Revision ID: 20260627_0005
Revises: 20260627_0004
Create Date: 2026-06-27
"""
from __future__ import annotations

from alembic import op

from app_api.models import (
    RLS_USING_PREDICATE,
    VvBrandKit,
    VvKolPersona,
    VvTemplate,
)

revision = "20260627_0005"
down_revision = "20260627_0004"
branch_labels = None
depends_on = None

_RELAXED = f"(org_id IS NULL OR {RLS_USING_PREDICATE})"
_STRICT = f"({RLS_USING_PREDICATE})"


def upgrade() -> None:
    bind = op.get_bind()
    VvTemplate.__table__.create(bind, checkfirst=True)
    VvKolPersona.__table__.create(bind, checkfirst=True)
    VvBrandKit.__table__.create(bind, checkfirst=True)

    # Seed system rows (org_id NULL) TRƯỚC khi bật RLS (WITH CHECK sẽ chặn insert NULL-org sau đó).
    op.bulk_insert(VvTemplate.__table__, [
        {"name": "Review sản phẩm", "description": "KOL review sản phẩm theo kịch bản",
         "category": "review", "sort_order": 0,
         "preset": {"feature": "review", "videoType": "kol_full",
                    "brief": "Làm video review sản phẩm theo kịch bản, KOL nói tự nhiên, nêu ưu điểm chính."}},
        {"name": "Lookbook thời trang", "description": "KOL trình diễn SP bối cảnh editorial",
         "category": "lookbook", "sort_order": 1,
         "preset": {"feature": "lookbook", "videoType": "kol_full",
                    "brief": "Lookbook thời trang: KOL trình diễn/giới thiệu sản phẩm trong bối cảnh editorial sang."}},
        {"name": "Quảng cáo sản phẩm", "description": "Biến 1 ảnh SP thành video quảng cáo",
         "category": "product_ad", "sort_order": 2,
         "preset": {"feature": "product_ad", "videoType": "product_ad", "brief": ""}},
        {"name": "Văn bản → Video", "description": "AI tạo khung từ mô tả",
         "category": "text_to_video", "sort_order": 3,
         "preset": {"feature": "text_to_video", "videoType": "product_ad", "brief": "", "frameMode": "ai"}},
    ])
    op.bulk_insert(VvKolPersona.__table__, [
        {"name": "Linh", "description": "Nữ KOL trẻ trung, thân thiện, giọng miền Bắc nhẹ nhàng",
         "gender": "female", "voice_gender": "female", "source": "ai",
         "moderation_status": "APPROVED", "sort_order": 0},
        {"name": "Minh", "description": "Nam KOL năng động, phong cách đời thường, giọng trầm ấm",
         "gender": "male", "voice_gender": "male", "source": "ai",
         "moderation_status": "APPROVED", "sort_order": 1},
        {"name": "Hà", "description": "Nữ KOL thanh lịch, hợp thời trang & mỹ phẩm",
         "gender": "female", "voice_gender": "female", "source": "ai",
         "moderation_status": "APPROVED", "sort_order": 2},
    ])

    # RLS NỚI (system + own) cho templates/personas; RLS chuẩn (own) cho brand_kits.
    for t in ("vv_templates", "vv_kol_personas"):
        op.execute(f"ALTER TABLE {t} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {t} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY org_isolation ON {t} USING ({_RELAXED}) WITH CHECK ({_STRICT})"
        )
    op.execute("ALTER TABLE vv_brand_kits ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE vv_brand_kits FORCE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY org_isolation ON vv_brand_kits USING ({_STRICT}) WITH CHECK ({_STRICT})"
    )

    # Back 3 cột đặt-chỗ trên jobs bằng FK thật (SET NULL — xoá template/persona/kit không xoá job).
    for col, ref in (
        ("template_id", "vv_templates"),
        ("kol_persona_id", "vv_kol_personas"),
        ("brand_kit_id", "vv_brand_kits"),
    ):
        cname = f"fk_jobs_{col}"
        op.execute(
            f"ALTER TABLE jobs ADD CONSTRAINT {cname} FOREIGN KEY ({col}) "
            f"REFERENCES {ref}(id) ON DELETE SET NULL NOT VALID"
        )
        op.execute(f"ALTER TABLE jobs VALIDATE CONSTRAINT {cname}")


def downgrade() -> None:
    for col in ("template_id", "kol_persona_id", "brand_kit_id"):
        op.execute(f"ALTER TABLE jobs DROP CONSTRAINT IF EXISTS fk_jobs_{col}")
    bind = op.get_bind()
    VvBrandKit.__table__.drop(bind, checkfirst=True)
    VvKolPersona.__table__.drop(bind, checkfirst=True)
    VvTemplate.__table__.drop(bind, checkfirst=True)
