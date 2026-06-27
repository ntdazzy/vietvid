"""Analyzer v2 — Decision Engine: chọn mode/format/KOL/scene/voice/duration/resolution.

V8.2 Phase 4: 1 call Gemini Flash (~$0.002) khi ANALYZER_LLM_ENABLED + có product dict;
validate CỨNG từng trường — hỏng 1 trường → fallback TOÀN BỘ heuristic (`_analyze_heuristic`,
logic v1 giữ nguyên). LLM lỗi/timeout → heuristic + warning. Người vận hành chọn tay
trường nào → GIỮ NGUYÊN trường đó, LLM chỉ điền chỗ trống.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from sqlalchemy import select

from config.settings import settings
from core.database import db
from core.logger import logger
from core.models import AdFormat, KolCharacter, KolStatus, ScenePreset

# Ngành cần "người thật review" → kol_full; còn lại product_only cho rẻ.
_KOL_CATEGORIES = {"fashion", "beauty", "thời trang", "mỹ phẩm", "làm đẹp"}
_FORMAT_BY_MODE = {"kol_full": "ugc_review", "product_only": "product_broll"}


@dataclass(frozen=True)
class AnalyzeResult:
    mode: str
    format_key: str
    kol_id: int | None
    seconds: int
    reason: str
    # V8.2 Phase 4 (mặc định rỗng để caller cũ không vỡ):
    scene_key: str = ""
    voice_gender: str = ""
    resolution: str = ""
    promo_appeal: int = -1  # -1 = chưa chấm (heuristic không chấm)


def analyze_product(
    *,
    category: str,
    requested_mode: str = "auto",
    requested_format: str = "",
    requested_kol_id: int | None = None,
    purpose: str = "final",
    requested_seconds: int = 0,
    product: dict | None = None,
) -> AnalyzeResult:
    """``product`` (name/price/description/tier) → bật đường LLM; thiếu → heuristic như v1."""
    heuristic = _analyze_heuristic(
        category=category,
        requested_mode=requested_mode,
        requested_format=requested_format,
        requested_kol_id=requested_kol_id,
        purpose=purpose,
        requested_seconds=requested_seconds,
    )
    if not settings.analyzer_llm_enabled or not product:
        return heuristic
    try:
        llm = _analyze_llm(
            category=category,
            product=product,
            requested_mode=requested_mode,
            requested_format=requested_format,
            requested_kol_id=requested_kol_id,
            requested_seconds=requested_seconds,
            purpose=purpose,
        )
    except Exception as exc:  # noqa: BLE001 — LLM lỗi/timeout/validate fail → heuristic toàn bộ
        logger.warning(f"[analyzer] LLM fail → dùng heuristic: {str(exc)[:200]}")
        return heuristic
    return llm


def _analyze_heuristic(
    *,
    category: str,
    requested_mode: str = "auto",
    requested_format: str = "",
    requested_kol_id: int | None = None,
    purpose: str = "final",
    requested_seconds: int = 0,
) -> AnalyzeResult:
    """Heuristic v1 — GIỮ NGUYÊN logic (rẻ, đoán được, fallback tin cậy)."""
    reasons: list[str] = []

    mode = (requested_mode or "auto").lower()
    if mode in {"", "auto"}:
        is_kol_niche = (category or "").strip().lower() in _KOL_CATEGORIES
        mode = "kol_full" if is_kol_niche else "product_only"
        reasons.append(f"auto-mode theo ngành '{category}' → {mode}")
    else:
        reasons.append(f"mode do người vận hành chọn: {mode}")

    format_key = (requested_format or "").strip()
    if not format_key:
        format_key = _FORMAT_BY_MODE.get(mode, "product_broll")
        reasons.append(f"auto-format → {format_key}")

    kol_id = requested_kol_id
    if mode in {"kol_full", "premium"} and kol_id is None:
        kol_id = _pick_active_kol(category)
        reasons.append(
            f"auto-KOL → id={kol_id}" if kol_id else "không có KOL ACTIVE — cần tạo ở /kol-ai"
        )

    if requested_seconds > 0:
        seconds = max(4, min(15, int(requested_seconds)))
    elif purpose == "draft":
        seconds = int(settings.video_draft_seconds or 5)
    else:
        seconds = int(settings.video_final_seconds or 10)

    return AnalyzeResult(
        mode=mode,
        format_key=format_key,
        kol_id=kol_id,
        seconds=seconds,
        reason="; ".join(reasons),
    )


def _analyze_llm(
    *,
    category: str,
    product: dict,
    requested_mode: str,
    requested_format: str,
    requested_kol_id: int | None,
    requested_seconds: int,
    purpose: str,
) -> AnalyzeResult:
    """1 call Gemini Flash → JSON quyết định; validate cứng từng trường (sai → raise)."""
    from module2_brain.llm.v5_clients import complete_with_fallback

    with db.transaction() as s:
        formats = {
            f.key: f for f in s.scalars(select(AdFormat).where(AdFormat.status == "ACTIVE"))
        }
        kols = list(s.scalars(select(KolCharacter).where(KolCharacter.status == KolStatus.ACTIVE)))
        scenes = list(s.scalars(select(ScenePreset).where(ScenePreset.status == "ACTIVE")))
        for obj in list(formats.values()) + kols + scenes:
            s.expunge(obj)
    if not formats:
        raise ValueError("chưa có ad_formats ACTIVE")

    tier = str(product.get("tier") or "")
    catalog = {
        "formats": [
            {"key": f.key, "label": f.label, "requires_kol": f.requires_kol} for f in formats.values()
        ],
        "kols": [{"id": k.id, "name": k.name, "gender": k.gender, "tags": k.tags} for k in kols],
        "scenes": [
            {"key": sc.key, "label": sc.label, "gender_hint": sc.gender_hint} for sc in scenes
        ],
    }
    system = (
        "Bạn là Decision Engine chọn cấu hình video quảng cáo affiliate. "
        "Dựa trên sản phẩm + danh mục hợp lệ, trả về DUY NHẤT JSON object: "
        '{"mode": "kol_full|product_only", "format_key": "...", "kol_id": <int|null>, '
        '"scene_key": "...", "voice_gender": "nam|nữ|", "seconds": 10|15, '
        '"resolution": "480p|720p", "promo_appeal": 0-10, "reason": "ngắn gọn tiếng Việt"}. '
        "Quy tắc: format/kol/scene PHẢI lấy từ danh mục; mode kol_full khi sản phẩm hợp người "
        "thật review (thời trang/làm đẹp/đeo/mặc), product_only cho đồ gia dụng/tiêu dùng rẻ; "
        "resolution mặc định 480p — 720p CHỈ khi sản phẩm tier A và promo_appeal >= 8; "
        "promo_appeal = độ hấp dẫn làm video bán hàng (0-10, cân nhắc giá/%hh/độ viral)."
    )
    prompt = json.dumps(
        {
            "product": {
                "name": product.get("name", ""),
                "price": product.get("price", ""),
                "description": str(product.get("description") or "")[:500],
                "category": category,
                "tier": tier,
            },
            "catalog": catalog,
            "operator_locked": {
                "mode": requested_mode if requested_mode not in {"", "auto"} else None,
                "format_key": requested_format or None,
                "kol_id": requested_kol_id,
                "seconds": requested_seconds or None,
            },
        },
        ensure_ascii=False,
    )
    raw = complete_with_fallback(system, prompt, gemini_model=settings.gemini_model)
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-z]*\s*|\s*```$", "", text, flags=re.IGNORECASE | re.MULTILINE)
    try:
        data = json.loads(text)
    except ValueError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError(f"LLM không trả JSON: {text[:120]}") from None
        data = json.loads(match.group(0))
    if not isinstance(data, dict):
        raise ValueError("LLM JSON không phải object")

    # ── Validate CỨNG từng trường (sai 1 trường → raise → heuristic toàn bộ) ──
    mode = str(data.get("mode") or "").strip().lower()
    if mode not in {"kol_full", "product_only"}:
        raise ValueError(f"mode bịa: {mode!r}")
    format_key = str(data.get("format_key") or "").strip()
    if format_key not in formats:
        raise ValueError(f"format bịa: {format_key!r}")
    kol_id = data.get("kol_id")
    if kol_id is not None:
        if not isinstance(kol_id, int) or kol_id not in {k.id for k in kols}:
            raise ValueError(f"kol_id bịa: {kol_id!r}")
    if mode == "kol_full" and kol_id is None:
        raise ValueError("mode kol_full nhưng kol_id null")
    scene_key = str(data.get("scene_key") or "").strip()
    if scene_key and scene_key not in {sc.key for sc in scenes}:
        raise ValueError(f"scene_key bịa: {scene_key!r}")
    voice_gender = str(data.get("voice_gender") or "").strip().lower()
    if voice_gender not in {"nam", "nữ", "nu", ""}:
        raise ValueError(f"voice_gender bịa: {voice_gender!r}")
    voice_gender = "nữ" if voice_gender == "nu" else voice_gender
    seconds = data.get("seconds")
    if seconds not in {10, 15}:
        raise ValueError(f"seconds ngoài {{10,15}}: {seconds!r}")
    promo_appeal = data.get("promo_appeal")
    if not isinstance(promo_appeal, int) or not 0 <= promo_appeal <= 10:
        raise ValueError(f"promo_appeal hỏng: {promo_appeal!r}")
    resolution = str(data.get("resolution") or "480p").strip()
    if resolution not in {"480p", "720p"}:
        raise ValueError(f"resolution bịa: {resolution!r}")
    if resolution == "720p" and not (tier == "A" and promo_appeal >= 8):
        raise ValueError(f"720p không đủ điều kiện (tier={tier!r} promo_appeal={promo_appeal})")
    reason = str(data.get("reason") or "").strip()[:300]

    # ── Người vận hành chọn gì GIỮ NGUYÊN (LLM chỉ điền chỗ trống) ──
    if requested_mode not in {"", "auto"}:
        mode = requested_mode.lower()
    if requested_format:
        format_key = requested_format
    if requested_kol_id is not None:
        kol_id = requested_kol_id
    if requested_seconds > 0:
        seconds = max(4, min(15, int(requested_seconds)))
    if mode == "premium":
        # premium do người vận hành ép — giữ nguyên đường cũ
        kol_id = kol_id or _pick_active_kol(category)

    return AnalyzeResult(
        mode=mode,
        format_key=format_key,
        kol_id=kol_id,
        seconds=int(seconds),
        reason=f"LLM: {reason}",
        scene_key=scene_key,
        voice_gender=voice_gender,
        resolution=resolution,
        promo_appeal=promo_appeal,
    )


def _pick_active_kol(category: str) -> int | None:
    """KOL ACTIVE có tag khớp ngách, không có thì KOL ACTIVE bất kỳ."""
    needle = (category or "").strip().lower()
    with db.transaction() as session:
        kols = session.scalars(
            select(KolCharacter).where(KolCharacter.status == KolStatus.ACTIVE)
        ).all()
        if not kols:
            return None
        if needle:
            for kol in kols:
                if needle in (kol.tags or "").lower():
                    return kol.id
        return kols[0].id
