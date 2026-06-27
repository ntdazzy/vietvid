"""Worker video_engine — process nền trong orchestrator: nhặt job QUEUED → chạy pipeline.

Job QUEUED_BUDGET / WAITING_CONFIG được thử lại theo chu kỳ (5 phút) — khi founder nạp
budget/điền key thì tự chạy tiếp, không cần bấm lại.
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from config.settings import settings
from core.database import db
from core.logger import logger
from core.models import VideoJob, VideoJobStatus
from video_engine.formats import ensure_default_formats
from video_engine.kols import ensure_default_kols
from video_engine.pipeline import recompose_job, run_job
from video_engine.scenes import ensure_default_scenes

_RETRY_BLOCKED_AFTER = timedelta(minutes=5)


def main_loop() -> None:
    """Vòng lặp chính — gọi từ orchestrator (đã setup_logging + reset_for_fork)."""
    ensure_default_formats()
    ensure_default_scenes()
    ensure_default_kols()
    _requeue_orphan_running()
    _flag_missing_output_files()
    logger.info("[video-worker] sẵn sàng — chờ video_jobs QUEUED")
    while True:
        job_id = _pick_next_job()
        if job_id is None:
            # V8.2 Phase 5: idle → autopilot tick (poll DB — không nghe EventBus, không process mới).
            try:
                from video_engine.autopilot import autopilot_tick

                autopilot_tick()
            except Exception:  # noqa: BLE001 — autopilot lỗi không được giết worker
                logger.exception("[video-worker] autopilot_tick lỗi")
            time.sleep(settings.video_worker_poll_seconds)
            continue
        logger.info(f"[video-worker] nhận job={job_id}")
        # V8.3-Q6: cờ recompose → chỉ chạy lại VOICING→COMPOSING→QA từ clip gốc ($0).
        # QA P1#33: bọc try/except — lỗi NGOÀI try của pipeline (load snapshot/makedirs/estimate) KHÔNG
        # được escape làm chết video_engine (storm restart → disable). Đánh job FAILED rồi tiếp job khác.
        try:
            if _pop_recompose_flag(job_id):
                recompose_job(job_id)
            else:
                run_job(job_id)
        except Exception:  # noqa: BLE001 — 1 job độc không được giết worker
            logger.exception(f"[video-worker] job={job_id} lỗi ngoài pipeline — đánh FAILED, chạy tiếp")
            _mark_job_failed(job_id)


def _mark_job_failed(job_id: int) -> None:
    """QA P1#33: đánh job FAILED khi run_job ném lỗi ngoài pipeline (best-effort, không ném tiếp)."""
    try:
        with db.transaction() as session:
            job = session.get(VideoJob, job_id)
            if job is not None and job.status not in ("READY", "APPROVED", "POSTED"):
                job.status = "FAILED"
                job.error = "worker: lỗi ngoài pipeline (xem log)"
    except Exception:  # noqa: BLE001
        logger.exception(f"[video-worker] không đánh FAILED được job={job_id}")


def _pop_recompose_flag(job_id: int) -> bool:
    """Đọc + XOÁ cờ params.recompose_requested (xoá ngay để không lặp vô hạn)."""
    with db.transaction() as session:
        job = session.get(VideoJob, job_id)
        if job is None:
            return False
        try:
            params = json.loads(job.params or "{}")
        except ValueError:
            return False
        if not params.get("recompose_requested"):
            return False
        params["recompose_requested"] = False
        job.params = json.dumps(params, ensure_ascii=False)
        return True


def _requeue_orphan_running() -> None:
    """Job RUNNING mồ côi (worker trước chết giữa chừng) → QUEUED chạy lại.

    An toàn vì chỉ có MỘT worker video_engine; pipeline tự resume task Seedance cũ
    qua params.piapi_task_id nên không trả tiền video 2 lần.
    """
    with db.transaction() as session:
        orphans = session.scalars(
            select(VideoJob).where(VideoJob.status == VideoJobStatus.RUNNING)
        ).all()
        for job in orphans:
            job.status = VideoJobStatus.QUEUED
            logger.warning(f"[video-worker] job={job.id} RUNNING mồ côi → QUEUED chạy lại")


def _flag_missing_output_files() -> None:
    """storage/video_engine nằm NGOÀI git → file final.mp4 có thể bay (git clean/checkout/xoá storage)
    trong khi DB vẫn READY/APPROVED trỏ final_path. Quét lúc khởi động: job có final_path nhưng file
    không còn → ghi job.error (marker FILE_MISSING) + cảnh báo để operator biết (web /jobs/{id}/video
    404). KHÔNG đổi status: file có thể khôi phục từ backup, và APPROVED không nên tự lật FAILED.
    """
    marker = "FILE_MISSING:"
    missing: list[int] = []
    with db.transaction() as session:
        jobs = session.scalars(
            select(VideoJob).where(
                VideoJob.status.in_([VideoJobStatus.READY, VideoJobStatus.APPROVED])
            )
        ).all()
        for job in jobs:
            path = (job.final_path or "").strip()
            if path and not os.path.exists(path):
                missing.append(job.id)
                if not (job.error or "").startswith(marker):
                    job.error = f"{marker} file output không còn ({path}) — cần render lại."
    if missing:
        logger.warning(
            f"[video-worker] {len(missing)} job READY/APPROVED MẤT file output "
            f"(storage/video_engine ngoài git): ids={missing}"
        )


def _pick_next_job() -> int | None:
    """QUEUED trước; job bị chặn (budget/config) thử lại sau mỗi 5 phút."""
    now = datetime.now(timezone.utc)
    with db.transaction() as session:
        # LANE: ưu tiên job KIẾM TIỀN (product/kol/affiliate) trước; long_narrative (render ~1.75h)
        # CHỈ được pick khi KHÔNG còn job khác chờ → video YouTube dài không chen trước queue product.
        # (Lưu ý: job long_narrative ĐANG chạy vẫn giữ worker tới khi xong — muốn chạy SONG SONG hẳn
        #  thì chạy 1 tiến trình worker thứ 2 lọc mode='long_narrative'; xem docs/PLAN-youtube-publish-bridge.md.)
        # Job NẶNG/CHẬM (long_narrative ~1.75h + film_recap review phim) cùng lane chậm — nhường
        # queue product. PHẢI khớp ở CẢ HAI query (cùng slow_modes), không thì film_recap kẹt vĩnh
        # viễn vì không lane nào vớt.
        slow_modes = ["long_narrative", "film_recap"]
        job = session.scalar(
            select(VideoJob)
            .where(VideoJob.status == VideoJobStatus.QUEUED, VideoJob.mode.not_in(slow_modes))
            .order_by(VideoJob.created_at)
            .limit(1)
        )
        if job is None:
            job = session.scalar(
                select(VideoJob)
                .where(VideoJob.status == VideoJobStatus.QUEUED, VideoJob.mode.in_(slow_modes))
                .order_by(VideoJob.created_at)
                .limit(1)
            )
        if job is not None:
            return job.id
        blocked = session.scalars(
            select(VideoJob)
            .where(
                VideoJob.status.in_(
                    [VideoJobStatus.QUEUED_BUDGET, VideoJobStatus.WAITING_CONFIG]
                )
            )
            .order_by(VideoJob.created_at)
        ).all()
        for candidate in blocked:
            if _last_attempt(candidate) <= now - _RETRY_BLOCKED_AFTER:
                return candidate.id
    return None


def _last_attempt(job: VideoJob) -> datetime:
    try:
        raw = (json.loads(job.stage_timings or "{}") or {}).get("_last_attempt", "")
        parsed = datetime.fromisoformat(raw)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        created = job.created_at
        if created is None:
            return datetime.fromtimestamp(0, tz=timezone.utc)
        return created if created.tzinfo else created.replace(tzinfo=timezone.utc)
