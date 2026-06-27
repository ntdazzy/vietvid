"""Provider video qua fal.ai (aggregator) — 1 key mở khoá Seedance/Kling/Hailuo/Luma/Pika/Runway.

Dùng fal Queue API: submit -> poll status -> tải mp4. Gated bởi FAL_API_KEY (ProviderNotConfigured
nếu thiếu — tuyệt đối không chạy giả). Kích hoạt gọi thật khi có key; cấu trúc theo fal docs.
"""

from __future__ import annotations

import base64
import os
import time

import httpx

from config.settings import settings
from video_engine.providers.base import (
    ProviderNotConfiguredError,
    ProviderRejectedError,
    VideoEngineError,
)


def _data_uri(path: str) -> str:
    ext = os.path.splitext(path)[1].lstrip(".").lower() or "png"
    mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
    with open(path, "rb") as f:
        return f"data:{mime};base64," + base64.b64encode(f.read()).decode("ascii")


class FalVideoProvider:
    name = "fal"

    def __init__(self, *, model: str | None = None) -> None:
        self._key = (settings.fal_api_key or "").strip()
        if not self._key:
            raise ProviderNotConfiguredError("Thiếu FAL_API_KEY (fal.ai)")
        self._model = (model or settings.fal_video_model or "").strip()
        if not self._model:
            raise ProviderNotConfiguredError("Thiếu fal_video_model")
        self._timeout = float(getattr(settings, "video_piapi_timeout_seconds", 60) or 60)
        self._max_wait = float(getattr(settings, "video_piapi_max_wait_seconds", 600) or 600)
        self._poll = float(getattr(settings, "video_piapi_poll_interval_seconds", 5) or 5)

    def _headers(self) -> dict:
        return {"Authorization": f"Key {self._key}", "Content-Type": "application/json"}

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
        args: dict = {"prompt": prompt, "duration": int(seconds), "aspect_ratio": aspect or "9:16"}
        if resolution:
            args["resolution"] = resolution
        if image_paths:
            args["image_url"] = _data_uri(image_paths[0])  # i2v: ảnh khung làm điều kiện

        submit = httpx.post(f"https://queue.fal.run/{self._model}", json=args,
                            headers=self._headers(), timeout=self._timeout)
        if submit.status_code in (400, 422):
            raise ProviderRejectedError(f"fal từ chối input: {submit.text[:200]}", final=True)
        submit.raise_for_status()
        data = submit.json()
        status_url = data.get("status_url") or f"https://queue.fal.run/{self._model}/requests/{data.get('request_id')}/status"
        response_url = data.get("response_url") or f"https://queue.fal.run/{self._model}/requests/{data.get('request_id')}"

        deadline = time.monotonic() + self._max_wait
        while time.monotonic() < deadline:
            st = httpx.get(status_url, headers=self._headers(), timeout=self._timeout).json()
            status = st.get("status")
            if status == "COMPLETED":
                break
            if status in ("FAILED", "ERROR"):
                raise VideoEngineError(f"fal job lỗi: {st}")
            time.sleep(self._poll)
        else:
            raise VideoEngineError(f"fal job quá {self._max_wait}s chưa xong")

        result = httpx.get(response_url, headers=self._headers(), timeout=self._timeout).json()
        video_url = (result.get("video") or {}).get("url") or result.get("video_url")
        if not video_url:
            raise VideoEngineError(f"fal không trả video url: {str(result)[:200]}")
        clip = httpx.get(video_url, timeout=self._timeout)
        clip.raise_for_status()
        with open(out_path, "wb") as f:
            f.write(clip.content)
        return out_path
