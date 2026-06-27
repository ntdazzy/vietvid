"""Image stage — sinh ảnh KOL+sản phẩm / ảnh hero bằng provider cấu hình."""

from __future__ import annotations

from config.settings import settings
from video_engine.providers.base import ImageProvider


def build_image_provider() -> ImageProvider:
    name = (settings.image_provider or "local").strip().lower()
    if name == "mock" or settings.use_fake_clients:
        from video_engine.image_stage.mock import MockImageProvider

        return MockImageProvider()
    if name == "local":
        from video_engine.image_stage.local import LocalImageProvider

        return LocalImageProvider()
    if name == "gemini":
        from video_engine.image_stage.gemini import GeminiImageProvider

        return GeminiImageProvider()
    if name == "hybrid":
        from video_engine.providers.base import ProviderNotConfiguredError

        raise ProviderNotConfiguredError(
            "IMAGE_PROVIDER=hybrid có Gemini fallback nên không dùng trong flow chính. Đặt IMAGE_PROVIDER=local."
        )
    from video_engine.providers.base import ProviderNotConfiguredError

    raise ProviderNotConfiguredError(f"IMAGE_PROVIDER không hỗ trợ: {name}")
