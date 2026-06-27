"""Video stage — sinh clip i2v. Provider đơn (Seedance PiAPI / fal / mock) HOẶC chain fallback."""

from __future__ import annotations

from config.settings import settings
from video_engine.providers.base import VideoProvider


def _build_one(name: str) -> VideoProvider:
    name = (name or "").strip().lower()
    if name == "mock":
        from video_engine.video_stage.mock import MockVideoProvider

        return MockVideoProvider()
    if name in ("seedance_piapi", "seedance", "piapi"):
        from video_engine.video_stage.seedance_piapi import SeedancePiapiProvider

        return SeedancePiapiProvider()
    if name == "fal":
        from video_engine.video_stage.fal_video import FalVideoProvider

        return FalVideoProvider()
    from video_engine.providers.base import ProviderNotConfiguredError

    raise ProviderNotConfiguredError(f"VIDEO_PROVIDER không hỗ trợ: {name}")


def build_video_provider() -> VideoProvider:
    if settings.use_fake_clients:
        from video_engine.video_stage.mock import MockVideoProvider

        return MockVideoProvider()

    # Chain fallback: 'fal,seedance_piapi,mock' → thử lần lượt, bỏ provider chưa cấu hình.
    chain = (getattr(settings, "video_provider_chain", "") or "").strip()
    if chain:
        from video_engine.providers.base import ProviderNotConfiguredError
        from video_engine.video_stage.router import RoutedVideoProvider

        built: list[VideoProvider] = []
        for nm in [c for c in chain.split(",") if c.strip()]:
            try:
                built.append(_build_one(nm))
            except ProviderNotConfiguredError:
                continue  # thiếu key → bỏ qua, dùng cái kế trong ladder
        if not built:
            raise ProviderNotConfiguredError(f"Không provider nào khả dụng trong chain: {chain}")
        return built[0] if len(built) == 1 else RoutedVideoProvider(built)

    return _build_one(settings.video_provider or "seedance_piapi")
