"""Router video đa-provider — thử lần lượt theo ladder, fallback khi lỗi hạ tầng.

Quy tắc (theo SYSTEM_DESIGN): ProviderRejectedError (moderation) KHÔNG fallback (đổi provider vô
ích, cùng nội dung sẽ bị từ chối lại) → ném ngay. Lỗi hạ tầng/không-cấu-hình → sang provider kế.
"""

from __future__ import annotations

import logging

from video_engine.providers.base import (
    ProviderNotConfiguredError,
    ProviderRejectedError,
    VideoProvider,
)

logger = logging.getLogger("vietvid")


class RoutedVideoProvider:
    name = "routed"

    def __init__(self, providers: list[VideoProvider]) -> None:
        if not providers:
            raise ProviderNotConfiguredError("Router rỗng: không provider nào khả dụng")
        self._providers = providers

    def generate(self, **kwargs) -> str:
        last_exc: Exception | None = None
        for i, p in enumerate(self._providers):
            try:
                return p.generate(**kwargs)
            except ProviderRejectedError:
                raise  # nội dung bị từ chối → fallback vô nghĩa
            except Exception as exc:  # noqa: BLE001 — lỗi hạ tầng → thử provider kế
                last_exc = exc
                logger.warning(
                    "video router: provider %s lỗi (%s), fallback %s/%s",
                    getattr(p, "name", "?"), exc, i + 1, len(self._providers),
                )
        raise last_exc or ProviderNotConfiguredError("Tất cả provider đều lỗi")
