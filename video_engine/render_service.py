"""render(spec, sink) — entry STATELESS của engine (M0).

Port trung thực `pipeline.run_job` cho luồng review (mode product_ad/premium):
- KHÔNG đọc/ghi DB. Snapshot dựng từ `spec.to_snapshot()`.
- Mọi trạng thái/asset đi qua `sink.*` (NullSink mặc định) thay vì `_set_status(job_id,...)`.
- 3 chỗ run_job đọc DB trong stage → dùng `spec.scene_prompt` / `spec.structure_reference`;
  formula_bank (đọc+ghi DB) TẠM BỎ ở M0 (app_api inject sau).
- Ngân sách ledger (reserve/settle USD/ngày) BỎ — chi phí trả về trong RenderResult; ví ACID
  do app_api (HOLD/SETTLE).

Helper THUẦN (không DB) tái dùng nguyên từ pipeline: _ensure_product_image, _build_product_facts,
_use_native_audio, _resolve_user_music, _plan_rank.

long_narrative / film_recap: hoãn sang M1+ (raise NotImplementedError) — 2 runner đó cũng kéo
helper DB của pipeline, cần tách sink riêng (mục 5.3b plan).
"""

from __future__ import annotations

import os
import tempfile

from config.settings import settings
from core.config_gate import video_engine_config_ready
from core.logger import logger
from core.models import VideoJobStatus
from core.redaction import safe_error_detail
from video_engine import director as director_mod
from video_engine.compose import compose_final
from video_engine.image_stage import build_image_provider
from video_engine.pipeline import (
    _build_product_facts,
    _ensure_product_image,
    _plan_rank,
    _resolve_user_music,
    _use_native_audio,
)
from video_engine.providers.base import (
    ProviderNotConfiguredError,
    ProviderRejectedError,
    VideoBudgetError,
    VideoEngineError,
)
from video_engine.providers.routing import estimate_job_cost, route_video
from video_engine.qa import qa_final_video, qa_image_match
from video_engine.spec import JobSpec, RenderResult
from video_engine.sink import JobSink, NullSink
from video_engine.video_stage import build_video_provider
from video_engine.voice import synthesize_narration_segmented

_MAX_IMAGE_RETRIES = 2


def render(spec: JobSpec, sink: JobSink | None = None) -> RenderResult:
    """Chạy pipeline review cho 1 JobSpec, trả RenderResult. KHÔNG chạm DB."""
    sink = sink or NullSink()
    snapshot = spec.to_snapshot()
    workdir = spec.workdir or tempfile.mkdtemp(prefix=f"vietvid_{spec.job_ref}_")
    os.makedirs(workdir, exist_ok=True)

    if snapshot["mode"] in ("long_narrative", "film_recap"):
        raise NotImplementedError(
            f"mode={snapshot['mode']} chưa tách stateless (M1+); M0 chỉ review (product_ad/premium)."
        )

    is_mock = (settings.video_provider or "").strip().lower() == "mock"

    def _result(status: str, *, path: str = "", error: str = "", cost: float = 0.0,
                plan: dict | None = None, report: dict | None = None, fault: str = "") -> RenderResult:
        return RenderResult(
            status=status, path=path, error=error, cost_usd=round(cost, 4),
            clips_used=sink.clips_used,                  # đọc trực tiếp: sink thiếu → lỗi to (không degrade thầm)
            stage_timings=sink.stage_timings or {},
            shot_plan=plan, qa_report=report,
            resume_task_id=sink.piapi_task_id,
            fault_class=fault,
        )

    # Config-gate kiểm Seedance/PiAPI — bỏ khi chạy mock (verify offline).
    if not is_mock:
        gate = video_engine_config_ready()
        if not gate.ready:
            sink.set_status(VideoJobStatus.WAITING_CONFIG, error=gate.reason_text())
            return _result(VideoJobStatus.WAITING_CONFIG, error=gate.reason_text(), fault="system")

    estimate = estimate_job_cost(
        snapshot["mode"], snapshot["purpose"], snapshot["seconds"], snapshot["resolution"]
    )
    actual_cost = 0.0
    plan: dict | None = None
    try:
        sink.set_status(VideoJobStatus.RUNNING, error="")
        route = route_video(snapshot["mode"], snapshot["purpose"], snapshot["resolution"])
        sink.update_job(
            model_id=route.model_id, resolution=route.resolution, speed_tier=route.speed_tier,
            moderation_policy=route.moderation_policy, provider_video=route.provider,
            provider_image=settings.image_provider,
            estimated_cost_usd=estimate["total_usd"], max_cost_usd=estimate["total_usd"] * 1.5,
        )

        # ẢNH SẠCH (clean-plate) tính TRƯỚC DIRECTING.
        product_image = _ensure_product_image(snapshot["product"], workdir)
        public_url = (snapshot["product"].get("image_url") or "").strip()
        clean_result = None
        if (snapshot["mode"] != "premium" and settings.video_clean_plate_enabled
                and snapshot["purpose"] != "draft"):
            from video_engine.image_stage.clean_plate import generate_clean_plate

            clean_result = generate_clean_plate(
                product=snapshot["product"], product_image=product_image,
                product_desc="", out_dir=workdir, aspect="9:16",
            )
            actual_cost += clean_result.cost
        describe_image = clean_result.path if (clean_result and clean_result.passed) else product_image

        # 1) DIRECTING ──────────────────────────────────────────────────
        sink.stage_start("DIRECTING")
        from video_engine.analyzer.product_describe import describe_product

        product_desc = describe_product(
            image_path=describe_image, product_name=snapshot["product"].get("name", ""),
        )
        ref_breakdown = ""
        ref_url = (snapshot["params"].get("video_ref_url") or "").strip()
        if ref_url:
            from video_engine.analyzer.video_understand import (
                analyze_reference_video,
                format_breakdown_for_prompt,
            )
            ref_breakdown = format_breakdown_for_prompt(analyze_reference_video(ref_url))
        user_brief = snapshot["params"].get("brief", "")
        _narr_override = (snapshot["params"].get("narration_override") or "").strip()
        if _narr_override:
            user_brief = (
                user_brief
                + " | LỜI ĐỌC ĐÃ CHỐT (video_prompt phải minh hoạ ĐÚNG mạch lời này, từng cảnh khớp "
                f"câu, KHÔNG đổi lời): {_narr_override}"
            ).strip()
        # scene_key DB read (run_job 155-159) → spec.scene_prompt (app_api resolve trước)
        if spec.scene_prompt:
            user_brief = (user_brief + " | Bối cảnh: " + spec.scene_prompt[:400]).strip()
        product_facts = _build_product_facts(snapshot["product"])
        # template_id DB read (run_job 162-170) → spec.structure_reference.
        # formula_bank (run_job 171-216, đọc+ghi DB) TẠM BỎ ở M0.
        structure_reference = spec.structure_reference
        formula_block = ""

        from video_engine.director.strategist import build_creative_brief

        creative_brief = build_creative_brief(
            product=snapshot["product"], product_description=product_desc,
            product_facts=product_facts, format_label=snapshot["format_label"],
            structure_reference=structure_reference, seconds=snapshot["seconds"],
        )
        if creative_brief:
            sink.merge_params({"angle": creative_brief.get("angle", "")})

        voice_gender = (
            snapshot["params"].get("voice_gender") or (snapshot["kol"] or {}).get("gender", "")
        )
        kol_speaks = _use_native_audio(snapshot)
        from video_engine.director.critic import review_shot_plan

        rounds = max(1, min(4, int(settings.director_review_max_rounds or 1)))
        threshold = float(settings.director_critic_threshold or 7.0)
        min_fit = float(settings.director_review_min_product_fit or 0.0)
        _clean = bool(snapshot["params"].get("clean_clip"))
        best_plan = best_verdict = None
        hints = ""
        for attempt in range(1, rounds + 1):
            brief_in = (
                user_brief if not hints
                else (user_brief + f"\nKHẮC PHỤC điểm yếu critic đã chỉ: {hints}").strip()
            )
            plan = director_mod.write_shot_plan(
                product=snapshot["product"], format_label=snapshot["format_label"],
                format_system_prompt=snapshot["format_prompt"], mode=snapshot["mode"],
                seconds=snapshot["seconds"], kol=snapshot["kol"], user_brief=brief_in,
                product_description=product_desc, aspect="9:16",
                reference_breakdown=ref_breakdown, formula_block=formula_block,
                overlay_policy=snapshot.get("overlay_policy", "allow"),
                product_facts=product_facts, voice_gender=voice_gender,
                kol_speaks=kol_speaks, creative_brief=creative_brief,
            )
            verdict = {} if _clean else review_shot_plan(
                plan, product_facts, product=snapshot["product"],
                format_label=snapshot["format_label"],
            )
            new_scored = verdict.get("score") is not None
            best_scored = best_verdict is not None and best_verdict.get("score") is not None
            if (best_verdict is None or (new_scored and not best_scored)
                    or (new_scored == best_scored
                        and _plan_rank(verdict, min_fit) >= _plan_rank(best_verdict, min_fit))):
                best_plan, best_verdict = plan, verdict
            score = verdict.get("score")
            fit = verdict.get("product_fit")
            if (score is None or score >= threshold) and (fit is None or fit >= min_fit):
                break
            hints = "; ".join(verdict.get("rewrite_hints") or verdict.get("weaknesses") or [])
            if attempt < rounds:
                logger.info(f"[render] job={spec.job_ref} review vòng {attempt}/{rounds} score={score} fit={fit}")
        plan, verdict = best_plan, best_verdict
        if _narr_override and plan is not None:
            plan["narration"] = _narr_override
        _vp_override = (snapshot["params"].get("video_prompt") or "").strip()
        if _vp_override and plan is not None:
            plan["video_prompt"] = _vp_override
        # Bản yếu/lệch SP: SaaS không có autopilot → chỉ gắn cảnh báo, vẫn render (job tay).
        score2 = verdict.get("score") if verdict else None
        fit2 = verdict.get("product_fit") if verdict else None
        if (score2 is not None and score2 < 5) or (fit2 is not None and fit2 < 4):
            reason = (f"critic score={score2}/10" if (score2 is not None and score2 < 5)
                      else f"product_fit={fit2}/10 (lệch sản phẩm)")
            sink.merge_params({"script_warning": f"{reason} sau {rounds} vòng"})
        sink.save_shot_plan(plan, critic=verdict)
        critic_note = (f"critic={verdict['score']:.1f}" if verdict.get("score") is not None
                       else "critic fail-open")
        sink.stage_end("DIRECTING", "ok", note=critic_note)

        # 2) IMAGING ────────────────────────────────────────────────────
        sink.stage_start("IMAGING")
        hero_image = ""
        if snapshot["mode"] != "premium":
            start_frame = public_url if public_url.startswith("https://") else product_image
            note = "ảnh sản phẩm gốc làm khung đầu; người tả bằng prompt"
            if clean_result is not None:
                sink.add_asset("image", clean_result.path, f"clean_plate:{clean_result.method}",
                               clean_result.cost,
                               qa_report=(clean_result.reports[-1] if clean_result.reports else None))
                if clean_result.passed:
                    start_frame = clean_result.path
                    if clean_result.method != "mock":
                        hero_image = clean_result.path
                    note = f"ảnh sạch ({clean_result.method}) giữ pixel gốc làm khung đầu"
                else:
                    note = "clean-plate fail-soft → ảnh sản phẩm gốc làm khung đầu"
            sink.stage_end("IMAGING", "ok", note=note)
        else:
            start_frame, image_cost = _imaging_gated(spec, snapshot, plan, product_image, workdir, sink)
            actual_cost += image_cost
            sink.stage_end("IMAGING", "ok")

        # Clip music-only (không lời, không phải clip thô) BẮT BUỘC có nhạc → kiểm trước render.
        if (bool(snapshot["params"].get("voiceover_off"))
                and not bool(snapshot["params"].get("clean_clip"))
                and not _resolve_user_music(spec.job_ref, snapshot)):
            raise VideoEngineError(
                "Clip nhạc-nền (không lời) nhưng không tìm được nhạc khả dụng — cấu hình nhạc hoặc chọn 'Clip thô'."
            )

        # 3) RENDERING_VIDEO ────────────────────────────────────────────
        sink.stage_start("RENDERING_VIDEO")
        clip_path = os.path.join(workdir, "clip.mp4")
        if start_frame:
            from core.image_normalize import pad_image_to_aspect

            local_frame = start_frame if not start_frame.startswith("http") else product_image
            if local_frame and os.path.exists(local_frame):
                start_frame = pad_image_to_aspect(
                    local_frame, workdir, aspect_w=9, aspect_h=16, short_edge=720,
                    stem="start_frame_padded",
                )
        video_provider = build_video_provider()
        video_kwargs = dict(
            prompt=plan["video_prompt"], out_path=clip_path, seconds=snapshot["seconds"],
            aspect="9:16", resolution=route.resolution, model_id=route.model_id,
            image_paths=[start_frame] if start_frame else None,
            on_created=lambda tid: sink.merge_params({"piapi_task_id": tid}),
            resume_task_id=snapshot["params"].get("piapi_task_id", ""),
        )
        try:
            video_provider.generate(**video_kwargs)
        except ProviderRejectedError as exc:
            if exc.final or not route.retry_allowed:
                raise
            logger.warning(f"[render] job={spec.job_ref} video reject (strict) → retry 1 lần")
            video_provider.generate(**video_kwargs)
        video_cost = round(snapshot["seconds"] * route.usd_per_second, 4)
        if video_provider.name != "mock":
            actual_cost += video_cost
        sink.add_asset("video", clip_path, video_provider.name, video_cost)
        sink.stage_end("RENDERING_VIDEO", "ok")

        # beat 'khoe SP' = ảnh sạch + Ken Burns prepend (chỉ final + có hero + không native).
        hero_extra = 0.0
        hero_s = int(settings.video_product_hero_seconds or 0)
        if bool(snapshot["params"].get("clean_clip")):
            hero_s = 0
        if hero_s > 0 and snapshot["purpose"] == "final" and hero_image and not _use_native_audio(snapshot):
            from video_engine.compose.product_hero import prepend_product_hero

            combined = prepend_product_hero(
                clip_path=clip_path, clean_image=hero_image, seconds=hero_s,
                out_path=os.path.join(workdir, "clip_hero.mp4"),
            )
            if combined:
                clip_path = combined
                hero_extra = hero_s - 0.4

        # 4-6) VOICING → COMPOSING → QA
        final_path, report, finishing_cost = _finishing(
            spec, snapshot, plan, clip_path, product_image, workdir, sink,
            extra_video_seconds=hero_extra,
            tail_image=(clean_result.path if (clean_result and clean_result.passed) else ""),
        )
        actual_cost += finishing_cost
        if not report["passed"]:
            sink.update_job(final_path=final_path, actual_cost_usd=round(actual_cost, 4))
            err = "; ".join(report["reasons"])[:500]
            sink.set_status(VideoJobStatus.QA_FAIL, error=err)
            return _result(VideoJobStatus.QA_FAIL, path=final_path, error=err, cost=actual_cost,
                           plan=plan, report=report, fault="input")

        sink.update_job(final_path=final_path, actual_cost_usd=round(actual_cost, 4))
        sink.set_status(VideoJobStatus.READY, error="")
        logger.info(f"[render] job={spec.job_ref} READY · ${actual_cost:.3f} (est ${estimate['total_usd']:.3f})")
        return _result(VideoJobStatus.READY, path=final_path, cost=actual_cost, plan=plan, report=report)

    except ProviderRejectedError as exc:
        err = f"Provider từ chối nội dung (final={exc.final}): {exc}"[:500]
        sink.set_status(VideoJobStatus.QA_FAIL, error=err)
        return _result(VideoJobStatus.QA_FAIL, error=err, cost=actual_cost, plan=plan, fault="input")
    except ProviderNotConfiguredError as exc:
        sink.set_status(VideoJobStatus.WAITING_CONFIG, error=str(exc))
        return _result(VideoJobStatus.WAITING_CONFIG, error=str(exc), cost=actual_cost, fault="system")
    except VideoBudgetError as exc:
        # Giữ cho đối xứng hợp đồng exception; M0 đã bỏ reserve/settle budget nên nhánh này
        # gần như không xảy ra. fault="" vì QUEUED_BUDGET là TÁI-XẾP-HÀNG, không phải lỗi
        # (app_api KHÔNG được coi đây là system-fault để hoàn/charge nhầm).
        sink.set_status(VideoJobStatus.QUEUED_BUDGET, error=str(exc))
        return _result(VideoJobStatus.QUEUED_BUDGET, error=str(exc), cost=actual_cost, fault="")
    except VideoEngineError as exc:
        # no image / no music = lỗi đầu vào.
        sink.set_status(VideoJobStatus.FAILED, error=safe_error_detail(exc, limit=500))
        return _result(VideoJobStatus.FAILED, error=safe_error_detail(exc, limit=500),
                       cost=actual_cost, plan=plan, fault="input")
    except Exception as exc:  # noqa: BLE001
        logger.exception(f"[render] job={spec.job_ref} THẤT BẠI")
        sink.set_status(VideoJobStatus.FAILED, error=safe_error_detail(exc, limit=500))
        return _result(VideoJobStatus.FAILED, error=safe_error_detail(exc, limit=500),
                       cost=actual_cost, plan=plan, fault="system")


def _finishing(
    spec: JobSpec, snapshot: dict, plan: dict, clip_path: str, product_image: str,
    workdir: str, sink: JobSink, *, extra_video_seconds: float = 0.0, tail_image: str = "",
) -> tuple[str, dict, float]:
    """VOICING → COMPOSING → QA (stateless port của pipeline._finishing_stages)."""
    cost = 0.0
    sink.stage_start("VOICING")
    voice_path = ""
    voice_delay_s = 0.9
    voiceover_off = bool(snapshot["params"].get("voiceover_off"))
    clean_clip = bool(snapshot["params"].get("clean_clip"))
    if clean_clip:
        voiceover_off = True
    use_native = _use_native_audio(snapshot) and not voiceover_off
    if clean_clip:
        sink.stage_end("VOICING", "ok", note="CLIP THÔ — không chữ, không nhạc (user tự ghép)")
    elif voiceover_off:
        sink.stage_end("VOICING", "ok", note="KHÔNG LỜI — nhạc nền làm tiếng chính")
    elif not use_native:
        voice_path = os.path.join(workdir, "voice.wav")
        voice_gender = (
            snapshot["params"].get("voice_gender") or (snapshot["kol"] or {}).get("gender", "")
        )
        voice_id = snapshot["params"].get("voice_id") or (snapshot["kol"] or {}).get("voice_id", "")
        if not voice_id:
            from video_engine.voice import pick_voice

            voice_id = pick_voice(
                gender=voice_gender,
                seed=f"{spec.job_ref}-{snapshot['product'].get('category', '')}",
            )
        _, voice_starts, voice_engine = synthesize_narration_segmented(
            plan["narration"], voice_path, voice_id=voice_id, gender=voice_gender, delay_s=voice_delay_s,
        )
        hidden = {
            k.strip().lower()
            for k in (settings.video_overlay_hidden_kinds or "").split(",") if k.strip()
        }
        if hidden:
            plan["text_overlays"] = [
                ov for ov in (plan.get("text_overlays") or [])
                if (ov.get("kind") or "").strip().lower() not in hidden
            ]
        from video_engine.voice import align_overlay_times

        align_overlay_times(plan["narration"], plan.get("text_overlays") or [], voice_starts)
        sink.update_overlays(plan.get("text_overlays") or [])
        cost += 0.01
        voice_degraded = voice_engine == "edge"
        if voice_degraded:
            sink.merge_params({"voice_degraded": True, "voice_engine": voice_engine})
            logger.warning(f"[render] job={spec.job_ref} VOICING degraded → edge")
        sink.add_asset("voice", voice_path, voice_engine, 0.01)
        sink.stage_end("VOICING", "ok",
                       note=f"engine={voice_engine}, {len(voice_starts)} câu"
                            + (" ⚠️ FALLBACK EDGE" if voice_degraded else ""))
    else:
        sink.stage_end("VOICING", "ok", note="dùng audio Seedance sinh sẵn (nhạc+SFX)")

    # 5) COMPOSING
    sink.stage_start("COMPOSING")
    final_path = os.path.join(workdir, "final.mp4")
    tail_s = int(settings.video_cta_tail_seconds or 0)
    use_tail = tail_s > 0 and snapshot["purpose"] == "final" and not use_native and not voiceover_off
    user_music_path = ""
    if voiceover_off and not clean_clip:
        user_music_path = _resolve_user_music(spec.job_ref, snapshot)
    cta_tail_spec = None
    if use_tail:
        cta_tail_spec = {
            "product_image": tail_image if (tail_image and os.path.exists(tail_image)) else product_image,
            "price_text": _build_product_facts(snapshot["product"]).get("price", ""),
            "short_name": snapshot["product"].get("name", ""),
        }
    compose_final(
        video_path=clip_path, audio_path=voice_path, out_path=final_path,
        narration=plan["narration"], polish=snapshot["purpose"] != "draft",
        keep_source_audio=use_native,
        voice_delay_ms=0 if (use_native or voiceover_off) else int(voice_delay_s * 1000),
        text_overlays=([] if clean_clip else (plan.get("text_overlays") or [])),
        cta_tail_spec=cta_tail_spec, music_path=user_music_path,
        music_hint=f"{snapshot['product'].get('name', '')} {snapshot['product'].get('category', '')}",
    )
    sink.add_asset("compose", final_path, "local_ffmpeg", 0.0)
    sink.stage_end("COMPOSING", "ok", note=f"tail={tail_s}s" if use_tail else "")

    # 6) QA
    sink.stage_start("QA")
    expected_seconds = snapshot["seconds"] + extra_video_seconds + (tail_s - 0.4 if use_tail else 0)
    # Video CÓ LỜI: thành phẩm dài theo NARRATION (clip kéo dài để khớp giọng) → expected phải theo
    # độ dài giọng, tránh QA fail oan "thời lượng lệch nhiều" khi kịch bản đọc dài hơn clip (vd KOL).
    if voice_path and os.path.exists(voice_path):
        from video_engine.qa import _ffprobe

        _vp = _ffprobe(voice_path)
        if _vp and _vp.get("duration"):
            expected_seconds = max(expected_seconds, float(_vp["duration"]) + voice_delay_s)
    expected_texts = [] if clean_clip else [str(ov.get("text") or "") for ov in plan.get("text_overlays") or []]
    if use_tail and cta_tail_spec:
        expected_texts += [cta_tail_spec["short_name"][:42], cta_tail_spec["price_text"], "MUA NGAY"]
    report = qa_final_video(
        final_path=final_path, expected_seconds=expected_seconds, aspect="9:16",
        product_image=product_image, check_product_match=snapshot["purpose"] == "final",
        expected_texts=[t for t in expected_texts if t],
        text_scan_until=float(snapshot["seconds"]) if use_tail else None,
        narration=("" if (use_native or voiceover_off) else (plan.get("narration") or "")),
    )
    sink.add_asset("qa", final_path, "local", 0.0, qa_report=report)
    sink.stage_end("QA", "fail" if not report["passed"] else "ok",
                   note=("; ".join(report["reasons"])[:300]) if not report["passed"] else "")
    return final_path, report, cost


def _imaging_gated(
    spec: JobSpec, snapshot: dict, plan: dict, product_image: str, workdir: str, sink: JobSink,
) -> tuple[str, float]:
    """Sinh ảnh + QA match, regenerate ≤2 lần (stateless port của _generate_gated_image)."""
    provider = build_image_provider()
    refs = [p for p in [product_image, (snapshot["kol"] or {}).get("image_path", "")] if p]
    prompts = plan["image_prompts"] or [plan["video_prompt"]]
    base_prompt = prompts[0]
    cost = 0.0
    last_reasons: list[str] = []
    for attempt in range(1 + _MAX_IMAGE_RETRIES):
        out_path = os.path.join(workdir, f"image_{attempt}.png")
        prompt = base_prompt
        if attempt and last_reasons:
            prompt += " | FIX STRICTLY: " + "; ".join(last_reasons)[:300]
        generated = provider.generate(prompt=prompt, out_path=out_path, input_image_paths=refs)
        if not generated or not os.path.exists(out_path):
            raise VideoEngineError(f"{provider.name} không sinh được ảnh và Gemini fallback bị tắt.")
        if provider.name == "gemini":
            cost += float(settings.video_image_cost_usd)
        report = qa_image_match(product_image, out_path)
        sink.add_asset(
            "image", out_path, provider.name,
            float(settings.video_image_cost_usd) if provider.name == "gemini" else 0.0,
            qa_report=report,
        )
        if report.get("passed"):
            return out_path, round(cost, 4)
        last_reasons = report.get("reasons") or ["ảnh không khớp sản phẩm"]
    raise ProviderRejectedError(
        "Ảnh KOL/sản phẩm không qua CỔNG MATCH sau "
        f"{1 + _MAX_IMAGE_RETRIES} lần: {'; '.join(last_reasons)[:300]}",
        final=True,
    )
