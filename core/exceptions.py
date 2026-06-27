"""Exception riêng của hệ thống — giúp bắt lỗi theo từng tầng module."""

from __future__ import annotations


class AffiliateBotError(Exception):
    """Lỗi gốc của toàn hệ thống."""


class DataSourceError(AffiliateBotError):
    """Lỗi khi lấy dữ liệu từ một nguồn (Module 1)."""


class ScoringError(AffiliateBotError):
    """Lỗi khi chuẩn hóa / chấm điểm P (Module 1)."""


class LLMError(AffiliateBotError):
    """Lỗi khi gọi LLM (Module 2)."""


class WorkflowError(AffiliateBotError):
    """Lỗi trong vòng lặp 2 agent (Module 2)."""


class RenderError(AffiliateBotError):
    """Lỗi khi dựng audio/video (Module 3)."""
