"""Quy đổi USD→credit — ĐIỂM DUY NHẤT (mục 6.3 plan). Snapshot rate vào mỗi ledger row."""

from __future__ import annotations

import math

from app_api.config import CREDIT_PRICE_VND, USD_TO_VND, VIDEO_MARGIN_MULTIPLIER


def usd_to_credits(usd: float) -> int:
    """GIÁ VỐN thật → credits: ceil(usd * USD_TO_VND / CREDIT_PRICE_VND). Làm tròn LÊN.
    Dùng cho ledger usd_cost + budget guard (KHÔNG markup — phản ánh chi phí provider thật)."""
    if usd <= 0:
        return 0
    return math.ceil(float(usd) * USD_TO_VND / CREDIT_PRICE_VND)


def usd_to_credits_billed(usd: float) -> int:
    """GIÁ BÁN cho khách = credits của (giá vốn × VIDEO_MARGIN_MULTIPLIER). Tách khỏi usd_to_credits
    để margin minh bạch + chỉnh bằng 1 hằng số. Dùng khi HOLD và SETTLE render job."""
    return usd_to_credits(float(usd) * VIDEO_MARGIN_MULTIPLIER)
