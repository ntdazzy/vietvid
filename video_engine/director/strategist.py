"""Affiliate Strategist (V8.5) — phân tích SẢN PHẨM THẬT + chọn GÓC thuyết phục + beat-plan.

Một call Gemini text: đọc {sản phẩm + mô tả-hình (describe_product) + facts THẬT + cấu trúc
template đã chọn} → ``CreativeBrief`` đặc thù cho ĐÚNG sản phẩm đó. Lấy CẤU TRÚC/NHỊP từ
template, TUYỆT ĐỐI không bê tên/chi tiết sản phẩm trong template sang. Đây là lớp biến
"format = khung" thành "kịch bản hợp sản phẩm + đánh tâm lý mua hàng".

Fail-soft: thiếu key / LLM lỗi / JSON hỏng → trả None (Director chạy như cũ, không nghẽn job).
"""

from __future__ import annotations

import json
import re

from config.settings import settings
from core.logger import logger

# Góc thuyết phục — Strategist chọn 1 cái HỢP NHẤT với sản phẩm (không mặc định).
ANGLES = (
    "problem_solution",  # SP giải quyết 1 nỗi đau rõ — gadget tiện ích, đồ gia dụng
    "social_proof",  # đám đông đã mua/khen — đồ trend, best-seller
    "transformation",  # before→after, lên đời — làm đẹp, thời trang, decor
    "fomo_scarcity",  # sợ bỏ lỡ, sale/limited — deal hời, hàng hot
    "comparison",  # so với loại rẻ/cũ — đồ công nghệ, đồ bền
    "curiosity_gap",  # tò mò "cái này là gì/sao hay vậy" — sản phẩm lạ
)

_SYSTEM = (
    "Bạn là chiến lược gia content affiliate người Việt, cực sắc về TÂM LÝ MUA HÀNG trên "
    "TikTok/Shopee. Nhiệm vụ: phân tích SẢN PHẨM THẬT của người dùng, chọn GÓC thuyết phục "
    "hợp sản phẩm nhất, rồi vạch beat-plan kịch bản bán hàng đánh trúng người mua. "
    "DỒN ĐÁNH CẢM XÚC + KHAO KHÁT: khoét nỗi đau → vẽ giấc mơ 'dùng/mặc vào là lên đời' → "
    "sợ bỏ lỡ → dụ chốt đơn. KHÔNG cần lượt bán/đánh giá — thuyết phục bằng cảm xúc + lợi ích THẬT. "
    "GIỌNG TỰ QUAY TỰ THOẠI (UGC, ngôi thứ nhất 'mình/tui') — như người dùng review món đồ mình rồi "
    "rủ mua, KHÔNG phải MC/TVC sáo rỗng. "
    "Bạn KHÔNG viết lời thoại cuối cùng — chỉ vạch chiến lược + ý từng cảnh để đạo diễn dựng. "
    "CHỈ trả JSON thuần, không markdown."
)

_RUBRIC = """Phân tích sản phẩm rồi trả DUY NHẤT 1 JSON object đúng schema:
{
 "target_buyer": "chân dung người mua (tuổi/giới/bối cảnh dùng), 1 câu",
 "pain_points": ["2-3 nỗi đau/nhu cầu THẬT sản phẩm giải quyết"],
 "usps": ["2-3 điểm bán mạnh nhất, mỗi cái gắn 1 đặc điểm THẬT của sản phẩm"],
 "angle": "1 trong %(angles)s — chọn cái HỢP sản phẩm nhất",
 "why": "1 câu vì sao góc này hợp sản phẩm này",
 "big_promise": "thông điệp lõi DUY NHẤT muốn người xem nhớ (1 câu, tiếng Việt)",
 "hook_line": "câu hook tiếng Việt ≤6 từ cho 0-2s đầu, đặc thù cho ĐÚNG sản phẩm này (câu hỏi/cú sốc/con số)",
 "beats": [
   {"label":"hook|pain|desire|benefit|cta","shows":"cảnh/hành động với SP (ý, không phải prompt)","says":"ý người nói ở cảnh này (tiếng Việt, ngắn)"}
 ],
 "cta_plan": "CTA dụ chốt đơn + móc khẩn cấp/sợ bỏ lỡ (tiếng Việt, ngắn)"
}

QUY TẮC BẮT BUỘC:
- beats phải bám CẤU TRÚC/NHỊP của FORMAT (và STRUCTURE_REFERENCE nếu có) — nhưng MỌI nội dung
  (shows/says) phải nói về ĐÚNG sản phẩm của người dùng dưới đây. TUYỆT ĐỐI KHÔNG bê tên/chi tiết
  sản phẩm trong STRUCTURE_REFERENCE (đó chỉ là MẪU CẤU TRÚC của sản phẩm khác — học nhịp, không học nội dung).
- KHÔNG nêu lượt đã bán / số sao (kể cả khi có) — ĐÁNH TÂM LÝ thay vì khoe số. KHÔNG bịa số,
  KHÔNG hứa "chữa khỏi/100%/giảm cân thần tốc". Số THẬT trong PRODUCT_FACTS (giá) chỉ dùng nếu HỢP, không bắt buộc.
- DỒN ĐÁNH TÂM LÝ: hook giữ chân → khoét NỖI ĐAU cụ thể → VẼ GIẤC MƠ (hình dung bản thân lên đời
  khi dùng: đẹp/cao/sang/tự tin/được khen/hợp mọi outfit) → khao khát + sợ bỏ lỡ → DỤ chốt đơn.
- Số beats ~ %(nbeats)s cho video %(seconds)ss. Tiếng Việt đời thường, dụ dỗ, không sáo rỗng."""


def build_creative_brief(
    *,
    product: dict,
    product_description: str = "",
    product_facts: dict | None = None,
    format_label: str = "",
    structure_reference: str = "",
    seconds: int = 15,
) -> dict | None:
    """Trả CreativeBrief dict hoặc None (fail-soft). ``structure_reference`` = prompt template
    đã chọn (lấy CẤU TRÚC), ``product_description`` = mô tả-hình từ Gemini Vision (B3)."""
    if not settings.strategist_enabled:
        return None
    from core.config_checks import looks_real_secret

    if not looks_real_secret(settings.gemini_api_key or "") and not looks_real_secret(
        settings.groq_api_key or ""
    ):
        return None

    nbeats = max(3, min(6, round(seconds / 3)))
    facts = product_facts or {}
    ref = (structure_reference or "").strip()[:2000]
    ref_block = (
        f"\nSTRUCTURE_REFERENCE (chỉ học CẤU TRÚC/NHỊP/TIMECODE — KHÔNG copy sản phẩm trong này):\n{ref}"
        if ref
        else ""
    )
    # .replace (KHÔNG %-format / .format): rubric có literal "100%" và "{...}" JSON.
    rubric = (
        _RUBRIC.replace("%(angles)s", ", ".join(ANGLES))
        .replace("%(nbeats)s", str(nbeats))
        .replace("%(seconds)s", str(seconds))
    )
    user = (
        f"SẢN PHẨM CỦA NGƯỜI DÙNG:\n"
        f"- Tên: {product.get('name', '')}\n"
        f"- Ngành: {product.get('category', '')}\n"
        f"- Giá: {product.get('price', '')}\n"
        f"- Mô tả: {(product.get('description') or '')[:600]}\n"
        f"- Mô tả hình ảnh (Vision): {(product_description or '')[:600]}\n"
        f"PRODUCT_FACTS (số THẬT, nguồn duy nhất cho proof): {json.dumps(facts, ensure_ascii=False)}\n"
        f"FORMAT: {format_label} · Thời lượng: {seconds}s.{ref_block}\n\n"
        + rubric
    )

    try:
        from module2_brain.llm.v5_clients import complete_with_fallback

        raw = complete_with_fallback(_SYSTEM, user, gemini_model=settings.gemini_model)
    except Exception as exc:  # noqa: BLE001 — fail-soft: Strategist không được nghẽn pipeline
        logger.warning(f"[strategist] LLM lỗi → bỏ qua (Director chạy như cũ): {str(exc)[:200]}")
        return None

    brief = _parse(raw)
    if brief is None:
        logger.warning("[strategist] output không phải JSON dùng được → bỏ qua")
        return None
    logger.info(
        f"[strategist] angle={brief.get('angle')} hook='{(brief.get('hook_line') or '')[:40]}' "
        f"beats={len(brief.get('beats') or [])} cho '{product.get('name', '')[:40]}'"
    )
    return brief


def format_brief_for_director(brief: dict) -> str:
    """Ghép CreativeBrief thành block text nhúng vào prompt Director."""
    beats = brief.get("beats") or []
    beat_lines = "\n".join(
        f"  {i + 1}. [{b.get('label', '')}] CẢNH: {b.get('shows', '')} | LỜI: {b.get('says', '')}"
        for i, b in enumerate(beats)
        if isinstance(b, dict)
    )
    return (
        "\nCHIẾN LƯỢC AFFILIATE (BÁM SÁT — đây là xương sống kịch bản, hợp ĐÚNG sản phẩm này):\n"
        f"- Góc thuyết phục: {brief.get('angle', '')} ({brief.get('why', '')})\n"
        f"- Người mua: {brief.get('target_buyer', '')}\n"
        f"- Thông điệp lõi: {brief.get('big_promise', '')}\n"
        f"- HOOK 0-2s: \"{brief.get('hook_line', '')}\"\n"
        f"- Beat-plan:\n{beat_lines}\n"
        f"- CTA chốt: {brief.get('cta_plan', '')}\n"
        "Viết narration/video_prompt BÁM beat-plan trên, nói về ĐÚNG sản phẩm người dùng, số liệu từ PRODUCT_FACTS."
    )


def _parse(raw: str) -> dict | None:
    text = (raw or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-z]*\s*|\s*```$", "", text, flags=re.IGNORECASE | re.MULTILINE)
    try:
        data = json.loads(text)
    except ValueError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            return None
        try:
            data = json.loads(match.group(0))
        except ValueError:
            return None
    if not isinstance(data, dict) or not data.get("hook_line"):
        return None
    # Chuẩn hoá tối thiểu — chống field thiếu/sai kiểu làm vỡ Director.
    data["beats"] = [b for b in (data.get("beats") or []) if isinstance(b, dict)][:6]
    angle = str(data.get("angle") or "").strip().lower()
    data["angle"] = angle if angle in ANGLES else "problem_solution"
    return data
