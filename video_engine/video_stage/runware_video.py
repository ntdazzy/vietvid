"""Provider video qua Runware (FALLBACK khi CometAPI lỗi — host hợp pháp, peer fal.ai).

Luồng: POST api.runware.ai/v1 mảng [{"taskType":"videoInference",...}] -> poll getResponse theo
taskUUID -> tải mp4. Gated bởi RUNWARE_API_KEY (ProviderNotConfigured nếu thiếu → router bỏ qua).

⚠️ CHƯA TEST với key thật — best-effort theo Runware docs. 3 quirk cần verify khi render thử:
  (1) AIR id Seedance 2.0-fast (settings.runware_video_model, mặc định 'bytedance:3@1' — XÁC MINH).
  (2) async deliveryMethod + cách poll (getResponse) vs trả ngay videoURL.
  (3) map resolution+aspect -> width/height (Runware cần số px tường minh).
Runware là FALLBACK nên ít rủi ro hơn (chỉ chạy khi CometAPI sập).
"""

from __future__ import annotations

import base64
import os
import time
import uuid

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


def _dims(resolution: str, aspect: str) -> tuple[int, int]:
    """resolution ('480p'/'720p'/'1080p') + aspect ('9:16') -> (width,height). ⚠️ TODO verify quy ước."""
    short = int("".join(c for c in (resolution or "480p") if c.isdigit()) or "480")
    try:
        a, b = (aspect or "9:16").split(":")
        ra, rb = int(a), int(b)
    except Exception:  # noqa: BLE001
        ra, rb = 9, 16
    if ra <= rb:  # dọc: short = width
        return short, round(short * rb / ra / 2) * 2
    return round(short * ra / rb / 2) * 2, short  # ngang: short = height


class RunwareVideoProvider:
    name = "runware"

    def __init__(self, *, model: str | None = None) -> None:
        self._key = (settings.runware_api_key or "").strip()
        if not self._key:
            raise ProviderNotConfiguredError("Thiếu RUNWARE_API_KEY")
        self._url = (settings.runware_base_url or "https://api.runware.ai/v1").rstrip("/")
        self._model = (model or settings.runware_video_model or "bytedance:3@1").strip()
        self._timeout = float(getattr(settings, "video_piapi_timeout_seconds", 60) or 60)
        self._max_wait = float(getattr(settings, "video_piapi_max_wait_seconds", 900) or 900)
        self._poll = float(getattr(settings, "video_piapi_poll_interval_seconds", 5) or 5)

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._key}", "Content-Type": "application/json"}

    @staticmethod
    def _find_video_url(resp: dict) -> str | None:
        data = resp.get("data") or []
        for row in data if isinstance(data, list) else [data]:
            url = row.get("videoURL") or row.get("video_url") or row.get("videoUrl")
            if url:
                return url
        return None

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
        w, h = _dims(resolution, aspect)
        task_uuid = str(uuid.uuid4())
        task: dict = {
            "taskType": "videoInference", "taskUUID": task_uuid, "model": self._model,
            "positivePrompt": prompt, "duration": int(seconds), "width": w, "height": h,
            "numberResults": 1,
        }
        if image_paths:
            # ⚠️ TODO(verify): tên field ảnh khung-đầu (frameImages) + format.
            task["frameImages"] = [{"inputImage": _data_uri(image_paths[0])}]

        submit = httpx.post(self._url, json=[task], headers=self._headers(), timeout=self._timeout)
        if submit.status_code in (400, 422):
            raise ProviderRejectedError(f"Runware từ chối input: {submit.text[:200]}", final=True)
        submit.raise_for_status()
        resp = submit.json()
        video_url = self._find_video_url(resp)  # đôi khi trả ngay (sync)

        deadline = time.monotonic() + self._max_wait
        while not video_url and time.monotonic() < deadline:
            time.sleep(self._poll)
            poll = httpx.post(self._url, json=[{"taskType": "getResponse", "taskUUID": task_uuid}],
                              headers=self._headers(), timeout=self._timeout).json()
            if any(str(e.get("code") or "").lower() in ("error", "failed")
                   for e in (poll.get("errors") or [])):
                raise VideoEngineError(f"Runware job lỗi: {str(poll)[:200]}")
            video_url = self._find_video_url(poll)
        if not video_url:
            raise VideoEngineError(f"Runware không trả videoURL trong {self._max_wait}s")

        clip = httpx.get(video_url, timeout=self._timeout)
        clip.raise_for_status()
        with open(out_path, "wb") as f:
            f.write(clip.content)
        return out_path
