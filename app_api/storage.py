"""Lưu trữ media (Sóng 2/B) — local (mặc định) + S3/R2 khi cấu hình.

store_output: nếu STORAGE_* set + có boto3 → upload lên bucket, trả URL công khai (hoặc key);
ngược lại trả nguyên local_path. Degrade graceful — lỗi upload KHÔNG làm hỏng render.

cleanup_workdir: dọn thư mục tạm của job (fix bug "tmp phình" — audit P1). Cloud-mode dọn sạch;
local-mode giữ lại final.mp4 (đang serve), xoá intermediate (ảnh/clip/voice — phần lớn dung lượng).
"""

from __future__ import annotations

import logging
import os
import shutil
import tempfile
import time

from app_api import config

log = logging.getLogger("vietvid")

_JOBS_ROOT = os.path.join(tempfile.gettempdir(), "vietvid_jobs")


def _workdir(job_id) -> str:
    return os.path.join(_JOBS_ROOT, str(job_id))


def store_output(local_path: str, job_id) -> str:
    """Upload final.mp4 lên S3/R2 nếu cấu hình → trả URL; ngược lại trả local_path."""
    if not config.storage_configured() or not local_path or not os.path.exists(local_path):
        return local_path
    try:
        import boto3  # lazy: chỉ cần khi bật cloud

        client = boto3.client(
            "s3",
            endpoint_url=config.STORAGE_ENDPOINT or None,
            aws_access_key_id=config.STORAGE_ACCESS_KEY,
            aws_secret_access_key=config.STORAGE_SECRET_KEY,
            region_name=config.STORAGE_REGION or "auto",
        )
        key = f"videos/{job_id}.mp4"
        client.upload_file(local_path, config.STORAGE_BUCKET, key,
                           ExtraArgs={"ContentType": "video/mp4"})
        if config.STORAGE_PUBLIC_BASE:
            return f"{config.STORAGE_PUBLIC_BASE.rstrip('/')}/{key}"
        return f"s3://{config.STORAGE_BUCKET}/{key}"
    except Exception:  # noqa: BLE001 — lỗi upload không được làm hỏng job; giữ local.
        log.exception("store_output: upload lỗi, giữ file local")
        return local_path


def cleanup_workdir(job_id, *, keep: str | None = None) -> None:
    """Dọn workdir của job. keep=None → xoá cả thư mục; keep=<path> → giữ file đó, xoá còn lại."""
    wd = _workdir(job_id)
    if not os.path.isdir(wd):
        return
    try:
        if keep is None:
            shutil.rmtree(wd, ignore_errors=True)
            return
        keep_abs = os.path.abspath(keep)
        for name in os.listdir(wd):
            p = os.path.join(wd, name)
            if os.path.abspath(p) == keep_abs:
                continue
            if os.path.isdir(p):
                shutil.rmtree(p, ignore_errors=True)
            else:
                try:
                    os.remove(p)
                except OSError:
                    pass
    except OSError:
        log.exception("cleanup_workdir lỗi cho job %s", job_id)


def sweep_old_workdirs(*, older_than_hours: float = 48) -> int:
    """Reaper: xoá workdir mồ côi (job đã chết, thư mục quá hạn) ở CLOUD-mode. Trả số dir đã xoá.

    Chỉ quét khi storage cloud bật (local-mode final.mp4 đang serve → KHÔNG xoá)."""
    if not config.storage_configured() or not os.path.isdir(_JOBS_ROOT):
        return 0
    cutoff = time.time() - older_than_hours * 3600
    n = 0
    for name in os.listdir(_JOBS_ROOT):
        d = os.path.join(_JOBS_ROOT, name)
        try:
            if os.path.isdir(d) and os.path.getmtime(d) < cutoff:
                shutil.rmtree(d, ignore_errors=True)
                n += 1
        except OSError:
            pass
    return n
