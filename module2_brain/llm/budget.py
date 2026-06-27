"""Sổ ngân sách LLM theo ngày (chống cháy túi) — khuôn theo module3_render/motion._reserve_budget.

Mỗi campaign chạy bộ não V5 "đặt chỗ" một khoản chi phí ước tính + 1 lượt campaign trong ngày.
Vượt ngân sách USD/ngày HOẶC vượt số campaign/ngày → raise LLMBudgetError để orchestrator hoãn,
KHÔNG gọi LLM. Ledger ghi atomic (tmp → os.replace) để an toàn đa tiến trình.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from config.settings import settings


class LLMBudgetError(RuntimeError):
    """Vượt ngân sách LLM ngày (chi phí hoặc số campaign) → hoãn sang ngày sau."""


def _read_llm_ledger() -> dict:
    path = settings.llm_budget_ledger_path
    if not path or not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as fh:
            payload = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_llm_ledger(payload: dict) -> None:
    path = settings.llm_budget_ledger_path
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2, sort_keys=True)
    os.replace(tmp, path)


def llm_budget_ready() -> bool:
    """Cấu hình ngân sách hợp lệ để chạy bộ não V5 (có trần chi phí + trần số campaign)."""
    return (
        float(settings.llm_daily_budget_usd or 0.0) > 0
        and int(settings.llm_max_campaigns_per_day or 0) > 0
    )


def llm_budget_status() -> dict:
    """Trạng thái còn lại trong ngày (chỉ đọc, KHÔNG đặt chỗ) — cho dashboard/log."""
    today = datetime.now(timezone.utc).date().isoformat()
    day = _read_llm_ledger().get(today, {}) or {}
    return {
        "date": today,
        "spent_usd": round(float(day.get("spent_usd", 0.0) or 0.0), 4),
        "campaigns": int(day.get("campaigns", 0) or 0),
        "budget_usd": float(settings.llm_daily_budget_usd or 0.0),
        "max_campaigns": int(settings.llm_max_campaigns_per_day or 0),
    }


def reserve_llm_campaign_budget(label: str = "campaign") -> float:
    """Đặt chỗ 1 campaign chạy bộ não V5. Vượt ngân sách → LLMBudgetError (orchestrator hoãn)."""
    budget = float(settings.llm_daily_budget_usd or 0.0)
    cost = float(settings.llm_estimated_cost_per_campaign_usd or 0.0)
    max_campaigns = int(settings.llm_max_campaigns_per_day or 0)
    if budget <= 0 or max_campaigns <= 0:
        raise LLMBudgetError(
            "Bộ não V5 cần LLM_DAILY_BUDGET_USD > 0 và LLM_MAX_CAMPAIGNS_PER_DAY > 0 "
            "để tránh phát sinh chi phí ngoài ý muốn."
        )
    today = datetime.now(timezone.utc).date().isoformat()
    ledger = _read_llm_ledger()
    day = ledger.setdefault(today, {})
    spent = float(day.get("spent_usd", 0.0) or 0.0)
    campaigns = int(day.get("campaigns", 0) or 0)
    if campaigns >= max_campaigns:
        raise LLMBudgetError(f"Vượt số campaign/ngày: {campaigns}/{max_campaigns} (label={label}).")
    if spent + cost > budget:
        raise LLMBudgetError(
            f"Vượt ngân sách LLM ngày: spent={spent:.4f}, cost={cost:.4f}, budget={budget:.2f}."
        )
    day["spent_usd"] = round(spent + cost, 4)
    day["campaigns"] = campaigns + 1
    _write_llm_ledger(ledger)
    return cost
