"""Giao diện chung cho mọi client LLM."""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseLLMClient(ABC):
    name: str = "base"

    @abstractmethod
    async def complete(self, system: str, prompt: str) -> str:
        """Gửi system + prompt, trả về text thô (kỳ vọng chứa JSON)."""
        raise NotImplementedError
