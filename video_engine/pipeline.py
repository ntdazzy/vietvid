"""Pipeline 1 job: DIRECTING → IMAGING(+match gate) → RENDERING_VIDEO → VOICING
→ COMPOSING → QA → READY. Mỗi stage ghi timing/cost/asset vào DB để web đọc trực tiếp.

Luật tiền: reserve ngân sách TRƯỚC (ước tính), settle SAU theo chi phí thật.
Luật retry: ảnh được regenerate ≤2 lần tại CỔNG MATCH (rẻ); video strict retry 1 lần,
video less-restriction reject là FINAL → QA_FAIL (không đốt thêm tiền).
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone

import httpx
from sqlalchemy import select

from config.settings import settings
from core.config_gate import video_engine_config_ready
from core.database import db
from core.logger import logger
from core.models import KolCharacter, Product, ShotPlan, VideoJob, VideoJobStatus, VideoStageAsset
from core.redaction import safe_error_detail
from video_engine import director as director_mod
from video_engine.compose import compose_final
from video_engine.formats import get_format
from video_engine.image_stage import build_image_provider
from video_engine.providers.base import (
    ProviderNotConfiguredError,
    ProviderRejectedError,
    VideoBudgetError,
    VideoEngineError,
)
from video_engine.providers.ledger import reserve_video_budget, settle_video_budget
from video_engine.providers.routing import estimate_job_cost, route_video
from video_engine.qa import qa_final_video, qa_image_match
from video_engine.video_stage import build_video_provider
from video_engine.voice import synthesize_narration_segmented

_MAX_IMAGE_RETRIES = 2


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def run_job(job_id: int) -> None:
    """Chạy toàn pipeline cho 1 job. Mọi kết cục đều được ghi status rõ vào DB."""
    snapshot = _load_snapshot(job_id)
    if snapshot is None:
        return
    job_dir = os.path.join(settings.video_engine_output_dir, f"job_{job_id}")
    os.makedirs(job_dir, exist_ok=True)

    # Long-form (mode="long_narrative"): rẽ nhánh TRƯỚC config-gate VÀ trước reserve. Gate kiểm
    # Seedance/PIAPI — thứ long-form KHÔNG dùng (chỉ ảnh Gemini + TTS + ASR) → để gate chặn = WAITING_CONFIG
    # OAN. Long-form có fail-soft riêng (thiếu Gemini/Vbee → FAILED rõ). Estimator riêng (KHÔNG Seedance/giây).
    if snapshot["mode"] == "long_narrative":
        from video_engine.long_narrative.runner import render_long_narrative

        render_long_narrative(job_id, snapshot, job_dir)
        return

    # Review phim (mode="film_recap"): rẽ nhánh TRƯỚC config-gate — chỉ dùng yt-dlp + ASR + ffmpeg,
    # KHÔNG Seedance/PIAPI (gate sẽ chặn OAN = WAITING_CONFIG). Reserve + fail-soft riêng trong handler.
    if snapshot["mode"] == "film_recap":
        from video_engine.film_recap.runner import render_film_recap

        render_film_recap(job_id, snapshot, job_dir)
        return

    gate = video_engine_config_ready()
    if not gate.ready:
        _set_status(job_id, VideoJobStatus.WAITING_CONFIG, error=gate.reason_text())
        return

    estimate = estimate_job_cost(
        snapshot["mode"], snapshot["purpose"], snapshot["seconds"], snapshot["resolution"]
    )
    try:
        reserved, budget_day = reserve_video_budget(estimate["total_usd"])
    except VideoBudgetError as exc:
        _set_status(job_id, VideoJobStatus.QUEUED_BUDGET, error=str(exc))
        return

    actual_cost = 0.0
    try:
        _set_status(job_id, VideoJobStatus.RUNNING, error="")
        route = route_video(snapshot["mode"], snapshot["purpose"], snapshot["resolution"])
        _update_job(
            job_id,
            model_id=route.model_id,
            resolution=route.resolution,
            speed_tier=route.speed_tier,
            moderation_policy=route.moderation_policy,
            provider_video=route.provider,
            provider_image=settings.image_provider,
            estimated_cost_usd=estimate["total_usd"],
            max_cost_usd=estimate["total_usd"] * 1.5,
        )

        # V8.6: ẢNH SẠCH (clean-plate) tính TRƯỚC DIRECTING → describe_product tả ẢNH SẠCH (1 sản phẩm),
        # KHÔNG phải ảnh marketing/collage → video_prompt focus, không nhiễm "3 wash + banner MIAA".
        product_image = _ensure_product_image(snapshot["product"], job_dir)
        public_url = (snapshot["product"].get("image_url") or "").strip()
        clean_result = None
        if (
            snapshot["mode"] != "premium"
            and settings.video_clean_plate_enabled
            and snapshot["purpose"] != "draft"
        ):
            from video_engine.image_stage.clean_plate import generate_clean_plate

            clean_result = generate_clean_plate(
                product=snapshot["product"], product_image=product_image,
                product_desc="", out_dir=job_dir,
                aspect="9:16",
            )
            actual_cost += clean_result.cost
        describe_image = (
            clean_result.path if (clean_result and clean_result.passed) else product_image
        )

        # 1) DIRECTING ──────────────────────────────────────────────────
        _stage_start(job_id, "DIRECTING")
        # B3: bóc mô tả sản phẩm siêu chi tiết (Gemini Vision) trên ẢNH SẠCH → giữ logo/nhãn đúng (autovis).
        from video_engine.analyzer.product_describe import describe_product

        product_desc = describe_product(
            image_path=describe_image,
            product_name=snapshot["product"].get("name", ""),
        )
        # B7: nếu có video mẫu → Gemini bóc "công thức viral" để Director remake theo
        ref_breakdown = ""
        ref_url = (snapshot["params"].get("video_ref_url") or "").strip()
        if ref_url:
            from video_engine.analyzer.video_understand import (
                analyze_reference_video,
                format_breakdown_for_prompt,
            )
            ref_breakdown = format_breakdown_for_prompt(analyze_reference_video(ref_url))
        # Bối cảnh (KOL Studio): nhúng scene prompt vào brief để Director dựng đúng bối cảnh
        user_brief = snapshot["params"].get("brief", "")
        # V8.6: khoá narration đã duyệt — video_prompt phải minh hoạ ĐÚNG mạch lời này (lời ép sau critic loop).
        _narr_override = (snapshot["params"].get("narration_override") or "").strip()
        if _narr_override:
            user_brief = (
                user_brief
                + " | LỜI ĐỌC ĐÃ CHỐT (video_prompt phải minh hoạ ĐÚNG mạch lời này, từng cảnh khớp "
                f"câu, KHÔNG đổi lời): {_narr_override}"
            ).strip()
        scene_key = (snapshot["params"].get("scene_key") or "").strip()
        if scene_key:
            from core.models import ScenePreset
            with db.transaction() as s:
                sp = s.get(ScenePreset, scene_key)
                if sp and sp.image_prompt:
                    user_brief = (user_brief + " | Bối cảnh: " + sp.image_prompt[:400]).strip()
        product_facts = _build_product_facts(snapshot["product"])
        # V8.5: template đã chọn (template_id) → CẤU TRÚC tham chiếu cho Strategist (học nhịp, KHÔNG copy nội dung).
        structure_reference = ""
        template_id = snapshot["params"].get("template_id")
        if template_id:
            from core.models import PromptTemplate

            with db.transaction() as s:
                tpl = s.get(PromptTemplate, int(template_id))
                if tpl is not None:
                    structure_reference = tpl.prompt_vi or tpl.prompt_en or ""
        # V8.6: nối Formula Bank (gồm trend Bậc 3 đã duyệt) vào LUỒNG THẬT. Trước đây formula chỉ
        # dùng khi KHÔNG có brief → Strategist bật mặc định ⇒ trend gần như vô dụng. Nay: user CHƯA
        # chọn template → lấy 1 công thức (ưu tiên trend thắng) làm structure_reference cho Strategist
        # → brief học nhịp/cấu trúc trend. Chọn 1 LẦN, tái dùng (pick_formulas tự đếm uses cho
        # explore/exploit); chỉ chọn khi công thức THỰC SỰ được dùng (để credit_formula_wins đúng).
        from video_engine.director.formula_bank import format_for_prompt, pick_formulas

        picked_formulas: list = []
        if not structure_reference:
            picked_formulas = pick_formulas(
                snapshot.get("format_key", ""),
                snapshot["product"].get("category", ""),
                snapshot["product"].get("name", ""),
            )
            if picked_formulas:
                # Ưu tiên công thức TREND (founder duyệt) làm cấu trúc tham chiếu; không có thì lấy top.
                ref = next(
                    (f for f in picked_formulas if str(f.source or "").startswith("trend_")),
                    picked_formulas[0],
                )
                structure_reference = ref.prompt_vi or ref.prompt_en or ""
        # V8.5: Affiliate Strategist — phân tích SP + chọn góc thuyết phục + beat-plan (xương sống kịch bản).
        from video_engine.director.strategist import build_creative_brief

        creative_brief = build_creative_brief(
            product=snapshot["product"],
            product_description=product_desc,
            product_facts=product_facts,
            format_label=snapshot["format_label"],
            structure_reference=structure_reference,
            seconds=snapshot["seconds"],
        )
        if creative_brief:
            _merge_params(job_id, {"angle": creative_brief.get("angle", "")})
        # Few-shot raw chỉ khi KHÔNG có brief; chưa chọn (vì user đã chọn template) → chọn giờ.
        formula_block = ""
        if not creative_brief:
            if not picked_formulas:
                picked_formulas = pick_formulas(
                    snapshot.get("format_key", ""),
                    snapshot["product"].get("category", ""),
                    snapshot["product"].get("name", ""),
                )
            formula_block = format_for_prompt(picked_formulas)
        if picked_formulas:
            _merge_params(job_id, {"formula_key": ",".join(f.key for f in picked_formulas)})
        voice_gender = (
            snapshot["params"].get("voice_gender")
            or (snapshot["kol"] or {}).get("gender", "")
        )
        # 2026-06-11: native → KOL nói (Seedance tự đọc + lip-sync); vbee → KOL IM (clip không
        # giọng, vbee ghép riêng — tránh chồng giọng + lệch môi vì Seedance đọc tiếng Việt lơ lớ).
        kol_speaks = _use_native_audio(snapshot)
        # V8.5: vòng review→viết-lại ĐA CHIỀU ≤ N (critic chấm score + product_fit → hint → viết lại;
        # giữ bản TỐT NHẤT). Fail-open: critic lỗi không nghẽn job tay.
        from video_engine.director.critic import review_shot_plan

        rounds = max(1, min(4, int(settings.director_review_max_rounds or 1)))  # cap 4 — chặn đốt LLM
        threshold = float(settings.director_critic_threshold or 7.0)
        min_fit = float(settings.director_review_min_product_fit or 0.0)
        # Clip THÔ: chỉ cần video_prompt cho i2v; Critic chỉ chấm lời thoại/CTA — thứ clip thô VỨT đi
        # → bỏ gọi Critic (tiết kiệm 1 call LLM/clip trên đường mặc định). 1 vòng write là đủ.
        _clean = bool(snapshot["params"].get("clean_clip"))
        best_plan = best_verdict = None
        hints = ""
        for attempt in range(1, rounds + 1):
            brief_in = (
                user_brief
                if not hints
                else (user_brief + f"\nKHẮC PHỤC điểm yếu critic đã chỉ: {hints}").strip()
            )
            plan = director_mod.write_shot_plan(
                product=snapshot["product"],
                format_label=snapshot["format_label"],
                format_system_prompt=snapshot["format_prompt"],
                mode=snapshot["mode"],
                seconds=snapshot["seconds"],
                kol=snapshot["kol"],
                user_brief=brief_in,
                product_description=product_desc,
                aspect="9:16",
                reference_breakdown=ref_breakdown,
                formula_block=formula_block,
                overlay_policy=snapshot.get("overlay_policy", "allow"),
                product_facts=product_facts,
                voice_gender=voice_gender,
                kol_speaks=kol_speaks,
                creative_brief=creative_brief,
            )
            verdict = {} if _clean else review_shot_plan(
                plan, product_facts, product=snapshot["product"],
                format_label=snapshot["format_label"],
            )
            # Giữ bản TỐT NHẤT: điểm THẬT luôn thắng bản fail-open (score None) để không che mất
            # bản yếu thật (autopilot cần thấy điểm yếu mà skip). Cùng dạng → so _plan_rank.
            new_scored = verdict.get("score") is not None
            best_scored = best_verdict is not None and best_verdict.get("score") is not None
            if (
                best_verdict is None
                or (new_scored and not best_scored)
                or (
                    new_scored == best_scored
                    and _plan_rank(verdict, min_fit) >= _plan_rank(best_verdict, min_fit)
                )
            ):
                best_plan, best_verdict = plan, verdict
            score = verdict.get("score")
            fit = verdict.get("product_fit")
            ok_score = score is None or score >= threshold
            ok_fit = fit is None or fit >= min_fit
            if ok_score and ok_fit:
                break
            hints = "; ".join(verdict.get("rewrite_hints") or verdict.get("weaknesses") or [])
            if attempt < rounds:
                logger.info(
                    f"[pipeline] job={job_id} review vòng {attempt}/{rounds} "
                    f"score={score} fit={fit} → Director viết lại (hints: {hints[:120]})"
                )
        plan, verdict = best_plan, best_verdict
        # V8.6: khoá narration — dùng ĐÚNG Y lời founder đã chốt (bỏ qua narration Director tự sinh).
        if _narr_override and plan is not None:
            plan["narration"] = _narr_override
        # User tự nhập/sửa PROMPT Seedance ở màn TikTok → dùng Y NGUYÊN (bỏ video_prompt Director sinh).
        # i2v vẫn lấy ảnh SP làm khung đầu; prompt này điều khiển chuyển động/bối cảnh ("tạo lại từ prompt").
        _vp_override = (snapshot["params"].get("video_prompt") or "").strip()
        if _vp_override and plan is not None:
            plan["video_prompt"] = _vp_override
        # Bản cuối quá yếu HOẶC lệch sản phẩm rõ (product_fit 0-3 = nói sai/lẫn SP khác) → autopilot
        # skip (không đốt $ render); job tay vẫn render kèm cảnh báo.
        score2 = verdict.get("score") if verdict else None
        fit2 = verdict.get("product_fit") if verdict else None
        weak = score2 is not None and score2 < 5
        leaked = fit2 is not None and fit2 < 4
        if weak or leaked:
            reason = (
                f"critic score={score2}/10" if weak else f"product_fit={fit2}/10 (lệch sản phẩm)"
            )
            if snapshot["params"].get("source") == "autopilot":
                from video_engine.autopilot import _mark_skip

                _mark_skip(snapshot["product"]["id"], reason)
                raise VideoEngineError(
                    f"SCRIPT_WEAK: {reason} sau {rounds} vòng — autopilot không render"
                )
            _merge_params(job_id, {"script_warning": f"{reason} sau {rounds} vòng"})
        _save_shot_plan(job_id, plan, critic=verdict)
        critic_note = (
            f"critic={verdict['score']:.1f}" if verdict.get("score") is not None
            else "critic fail-open"
        )
        _stage_end(job_id, "DIRECTING", "ok", note=critic_note)

        # 2) IMAGING — dùng ẢNH SẠCH đã tính trước DIRECTING (clean_result) làm khung đầu i2v.
        _stage_start(job_id, "IMAGING")
        hero_image = ""  # ảnh SẠCH (pixel gốc) cho beat khoe SP Ken Burns (Phase 2) — set khi clean-plate đạt
        if snapshot["mode"] != "premium":
            # Ảnh sản phẩm làm khung đầu; người (KOL) tả bằng TEXT trong prompt (né deepfake PiAPI).
            start_frame = public_url if public_url.startswith("https://") else product_image
            note = "ảnh sản phẩm gốc làm khung đầu; người tả bằng prompt"
            if clean_result is not None:
                _add_stage_asset(
                    job_id, "image", clean_result.path, f"clean_plate:{clean_result.method}",
                    clean_result.cost,
                    qa_report=(clean_result.reports[-1] if clean_result.reports else None),
                )
                if clean_result.passed:
                    start_frame = clean_result.path
                    if clean_result.method != "mock":
                        hero_image = clean_result.path  # ảnh sạch local → beat khoe SP (Phase 2)
                    note = f"ảnh sạch ({clean_result.method}) giữ pixel gốc làm khung đầu"
                else:
                    note = "clean-plate fail-soft → ảnh sản phẩm gốc làm khung đầu"
            _stage_end(job_id, "IMAGING", "ok", note=note)
        else:
            # premium: sinh 1 ảnh hero Gemini (bố cục đẹp hơn) — vẫn KHÔNG ghép mặt người.
            # (clean-plate chỉ cho non-premium; premium dùng _generate_gated_image riêng.)
            start_frame, image_cost = _generate_gated_image(
                job_id, snapshot, plan, product_image, job_dir
            )
            actual_cost += image_cost
            _stage_end(job_id, "IMAGING", "ok")

        # Clip KHÔNG LỜI mà nhạc-là-tiếng-chính (KHÔNG phải clip thô) → BẮT BUỘC có nhạc, kiểm TRƯỚC
        # render để không đốt $ ra clip CÂM. CLIP THÔ thì KHÔNG cần nhạc: ra clip raw im lặng (user tự
        # ghép nhạc / dùng tiếng Seedance) — không chặn render vì thiếu nhạc.
        if (bool(snapshot["params"].get("voiceover_off"))
                and not bool(snapshot["params"].get("clean_clip"))
                and not _resolve_user_music(job_id, snapshot)):
            raise VideoEngineError(
                "Clip nhạc-nền (không lời) nhưng không tìm được nhạc khả dụng (music_audio_path không "
                "hợp lệ và BG_MUSIC_DIR rỗng/thiếu) — cấu hình nhạc, hoặc chọn 'Clip thô' để khỏi cần nhạc."
            )

        # 3) RENDERING_VIDEO ────────────────────────────────────────────
        _stage_start(job_id, "RENDERING_VIDEO")
        clip_path = os.path.join(job_dir, "clip.mp4")
        # Seedance i2v lấy TỈ LỆ video theo ẢNH khung đầu (bỏ qua aspect_ratio) → ảnh SP gần vuông
        # cho video 1:1/3:4 dù xin 9:16. Đệm ảnh LOCAL về đúng khung để video ra đúng dọc/ngang.
        if start_frame:
            from core.image_normalize import pad_image_to_aspect

            # D2 (job 53: clip ra 960×960): khi khung đầu là URL https (clean-plate off/fail),
            # KHÔNG đệm được (pad cần file local) → Seedance lấy tỉ lệ ảnh gần-vuông → clip vuông.
            # Dùng bản LOCAL (product_image đã tải sẵn từ URL) để đệm; ảnh 720×1280 nhỏ → Seedance
            # base64-embed (né lỗi upload-403). Pad luôn áp cho 9:16/16:9 → clip luôn đúng dọc/ngang.
            local_frame = start_frame if not start_frame.startswith("http") else product_image
            if local_frame and os.path.exists(local_frame):
                start_frame = pad_image_to_aspect(
                    local_frame, job_dir, aspect_w=9, aspect_h=16, short_edge=720, stem="start_frame_padded"
                )
        video_provider = build_video_provider()
        video_kwargs = dict(
            prompt=plan["video_prompt"],
            out_path=clip_path,
            seconds=snapshot["seconds"],
            aspect="9:16",
            resolution=route.resolution,
            model_id=route.model_id,
            image_paths=[start_frame] if start_frame else None,
            # Lưu task_id NGAY khi tạo → job fail giữa chừng vẫn resume được, không trả tiền 2 lần.
            on_created=lambda tid: _merge_params(job_id, {"piapi_task_id": tid}),
            resume_task_id=snapshot["params"].get("piapi_task_id", ""),
        )
        try:
            video_provider.generate(**video_kwargs)
        except ProviderRejectedError as exc:
            if exc.final or not route.retry_allowed:
                raise
            logger.warning(f"[pipeline] job={job_id} video bị reject (strict) → retry 1 lần")
            video_provider.generate(**video_kwargs)
        video_cost = round(snapshot["seconds"] * route.usd_per_second, 4)
        if video_provider.name != "mock":
            actual_cost += video_cost
        _add_stage_asset(job_id, "video", clip_path, video_provider.name, video_cost)
        _stage_end(job_id, "RENDERING_VIDEO", "ok")

        # V8.6: beat 'khoe SP' = ảnh SẠCH (pixel gốc) + Ken Burns prepend đầu video (KHÔNG i2v →
        # giữ 100% SP), xfade vào clip lifestyle. Chỉ voiceover (native giữ audio Seedance → bỏ).
        # Fail-soft: dựng hero lỗi → clip gốc. Lưu video asset (raw clip) TRƯỚC → recompose dùng clip raw.
        hero_extra = 0.0
        hero_s = int(settings.video_product_hero_seconds or 0)
        # Clip THÔ = video thật nguyên bản, KHÔNG chèn ảnh product-hero ở đầu.
        if bool(snapshot["params"].get("clean_clip")):
            hero_s = 0
        if hero_s > 0 and snapshot["purpose"] == "final" and hero_image and not _use_native_audio(snapshot):
            from video_engine.compose.product_hero import prepend_product_hero

            combined = prepend_product_hero(
                clip_path=clip_path, clean_image=hero_image, seconds=hero_s,
                out_path=os.path.join(job_dir, "clip_hero.mp4"),
            )
            if combined:
                clip_path = combined
                hero_extra = hero_s - 0.4
                logger.info(
                    f"[pipeline] job={job_id} prepend product-hero {hero_s}s "
                    f"(Ken Burns ảnh sạch, +{hero_extra:.1f}s)"
                )

        # 4-6) VOICING → COMPOSING → QA (dùng chung với recompose_job — V8.3-Q6)
        final_path, report, finishing_cost = _finishing_stages(
            job_id, snapshot, plan, clip_path, product_image, job_dir, extra_video_seconds=hero_extra,
            tail_image=(clean_result.path if (clean_result and clean_result.passed) else ""),
        )
        actual_cost += finishing_cost
        if not report["passed"]:
            _update_job(job_id, final_path=final_path, actual_cost_usd=round(actual_cost, 4))
            _set_status(
                job_id, VideoJobStatus.QA_FAIL, error="; ".join(report["reasons"])[:500]
            )
            return

        _update_job(job_id, final_path=final_path, actual_cost_usd=round(actual_cost, 4))
        _set_status(job_id, VideoJobStatus.READY, error="")
        logger.info(
            f"[pipeline] job={job_id} READY · chi phí thật ${actual_cost:.3f} "
            f"(ước tính ${estimate['total_usd']:.3f})"
        )
    except VideoBudgetError as exc:
        _set_status(job_id, VideoJobStatus.QUEUED_BUDGET, error=str(exc))
    except ProviderNotConfiguredError as exc:
        _set_status(job_id, VideoJobStatus.WAITING_CONFIG, error=str(exc))
    except ProviderRejectedError as exc:
        _update_job(job_id, actual_cost_usd=round(actual_cost, 4))
        _set_status(
            job_id,
            VideoJobStatus.QA_FAIL,
            error=f"Provider từ chối nội dung (final={exc.final}): {exc}"[:500],
        )
    except Exception as exc:  # noqa: BLE001 — lỗi kỹ thuật → FAILED, không rơi im lặng
        logger.exception(f"[pipeline] job={job_id} THẤT BẠI")
        _update_job(job_id, actual_cost_usd=round(actual_cost, 4))
        _set_status(job_id, VideoJobStatus.FAILED, error=safe_error_detail(exc, limit=500))
    finally:
        settle_video_budget(reserved, actual_cost, day=budget_day)


# ── stage 4-6 dùng chung (run_job + recompose_job) ────────────────────
def _finishing_stages(
    job_id: int, snapshot: dict, plan: dict, clip_path: str, product_image: str, job_dir: str,
    extra_video_seconds: float = 0.0,  # V8.6: hero Ken Burns prepend (+hero_s−0.4) → QA duration đúng
    tail_image: str = "",  # V8.6: ảnh CTA tail (ưu tiên ảnh SẠCH thay vì collage gốc); "" → product_image
) -> tuple[str, dict, float]:
    """VOICING → COMPOSING → QA. Trả (final_path, qa_report, chi phí phát sinh).

    KHÔNG set status job — caller (run_job / recompose_job) quyết theo report.
    """
    cost = 0.0
    # 4) VOICING — giọng Seedance tiếng Việt lơ lớ (1/10) → TTS đè giọng cho mọi mode.
    _stage_start(job_id, "VOICING")
    voice_path = ""
    voice_delay_s = 0.9  # V8.3-Q3.2: hook = chữ local chiếm 0-0.9s
    voiceover_off = bool(snapshot["params"].get("voiceover_off"))
    clean_clip = bool(snapshot["params"].get("clean_clip"))  # clip THÔ: không chữ + không nhạc (user tự ghép)
    if clean_clip:
        voiceover_off = True  # clip thô luôn = không lời
    use_native = _use_native_audio(snapshot) and not voiceover_off
    if clean_clip:
        _stage_end(job_id, "VOICING", "ok", note="CLIP THÔ — không chữ, không nhạc (user tự ghép nhạc)")
    elif voiceover_off:
        _stage_end(job_id, "VOICING", "ok", note="KHÔNG LỜI — nhạc nền làm tiếng chính (clip music-only)")
    elif not use_native:
        voice_path = os.path.join(job_dir, "voice.wav")
        voice_gender = (
            snapshot["params"].get("voice_gender")
            or (snapshot["kol"] or {}).get("gender", "")
        )
        voice_id = snapshot["params"].get("voice_id") or (snapshot["kol"] or {}).get("voice_id", "")
        if not voice_id:
            # V8.2 Phase 0: chưa chỉ định giọng → kho nam/nữ theo voice_gender/gender KOL.
            from video_engine.voice import pick_voice

            voice_id = pick_voice(
                gender=voice_gender,
                # Seed theo TỪNG VIDEO (job_id) thay vì theo ngành hàng → mỗi video xoay
                # giọng khác nhau khi kho giọng (vbee) có >1 mã, thay vì cả ngành một giọng.
                seed=f"{job_id}-{snapshot['product'].get('category', '')}",
            )
        # V8.3-Q2: gender → gemini_tts chọn giọng nam/nữ. Q2b: TTS từng câu + starts[]
        # → overlay sent=i hiện ĐÚNG lúc giọng đọc câu i (đè t ước lượng của Director).
        _, voice_starts, voice_engine = synthesize_narration_segmented(
            plan["narration"], voice_path,
            voice_id=voice_id, gender=voice_gender, delay_s=voice_delay_s,
        )
        # 2026-06-13 (founder): ẩn kind overlay không muốn vẽ (mặc định 'hook') — giọng VẪN đọc hook.
        hidden = {
            k.strip().lower()
            for k in (settings.video_overlay_hidden_kinds or "").split(",")
            if k.strip()
        }
        if hidden:
            plan["text_overlays"] = [
                ov for ov in (plan.get("text_overlays") or [])
                if (ov.get("kind") or "").strip().lower() not in hidden
            ]
        # 2026-06-13 (founder 'giọng không khớp chữ'): gán mốc overlay theo CÂU giọng THỰC SỰ đọc
        # nội dung (khớp kind/từ khoá) thay vì sent Director đoán (hay lệch). Mutate tại chỗ.
        from video_engine.voice import align_overlay_times

        align_overlay_times(plan["narration"], plan.get("text_overlays") or [], voice_starts)
        # F4a: lưu overlay đã đồng bộ mốc vào ShotPlan (DB/dashboard hiện ĐÚNG giờ thật của video).
        _update_shot_plan_overlays(job_id, plan.get("text_overlays") or [])
        cost += 0.01  # TTS biên
        # Báo cáo ENGINE THẬT (không phải settings.tts_provider): edge = last-resort, giọng kém.
        voice_degraded = voice_engine == "edge"
        if voice_degraded:
            _merge_params(job_id, {"voice_degraded": True, "voice_engine": voice_engine})
            logger.warning(
                f"[pipeline] job={job_id} VOICING degraded → edge (gemini+vbee đều lỗi/hết quota); "
                "giọng monotone — cân nhắc render lại khi engine chính hồi."
            )
        _add_stage_asset(job_id, "voice", voice_path, voice_engine, 0.01)
        _stage_end(
            job_id, "VOICING", "ok",
            note=(
                f"engine={voice_engine} (1-call, giọng nhất quán), {len(voice_starts)} câu"
                + (" ⚠️ FALLBACK EDGE — giọng kém, NÊN kiểm/đăng lại" if voice_degraded else "")
            ),
        )
    else:
        _stage_end(job_id, "VOICING", "ok", note="dùng audio Seedance sinh sẵn (nhạc+SFX)")

    # 5) COMPOSING — V8.3-Q3: đuôi CTA 6s local chỉ bản FINAL chế độ voiceover.
    _stage_start(job_id, "COMPOSING")
    final_path = os.path.join(job_dir, "final.mp4")
    tail_s = int(settings.video_cta_tail_seconds or 0)
    use_tail = tail_s > 0 and snapshot["purpose"] == "final" and not use_native and not voiceover_off
    # KHÔNG LỜI (gồm cả clip THÔ): chọn nhạc làm tiếng chính — nhạc người dùng (đã cắt 20s) hoặc
    # nhạc bản-quyền-sạch theo ngành. Clip THÔ giờ CŨNG có nhạc nền (yêu cầu: clip không chữ/ảnh nhưng CÓ nhạc).
    user_music_path = ""
    if voiceover_off and not clean_clip:  # clip THÔ = raw, KHÔNG nhạc (user tự ghép); chỉ clip music-only mới gắn nhạc
        user_music_path = _resolve_user_music(job_id, snapshot)
        logger.info(f"[pipeline] job={job_id} KHÔNG LỜI → nhạc: {os.path.basename(user_music_path) or '(không có)'}")
    elif clean_clip:
        logger.info(f"[pipeline] job={job_id} CLIP THÔ → không nhạc (raw, im lặng — user tự ghép)")
    cta_tail_spec = None
    if use_tail:
        cta_tail_spec = {
            "product_image": tail_image if (tail_image and os.path.exists(tail_image)) else product_image,
            "price_text": _build_product_facts(snapshot["product"]).get("price", ""),
            "short_name": snapshot["product"].get("name", ""),
        }
    compose_final(
        video_path=clip_path,
        audio_path=voice_path,
        out_path=final_path,
        narration=plan["narration"],
        polish=snapshot["purpose"] != "draft",
        keep_source_audio=use_native,
        # 2026-06-13: voiceover = giọng TTS SẠCH, KHÔNG trộn audio Seedance (audio Seedance
        # không ổn định: lúc nhạc, lúc có vocal/ngân → trộn ra "mấy giọng/khó nghe").
        # Hook đầu (cùng mốc starts[] Q2b) chừa cho chữ hook local; native/không-lời thì không trễ.
        voice_delay_ms=0 if (use_native or voiceover_off) else int(voice_delay_s * 1000),
        # V8.3-Q1: chữ giá/hook/CTA vẽ LOCAL (Seedance bị cấm vẽ chữ trong prompt). Clip THÔ = KHÔNG chữ.
        text_overlays=([] if clean_clip else (plan.get("text_overlays") or [])),
        cta_tail_spec=cta_tail_spec,
        # KHÔNG LỜI: nhạc người dùng/bản-quyền-sạch làm tiếng chính; voiceover thì để trống (tự chọn nền).
        music_path=user_music_path,
        # 2026-06-13: chọn nhạc nền HỢP NGÀNH theo tên SP + category.
        music_hint=f"{snapshot['product'].get('name', '')} {snapshot['product'].get('category', '')}",
    )
    _add_stage_asset(job_id, "compose", final_path, "local_ffmpeg", 0.0)
    _stage_end(job_id, "COMPOSING", "ok", note=f"tail={tail_s}s" if use_tail else "")

    # 6) QA cuối — Q3.5: có tail → thời lượng mong đợi = seconds + tail − 0.4 (xfade).
    _stage_start(job_id, "QA")
    expected_seconds = snapshot["seconds"] + extra_video_seconds + (tail_s - 0.4 if use_tail else 0)
    # Q5(a): danh sách chữ MONG ĐỢI cho text scan = overlay đã vẽ + chữ tail. Clip THÔ không vẽ chữ → rỗng.
    expected_texts = [] if clean_clip else [str(ov.get("text") or "") for ov in plan.get("text_overlays") or []]
    if use_tail and cta_tail_spec:
        expected_texts += [
            cta_tail_spec["short_name"][:42], cta_tail_spec["price_text"], "MUA NGAY"
        ]
    report = qa_final_video(
        final_path=final_path,
        expected_seconds=expected_seconds,
        aspect="9:16",
        product_image=product_image,
        check_product_match=snapshot["purpose"] == "final",
        expected_texts=[t for t in expected_texts if t],
        # Có tail → text scan CHỈ soi clip chính (tail local deterministic + ảnh shop có chữ).
        text_scan_until=float(snapshot["seconds"]) if use_tail else None,
        # V8.4: ASR kiểm giọng — CHỈ voiceover (native/không-lời không có TTS để đối chiếu).
        narration=("" if (use_native or voiceover_off) else (plan.get("narration") or "")),
    )
    _add_stage_asset(job_id, "qa", final_path, "local", 0.0, qa_report=report)
    if not report["passed"]:
        _stage_end(job_id, "QA", "fail", note="; ".join(report["reasons"])[:300])
    else:
        _stage_end(job_id, "QA", "ok")
    return final_path, report, cost


def recompose_job(job_id: int) -> None:
    """V8.3-Q6: RECOMPOSE $0 — chạy lại VOICING→COMPOSING→QA từ clip Seedance ĐÃ LƯU.

    Giọng/chữ/tail đều local → đổi chúng (VBEE_SPEED_RATE, TTS_PROVIDER, tail setting…)
    KHÔNG gọi lại Seedance ($1.21 → ~$0.01 TTS). Clip gốc: video_stage_assets stage="video".
    """
    snapshot = _load_snapshot(job_id)
    if snapshot is None:
        return
    with db.transaction() as session:
        clip_asset = session.scalar(
            select(VideoStageAsset)
            .where(VideoStageAsset.job_id == job_id, VideoStageAsset.stage == "video")
            .order_by(VideoStageAsset.id.desc())
            .limit(1)
        )
        clip_path = clip_asset.path if clip_asset else ""
        plan_row = session.scalar(
            select(ShotPlan).where(ShotPlan.job_id == job_id)
            .order_by(ShotPlan.id.desc()).limit(1)
        )
        plan = None
        if plan_row is not None:
            try:
                overlays = json.loads(plan_row.text_overlays or "[]")
            except ValueError:
                overlays = []
            plan = {
                "narration": plan_row.narration,
                "text_overlays": overlays,
                "video_prompt": plan_row.video_prompt,
                "cta": plan_row.cta,
            }
        prev_cost = 0.0
        job = session.get(VideoJob, job_id)
        if job is not None:
            prev_cost = float(job.actual_cost_usd or 0.0)
    if not clip_path or not os.path.exists(clip_path):
        _set_status(job_id, VideoJobStatus.FAILED,
                    error="recompose: không có clip Seedance gốc (stage=video)")
        return
    if not plan or not (plan.get("narration") or "").strip():
        _set_status(job_id, VideoJobStatus.FAILED, error="recompose: không có shot plan")
        return

    job_dir = os.path.join(settings.video_engine_output_dir, f"job_{job_id}")
    os.makedirs(job_dir, exist_ok=True)
    logger.info(f"[pipeline] job={job_id} RECOMPOSE $0 từ {clip_path}")
    try:
        _set_status(job_id, VideoJobStatus.RUNNING, error="")
        # Clip music-only (không lời, KHÔNG phải clip thô) cần nhạc; CLIP THÔ thì raw im lặng — không chặn.
        if (bool(snapshot["params"].get("voiceover_off"))
                and not bool(snapshot["params"].get("clean_clip"))
                and not _resolve_user_music(job_id, snapshot)):
            _set_status(
                job_id, VideoJobStatus.FAILED,
                error="recompose clip nhạc-nền (không lời) nhưng không có nhạc khả dụng (music_audio_path/BG_MUSIC_DIR).",
            )
            return
        product_image = _ensure_product_image(snapshot["product"], job_dir)
        # V8.6: recompose giữ CTA tail ảnh SẠCH nếu job đã sinh (clean.jpg trong job_dir).
        _clean_tail = os.path.join(job_dir, "clean.jpg")
        final_path, report, cost = _finishing_stages(
            job_id, snapshot, plan, clip_path, product_image, job_dir,
            tail_image=(_clean_tail if os.path.exists(_clean_tail) else ""),
        )
        total = round(prev_cost + cost, 4)
        if not report["passed"]:
            _update_job(job_id, final_path=final_path, actual_cost_usd=total)
            _set_status(job_id, VideoJobStatus.QA_FAIL, error="; ".join(report["reasons"])[:500])
            return
        _update_job(job_id, final_path=final_path, actual_cost_usd=total)
        _set_status(job_id, VideoJobStatus.READY, error="")
        logger.info(f"[pipeline] job={job_id} RECOMPOSE → READY (+${cost:.3f}, KHÔNG gọi PiAPI)")
    except Exception as exc:  # noqa: BLE001 — recompose lỗi → FAILED rõ ràng
        logger.exception(f"[pipeline] job={job_id} RECOMPOSE thất bại")
        _set_status(job_id, VideoJobStatus.FAILED, error=safe_error_detail(exc, limit=500))


# ── stage IMAGING với cổng match ──────────────────────────────────────
def _generate_gated_image(
    job_id: int, snapshot: dict, plan: dict, product_image: str, job_dir: str
) -> tuple[str, float]:
    """Sinh ảnh + QA match, regenerate ≤2 lần. Trả (path ảnh đạt, chi phí ảnh)."""
    provider = build_image_provider()
    refs = [p for p in [product_image, (snapshot["kol"] or {}).get("image_path", "")] if p]
    prompts = plan["image_prompts"] or [plan["video_prompt"]]
    base_prompt = prompts[0]
    cost = 0.0
    last_reasons: list[str] = []
    for attempt in range(1 + _MAX_IMAGE_RETRIES):
        out_path = os.path.join(job_dir, f"image_{attempt}.png")
        prompt = base_prompt
        if attempt and last_reasons:
            prompt += " | FIX STRICTLY: " + "; ".join(last_reasons)[:300]
        generated = provider.generate(prompt=prompt, out_path=out_path, input_image_paths=refs)
        if not generated or not os.path.exists(out_path):
            raise VideoEngineError(f"{provider.name} không sinh được ảnh và Gemini fallback bị tắt.")
        if provider.name == "gemini":
            cost += float(settings.video_image_cost_usd)
        report = qa_image_match(product_image, out_path)
        _add_stage_asset(
            job_id, "image", out_path, provider.name,
            float(settings.video_image_cost_usd) if provider.name == "gemini" else 0.0,
            qa_report=report,
        )
        if report.get("passed"):
            return out_path, round(cost, 4)
        last_reasons = report.get("reasons") or ["ảnh không khớp sản phẩm"]
        logger.warning(
            f"[pipeline] job={job_id} ảnh lần {attempt + 1} FAIL match: {last_reasons}"
        )
    raise ProviderRejectedError(
        "Ảnh KOL/sản phẩm không qua được CỔNG MATCH sau "
        f"{1 + _MAX_IMAGE_RETRIES} lần: {'; '.join(last_reasons)[:300]}",
        final=True,  # không gọi video — tiết kiệm tiền, founder sửa input/prompt
    )


# ── snapshot + DB helpers ─────────────────────────────────────────────
def _load_snapshot(job_id: int) -> dict | None:
    with db.transaction() as session:
        job = session.get(VideoJob, job_id)
        if job is None:
            logger.error(f"[pipeline] job_id={job_id} không tồn tại")
            return None
        product = session.get(Product, job.product_id) if job.product_id else None
        kol = session.get(KolCharacter, job.kol_id) if job.kol_id else None
        try:
            params = json.loads(job.params or "{}")
        except ValueError:
            params = {}
        fmt = get_format(job.format_key) if job.format_key else None
        product_dict = {
            "id": product.id if product else None,
            "name": product.name if product else params.get("product_name", ""),
            "category": product.category if product else "",
            "price": f"{product.price:,.0f} {product.currency}" if product and product.price else "",
            "description": product.description if product else params.get("brief", ""),
            "image_path": product.image_path if product else "",
            "image_paths_json": product.image_paths_json if product else "[]",
            "image_url": product.image_url if product else "",
            # V8.5: proof THẬT cho Strategist/Director (sao + lượt bán) — không bịa.
            "rating": product.rating if product else 0.0,
            "rating_count": product.rating_count if product else 0,
            "sales_volume": product.sales_volume if product else 0.0,
        }
        kol_dict = None
        if kol is not None:
            kol_dict = {
                "id": kol.id,
                "name": kol.name,
                "gender": kol.gender,
                "style": kol.style,
                "character_sheet": kol.character_sheet,
                "image_path": kol.image_path,
                "voice_id": kol.voice_id,
            }
        return {
            "mode": job.mode,
            "purpose": job.purpose,
            "seconds": job.seconds,
            "resolution": job.resolution,
            "params": params,
            "product": product_dict,
            "kol": kol_dict,
            "format_key": job.format_key,
            # V8.2 Phase 3: chính sách chữ trên video theo format (require|allow|forbid).
            "overlay_policy": getattr(fmt, "overlay_policy", "") or "allow" if fmt else "allow",
            "format_label": fmt.label if fmt else job.format_key or "B-roll sản phẩm",
            "format_prompt": (
                fmt.director_system_prompt
                if fmt and fmt.director_system_prompt
                else _fallback_format_prompt()
            ),
        }


def _fallback_format_prompt() -> str:
    from video_engine.formats import DEFAULT_FORMATS

    return DEFAULT_FORMATS[-1]["director_system_prompt"]


def _ensure_product_image(product: dict, job_dir: str) -> str:
    """Ảnh sản phẩm thật (local) — tải từ image_url nếu chưa có file local."""
    try:
        paths = [p for p in json.loads(product.get("image_paths_json") or "[]") if p]
    except ValueError:
        paths = []
    for candidate in [product.get("image_path"), *paths]:
        if candidate and os.path.exists(candidate):
            return candidate
    url = (product.get("image_url") or "").strip()
    if url.startswith("https://"):
        target = os.path.join(job_dir, "product_src.jpg")
        try:
            with httpx.Client(timeout=30.0, follow_redirects=True) as client:
                resp = client.get(url)
                if resp.status_code == 200 and resp.content:
                    with open(target, "wb") as f:
                        f.write(resp.content)
                    return target
        except httpx.HTTPError as exc:
            logger.warning(f"[pipeline] tải ảnh sản phẩm lỗi: {exc}")
    raise VideoEngineError(
        "Sản phẩm không có ảnh local/URL hợp lệ — input gate phải chặn từ đầu."
    )


def _set_status(job_id: int, status: str, *, error: str | None = None) -> None:
    with db.transaction() as session:
        job = session.get(VideoJob, job_id)
        if job is None:
            return
        job.status = status
        if error is not None:
            job.error = error
        timings = _parse_timings(job.stage_timings)
        timings["_last_attempt"] = _now_iso()
        job.stage_timings = json.dumps(timings, ensure_ascii=False)


def _update_job(job_id: int, **fields) -> None:
    with db.transaction() as session:
        job = session.get(VideoJob, job_id)
        if job is None:
            return
        for key, value in fields.items():
            setattr(job, key, value)


def _merge_params(job_id: int, extra: dict) -> None:
    with db.transaction() as session:
        job = session.get(VideoJob, job_id)
        if job is None:
            return
        try:
            params = json.loads(job.params or "{}")
        except ValueError:
            params = {}
        params.update(extra)
        job.params = json.dumps(params, ensure_ascii=False)


def _parse_timings(raw: str) -> dict:
    try:
        data = json.loads(raw or "{}")
        return data if isinstance(data, dict) else {}
    except ValueError:
        return {}


def _stage_start(job_id: int, stage: str) -> None:
    with db.transaction() as session:
        job = session.get(VideoJob, job_id)
        if job is None:
            return
        timings = _parse_timings(job.stage_timings)
        timings[stage] = {"start": _now_iso(), "status": "running"}
        job.stage_timings = json.dumps(timings, ensure_ascii=False)
    logger.info(f"[pipeline] job={job_id} stage={stage} bắt đầu")


def _stage_end(job_id: int, stage: str, status: str, *, note: str = "") -> None:
    with db.transaction() as session:
        job = session.get(VideoJob, job_id)
        if job is None:
            return
        timings = _parse_timings(job.stage_timings)
        entry = timings.get(stage) or {}
        entry.update({"end": _now_iso(), "status": status})
        if note:
            entry["note"] = note
        timings[stage] = entry
        job.stage_timings = json.dumps(timings, ensure_ascii=False)


def _save_shot_plan(job_id: int, plan: dict, critic: dict | None = None) -> None:
    with db.transaction() as session:
        session.add(
            ShotPlan(
                job_id=job_id,
                storyboard=json.dumps(plan.get("storyboard") or [], ensure_ascii=False),
                narration=plan.get("narration") or "",
                image_prompts=json.dumps(plan.get("image_prompts") or [], ensure_ascii=False),
                video_prompt=plan.get("video_prompt") or "",
                cta=plan.get("cta") or "",
                text_overlays=json.dumps(plan.get("text_overlays") or [], ensure_ascii=False),
                critic_score=(critic or {}).get("score"),
                critic_notes=json.dumps(
                    {k: (critic or {}).get(k) for k in ("hook", "pain_benefit", "proof", "cta",
                                                        "natural", "format_adherence", "product_fit",
                                                        "weaknesses", "rewrite_hints")},
                    ensure_ascii=False,
                ) if critic else "",
            )
        )


def _update_shot_plan_overlays(job_id: int, overlays: list[dict]) -> None:
    """F4a (2026-06-13): ghi đè text_overlays của ShotPlan mới nhất SAU khi remap mốc theo giọng.

    Giữ checkpoint _save_shot_plan ở DIRECTING (lưu sớm phòng job fail); chỉ cập nhật mốc t đã
    đồng bộ giọng để dashboard hiện đúng giờ overlay THẬT trong video (trước đây hiện mốc Director đoán).
    """
    with db.transaction() as session:
        sp = session.scalar(
            select(ShotPlan).where(ShotPlan.job_id == job_id).order_by(ShotPlan.id.desc())
        )
        if sp is not None:
            sp.text_overlays = json.dumps(overlays, ensure_ascii=False)


def _use_native_audio(snapshot: dict) -> bool:
    """V8.2: native Seedance hay vbee voice-over — theo VIDEO_AUDIO_MODE.

    2026-06-11 (founder + bằng chứng tai nghe): giọng tiếng Việt native Seedance LƠ LỚ
    (Gemini chấm phát âm 1/10, transcript sai dấu thanh hệ thống) → mode "auto" dùng
    vbee ĐÈ GIỌNG + giữ nhạc/SFX Seedance làm nền (mix) cho MỌI loại video.
    Ép giữ giọng Seedance: VIDEO_AUDIO_MODE=native.
    """
    mode_setting = (settings.video_audio_mode or "auto").strip().lower()
    return mode_setting == "native"


def _path_within(path: str, allowed_dirs: list[str]) -> bool:
    """True nếu ``path`` nằm TRONG một thư mục cho phép (realpath containment) — chặn path traversal:
    music_audio_path do client gửi không được trỏ ra file tuỳ ý ngoài kho nhạc."""
    try:
        rp = os.path.realpath(path)
    except OSError:
        return False
    for d in allowed_dirs:
        d = (d or "").strip()
        if not d:
            continue
        try:
            base = os.path.realpath(d)
            if os.path.commonpath([rp, base]) == base:
                return True
        except (OSError, ValueError):
            continue
    return False


def _resolve_user_music(job_id: int, snapshot: dict) -> str:
    """Nhạc cho clip KHÔNG LỜI (tiếng chính): ưu tiên music_audio_path NGƯỜI DÙNG nhưng CHỈ nhận file
    trong TIKTOK_AUDIO_DIR/BG_MUSIC_DIR (chặn mux file tuỳ ý trên server); không hợp lệ → nhạc
    bản-quyền-sạch hợp ngành (force=True bỏ qua cờ BG_MUSIC_ENABLED). "" = không có nhạc khả dụng."""
    from video_engine.compose import _pick_bg_music

    raw = (snapshot["params"].get("music_audio_path") or "").strip()
    if raw and os.path.exists(raw) and _path_within(
        raw, [settings.tiktok_audio_dir, settings.bg_music_dir]
    ):
        return raw
    return _pick_bg_music(
        seed=f"{job_id}-{snapshot['product'].get('category', '')}",
        hint=f"{snapshot['product'].get('name', '')} {snapshot['product'].get('category', '')}",
        force=True,
    )


def _plan_rank(verdict: dict | None, min_fit: float) -> float:
    """Xếp hạng bản kịch bản để giữ bản TỐT NHẤT qua các vòng: ưu tiên product_fit đạt, rồi score.

    Bản lệch sản phẩm (product_fit < ngưỡng) bị phạt nặng để không thắng bản khớp dù điểm tổng cao.
    """
    if not verdict:
        return -1.0
    score = verdict.get("score")
    base = -1.0 if score is None else float(score)
    fit = verdict.get("product_fit")
    if fit is not None and fit < min_fit:
        base -= 5.0
    return base


def _build_product_facts(product: dict) -> dict:
    """Facts THẬT cho chữ overlay (giá dạng '149K' chống méo chữ 480p) — thiếu thì bỏ trống."""
    facts: dict = {}
    price = product.get("price") or ""
    if price:
        # snapshot price dạng "149,000 VND" → rút số → nhãn ngắn "149K"
        digits = re.sub(r"[^\d]", "", str(price))
        if digits:
            vnd = int(digits)
            if vnd >= 1_000_000:
                label = f"{vnd / 1_000_000:.1f}".rstrip("0").rstrip(".") + "TR"
            elif vnd >= 1_000:
                label = f"{round(vnd / 1000)}K"
            else:
                label = str(vnd)
            facts["price"] = label
    # V8.5: rating/sold THẬT làm proof (chống bịa — prompt được phép trích sao/lượt bán; thiếu thì bỏ trống).
    rating = float(product.get("rating") or 0)
    rating_count = int(product.get("rating_count") or 0)
    if rating > 0 and rating_count > 0:
        facts["rating"] = f"{rating:.1f}"
        facts["rating_count"] = rating_count
    sold = int(product.get("sales_volume") or 0)
    if sold > 0:
        facts["sold"] = sold
    return facts


def _add_stage_asset(
    job_id: int,
    stage: str,
    path: str,
    provider: str,
    cost_usd: float,
    *,
    qa_report: dict | None = None,
) -> None:
    with db.transaction() as session:
        session.add(
            VideoStageAsset(
                job_id=job_id,
                stage=stage,
                path=path,
                provider=provider or "",
                cost_usd=round(float(cost_usd), 4),
                qa_report=json.dumps(qa_report or {}, ensure_ascii=False),
            )
        )
