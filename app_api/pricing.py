"""Quy đổi USD→credit — ĐIỂM DUY NHẤT (mục 6.3 plan). Snapshot rate vào mỗi ledger row."""

from __future__ import annotations

import math

from app_api.config import CREDIT_PRICE_VND, USD_TO_VND


def usd_to_credits(usd: float) -> int:
    """credits = ceil(usd * USD_TO_VND / CREDIT_PRICE_VND). Làm tròn LÊN (nền tảng không lỗ lẻ)."""
    if usd <= 0:
        return 0
    return math.ceil(float(usd) * USD_TO_VND / CREDIT_PRICE_VND)
