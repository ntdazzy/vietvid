"""shot_critic.py — CRITIC chấm điểm shot-plan (lớp an toàn chất lượng Stage 2, founder chốt).

AI thứ 2 chấm bố cục đạo diễn theo rubric 5 tiêu chí + trả góp ý 1 dòng → planner regen 1 lần nếu yếu.
Dùng model NHANH (gemini-2.5-flash/Groq) để giảm độ trễ. FAIL-SOFT: LLM lỗi → chấm bằng heuristic tất định
(tỉ lệ người dẫn, glitch, đa dạng chất liệu) — KHÔNG bao giờ làm hỏng pipeline.

KHÔNG import shot_planner (tránh vòng) — chỉ ĐỌC field của ShotSpec (duck-typed).
"""

from __future__ import annotations

import json
import re

from config.settings import settings
from core.logger import logger

_SYSTEM = (
    "Bạn là GIÁM ĐỐC HÌNH ẢNH khó tính của kênh Vui Vẻ/Lóng. Chấm shot-plan theo 5 tiêu chí: "
    "1) CHẤT LIỆU khớp nội dung; 2) NHỊP nhanh ~2-3s + đa dạng; 3) NGƯỜI DẪN ~55% shot (HÌNH CHÍNH kênh, "
    "mỗi lần 1 pose khác), B-roll ĐƠN GIẢN (icon/ảnh/logo), KHÔNG cảnh doodle phức tạp; "
    "4) CHUYỂN ĐỘNG khớp cảm xúc; 5) KHÔNG LẶP KHUÔN NỘI DUNG. ⛔ PHẠT NẶNG (score ≤4) nếu nhiều shot cùng tả "
    "1 CẢNH (vd lặp '2 người đối đầu/chỉ tay nhau') — founder than 'video toàn 1 ảnh'. Mỗi shot phải 1 CHỦ "
    "THỂ/GÓC KHÁC. feedback PHẢI chỉ rõ shot nào lặp + bảo tách single-subject. "
    "CHỈ trả JSON {\"score\":<0-10>,\"feedback\":\"1 câu sửa cụ thể\"}."
)


def _summarize(specs: list, beat) -> str:
    rows = []
    for i, s in enumerate(specs):
        p = "none" if s.presenter is None else f"{s.presenter.get('role')}/{s.presenter.get('side')}"
        c = s.content
        subj = (c.get("hint") or c.get("entity") or c.get("query") or "")[:50]   # ĐƯA NỘI DUNG cho critic THẤY
        rows.append(f"  {i}: seg{s.seg} {c.get('kind')} \"{subj}\" presenter={p}")
    return f"BEAT cảm-xúc={beat.context} callout='{beat.callout}'\nSHOTS (xem CỘT nội dung — bắt LẶP):\n" + "\n".join(rows)


_CONF_KW = ("đối đầu", "đối đầu", "cãi", "versus", " vs ", "vs.", "cả hai", "hai người", "hai cầu thủ",
            "đối thủ", "chỉ tay nhau", "tay đôi", "so kè", "đấu nhau")


def _content_flags(specs: list) -> tuple[float, int]:
    """(tỉ-lệ-hint-ĐỘC-NHẤT, số-shot-ĐỐI-ĐẦU). Critic MÙ nội dung là lý do video 'toàn 1 ảnh' → đo ở đây."""
    hints = [(s.content.get("hint") or s.content.get("entity") or s.content.get("query") or "").lower().strip()
             for s in specs]
    hints = [h for h in hints if h]
    if len(hints) < 3:
        return 1.0, 0
    conf = sum(1 for h in hints if any(k in h for k in _CONF_KW))
    sigs = [" ".join(h.split()[:3]) for h in hints]               # chữ ký 3-từ-đầu
    uniq = len(set(sigs)) / len(sigs)
    return uniq, conf


def _heuristic(specs: list) -> float:
    """Chấm tất định khi không có LLM: phạt thiếu/thừa người dẫn, glitch nhiều, kém đa dạng chất liệu + NỘI DUNG."""
    n = len(specs) or 1
    pres_ratio = sum(1 for s in specs if s.presenter is not None) / n
    glitch_ratio = sum(1 for s in specs if s.transition_in == "glitch") / n
    kinds = len({s.content.get("kind") for s in specs})
    uniq, conf = _content_flags(specs)
    score = 8.0
    if pres_ratio < 0.4:
        score -= 2.0                       # người dẫn LÀ HÌNH CHÍNH kênh (~55%) — quá ít = không bám kênh gốc
    elif pres_ratio > 0.85:
        score -= 1.5                       # quá nhiều = thiếu B-roll đổi cảnh
    if glitch_ratio > 0.25:
        score -= 1.5
    if n >= 3 and kinds == 1:
        score -= 1.0                       # 1 chất liệu duy nhất = đơn điệu
    if uniq < 0.6:
        score -= 2.5                       # NHIỀU hint NA NÁ nhau = "toàn 1 ảnh"
    if conf > 1:
        score -= 2.0                       # >1 cảnh "đối đầu/2 người" = lặp khuôn founder ghét
    return max(0.0, score)


def score_plan(specs: list, beat) -> tuple[float, str]:
    """Trả (điểm 0-10, góp ý). LLM lỗi → (heuristic, "") (không regen vô ích nếu không có góp ý cụ thể)."""
    from module2_brain.llm.v5_clients import complete_with_fallback

    # CHẶN CỨNG tất định nội dung — áp DÙ LLM chấm cao (critic LLM hay bỏ sót lặp). Đây là lưới an toàn
    # chống "video toàn 1 ảnh" founder than: nhiều hint na ná / >1 cảnh đối-đầu → ép điểm thấp + feedback rõ.
    uniq, conf = _content_flags(specs)
    det_fb = ""
    if conf > 1:
        det_fb = (f"CÓ {conf} shot tả cảnh '2 người đối đầu/cùng khung' — LẶP, founder ghét. Giữ TỐI ĐA 1, "
                  "các shot kia tách SINGLE-SUBJECT (1 cầu thủ riêng làm động tác / 1 cúp / 1 con số / 1 "
                  "countryball / 1 meme phản ứng). ")
    if uniq < 0.6:
        det_fb += "NHIỀU hint na ná nhau — mỗi shot phải 1 CHỦ THỂ/GÓC KHÁC hẳn, trộn kind (doodle/meme/countryball/diagram/object). "
    det_cap = 4.0 if (conf > 1 or uniq < 0.6) else 10.0   # có lặp → trần 4 (dưới ngưỡng 7 → bắt regen)

    try:
        raw = complete_with_fallback(_SYSTEM, _summarize(specs, beat), gemini_model=settings.gemini_model)
        text = (raw or "").strip()
        if text.startswith("```"):
            text = re.sub(r"^```[a-z]*\s*|\s*```$", "", text, flags=re.IGNORECASE | re.MULTILINE)
        m = re.search(r"\{.*\}", text, re.DOTALL)
        data = json.loads(m.group(0)) if m else {}
        score = float(data.get("score", _heuristic(specs)))
        score = min(score, det_cap)                                   # ép trần nếu lặp nội dung
        fb = (det_fb + str(data.get("feedback") or "")).strip()[:300]
        return (max(0.0, min(10.0, score)), fb)
    except Exception as exc:  # noqa: BLE001 — fail-soft: heuristic CÓ phạt nội dung + feedback tất định → vẫn regen được
        logger.warning(f"[critic] LLM lỗi → heuristic: {str(exc)[:120]}")
        return (min(_heuristic(specs), det_cap), det_fb.strip())
