"""Protocol + lỗi chuẩn cho provider ảnh/video của video_engine (fail-closed)."""

from __future__ import annotations

from typing import Protocol


class VideoEngineError(RuntimeError):
    """Lỗi chung của video_engine."""


class VideoBudgetError(VideoEngineError):
    """Vượt ngân sách ngày → job xếp hàng (QUEUED_BUDGET), không gọi API."""


class ProviderNotConfiguredError(VideoEngineError):
    """Thiếu key/cấu hình → WAITING_CONFIG, tuyệt đối không chạy giả."""


class ProviderRejectedError(VideoEngineError):
    """Provider từ chối nội dung (moderation).

    ``final=True`` (model less-restriction): KHÔNG retry video — đẩy việc sửa
    về khâu ảnh/prompt. ``final=False`` (model strict): được thử lại 1 lần.
    """

    def __init__(self, message: str, *, final: bool) -> None:
        super().__init__(message)
        self.final = final


class ImageProvider(Protocol):
    name: str

    def generate(
        self,
        *,
        prompt: str,
        out_path: str,
        input_image_paths: list[str] | None = None,
    ) -> str:
        """Sinh 1 ảnh từ prompt (+ ảnh tham chiếu nếu có). Trả path ảnh đã lưu."""
        ...


class VideoProvider(Protocol):
    name: str

    def generate(
        self,
        *,
        prompt: str,
        out_path: str,
        seconds: int,
        aspect: str,
        resolution: str,
        model_id: str,
        image_paths: list[str] | None = None,
    ) -> str:
        """Sinh 1 clip mp4 (i2v nếu có image_paths). Trả path mp4 đã lưu."""
        ...
