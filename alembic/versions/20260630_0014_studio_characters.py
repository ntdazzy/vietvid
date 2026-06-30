"""Studio Tier 3 — vv_characters (nhân vật AI tái dùng, clone openart /suite/character).

RLS NỚI (system + own) như personas/templates. 3 lối tạo (source): image/describe/build.

Theo D6 (org_id nullable + policy nới cho bảng có row hệ thống: USING org_id IS NULL OR =GUC;
WITH CHECK =GUC; seed globals TRƯỚC khi bật RLS) và D7 (dùng lại RLS_USING_PREDICATE nguyên văn).

Revision ID: 20260630_0014
Revises: 20260629_0013
Create Date: 2026-06-30
"""
from __future__ import annotations

from alembic import op

from app_api.models import RLS_USING_PREDICATE, VvCharacter

revision = "20260630_0014"
down_revision = "20260629_0013"
branch_labels = None
depends_on = None

_RELAXED = f"(org_id IS NULL OR {RLS_USING_PREDICATE})"
_STRICT = f"({RLS_USING_PREDICATE})"


def upgrade() -> None:
    bind = op.get_bind()
    VvCharacter.__table__.create(bind, checkfirst=True)

    # Seed nhân vật hệ thống (org_id NULL) TRƯỚC khi bật RLS (WITH CHECK chặn insert NULL-org sau đó).
    # Dùng lại ảnh /kol/lib có sẵn để lưới mẫu không rỗng (giống "templates" của openart).
    op.bulk_insert(VvCharacter.__table__, [
        {"name": "An", "description": "Người dẫn nữ trẻ trung, gần gũi — hợp review & đời thường",
         "source": "image", "gender": "female", "ethnicity": "Việt Nam", "age_range": "18-25",
         "vibe": "Năng động, thân thiện", "voice_gender": "female",
         "avatar_url": "/kol/lib/tt-nu1.jpg", "sort_order": 0},
        {"name": "Phong", "description": "Nam lịch lãm, phong cách đời thường — hợp thời trang nam",
         "source": "image", "gender": "male", "ethnicity": "Việt Nam", "age_range": "26-35",
         "vibe": "Lịch lãm, tự tin", "voice_gender": "male",
         "avatar_url": "/kol/lib/tt-nam1.jpg", "sort_order": 1},
        {"name": "Châu", "description": "Nữ thanh lịch, hợp mỹ phẩm & skincare",
         "source": "image", "gender": "female", "ethnicity": "Việt Nam", "age_range": "26-35",
         "vibe": "Thanh lịch, dịu dàng", "voice_gender": "female",
         "avatar_url": "/kol/lib/my-nu1.jpg", "sort_order": 2},
        {"name": "Khải", "description": "Nam năng động, khỏe khoắn — hợp gym & thể thao",
         "source": "image", "gender": "male", "ethnicity": "Việt Nam", "age_range": "26-35",
         "vibe": "Năng động, mạnh mẽ", "voice_gender": "male",
         "avatar_url": "/kol/lib/gym-nam1.jpg", "sort_order": 3},
    ])

    # RLS NỚI (system + own) cho vv_characters.
    op.execute("ALTER TABLE vv_characters ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE vv_characters FORCE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY org_isolation ON vv_characters USING ({_RELAXED}) WITH CHECK ({_STRICT})"
    )


def downgrade() -> None:
    bind = op.get_bind()
    VvCharacter.__table__.drop(bind, checkfirst=True)
