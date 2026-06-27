"""film_recap/script_recap.py — sinh kịch bản recap GỐC từ transcript phim (1 call LLM).

Tái dùng complete_with_fallback (như director.py). KHÔNG fork director.generate_script: nó ép phong
cách điểm-tin-nhiều-nguồn + schema ảnh-gen + bắt buộc CTA đăng-ký-kênh → sai ngữ cảnh recap phim.
"""
from __future__ import annotations

import json

from core.logger import logger

_SYSTEM_RECAP = (
    "Bạn là người kể chuyện phim trên TikTok/YouTube tiếng Việt. Nhiệm vụ: TÓM TẮT / BÌNH LUẬN lại "
    "một đoạn phim dựa trên transcript, bằng LỜI CỦA BẠN (KHÔNG chép nguyên thoại nhân vật). Giọng "
    "tự nhiên, cuốn, hài duyên; KHÔNG từ đệm sáo ('các bạn ơi', 'và rồi thì'); mỗi câu là 1 nhịp kể "
    "ngắn (1-2 câu), mạch lạc, không spoiler sạch cái kết."
)


def generate_recap_script(transcript_text: str, *, n_beats: int) -> list[str]:
    """LLM → N câu bình luận/tóm tắt GỐC. Fail-soft → [] (caller fallback)."""
    text = (transcript_text or "").strip()
    if not text:
        return []
    n = max(3, min(15, int(n_beats)))
    user = (
        f'Transcript phim (có thể lẫn tạp/ASR thô):\n"""{text[:6000]}"""\n\n'
        f"Viết ĐÚNG {n} câu kể/bình recap, mỗi câu 1 nhịp. Xuất JSON THUẦN, không markdown: "
        f'{{"beats": ["câu 1", "câu 2", ...]}}'
    )
    try:
        from config.settings import settings
        from module2_brain.llm.v5_clients import complete_with_fallback
        raw = complete_with_fallback(_SYSTEM_RECAP, user, gemini_model=settings.gemini_model)
    except Exception as exc:  # noqa: BLE001 — fail-soft
        logger.warning(f"[film_recap] LLM recap lỗi: {str(exc)[:160]}")
        return []
    lines = _parse_beats(raw)
    if not lines:
        logger.warning("[film_recap] recap script parse rỗng.")
    return lines[:n]


def _parse_beats(raw: str) -> list[str]:
    """Parse JSON {beats:[...]} (trích khối {...}); fallback tách dòng phi-rỗng."""
    s = (raw or "").strip()
    try:
        i, j = s.find("{"), s.rfind("}")
        if i >= 0 and j > i:
            data = json.loads(s[i:j + 1])
            if isinstance(data, dict) and isinstance(data.get("beats"), list):
                return [str(b).strip() for b in data["beats"] if str(b).strip()]
    except (ValueError, TypeError):
        pass
    return [ln.strip("-•*0123456789. \t") for ln in s.splitlines() if len(ln.strip()) > 8]
