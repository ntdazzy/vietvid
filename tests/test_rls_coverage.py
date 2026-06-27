"""Bất biến RLS coverage (SYSTEM_DESIGN D8): MỌI bảng có cột org_id PHẢI có
ENABLE + FORCE row-level-security + ít nhất 1 policy. Thiếu = rò chéo-tenant → CI đỏ.

Đây là lưới chặn lỗi nguy hiểm nhất khi thêm bảng tenant mới (quên policy = lộ data org khác).
"""

from __future__ import annotations

from sqlalchemy import text

from app_api.db import get_sessionmaker
from app_api.models import GLOBAL_ORG_TABLES


def test_every_org_scoped_table_has_forced_rls():
    s = get_sessionmaker()()
    try:
        tables = [
            r[0]
            for r in s.execute(text(
                "SELECT DISTINCT c.table_name "
                "FROM information_schema.columns c "
                "JOIN information_schema.tables t "
                "  ON t.table_name=c.table_name AND t.table_schema=c.table_schema "
                "WHERE c.column_name='org_id' AND c.table_schema='public' "
                "  AND t.table_type='BASE TABLE'"
            )).all()
            if r[0] not in GLOBAL_ORG_TABLES  # loại bảng global-org có chủ đích (D4/D5)
        ]
        assert tables, "không tìm thấy bảng nào có org_id (sai kết nối DB?)"

        missing = []
        for tbl in tables:
            row = s.execute(text(
                "SELECT relrowsecurity, relforcerowsecurity FROM pg_class WHERE relname=:t"
            ), {"t": tbl}).one()
            npol = s.execute(text(
                "SELECT count(*) FROM pg_policy WHERE polrelid = quote_ident(:t)::regclass"
            ), {"t": tbl}).scalar()
            if not (row[0] and row[1] and npol >= 1):
                missing.append(f"{tbl}(enable={row[0]},force={row[1]},policies={npol})")

        assert not missing, "Bảng tenant thiếu RLS FORCE+policy: " + ", ".join(missing)
    finally:
        s.close()
