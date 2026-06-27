"""Upload 1 video MẪU → bóc PHONG CÁCH QUAY (camera/chuyển động/nhịp/ánh sáng/bối cảnh) → soạn
1 video_prompt cho Seedance TÁI TẠO LẠI phong cách clip đó cho sản phẩm của user.

Cố ý CHỈ mô tả KỸ THUẬT QUAY (KHÔNG mô tả cơ thể/ngoại hình người): đúng mục đích style-transfer
cho video bán hàng, và giữ ràng buộc LỊCH SỰ của _scene_brief (người trưởng thành, khoe đồ thanh
lịch, không gợi cảm). KHÔNG bypass bộ lọc an toàn của Gemini — nếu Gemini từ chối clip
(PROHIBITED_CONTENT) thì trả lý do TRUNG THỰC để UI hướng dẫn dùng clip/ảnh khác.
"""

from __future__ import annotations

import json
import time

from config.settings import settings
from core.config_checks import looks_real_secret
from core.logger import logger

_STYLE_INSTRUCTION = (
    "Watch this short reference clip and extract ONLY its PRODUCTION STYLE so a similar "
    "product-marketing clip can be recreated. Do NOT describe the person's body, looks or clothing in "
    "any sexual way. Return ONLY a JSON object with keys: "
    '"camera" (static/handheld, angle, distance), "movement" (camera/subject motion), '
    '"pacing" (cuts vs holds, rhythm), "framing" (composition, headroom, crop), '
    '"lighting" (source/quality), "setting" (location/background/mood), '
    '"beats" (array of {"t":"0-3s","beat":"camera + action by timecode"}).'
)

_COMPOSE_INSTRUCTION = (
    "You are a prompt engineer for the Seedance video model. Using the PRODUCTION-STYLE breakdown "
    "below (from a reference clip), write ONE English video_prompt that recreates that style for the "
    "TARGET PRODUCT. Rules: vertical 9:16, authentic hand-held UGC phone video, natural lighting "
    "matching the reference. The subject is an ADULT model who DIRECTLY WEARS and showcases the "
    "product in a TASTEFUL, modest way (standing lookbook poses, change of angles); do NOT emphasise "
    "or sexualise the body, no suggestive framing. Map the reference camera/movement/pacing onto the "
    "product showcase, as timecoded beats summing to about {seconds} seconds. Output ONLY the prompt "
    "text (English, ~180-260 words, no markdown, no preamble)."
)


def _probe_duration(path: str) -> float:
    try:
        from video_engine.compose.ffmpeg import FFmpegProcessor

        return float(FFmpegProcessor.probe_duration(path) or 0.0)
    except Exception:  # noqa: BLE001 — duration phụ, lỗi → 0
        return 0.0


def _blocked(resp) -> bool:
    """True nếu Gemini CHẶN nội dung (finish_reason PROHIBITED/SAFETY/BLOCK)."""
    for c in (getattr(resp, "candidates", None) or []):
        fr = str(getattr(c, "finish_reason", "") or "").upper()
        if "PROHIBIT" in fr or "SAFETY" in fr or "BLOCK" in fr:
            return True
    return False


def _parse_json(text: str) -> dict:
    text = (text or "").strip()
    if not text:
        return {}
    if text.startswith("```"):
        import re

        text = re.sub(r"^```[a-z]*\s*|\s*```$", "", text, flags=re.IGNORECASE | re.MULTILINE)
    try:
        d = json.loads(text)
        return d if isinstance(d, dict) else {}
    except ValueError:
        import re

        m = re.search(r"\{.*\}", text, re.DOTALL)
        try:
            return json.loads(m.group(0)) if m else {}
        except ValueError:
            return {}


def _read_sample_style(video_path: str) -> dict:
    """Upload video lên Gemini Files API → đọc phong cách quay. Trả {ok, style, reason}."""
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.gemini_api_key)
        f = client.files.upload(file=video_path)
        for _ in range(30):  # chờ xử lý server-side (~tới 60s)
            st = getattr(getattr(f, "state", None), "name", "") or str(getattr(f, "state", ""))
            if st == "ACTIVE":
                break
            if st == "FAILED":
                return {"ok": False, "style": {}, "reason": "Gemini xử lý video thất bại — thử file khác."}
            time.sleep(2)
            f = client.files.get(name=f.name)
        resp = client.models.generate_content(
            model=settings.gemini_model,
            contents=[f, _STYLE_INSTRUCTION],
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        try:
            client.files.delete(name=f.name)
        except Exception:  # noqa: BLE001 — dọn best-effort
            pass
        if _blocked(resp):
            return {
                "ok": False, "style": {},
                "reason": "Gemini TỪ CHỐI phân tích clip này (nội dung nhạy cảm). "
                "Hãy dùng video mẫu phù hợp hơn, hoặc tải ẢNH sản phẩm để tạo clip.",
            }
        style = _parse_json(getattr(resp, "text", "") or "")
        if not style:
            return {"ok": False, "style": {}, "reason": "Không bóc được phong cách từ video — thử clip khác."}
        return {"ok": True, "style": style, "reason": ""}
    except Exception as exc:  # noqa: BLE001 — fail-soft
        logger.warning(f"[sample-to-prompt] đọc video lỗi: {str(exc)[:200]}")
        return {"ok": False, "style": {}, "reason": f"Lỗi đọc video: {str(exc)[:160]}"}


def _fallback_prompt(style: dict, product_name: str, seconds: int) -> str:
    who = product_name or "the product"
    head = (
        f"Vertical 9:16 authentic hand-held UGC phone video, natural lighting. An adult model directly "
        f"wears and showcases {who} in tasteful standing lookbook poses, changing angles; modest "
        f"framing, no sexualisation. ~{seconds}s. Recreate this production style:\n"
    )
    return (head + json.dumps(style, ensure_ascii=False, indent=2))[:3500]


def analyze_sample_to_seedance_prompt(
    video_path: str, *, product_name: str = "", product_desc: str = "", seconds: int = 5
) -> dict:
    """Trả {ok, video_prompt, breakdown, duration, reason}. Fail-soft + lý do TRUNG THỰC."""
    duration = _probe_duration(video_path)
    if not looks_real_secret(settings.gemini_api_key or ""):
        return {
            "ok": False, "reason": "Chưa cấu hình GEMINI_API_KEY → không quét được video.",
            "video_prompt": "", "breakdown": {}, "duration": duration,
        }

    read = _read_sample_style(video_path)
    if not read["ok"]:
        return {"ok": False, "reason": read["reason"], "video_prompt": "", "breakdown": {}, "duration": duration}
    style = read["style"]

    secs = seconds or (max(4, min(15, int(round(duration)))) if duration else 5)
    video_prompt = ""
    try:
        from google import genai

        client = genai.Client(api_key=settings.gemini_api_key)
        target = f"TARGET PRODUCT: {product_name or '(unspecified apparel)'}."
        if product_desc:
            target += f" Details: {product_desc}"
        resp = client.models.generate_content(
            model=settings.gemini_model,
            contents=[
                _COMPOSE_INSTRUCTION.format(seconds=secs),
                target,
                "PRODUCTION-STYLE BREAKDOWN (JSON):\n" + json.dumps(style, ensure_ascii=False),
            ],
        )
        if not _blocked(resp):
            video_prompt = (getattr(resp, "text", "") or "").strip()
    except Exception as exc:  # noqa: BLE001 — fail-soft → fallback template
        logger.warning(f"[sample-to-prompt] soạn prompt lỗi → fallback: {str(exc)[:160]}")

    if not video_prompt:
        video_prompt = _fallback_prompt(style, product_name, secs)

    return {"ok": True, "video_prompt": video_prompt[:3500], "breakdown": style, "duration": duration, "reason": ""}
