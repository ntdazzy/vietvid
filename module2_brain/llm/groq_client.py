"""Copywriter LLM — Groq Cloud (Llama 3 70B, free tier). SDK import lazy + retry."""

from __future__ import annotations

import asyncio
import time
from collections import deque

from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import settings
from core.exceptions import LLMError
from module2_brain.llm.base import BaseLLMClient
from module2_brain.llm.readiness import llm_config_issues

_RATE_LOCK = asyncio.Lock()
_REQUEST_TIMES: deque[float] = deque()


async def _rate_limit() -> None:
    """Giới hạn request/phút cho Groq để tránh 429 khi batch nhiều sản phẩm."""
    limit = max(1, settings.groq_requests_per_minute)
    window = 60.0
    while True:
        async with _RATE_LOCK:
            now = time.monotonic()
            while _REQUEST_TIMES and now - _REQUEST_TIMES[0] >= window:
                _REQUEST_TIMES.popleft()
            if len(_REQUEST_TIMES) < limit:
                _REQUEST_TIMES.append(now)
                return
            wait_s = window - (now - _REQUEST_TIMES[0])
        await asyncio.sleep(max(0.0, wait_s))


class GroqClient(BaseLLMClient):
    name = "groq"

    def __init__(self) -> None:
        issues = llm_config_issues("groq")
        if issues:
            raise LLMError("Groq config chưa sẵn sàng: " + "; ".join(issues))
        from groq import AsyncGroq  # import lazy: không bắt buộc cài khi chạy chế độ giả lập

        self._client = AsyncGroq(api_key=settings.groq_api_key)
        self._model = settings.groq_model

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10), reraise=True)
    async def complete(self, system: str, prompt: str) -> str:
        try:
            await _rate_limit()
            resp = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.8,
                response_format={"type": "json_object"},
            )
            return resp.choices[0].message.content or ""
        except Exception as exc:  # noqa: BLE001 — gói lại để retry & log thống nhất
            raise LLMError(f"Groq lỗi: {exc}") from exc
