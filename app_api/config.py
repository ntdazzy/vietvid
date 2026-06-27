"""Config app_api — đọc từ env (M1). M2+ sẽ hợp nhất vào config/registry.py.

CREDIT_PRICE_VND / USD_TO_VND là ĐIỂM QUY ĐỔI USD→credit DUY NHẤT (mục 6.3 plan):
credits(usd) = ceil(usd * USD_TO_VND / CREDIT_PRICE_VND). Snapshot vào mỗi ledger row.
"""

from __future__ import annotations

import os


def _int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, "").strip() or default)
    except ValueError:
        return default


# DB: ưu tiên VIETVID_DATABASE_URL, fallback DATABASE_URL, cuối cùng local vietvid.
DATABASE_URL: str = (
    os.environ.get("VIETVID_DATABASE_URL")
    or os.environ.get("DATABASE_URL")
    or "postgresql+psycopg2://vietvid:vietvid@localhost:5432/vietvid"
)

# Role app connect (non-superuser để FORCE RLS có hiệu lực — mục 6.1 plan). Để rỗng = dùng URL.
DB_APP_ROLE: str = os.environ.get("VIETVID_DB_APP_ROLE", "").strip()

# Quy đổi tiền (mục 6.3, 10.8 plan)
CREDIT_PRICE_VND: int = _int("CREDIT_PRICE_VND", 150)   # 1 credit = 150đ
USD_TO_VND: int = _int("USD_TO_VND", 25400)             # tỉ giá USD→VND

# GUC key cho RLS (mục 6.1)
RLS_GUC: str = "vietvid.current_org"
