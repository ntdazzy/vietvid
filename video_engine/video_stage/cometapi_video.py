"""Provider video qua CometAPI (reseller Seedance 2.0 rẻ — ƯU TIÊN giai đoạn đầu).

Luồng: POST /v1/videos -> poll GET /v1/videos/{id} -> tải mp4. Gated bởi COMETAPI_API_KEY
(ProviderNotConfigured nếu thiếu → router bỏ qua, KHÔNG chạy giả).

⚠️ CHƯA TEST với key thật. Cần render thử 1 clip để xác nhận 2 quirk:
  (1) JSON vs form-data ở POST /v1/videos (doc ghi "form-data"; đa số endpoint OpenAI-compatible nhận JSON).
  (2) cách truyền ẢNH i2v (tên field + URL/base64). Text-to-video chắc; i2v đánh dấu TODO.
Khớp giao diện VideoProvider (providers/base.py) như seedance_piapi/fal.
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


class CometapiVideoProvider:
    name = "cometapi"

    def __init__(self, *, model: str | None = None) -> None:
        self._key = (settings.cometapi_api_key or "").strip()
        if not self._key:
            raise ProviderNotConfiguredError("Thiếu COMETAPI_API_KEY")
        self._base = (settings.cometapi_base_url or "https://api.cometapi.com").rstrip("/")
        self._model = (model or settings.cometapi_video_model or "doubao-seedance-2-0-fast").strip()
        self._timeout = float(getattr(settings, "video_piapi_timeout_seconds", 60) or 60)
        self._max_wait = float(getattr(settings, "video_piapi_max_wait_seconds", 900) or 900)
        self._poll = float(getattr(settings, "video_piapi_poll_interval_seconds", 5) or 5)

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._key}", "Content-Type": "application/json"}

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
        body: dict = {
            "model": self._model,
            "prompt": prompt,
            # ĐÃ VERIFY 2026-06-30: CometAPI yêu cầu seconds là CHUỖI (gửi number → 400
            # "cannot unmarshal number into ... seconds of type string").
            "seconds": str(max(4, min(15, int(seconds)))),  # CometAPI: 4–15s, kiểu string
            "size": aspect or "9:16",
        }
        if image_paths:
            # ⚠️ TODO(verify): CometAPI nhận tới 9 ảnh tham chiếu; tên field + format (URL/base64)
            # cần xác nhận khi render thử. Tạm thử 'images' = list data-uri.
            body["images"] = [_data_uri(image_paths[0])]

        submit = httpx.post(f"{self._base}/v1/videos", json=body,
                            headers=self._headers(), timeout=self._timeout)
        if submit.status_code in (400, 422):
            raise ProviderRejectedError(f"CometAPI từ chối input: {submit.text[:200]}", final=True)
        submit.raise_for_status()
        d = submit.json()
        task_id = d.get("task_id") or d.get("id") or (d.get("data") or {}).get("id")
        if not task_id:
            raise VideoEngineError(f"CometAPI không trả task id: {str(d)[:200]}")

        video_url = None
        deadline = time.monotonic() + self._max_wait
        while time.monotonic() < deadline:
            st = httpx.get(f"{self._base}/v1/videos/{task_id}",
                           headers=self._headers(), timeout=self._timeout).json()
            data = st.get("data") or st
            status = str(st.get("status") or data.get("status") or "").lower()
            if status in ("success", "completed", "succeeded"):
                video_url = data.get("video_url") or st.get("video_url") or data.get("url")
                break
            if status in ("failed", "error"):
                raise VideoEngineError(f"CometAPI job lỗi: {str(st)[:200]}")
            time.sleep(self._poll)
        else:
            raise VideoEngineError(f"CometAPI job quá {self._max_wait}s chưa xong")

        # Tải clip — CHẶT (VERIFY 2026-06-30): có lúc status='completed' nhưng /content trả ~107 byte
        # rác (JSON lỗi), không phải video → check size + RETRY (ưu tiên video_url, fallback /content).
        content_url = f"{self._base}/v1/videos/{task_id}/content"
        last = b""
        for _ in range(5):
            try:
                if video_url:
                    clip = httpx.get(video_url, timeout=self._timeout)
                else:
                    clip = httpx.get(content_url, headers=self._headers(), timeout=self._timeout)
                last = clip.content
                if clip.status_code == 200 and len(clip.content) > 50_000:  # mp4 thật > 50KB
                    with open(out_path, "wb") as f:
                        f.write(clip.content)
                    return out_path
            except Exception:  # noqa: BLE001 — best-effort, retry
                pass
            # chưa được: thử lấy lại video_url từ status rồi chờ
            try:
                st = httpx.get(f"{self._base}/v1/videos/{task_id}",
                               headers=self._headers(), timeout=self._timeout).json()
                data = st.get("data") or st
                video_url = data.get("video_url") or st.get("video_url") or data.get("url") or video_url
            except Exception:  # noqa: BLE001
                pass
            time.sleep(self._poll)
        raise VideoEngineError(
            f"CometAPI tải clip lỗi sau 5 lần (status completed nhưng content {len(last)}B). task={task_id}"
        )
