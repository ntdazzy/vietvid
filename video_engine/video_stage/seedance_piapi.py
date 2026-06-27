"""Seedance 2.0 qua PiAPI — tạo task → poll → tải mp4 (khóa theo docs 2026-06-10).

API (đã verify):
- Upload ảnh tạm:  POST https://upload.theapi.app/api/ephemeral_resource
                   header x-api-key · body {file_name, file_data(base64)} → data.url (24h)
- Tạo task:        POST {base}/api/v1/task
                   body {model:"seedance", task_type:<model_id>, input:{...}}
- Poll:            GET  {base}/api/v1/task/{task_id} → data.status, data.output.video

Moderation: model strict được retry 1 lần; model *-less-restriction reject là FINAL
→ raise ``ProviderRejectedError(final=True)`` để pipeline đẩy việc sửa về khâu ảnh.
"""

from __future__ import annotations

import base64
import os
import time

import httpx

from config.settings import settings
from core.logger import logger
from core.config_checks import looks_real_secret
from video_engine.providers.base import (
    ProviderNotConfiguredError,
    ProviderRejectedError,
    VideoEngineError,
)

_REJECT_MARKERS = (
    "moderation", "reject", "censor", "policy", "flagged", "sensitive",
    "violat", "guideline", "community",  # "Your content violated community guidelines"
)


class SeedancePiapiProvider:
    name = "seedance_piapi"

    def __init__(self) -> None:
        key = (settings.piapi_api_key or "").strip()
        if not looks_real_secret(key):
            raise ProviderNotConfiguredError(
                "Thiếu PIAPI_API_KEY thật cho video stage → WAITING_CONFIG."
            )
        self._key = key
        self._base = settings.piapi_base_url.rstrip("/")

    # ── public ────────────────────────────────────────────────────────
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
        on_created=None,  # callback(task_id) — pipeline lưu để resume, tránh đốt tiền 2 lần
        resume_task_id: str = "",
    ) -> str:
        # Resume: job trước đã tạo task nhưng poll đứt (mạng) → poll lại task cũ trước.
        if resume_task_id:
            logger.info(f"[video-stage] resume poll task={resume_task_id}")
            try:
                video_url = self._poll(resume_task_id, model_id)
                self._download(video_url, out_path)
                logger.info(f"[video-stage] seedance task={resume_task_id} (resume) → {out_path}")
                return out_path
            except ProviderRejectedError:
                raise
            except VideoEngineError as exc:
                logger.warning(f"[video-stage] resume task cũ thất bại ({exc}) → tạo task mới")

        image_urls = [self._resolve_image(p) for p in (image_paths or []) if p]
        payload = {
            "model": "seedance",
            "task_type": model_id,
            "input": {
                "prompt": (prompt or "")[:4000],
                "mode": "first_last_frames" if image_urls else "text_to_video",
                "duration": max(4, min(15, int(seconds))),
                "aspect_ratio": "9:16",
                "resolution": resolution,
            },
        }
        if image_urls:
            payload["input"]["image_urls"] = image_urls[:2]  # first (+ last) frame
            # LƯU Ý (đã thử thật 2026-06-10): auto_upload_assets chỉ nhận URL CÔNG KHAI
            # (PiAPI tự tải về asset library) — bật flag với data-URI sẽ lỗi
            # InvalidParameter.URL. Vì vậy data-URI gửi THẲNG, không set flag.
        task_id = self._create_task(payload)
        logger.info(f"[video-stage] seedance task={task_id} ĐÃ TẠO (model={model_id})")
        if on_created is not None:
            try:
                on_created(task_id)
            except Exception:  # noqa: BLE001 — best-effort, NHƯNG mất task_id = resume hỏng
                # log.ERROR + task_id: nếu job interrupt giữa create↔download sẽ re-render TỪ ĐẦU
                # ($1.21) thay vì resume $0. Log task_id để khôi phục/audit thủ công.
                logger.error(
                    f"[video-stage] KHÔNG lưu được task_id={task_id} vào job params — "
                    "job gián đoạn sẽ render lại tốn tiền, KHÔNG resume. Cứu thủ công bằng task_id này."
                )
        video_url = self._poll(task_id, model_id)
        self._download(video_url, out_path)
        logger.info(f"[video-stage] seedance task={task_id} → {out_path}")
        return out_path

    # ── steps ─────────────────────────────────────────────────────────
    _upload_plan_blocked = False  # cache 403 "plan not allowed to upload" cho cả process

    def _resolve_image(self, path: str) -> str:
        """URL công khai → dùng thẳng. Ảnh local → upload tạm 24h; gói không cho upload
        (403 plan) → fallback gửi THẲNG data-URI base64 trong image_urls (đã verify chạy)."""
        if path.startswith("http://") or path.startswith("https://"):
            return path
        if not os.path.exists(path):
            raise VideoEngineError(f"Ảnh không tồn tại để upload: {path}")
        if not SeedancePiapiProvider._upload_plan_blocked:
            uploaded = self._try_upload(path)
            if uploaded:
                return uploaded
        logger.warning("[video-stage] gói PiAPI không cho upload → dùng data-URI base64")
        return _data_uri(path)

    def _try_upload(self, path: str) -> str | None:
        file_name = os.path.basename(path)
        with open(path, "rb") as f:
            file_data = base64.b64encode(f.read()).decode("ascii")
        with httpx.Client(timeout=settings.video_piapi_timeout_seconds) as client:
            resp = client.post(
                settings.piapi_upload_url,
                headers={"x-api-key": self._key},
                json={"file_name": file_name, "file_data": file_data},
            )
        if resp.status_code == 403 and "not allowed to upload" in resp.text:
            SeedancePiapiProvider._upload_plan_blocked = True
            return None
        if resp.status_code != 200:
            raise VideoEngineError(
                f"PiAPI upload ảnh lỗi HTTP {resp.status_code}: {resp.text[:200]}"
            )
        url = ((resp.json() or {}).get("data") or {}).get("url") or ""
        if not url:
            raise VideoEngineError(f"PiAPI upload không trả url: {resp.text[:200]}")
        return url

    def _create_task(self, payload: dict) -> str:
        # Payload kèm data-URI có thể ~vài MB; server nhận + tạo asset chậm —
        # đã đo thật >60s (2026-06-10) → read timeout riêng 240s cho create.
        create_timeout = httpx.Timeout(connect=15.0, read=240.0, write=120.0, pool=15.0)
        with httpx.Client(timeout=create_timeout) as client:
            resp = client.post(
                f"{self._base}/api/v1/task",
                headers={"x-api-key": self._key},
                json=payload,
            )
        if resp.status_code != 200:
            raise VideoEngineError(
                f"PiAPI tạo task lỗi HTTP {resp.status_code}: {resp.text[:300]}"
            )
        body = resp.json() or {}
        task_id = (body.get("data") or {}).get("task_id") or ""
        if not task_id:
            raise VideoEngineError(f"PiAPI không trả task_id: {str(body)[:300]}")
        return task_id

    def _poll(self, task_id: str, model_id: str) -> str:
        deadline = time.monotonic() + settings.video_piapi_max_wait_seconds
        final_reject = "less-restriction" in model_id
        consecutive_errors = 0
        while time.monotonic() < deadline:
            try:
                with httpx.Client(timeout=settings.video_piapi_timeout_seconds) as client:
                    resp = client.get(
                        f"{self._base}/api/v1/task/{task_id}",
                        headers={"x-api-key": self._key},
                    )
            except httpx.HTTPError as exc:
                # Mạng/timeout TẠM THỜI 1 request không được giết cả job — task vẫn chạy phía PiAPI.
                consecutive_errors += 1
                logger.warning(
                    f"[video-stage] poll lỗi tạm ({consecutive_errors}): {exc} — thử lại"
                )
                if consecutive_errors >= 10:
                    raise VideoEngineError(
                        f"Poll task {task_id} lỗi mạng {consecutive_errors} lần liên tiếp."
                    ) from exc
                time.sleep(settings.video_piapi_poll_interval_seconds)
                continue
            consecutive_errors = 0
            if resp.status_code != 200:
                raise VideoEngineError(
                    f"PiAPI poll lỗi HTTP {resp.status_code}: {resp.text[:200]}"
                )
            data = (resp.json() or {}).get("data") or {}
            status = str(data.get("status") or "").lower()
            if status == "completed":
                video_url = (data.get("output") or {}).get("video") or ""
                if not video_url:
                    raise VideoEngineError(f"Task xong nhưng thiếu output.video: {data}")
                return video_url
            if status == "failed":
                import json as _json

                error = data.get("error") or {}
                message = str(
                    error.get("message") or error.get("raw_message") or error or data
                )[:300]
                # Dò marker moderation trên TOÀN BỘ payload (không chỉ message rút gọn) — reject
                # nội dung có thể nằm ở field khác → tránh phân loại nhầm thành lỗi kỹ thuật FAILED.
                haystack = _json.dumps(data, ensure_ascii=False).lower()
                if any(marker in haystack for marker in _REJECT_MARKERS):
                    raise ProviderRejectedError(
                        f"Seedance từ chối nội dung: {message}", final=final_reject
                    )
                raise VideoEngineError(f"Seedance task FAILED: {message}")
            time.sleep(settings.video_piapi_poll_interval_seconds)
        raise VideoEngineError(
            f"Seedance task {task_id} quá {settings.video_piapi_max_wait_seconds}s chưa xong."
        )

    def _download(self, url: str, out_path: str) -> None:
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        with httpx.Client(timeout=120.0, follow_redirects=True) as client:
            with client.stream("GET", url) as resp:
                if resp.status_code != 200:
                    raise VideoEngineError(f"Tải video lỗi HTTP {resp.status_code}")
                with open(out_path, "wb") as f:
                    for chunk in resp.iter_bytes(chunk_size=1 << 16):
                        f.write(chunk)
        if os.path.getsize(out_path) < 10_000:
            raise VideoEngineError("File video tải về quá nhỏ — nghi hỏng.")


def _data_uri(path: str) -> str:
    import mimetypes

    # seedance:76 (2026-06-13): chặn ảnh quá lớn trước khi nhúng base64 vào create_task — payload
    # phình (base64 ~+33%) gây create chậm + nguy cơ timeout. Ảnh URL công khai không vào đây.
    size_mb = os.path.getsize(path) / (1024 * 1024)
    if size_mb > settings.piapi_image_max_size_mb:
        raise VideoEngineError(
            f"Ảnh {os.path.basename(path)} ({size_mb:.1f}MB) vượt trần "
            f"PIAPI_IMAGE_MAX_SIZE_MB={settings.piapi_image_max_size_mb}MB cho fallback data-URI — "
            "dùng URL ảnh công khai (https) hoặc giảm dung lượng ảnh."
        )
    mime = mimetypes.guess_type(path)[0] or "image/png"
    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{encoded}"
