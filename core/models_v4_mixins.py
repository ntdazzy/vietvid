"""Reusable pieces for V4 tables that need V5 links."""

from __future__ import annotations

from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, declarative_mixin, mapped_column


@declarative_mixin
class V5LegacyLinkMixin:
    """Soft link old V4 rows to the V5 campaign/variant reporting layer."""

    campaign_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    variant_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
