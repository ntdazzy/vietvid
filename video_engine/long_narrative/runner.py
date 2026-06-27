"""runner.py — render_long_narrative: handler cho mode='long_narrative' (early-branch run_job).

Reserve qua estimator RIÊNG (ảnh + TTS + ASR, video_usd=0) — KHÔNG `estimate_job_cost` (tính
Seedance/giây → 14' = hàng trăm $ làm nghẽn QUEUED_BUDGET). Director chạy WORKER-SIDE (INGESTING →
WRITING) nếu job chỉ có topic; hoặc dùng thẳng `beats` nếu đã có. Dùng lại ledger + helper DB của
`video_engine.pipeline` + `qa_final_video(aspect='16:9')`. **KHÔNG đụng** path Seedance/product.
"""

from __future__ import annotations

import os

from config.settings import settings
from core.logger import logger
from core.models import VideoJobStatus
from core.redaction import safe_error_detail
from video_engine.providers.base import VideoBudgetError
from video_engine.providers.ledger import ledger_snapshot, reserve_video_budget, settle_video_budget
from video_engine.qa import qa_final_video


def _default_visual_mode() -> str:
    return (settings.longform_visual_engine or "doodle_cutout").strip() or "doodle_cutout"


def estimate_long_narrative_cost(
    n_beats: int, total_chars: int, *, hero_i2v: bool = False, hero_seconds: float = 0.0,
    visual_mode: str | None = None,
) -> dict:
    """Chi phí long-form: ảnh × n_beats + TTS theo ký tự + ASR (free) + critic LLM text. video_usd=0.

    visual_mode quyết định image_usd: photo_meme = 0 (ảnh thật Wikimedia/og + meme, KHÔNG Gemini);
    doodle_ai = full (Gemini × n_beats); hybrid = ~½ (một nửa beat dùng Gemini doodle).
    """
    visual_mode = (visual_mode or _default_visual_mode()).strip().lower()
    per_image = float(settings.video_image_cost_usd or 0.0)
    planner_usd = 0.0
    if visual_mode == "photo_meme":
        image_usd = 0.0
    elif visual_mode == "vuive_layered":
        # đạo diễn AI đa-lớp: ~8 shot/beat, ~½ là doodle Gemini gen (nửa kia ảnh thật/meme/terminal $0);
        # + planner+critic shot-plan ~3 LLM text call/beat. KHÔNG còn giả định 1-ảnh/beat (hết qua-mặt ngân sách).
        image_usd = round(max(0, n_beats) * 8 * 0.5 * per_image, 4)
        planner_usd = round(max(0, n_beats) * 3 * 0.0006, 4)
    elif visual_mode == "hybrid":
        image_usd = round(max(0, n_beats) / 2 * per_image, 4)
    else:  # doodle_ai (mặc định)
        image_usd = round(max(0, n_beats) * per_image, 4)
    # Gemini TTS đắt hơn Vbee: ĐO THẬT ~1.9 token/ký tự, giá bảo thủ $10/1M out ≈ $0.000019/ký tự;
    # Vbee ≈ $0.0000025/ký tự. edge-tts + vieneu (clone LOCAL) = FREE ($0). Hệ số theo engine → trần
    # ngân sách job KHÔNG undershoot khi bật Gemini, KHÔNG tính dư khi dùng engine miễn phí.
    _eng = (settings.longform_tts_engine or "vbee").strip().lower()
    _tts_rate = 0.0 if _eng in ("edge", "vieneu") else (0.0000190 if _eng == "gemini" else 0.0000025)
    tts_usd = round(max(0, total_chars) * _tts_rate, 4)
    other_usd = 0.02
    # critic = vài LLM text call/vòng (content+fact+regenerate). Gemini rẻ (~$0.0006/vòng), Groq ~free.
    # Đập vào llm_daily_budget, KHÔNG phải ledger video — cộng vào estimate cho minh bạch.
    critic_usd = 0.0
    if settings.longform_critic_enabled:
        critic_usd = round(max(1, int(settings.longform_critic_max_rounds or 1)) * 0.0006, 4)
    video_usd = 0.0
    if hero_i2v and hero_seconds > 0:
        try:
            from video_engine.providers.routing import route_video
            r = route_video("premium", "final", "720p")
            video_usd = round(hero_seconds * r.usd_per_second, 4)
        except Exception:  # noqa: BLE001
            video_usd = 0.0
    total = round(image_usd + tts_usd + other_usd + critic_usd + video_usd + planner_usd, 4)
    return {"total_usd": max(total, 0.01), "n_beats": n_beats, "image_usd": image_usd,
            "tts_usd": tts_usd, "critic_usd": critic_usd, "video_usd": video_usd,
            "planner_usd": planner_usd, "visual_mode": visual_mode}


def _fit_budget_mode(visual_mode: str, est: dict, n_guess: int, chars_guess: int,
                     params: dict, remaining: float | None) -> tuple[str, dict]:
    """P5 budget-guard: nếu ước tính VƯỢT ngân sách CÒN LẠI mà chế độ hình đang đắt → TỰ HẠ sang
    photo_meme ($0 ảnh) cho vừa (thay vì xếp hàng/đốt vượt). Trả (visual_mode, est) có thể đã hạ.
    remaining=None (không đọc được sổ) → giữ nguyên (reserve sẽ tự chặn nếu vượt)."""
    if remaining is None or est["total_usd"] <= remaining or visual_mode == "photo_meme":
        return visual_mode, est
    cheap = estimate_long_narrative_cost(
        n_guess, chars_guess, hero_i2v=bool(params.get("hero_i2v")),
        hero_seconds=float(params.get("hero_seconds") or 0.0), visual_mode="photo_meme",
    )
    if cheap["total_usd"] <= remaining:
        logger.warning(
            f"[long_narrative] budget thấp (còn ${remaining:.2f} < ước ${est['total_usd']:.2f}) "
            f"→ TỰ HẠ chế độ hình {visual_mode}→photo_meme (${cheap['total_usd']:.2f})"
        )
        return "photo_meme", cheap
    return visual_mode, est


def _critic_note(n_beats: int, verdict: dict) -> str:
    if not verdict.get("enabled"):
        return f"{n_beats} beat (critic off)"
    return (
        f"{n_beats} beat · critic {verdict.get('rounds', 1)}x · score={verdict.get('score')} · "
        f"fact={'ok' if verdict.get('fact_ok', True) else 'WARN'}"
    )


def _expected_overlay_texts(script) -> list[str]:
    """Mọi chữ ta CHỦ ĐỘNG burn-in (render.py): watermark kênh + label + callout + lời đọc (cuộn
    thành caption ở CAPTION_Y). text_scan dùng danh sách này: `garbled` bắt font hỏng/mất dấu tiếng
    Việt (giá trị chính — long_narrative đăng CÔNG KHAI), `unexpected` chỉ kêu khi có chữ NGOÀI các
    nguồn này (long_narrative KHÔNG có Seedance vẽ chữ lạ nên gần như không kêu — chấp nhận)."""
    from video_engine.long_narrative.render import CHANNEL_WATERMARK
    raw = [CHANNEL_WATERMARK]
    for b in script.beats:
        raw.extend([b.label, b.callout, b.narration_text])
    seen: set[str] = set()
    uniq: list[str] = []
    for t in raw:
        t = (t or "").strip()
        if t and t not in seen:
            seen.add(t)
            uniq.append(t)
    return uniq


def _build_script(job_id: int, params: dict, stage_start, stage_end):
    """Lấy LongformScript + chạy CRITIC (content+fact+structural) TRƯỚC render. Trả (script, verdict)."""
    from video_engine.long_narrative import critic as critic_mod
    from video_engine.long_narrative.script_schema import LongformScript

    beats = params.get("beats")
    if beats:
        # Kịch bản có sẵn → KHÔNG regenerate (Director không tạo), nhưng VẪN chấm fact + structural (gắn cờ).
        script = LongformScript.from_obj({
            "title": params.get("title") or params.get("topic") or "",
            "category": params.get("category") or "",
            "beats": beats,
        })
        stage_start(job_id, "WRITING")
        _, verdict = critic_mod.critique_and_improve(
            script, params.get("topic") or params.get("title") or "",
            source_text=params.get("source_text") or "", regenerate=None,
        )
        stage_end(job_id, "WRITING", "done", note=_critic_note(len(script.beats), verdict))
        return script, verdict

    topic = (params.get("topic") or params.get("source_url") or "").strip()
    if not topic:
        raise ValueError("long_narrative: thiếu 'beats' và thiếu 'topic'/'source_url'.")
    from video_engine.long_narrative.director import generate_script
    from video_engine.long_narrative.ingest import gather_source

    visual_mode = params.get("visual_mode") or _default_visual_mode()
    stage_start(job_id, "INGESTING")
    src = gather_source(params.get("source_url") or topic, params.get("category", ""))
    stage_end(job_id, "INGESTING", "done", note=src.get("mode", ""))
    source_text = src.get("article") or src.get("context", "")
    # URL nguồn (cho og:image ở mode photo_meme) — lưu vào script.meta, tránh nhồi URL vào từng Beat.
    source_urls = [h.get("link", "") for h in (src.get("headlines") or []) if h.get("link")]
    if params.get("source_url"):
        source_urls.insert(0, str(params["source_url"]).strip())
    category = params.get("category", "")
    n = int(params.get("n_beats") or 8)

    stage_start(job_id, "WRITING")
    script = generate_script(topic, category, source_text=source_text, n_beats=n, visual_mode=visual_mode)
    if not script or not script.beats:
        stage_end(job_id, "WRITING", "fail")
        raise ValueError("Director không sinh được kịch bản (LLM lỗi/thiếu key).")
    script.meta["source_urls"] = source_urls

    # CRITIC loop: viết lại theo gợi ý (regenerate = gọi lại Director với feedback). Giữ bản điểm cao nhất.
    def _regen(hints: list[str]):
        return generate_script(
            topic, category, source_text=source_text, n_beats=n, visual_mode=visual_mode,
            feedback="\n".join(f"- {h}" for h in hints),
        )

    script, verdict = critic_mod.critique_and_improve(script, topic, source_text, regenerate=_regen)
    stage_end(job_id, "WRITING", "done", note=_critic_note(len(script.beats), verdict))
    return script, verdict


def render_long_narrative(job_id: int, snapshot: dict, job_dir: str) -> None:
    """Chạy trọn pipeline long-form cho 1 job. Tự ghi terminal status (run_job đã return sau gọi)."""
    from video_engine.pipeline import (
        _merge_params, _set_status, _stage_end, _stage_start, _update_job,
    )
    from video_engine.long_narrative import render as render_mod

    params = snapshot.get("params") or {}
    visual_mode = params.get("visual_mode") or _default_visual_mode()
    # ước tính TRƯỚC reserve: theo beats nếu có, không thì theo n_beats khai báo (Director chưa chạy).
    beats = params.get("beats")
    if beats:
        n_guess = len(beats)
        chars_guess = sum(
            len(blk.get("text", "")) for b in beats for blk in (b.get("narration_blocks") or [])
        ) or len(beats) * 600
    else:
        n_guess = max(3, min(21, int(params.get("n_beats") or 8)))
        chars_guess = n_guess * 700
    est = estimate_long_narrative_cost(
        n_guess, chars_guess,
        hero_i2v=bool(params.get("hero_i2v")), hero_seconds=float(params.get("hero_seconds") or 0.0),
        visual_mode=visual_mode,
    )
    # P5 budget-guard: ngân sách còn lại < ước tính + chế độ hình đắt → tự hạ photo_meme cho vừa.
    try:
        _snap = ledger_snapshot()
        _remaining = max(0.0, float(_snap.get("budget_usd", 0)) - float(_snap.get("spent_usd", 0)))
    except Exception:  # noqa: BLE001 — đọc sổ hỏng → bỏ qua, reserve tự chặn nếu vượt
        _remaining = None
    visual_mode, est = _fit_budget_mode(visual_mode, est, n_guess, chars_guess, params, _remaining)
    try:
        reserved, day = reserve_video_budget(est["total_usd"])
    except VideoBudgetError as exc:
        _set_status(job_id, VideoJobStatus.QUEUED_BUDGET, error=str(exc))
        return

    actual = 0.0
    try:
        _set_status(job_id, VideoJobStatus.RUNNING, error="")
        _update_job(
            job_id, provider_video="long_narrative", provider_image=settings.image_provider,
            resolution="1080p", model_id="long_narrative",
            estimated_cost_usd=est["total_usd"], max_cost_usd=round(est["total_usd"] * 1.5, 4),
        )
        script, critic_verdict = _build_script(job_id, params, _stage_start, _stage_end)
        n_beats = len(script.beats)
        # Fact-critic STRICT (opt-in): phát hiện bịa RÕ → FAIL job trước khi đốt tiền render.
        if critic_verdict.get("fact_fail_hard"):
            mism = critic_verdict.get("fact_mismatches") or []
            why = "; ".join(m.get("claim", "") for m in mism)[:200]
            raise ValueError(f"Fact-critic STRICT: kịch bản có dữ kiện sai so với nguồn → {why}")

        _stage_start(job_id, "RENDERING_VIDEO")
        script.meta["visual_mode"] = visual_mode   # render đọc từ script.meta (xuyên render_script→beat)
        out_path = os.path.join(job_dir, "final.mp4")
        result = render_mod.render_script(script, os.path.join(job_dir, "beats"), out_path)
        # bản 9:16 cho TikTok/Shorts (blur-pad, ~55s đầu) — fail-soft.
        shorts_path = render_mod.make_shorts_9x16(out_path, os.path.join(job_dir, "shorts_9x16.mp4"))
        _stage_end(job_id, "RENDERING_VIDEO", "done", note=f"~{result['duration']:.0f}s · {n_beats} beat")
        actual = est["total_usd"]  # local pipeline: chi phí ≈ reserve (ảnh thật + TTS), KHÔNG Seedance

        _stage_start(job_id, "QA")
        qa = qa_final_video(
            final_path=out_path, expected_seconds=result["duration"],
            aspect="16:9", check_product_match=False,
            expected_texts=_expected_overlay_texts(script), narration=script.full_narration,
            expect_cta=True,   # tái kiểm CTA đã thực sự đọc ở đuôi video (bắt beat CTA rớt/cụt)
        )
        passed = bool(qa.get("passed"))
        _stage_end(job_id, "QA", "done" if passed else "warn",
                   note=("OK" if passed else "; ".join(qa.get("reasons") or [])[:200]))

        _update_job(job_id, final_path=out_path, actual_cost_usd=round(actual, 4))
        _merge_params(job_id, {
            "final_path": out_path, "duration_s": round(result["duration"], 1),
            "qa_passed": passed, "n_beats": n_beats, "aspect": "16:9",
            "shorts_path": shorts_path or "",
            "title": script.title, "seo": script.meta.get("seo", {}),
            "qa_reasons": (qa.get("reasons") or [])[:5],
            "critic": critic_verdict,
        })
        _set_status(job_id, VideoJobStatus.READY, error="")
        logger.info(f"[long_narrative] job={job_id} READY · {n_beats} beat · "
                    f"~{result['duration']:.0f}s · ${actual:.3f}")
    except Exception as exc:  # noqa: BLE001
        logger.exception(f"[long_narrative] job={job_id} THẤT BẠI")
        _update_job(job_id, actual_cost_usd=round(actual, 4))
        _set_status(job_id, VideoJobStatus.FAILED, error=safe_error_detail(exc, limit=500))
    finally:
        settle_video_budget(reserved, actual, day=day)
