"""Critic LLM — Google Gen AI SDK mới (google-genai). SDK import lazy + retry.

Lưu ý: gói cũ `google-generativeai` đã bị Google ngừng hỗ trợ → dùng `google-genai`:
    from google import genai
    client = genai.Client(api_key=...)
    await client.aio.models.generate_content(model=..., contents=..., config=...)
"""

from __future__ import annotations

from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import settings
from core.exceptions import LLMError
from module2_brain.llm.base import BaseLLMClient
from module2_brain.llm.readiness import llm_config_issues


class GeminiClient(BaseLLMClient):
    name = "gemini"

    def __init__(self, model: str | None = None) -> None:
        issues = llm_config_issues("gemini")
        if issues:
            raise LLMError("Gemini config chưa sẵn sàng: " + "; ".join(issues))
        from google import genai  # import lazy: không bắt buộc cài khi chạy chế độ giả lập

        self._client = genai.Client(api_key=settings.gemini_api_key)
        # model riêng cho từng vai (copywriter vs critic); mặc định giữ gemini_model cũ.
        self._model = model or settings.gemini_model

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10), reraise=True)
    async def complete(self, system: str, prompt: str) -> str:
        from google.genai import types

        try:
            resp = await self._client.aio.models.generate_content(
                model=self._model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system,
                    response_mime_type="application/json",
                ),
            )
            return resp.text or ""
        except Exception as exc:  # noqa: BLE001
            raise LLMError(f"Gemini lỗi: {exc}") from exc
