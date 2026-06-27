"""Gemini 2.5 Flash Image — sinh ảnh KOL cầm/mặc/dùng sản phẩm hoặc ảnh hero.

Dùng google-genai (SDK mới, đã có sẵn trong dự án qua module2_brain). Ảnh tham chiếu
(ảnh sản phẩm thật, ảnh KOL) truyền kèm prompt để giữ đúng logo/màu/shape.
"""

from __future__ import annotations

import mimetypes
import os

from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import settings
from core.logger import logger
from core.config_checks import looks_real_secret
from video_engine.providers.base import ProviderNotConfiguredError, VideoEngineError


class GeminiImageProvider:
    name = "gemini"

    def __init__(self) -> None:
        if not looks_real_secret(settings.gemini_api_key or ""):
            raise ProviderNotConfiguredError(
                "Thiếu GEMINI_API_KEY thật cho image stage → WAITING_CONFIG."
            )
        from google import genai
        from google.genai import types

        # timeout 60s (ms): chống TREO VÔ HẠN khi gọi Gemini gen ảnh — trước đây không có timeout
        # nên KOL Studio bấm "Tạo KOL" quay spinner mãi (request không bao giờ trả về).
        self._client = genai.Client(
            api_key=settings.gemini_api_key,
            http_options=types.HttpOptions(timeout=60_000),
        )
        self._model = settings.video_gemini_image_model

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=2, max=8), reraise=True)
    def generate(
        self,
        *,
        prompt: str,
        out_path: str,
        input_image_paths: list[str] | None = None,
        aspect_ratio: str | None = None,
    ) -> str:
        from google.genai import types

        contents: list = []
        for path in input_image_paths or []:
            if not path or not os.path.exists(path):
                continue
            mime = mimetypes.guess_type(path)[0] or "image/png"
            with open(path, "rb") as f:
                contents.append(types.Part.from_bytes(data=f.read(), mime_type=mime))
        contents.append(prompt)
        # aspect_ratio ADDITIVE: chỉ set image_config khi caller yêu cầu (long_narrative 16:9).
        # Caller product KHÔNG truyền → config=None → hành vi cũ giữ nguyên byte-identical.
        gen_config = None
        if aspect_ratio:
            gen_config = types.GenerateContentConfig(
                image_config=types.ImageConfig(aspect_ratio=aspect_ratio)
            )
        try:
            resp = self._client.models.generate_content(
                model=self._model, contents=contents, config=gen_config
            )
        except Exception as exc:  # noqa: BLE001
            raise VideoEngineError(f"Gemini image lỗi: {str(exc)[:300]}") from exc
        image_bytes = _first_image_bytes(resp)
        if not image_bytes:
            text = (getattr(resp, "text", "") or "")[:200]
            raise VideoEngineError(f"Gemini không trả ảnh (text: {text!r}).")
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        with open(out_path, "wb") as f:
            f.write(image_bytes)
        logger.info(f"[image-stage] gemini đã sinh ảnh → {out_path}")
        return out_path


def _first_image_bytes(resp) -> bytes | None:
    for candidate in getattr(resp, "candidates", None) or []:
        content = getattr(candidate, "content", None)
        for part in getattr(content, "parts", None) or []:
            inline = getattr(part, "inline_data", None)
            data = getattr(inline, "data", None) if inline else None
            if data:
                return bytes(data)
    return None
