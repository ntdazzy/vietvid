"""Router video đa-provider — fallback ladder + fal gated by key. Unit (không DB)."""

from __future__ import annotations

import pytest

from video_engine.providers.base import (
    ProviderNotConfiguredError,
    ProviderRejectedError,
    VideoEngineError,
)
from video_engine.video_stage.router import RoutedVideoProvider


class _Boom:
    name = "boom"

    def generate(self, **kw):
        raise VideoEngineError("hạ tầng lỗi")


class _Reject:
    name = "reject"

    def generate(self, **kw):
        raise ProviderRejectedError("nội dung bị từ chối", final=True)


class _Ok:
    name = "ok"

    def __init__(self, ret="out.mp4"):
        self.ret = ret
        self.called = False

    def generate(self, **kw):
        self.called = True
        return self.ret


def test_fallback_skips_failing_provider():
    ok = _Ok("good.mp4")
    r = RoutedVideoProvider([_Boom(), ok])
    assert r.generate(prompt="x", out_path="o", seconds=5, aspect="9:16",
                      resolution="480p", model_id="m") == "good.mp4"
    assert ok.called


def test_moderation_reject_does_not_fallback():
    ok = _Ok()
    r = RoutedVideoProvider([_Reject(), ok])
    with pytest.raises(ProviderRejectedError):
        r.generate(prompt="x", out_path="o", seconds=5, aspect="9:16",
                   resolution="480p", model_id="m")
    assert not ok.called  # KHÔNG fallback khi bị từ chối nội dung


def test_all_fail_raises_last():
    r = RoutedVideoProvider([_Boom(), _Boom()])
    with pytest.raises(VideoEngineError):
        r.generate(prompt="x", out_path="o", seconds=5, aspect="9:16",
                   resolution="480p", model_id="m")


def test_empty_router_raises():
    with pytest.raises(ProviderNotConfiguredError):
        RoutedVideoProvider([])


def test_fal_provider_requires_key():
    # FAL_API_KEY chưa set → ProviderNotConfigured (không chạy giả)
    from video_engine.video_stage.fal_video import FalVideoProvider

    with pytest.raises(ProviderNotConfiguredError):
        FalVideoProvider()
