"""film_recap/runner.py — render_film_recap: handler mode='film_recap' (early-branch run_job).

source_mode='reupload' (P0): tải clip → ASR word-timings → 9:16 + caption ASS (GIỮ audio gốc) → QA.
Reserve ngân sách RIÊNG (provider='film_recap', daily_budget=film_recap_daily_budget_usd) — TÁCH
khỏi luồng affiliate. source_mode='recap' = P1 (chưa hỗ trợ → FAILED rõ). KHÔNG đụng Seedance/product.
"""
from __future__ import annotations

import os

from config.settings import settings
from core.logger import logger
from core.models import VideoJobStatus
from core.redaction import safe_error_detail
from video_engine.film_recap.compose_recap import compose_recap_mode, compose_reupload
from video_engine.film_recap.ingest import download
from video_engine.film_recap.scene_select import detect_scenes, even_segments, rank_scenes
from video_engine.film_recap.script_recap import generate_recap_script
from video_engine.providers.base import VideoBudgetError
from video_engine.providers.ledger import reserve_video_budget, settle_video_budget
from video_engine.film_recap.understand import clean_words
from video_engine.qa import qa_final_video

_PROVIDER = "film_recap"


def estimate_film_recap_cost(source_mode: str) -> dict:
    """Chi phí review phim: ASR (Groq free) + encode local (free). reupload ~$0.01; recap +LLM (P1)."""
    llm_usd = 0.0 if source_mode == "reupload" else 0.02  # recap: script LLM (P1)
    total = round(llm_usd + 0.01, 4)
    return {"total_usd": max(total, 0.01), "source_mode": source_mode}


def render_film_recap(job_id: int, snapshot: dict, job_dir: str) -> None:
    """Chạy trọn pipeline review phim cho 1 job. Tự ghi terminal status (run_job đã return sau gọi)."""
    from video_engine.pipeline import _merge_params, _set_status, _stage_end, _stage_start, _update_job

    params = snapshot.get("params") or {}
    url = (params.get("url") or "").strip()
    source_path = (params.get("source_path") or "").strip()  # file đã tải sẵn (local) — thay cho url
    source_mode = (params.get("source_mode") or "reupload").strip().lower()
    max_seconds = float(settings.film_recap_clip_max_seconds or 90)
    aspect = (params.get("aspect") or "9:16").strip()   # 9:16 (TikTok) | 16:9 (YouTube)

    if not url and not source_path:
        _set_status(job_id, VideoJobStatus.FAILED, error="Thiếu nguồn (link hoặc file đã tải) cho review phim.")
        return
    if source_mode not in ("reupload", "recap"):
        _set_status(job_id, VideoJobStatus.FAILED,
                    error=f"source_mode='{source_mode}' không hỗ trợ. Dùng 'reupload' hoặc 'recap'.")
        return

    est = estimate_film_recap_cost(source_mode)
    try:
        reserved, day = reserve_video_budget(
            est["total_usd"], provider=_PROVIDER,
            daily_budget=float(settings.film_recap_daily_budget_usd or 0.0),
        )
    except VideoBudgetError as exc:
        _set_status(job_id, VideoJobStatus.QUEUED_BUDGET, error=str(exc))
        return

    actual = 0.0
    try:
        _set_status(job_id, VideoJobStatus.RUNNING, error="")
        _update_job(job_id, provider_video="film_recap", resolution="1080p", model_id="film_recap",
                    estimated_cost_usd=est["total_usd"], max_cost_usd=round(est["total_usd"] * 1.5, 4))

        _stage_start(job_id, "INGEST")
        if source_path and os.path.exists(source_path):
            src = source_path  # đọc thẳng file đã tải (local), bỏ qua yt-dlp
        else:
            src = download(url, job_dir, max_mb=int(settings.film_recap_source_max_filesize_mb or 200))
        if not src or not os.path.exists(src):
            raise ValueError("Không lấy được nguồn — kiểm link (yt-dlp) hoặc đường dẫn file đã tải.")
        _stage_end(job_id, "INGEST", "done", note=("file" if source_path else "yt-dlp"))

        _stage_start(job_id, "ASR")
        words = clean_words(src, max_seconds=max_seconds)   # lọc hallucination + chỉ ASR cửa sổ burn (phim dài OK)
        _stage_end(job_id, "ASR", "done", note=f"{len(words)} từ")

        _stage_start(job_id, "COMPOSE")
        out_path = os.path.join(job_dir, "final.mp4")
        if source_mode == "reupload":
            res = compose_reupload(src, words, out_path, max_seconds=max_seconds, aspect=aspect)
        else:  # recap: kịch bản GỐC + giọng MỚI + clip minh hoạ (B1 chia đều)
            from video_engine.long_narrative.script_schema import Beat, NarrationBlock
            from video_engine.long_narrative.voice import reset_engine_state, synthesize_beat
            transcript = " ".join(w for w in (x.get("word", "").strip() for x in words) if w)
            lines = generate_recap_script(transcript, n_beats=int(settings.film_recap_recap_beats or 7))
            if not lines:
                raise ValueError("Sinh kịch bản recap thất bại (transcript rỗng/LLM lỗi).")
            reset_engine_state()  # xoá latch Gemini credit-out từ job TRƯỚC (cùng worker) → recap không rớt sai giọng
            voices = []
            for i, text in enumerate(lines):
                beat = Beat(narration_blocks=[NarrationBlock(speaker="narrator", text=text)])
                wav = os.path.join(job_dir, f"voice_{len(voices)}.wav")
                try:
                    synthesize_beat(beat, wav)
                except Exception as exc:  # noqa: BLE001 — 1 câu hỏng thì BỎ câu, KHÔNG giết cả job
                    logger.warning(f"[film_recap] recap synth câu {i} lỗi, bỏ: {str(exc)[:120]}")
                    continue
                voices.append(wav)
            if not voices:
                raise ValueError("Tất cả câu recap synth giọng thất bại (TTS chưa cấu hình?).")
            segs = rank_scenes(detect_scenes(src), src, want=len(voices),   # B2: chọn cảnh hay
                               min_len=float(settings.film_recap_scene_min_seconds or 1.2),
                               max_len=float(settings.film_recap_scene_max_seconds or 8.0))
            if not segs:
                raise ValueError("Không đọc được thời lượng clip nguồn để chia cảnh recap.")
            res = compose_recap_mode(src, segs, voices, out_path, max_seconds=max_seconds, aspect=aspect)
        _stage_end(job_id, "COMPOSE", "done", note=f"~{res['duration']:.0f}s")
        actual = est["total_usd"]

        _stage_start(job_id, "QA")
        qa = qa_final_video(final_path=out_path, expected_seconds=res["duration"],
                            aspect=aspect, check_product_match=False)
        passed = bool(qa.get("passed"))
        _stage_end(job_id, "QA", "done" if passed else "warn",
                   note=("OK" if passed else "; ".join(qa.get("reasons") or [])[:200]))

        _update_job(job_id, final_path=out_path, actual_cost_usd=round(actual, 4))
        _merge_params(job_id, {"final_path": out_path, "duration_s": round(res["duration"], 1),
                               "aspect": aspect, "source_mode": source_mode, "qa_passed": passed,
                               "qa_reasons": (qa.get("reasons") or [])[:5]})
        _set_status(job_id, VideoJobStatus.READY, error="")
        logger.info(f"[film_recap] job={job_id} READY · {source_mode} · ~{res['duration']:.0f}s · ${actual:.3f}")
    except Exception as exc:  # noqa: BLE001
        logger.exception(f"[film_recap] job={job_id} THẤT BẠI")
        _update_job(job_id, actual_cost_usd=round(actual, 4))
        _set_status(job_id, VideoJobStatus.FAILED, error=safe_error_detail(exc, limit=500))
    finally:
        settle_video_budget(reserved, actual, day=day, provider=_PROVIDER)
