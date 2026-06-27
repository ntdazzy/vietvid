"""Script Critic gate (V8.3-Q4 · mở rộng đa chiều V8.5) — chấm kịch bản TRƯỚC khi đốt $1.21 render.

Rubric 0-2/tiêu chí cho hook/pain_benefit/proof/cta/natural/format_adherence + ``product_fit``
0-10 (chiều TỚI HẠN: kịch bản có nói ĐÚNG sản phẩm người dùng không, có rò sản phẩm khác không).
FAIL-OPEN: LLM lỗi → ``{"score": None}`` + warning — KHÔNG nghẽn pipeline; chỉ autopilot
chặn cứng script yếu (job tay vẫn chạy kèm warning).
"""

from __future__ import annotations

import json
import re

from config.settings import settings
from core.logger import logger

_RUBRIC_PROMPT = """Bạn là chuyên gia thẩm định kịch bản video bán hàng TikTok/Shopee Việt Nam.
Chấm NARRATION dưới đây theo các tiêu chí:
- hook (0-2): 2s đầu có giữ chân người lướt không (câu hỏi/cú sốc/con số)?
- pain_benefit (0-2): chạm nỗi đau + lợi ích CỤ THỂ có số?
- proof (0-2): dùng bằng chứng THẬT từ PRODUCT_FACTS (sold/rating/giá) — bịa số = 0 điểm?
- cta (0-2): kêu gọi hành động có khẩn cấp/deadline?
- natural (0-2): văn nói tự nhiên (nè/nha/luôn), không liệt kê khô?
- format_adherence (0-2): có bám đúng định dạng "%(format)s" (nhịp/kiểu cảnh) không?
- product_fit (0-10): kịch bản có nói ĐÚNG SẢN PHẨM dưới đây không? Có nhắc tính năng/đặc điểm
  sản phẩm KHÔNG CÓ, hay lẫn sản phẩm khác (rò mẫu) không? Khớp hoàn toàn = 10; lệch/chung chung
  không rõ sản phẩm = 4-6; nói sai/lẫn sản phẩm khác = 0-3.
TRẢ DUY NHẤT JSON:
{"hook":0-2,"pain_benefit":0-2,"proof":0-2,"cta":0-2,"natural":0-2,"format_adherence":0-2,
 "product_fit":0-10,"score":0-10,"weaknesses":["..."],"rewrite_hints":["..."]}

SẢN PHẨM ĐÚNG (kịch bản PHẢI nói về cái này): %(product)s
PRODUCT_FACTS: %(facts)s
NARRATION: %(narration)s
CTA: %(cta)s"""


def _loads_lenient(text: str) -> dict:
    """Parse JSON chịu lỗi LLM: bỏ code-fence, bóc khối { } CÂN BẰNG (không greedy ăn cả prose
    đuôi), bỏ trailing comma. Giảm fail-open của critic (groq hay trả JSON hơi lệch)."""
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", (text or "").strip(), flags=re.IGNORECASE).strip()
    start = t.find("{")
    if start >= 0:
        depth = 0
        in_str = esc = False
        for i in range(start, len(t)):
            ch = t[i]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
            elif ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    t = t[start:i + 1]
                    break
    t = _strip_trailing_commas(t)  # bỏ dấu phẩy thừa trước } hoặc ] — CHỪA dấu phẩy nằm TRONG chuỗi
    return json.loads(t)


def _strip_trailing_commas(t: str) -> str:
    """Bỏ dấu phẩy thừa ngay trước } hoặc ] — nhưng CHỈ khi nằm NGOÀI chuỗi (string-aware).
    Regex mù trước đây ăn nhầm dấu phẩy trong giá trị chuỗi (vd "hello,}") → hỏng nội dung thầm lặng."""
    out: list[str] = []
    in_str = esc = False
    n = len(t)
    for i, ch in enumerate(t):
        if in_str:
            out.append(ch)
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
            out.append(ch)
            continue
        if ch == ",":
            j = i + 1
            while j < n and t[j] in " \t\r\n":
                j += 1
            if j < n and t[j] in "}]":
                continue  # bỏ dấu phẩy thừa
        out.append(ch)
    return "".join(out)


def review_shot_plan(
    plan: dict, product_facts: dict | None = None, product: dict | None = None,
    format_label: str = "",
) -> dict:
    """Chấm shot plan đa chiều → dict rubric. LLM lỗi → {"score": None} (fail-open).

    ``product`` (tên/ngành/mô tả) để chấm ``product_fit`` — chống rò sản phẩm khác.
    """
    try:
        from module2_brain.llm.v5_clients import complete_with_fallback

        p = product or {}
        product_line = (
            f"{p.get('name', '')} · {p.get('category', '')} · {(p.get('description') or '')[:200]}"
        )
        prompt = _RUBRIC_PROMPT % {
            "format": format_label or "(không rõ)",
            "product": product_line or "(không rõ)",
            "facts": json.dumps(product_facts or {}, ensure_ascii=False),
            "narration": str(plan.get("narration") or "")[:1500],
            "cta": str(plan.get("cta") or "")[:200],
        }
        raw = complete_with_fallback(
            "Bạn là critic kịch bản quảng cáo. Chỉ trả JSON.",
            prompt,
            gemini_model=settings.gemini_model,
        )
        data = _loads_lenient(raw or "")
        if not isinstance(data, dict) or not isinstance(data.get("score"), (int, float)):
            raise ValueError(f"critic JSON thiếu score: {(raw or '')[:120]}")
        data["score"] = max(0.0, min(10.0, float(data["score"])))
        if isinstance(data.get("product_fit"), (int, float)):
            data["product_fit"] = max(0.0, min(10.0, float(data["product_fit"])))
        else:
            data["product_fit"] = None
        data["weaknesses"] = [str(w) for w in (data.get("weaknesses") or [])][:5]
        data["rewrite_hints"] = [str(h) for h in (data.get("rewrite_hints") or [])][:5]
        return data
    except Exception as exc:  # noqa: BLE001 — fail-open: critic không được nghẽn pipeline
        logger.warning(f"[critic] lỗi LLM → fail-open (không chấm): {str(exc)[:200]}")
        return {"score": None, "product_fit": None, "weaknesses": [], "rewrite_hints": []}
