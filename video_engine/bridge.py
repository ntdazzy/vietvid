"""Bridge duyệt → đăng/doanh thu: dựng compat stub Script+RenderJob rồi ghi VideoAsset.

Đã verify: ``VideoAsset.render_job_id`` là FK bắt buộc và module4/module5 join
VideoAsset→RenderJob→Script→Product — nên KHÔNG drop-in được; stub giữ cho hệ cũ
chạy nguyên vẹn (publish gate, affiliate link, tracking token, review learning).
"""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone

from sqlalchemy import delete, select

from config.settings import settings
from core.database import db
from core.logger import logger
from core.models import (
    AssetStatus,
    Product,
    RenderJob,
    RenderStatus,
    Script,
    ShotPlan,
    VideoAsset,
    VideoJob,
    VideoJobStatus,
    VideoStageAsset,
)
from video_engine.providers.base import VideoEngineError

# Trạng thái KẾT THÚC mà job không có clip → an toàn để dọn hàng loạt (không đụng job đang chạy/chờ).
# 'CANCELLED' là chuỗi cũ trong DB (không nằm trong enum VideoJobStatus) — vẫn gom để dọn.
_NO_CLIP_TERMINAL_STATUSES = {
    VideoJobStatus.FAILED,
    VideoJobStatus.QA_FAIL,
    VideoJobStatus.REJECTED,
    "CANCELLED",
}


def approve_job(job_id: int) -> dict:
    """Duyệt job READY → tạo stub + VideoAsset APPROVED → hệ đăng/doanh thu cũ tiếp quản.

    Job không gắn product thật → chỉ đánh dấu APPROVED để tải xuống (không đẩy dispatch).
    """
    with db.transaction() as session:
        # KHOÁ row (Postgres FOR UPDATE) — serialize 2 lần duyệt song song: lời thứ 2 chờ tới khi lời 1
        # commit (status đã APPROVED) rồi rơi vào nhánh dưới → tránh tạo TRÙNG VideoAsset + affiliate link.
        job = session.scalar(select(VideoJob).where(VideoJob.id == job_id).with_for_update())
        if job is None:
            raise VideoEngineError(f"Không thấy video job id={job_id}")
        if job.status != VideoJobStatus.READY:
            raise VideoEngineError(f"Chỉ duyệt được job READY (hiện tại: {job.status}).")
        if not job.final_path or not os.path.exists(job.final_path):
            raise VideoEngineError("File final không tồn tại — không thể duyệt.")

        job.status = VideoJobStatus.APPROVED
        job.approved_at = datetime.now(timezone.utc)

        if not job.product_id:
            logger.info(f"[bridge] job={job_id} duyệt KHÔNG product → chỉ cho tải xuống")
            return {"job_id": job_id, "video_asset_id": None, "dispatch": False}

        narration = (
            session.scalar(
                select(ShotPlan.narration)
                .where(ShotPlan.job_id == job_id)
                .order_by(ShotPlan.id.desc())
                .limit(1)
            )
            or ""
        )

        # Stub Script: đủ field bắt buộc, đánh dấu nguồn để dễ truy vết.
        script = Script(
            product_id=job.product_id,
            status="APPROVED_AI",
            draft_text=narration or f"[video_engine job {job_id}]",
            final_json_path="",
            safety_passed=True,
            approved=True,
            critic_score=10.0,
            critic_feedback=f"video_engine bridge stub (job {job_id})",
        )
        session.add(script)
        session.flush()

        # Stub RenderJob DONE — không vướng unique-index active-script.
        render_job = RenderJob(
            script_id=script.id,
            status=RenderStatus.DONE,
            worker_pid=os.getpid(),
            started_at=job.approved_at,
            finished_at=job.approved_at,
        )
        session.add(render_job)
        session.flush()

        duration = _probe_duration(job.final_path)
        # V8.2 Phase 6: xếp lịch giờ vàng — None = fail-open đăng ngay (config rỗng/hỏng).
        from module4_dispatch.scheduler import next_golden_slot

        scheduled_at = next_golden_slot(session)
        asset = VideoAsset(
            render_job_id=render_job.id,
            video_job_id=job.id,
            fmt="9:16",
            file_path=job.final_path,
            duration_s=duration,
            has_captions=False,
            status=AssetStatus.APPROVED,
            license_status="APPROVED",  # asset 100% do AI sinh + compose local
            qa_status="PASS",
            qa_report_json='{"source": "video_engine", "gate": "qa_final_video"}',
            scheduled_at=scheduled_at,
        )
        session.add(asset)
        session.flush()
        asset_id = asset.id

        # Tracking token (sub_id) + hàng đợi affiliate link — tái dùng hệ cũ NGUYÊN bản.
        provider_name = settings.affiliate_link_provider or "shopee_cdp"
        try:
            from module5_revenue.tracking_tokens import ensure_video_tracking_token

            token = ensure_video_tracking_token(
                session, asset=asset, script=script, provider=provider_name
            )
            product = session.get(Product, job.product_id)
            product_url = (product.url or "").strip() if product else ""
            if product_url:
                from module4_dispatch.link_queue import (
                    enqueue_affiliate_link_request_in_session,
                )

                enqueue_affiliate_link_request_in_session(
                    session,
                    asset_id=asset_id,
                    product_url=product_url,
                    sub_id=token.token,
                    provider=provider_name,
                )
        except Exception as exc:  # noqa: BLE001 — link/token tạo lại được, không chặn duyệt
            logger.warning(f"[bridge] hook affiliate/tracking lỗi (tự chữa sau): {exc}")

    logger.info(f"[bridge] job={job_id} → VideoAsset id={asset_id} (APPROVED, chờ dispatch)")
    return {"job_id": job_id, "video_asset_id": asset_id, "dispatch": True}


def _claim_is_recent(iso: str, *, minutes: int = 30) -> bool:
    """Cờ 'uploading' còn mới? (chặn double-click; claim treo > minutes coi như hỏng, cho đăng lại)."""
    try:
        t = datetime.fromisoformat(iso)
    except (ValueError, TypeError):
        return False
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - t).total_seconds() < minutes * 60


def publish_long_narrative_youtube(job_id: int, *, privacy: str | None = None) -> dict:
    """Đăng video long_narrative (16:9) lên YouTube qua API — ĐƯỜNG RIÊNG, cách ly khỏi pipeline
    product/affiliate (KHÔNG VideoAsset/PublishJob/tracking/link → không đụng luồng kiếm tiền).

    Idempotent: đã đăng (params.youtube.video_id) → trả id cũ, KHÔNG upload lại (tránh video trùng +
    tốn quota). Metadata title/description/tags lấy từ SEO trong params (do Director sinh).
    """
    # Cổng AN TOÀN (RULES #1/#2: không đăng thật khi test). Mặc định TẮT → chặn MỌI lần đăng (kể cả
    # unlisted/public) cho tới khi founder bật `longform_youtube_publish_enabled` ở Credential Center.
    # Đây là chốt-chặn live-publish mà đường này trước đây thiếu (V5 product có publish_center_enabled).
    if not settings.longform_youtube_publish_enabled:
        raise VideoEngineError(
            "Đăng YouTube long_narrative đang TẮT (longform_youtube_publish_enabled=false). "
            "Bật ở Credential Center khi đã xem kỹ video + muốn đăng THẬT."
        )
    now = datetime.now(timezone.utc)
    # TX1: KHOÁ row (with_for_update) + idempotency + CLAIM cờ 'uploading' → fence double-click/retry.
    with db.transaction() as session:
        job = session.scalar(select(VideoJob).where(VideoJob.id == job_id).with_for_update())
        if job is None:
            raise VideoEngineError(f"Không thấy video job id={job_id}")
        if (job.mode or "") != "long_narrative":
            raise VideoEngineError("Đường đăng YouTube này chỉ dành cho video long_narrative.")
        if job.status not in {VideoJobStatus.READY, VideoJobStatus.APPROVED}:
            raise VideoEngineError(f"Chỉ đăng được job READY/APPROVED (hiện tại: {job.status}).")
        final_path = job.final_path or ""
        if not final_path or not os.path.exists(final_path):
            raise VideoEngineError("File final 16:9 không tồn tại — không thể đăng.")
        try:
            params = json.loads(job.params or "{}")
        except ValueError:
            params = {}
        yt = params.get("youtube") or {}
        already = yt.get("video_id")
        if already:
            logger.info(f"[bridge] job={job_id} đã đăng YouTube ({already}) → bỏ qua (idempotent)")
            return {"job_id": job_id, "youtube_video_id": already, "url": yt.get("url", ""), "duplicated": True}
        if yt.get("state") == "uncertain":
            raise VideoEngineError(
                "Lần đăng trước KHÔNG chắc đã lên YouTube (mất kết nối giữa chừng PUT). Kiểm YouTube Studio: "
                "nếu CHƯA có video → xoá cờ 'youtube' trong job rồi đăng lại; nếu ĐÃ có → không cần đăng lại."
            )
        if yt.get("state") == "uploading" and _claim_is_recent(yt.get("at", "")):
            raise VideoEngineError("Video đang được đăng lên YouTube (tiến trình khác) — đợi xong rồi thử lại.")
        seo = params.get("seo") or {}
        title = (seo.get("title") or (seo.get("titles") or [""])[0] or params.get("title") or "Video").strip()
        description = (seo.get("description") or "").strip()
        tags = seo.get("tags") or []
        # CLAIM uploading (commit khi thoát TX1) → request song song thấy cờ + bị chặn (chống đăng trùng).
        params["youtube"] = {"state": "uploading", "at": now.isoformat()}
        job.params = json.dumps(params, ensure_ascii=False)

    # Upload NGOÀI transaction (network dài, file vài trăm MB) — không giữ DB lock khi đang PUT.
    from module4_dispatch.providers import upload_youtube_video

    try:
        video_id = upload_youtube_video(final_path, title, description, tags=tags, privacy=privacy)
    except Exception as exc:
        # Phân loại pha lỗi: 'pre' = bytes CHƯA rời máy / bị từ chối rõ (4xx) → gỡ cờ cho đăng lại an toàn.
        # 'uncertain'/'created_unknown_id' = ĐÃ gửi bytes, video CÓ THỂ đã lên → KHÓA cờ 'uncertain', KHÔNG
        # tự đăng lại (tránh video TRÙNG công khai + tốn quota); người vận hành kiểm YouTube Studio rồi quyết.
        phase = getattr(exc, "phase", "pre")
        with db.transaction() as session:
            job = session.scalar(select(VideoJob).where(VideoJob.id == job_id).with_for_update())
            if job is not None:
                try:
                    p = json.loads(job.params or "{}")
                except ValueError:
                    p = {}
                if (p.get("youtube") or {}).get("state") == "uploading":
                    if phase == "pre":
                        p.pop("youtube", None)
                    else:
                        p["youtube"] = {"state": "uncertain", "at": now.isoformat(), "error": str(exc)[:200]}
                    job.params = json.dumps(p, ensure_ascii=False)
        raise
    url = f"https://youtu.be/{video_id}"

    with db.transaction() as session:
        job = session.scalar(select(VideoJob).where(VideoJob.id == job_id).with_for_update())
        if job is None:
            # Job bị xoá giữa upload — video ĐÃ lên YouTube nhưng không còn row để ghi. Vẫn TRẢ id (không
            # mất dấu video đã đăng) + KHÔNG raise (tránh báo nhầm thất bại sau khi đăng thành công).
            logger.error(f"[bridge] job={job_id} biến mất sau khi đăng YouTube {video_id} — không ghi được DB.")
            return {"job_id": job_id, "youtube_video_id": video_id, "url": url, "duplicated": False, "persisted": False}
        try:
            p = json.loads(job.params or "{}")
        except ValueError:
            p = {}
        p["youtube"] = {
            "video_id": video_id,
            "url": url,
            "privacy": privacy or settings.youtube_privacy_status,
            "published_at": datetime.now(timezone.utc).isoformat(),
        }
        job.params = json.dumps(p, ensure_ascii=False)
        if job.status == VideoJobStatus.READY:
            job.status = VideoJobStatus.APPROVED
            job.approved_at = datetime.now(timezone.utc)
    logger.info(f"[bridge] job={job_id} ĐÃ ĐĂNG YouTube → {url} (privacy={privacy or settings.youtube_privacy_status})")
    return {"job_id": job_id, "youtube_video_id": video_id, "url": url, "duplicated": False}


def reject_job(job_id: int, reason: str = "") -> dict:
    with db.transaction() as session:
        job = session.get(VideoJob, job_id)
        if job is None:
            raise VideoEngineError(f"Không thấy video job id={job_id}")
        if job.status not in {VideoJobStatus.READY, VideoJobStatus.QA_FAIL}:
            raise VideoEngineError(f"Job {job.status} không ở trạng thái từ chối được.")
        job.status = VideoJobStatus.REJECTED
        if reason:
            job.error = f"REJECTED: {reason}"[:500]
    return {"job_id": job_id, "status": VideoJobStatus.REJECTED}


def restore_job(job_id: int) -> dict:
    """Hoàn tác từ chối (lỡ bấm nhầm): REJECTED → READY, về lại hàng đợi duyệt + xoá cờ lỗi."""
    with db.transaction() as session:
        job = session.get(VideoJob, job_id)
        if job is None:
            raise VideoEngineError(f"Không thấy video job id={job_id}")
        if job.status != VideoJobStatus.REJECTED:
            raise VideoEngineError(f"Chỉ hoàn tác được job REJECTED (hiện tại: {job.status}).")
        # QA P1#5: undo là khôi phục TRẠNG THÁI — KHÔNG bắt buộc file tồn tại (trước đây file mất → undo 409,
        # job kẹt REJECTED mất luôn). Job READY mất file đã được lọc khỏi hàng đợi duyệt ở luồng review (P0#1).
        job.status = VideoJobStatus.READY
        job.error = ""
    return {"job_id": job_id, "status": VideoJobStatus.READY}


def delete_job(job_id: int) -> dict:
    """Xoá VĨNH VIỄN 1 video job: kịch bản (ShotPlan) + asset trung gian (VideoStageAsset)
    + bản ghi VideoJob + thư mục ``storage/video_engine/job_{id}``.

    Quan hệ shot_plans/stage_assets KHÔNG cascade nên phải xoá tay trước. Từ chối nếu job đã
    sinh VideoAsset (đã duyệt/vào luồng đăng-doanh thu) — phải từ chối (reject) job đó trước.
    """
    with db.transaction() as session:
        job = session.get(VideoJob, job_id)
        if job is None:
            raise VideoEngineError(f"Không thấy video job id={job_id}")
        linked = session.scalar(
            select(VideoAsset.id).where(VideoAsset.video_job_id == job_id).limit(1)
        )
        if linked is not None:
            raise VideoEngineError(
                "Job đã duyệt/đăng (có video xuất bản) — không xoá được. Hãy từ chối job trước."
            )
        final_path = job.final_path or ""
        session.execute(delete(ShotPlan).where(ShotPlan.job_id == job_id))
        session.execute(delete(VideoStageAsset).where(VideoStageAsset.job_id == job_id))
        session.delete(job)

    # Xoá thư mục job SAU khi commit DB. Chốt an toàn: chỉ rmtree thư mục có tên đúng job_{id}.
    job_dir = (
        os.path.dirname(final_path)
        if final_path
        else os.path.join("storage", "video_engine", f"job_{job_id}")
    )
    removed_dir = False
    if job_dir and os.path.isdir(job_dir) and os.path.basename(job_dir) == f"job_{job_id}":
        shutil.rmtree(job_dir, ignore_errors=True)
        removed_dir = True
    logger.info(f"[bridge] xoá job={job_id} (dir={'đã xoá' if removed_dir else 'không có'})")
    return {"job_id": job_id, "deleted": True, "dir_removed": removed_dir}


def cleanup_jobs_without_clip() -> dict:
    """Dọn mọi job KẾT THÚC mà không có file clip (final_path rỗng hoặc file đã mất).

    Chỉ đụng job ở trạng thái kết thúc (FAILED/QA_FAIL/REJECTED/CANCELLED) — KHÔNG xoá job
    đang chạy/chờ (RUNNING/QUEUED/WAITING_CONFIG) dù chưa có file.
    """
    with db.transaction() as session:
        jobs = session.scalars(select(VideoJob)).all()
        targets = [
            j.id
            for j in jobs
            if j.status in _NO_CLIP_TERMINAL_STATUSES
            and not (j.final_path and os.path.exists(j.final_path))
        ]
    removed: list[int] = []
    skipped: list[dict] = []
    for jid in targets:
        try:
            delete_job(jid)
            removed.append(jid)
        except VideoEngineError as exc:
            skipped.append({"job_id": jid, "reason": str(exc)})
    logger.info(f"[bridge] dọn job không clip: xoá {len(removed)}, bỏ qua {len(skipped)}")
    return {"removed": removed, "skipped": skipped, "count": len(removed)}


def _probe_duration(path: str) -> float:
    from video_engine.qa import _ffprobe

    probe = _ffprobe(path)
    return float(probe["duration"]) if probe else 0.0
