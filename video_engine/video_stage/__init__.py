"""Video stage — sinh clip i2v bằng provider cấu hình (Seedance PiAPI / mock)."""

from __future__ import annotations

from config.settings import settings
from video_engine.providers.base import VideoProvider


def build_video_provider() -> VideoProvider:
    name = (settings.video_provider or "seedance_piapi").strip().lower()
    if name == "mock" or settings.use_fake_clients:
        from video_engine.video_stage.mock import MockVideoProvider

        return MockVideoProvider()
    if name == "seedance_piapi":
        from video_engine.video_stage.seedance_piapi import SeedancePiapiProvider

        return SeedancePiapiProvider()
    from video_engine.providers.base import ProviderNotConfiguredError

    raise ProviderNotConfiguredError(f"VIDEO_PROVIDER không hỗ trợ: {name}")
