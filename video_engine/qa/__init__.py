"""QA gate — cổng fidelity CỨNG: sai sản phẩm = không cho READY.

Hai cổng:
1. ``qa_image_match`` — CỔNG MATCH ảnh trung gian (trước khi đốt tiền video):
   Gemini vision so ảnh sinh ra với ảnh sản phẩm thật (logo/màu/shape).
2. ``qa_final_video`` — cổng final: file phát được, đúng tỷ lệ/thời lượng,
   khung hình giữa video vẫn khớp sản phẩm.

Mock provider → bỏ kiểm vision (đánh dấu skipped) vì ảnh mock không phải để bán.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess

from video_engine.director.critic import _loads_lenient

from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import settings
from core.config_checks import looks_real_secret
from core.logger import logger

_MATCH_THRESHOLD = 0.7
_CTA_KW_FINAL = ("like", "đăng ký", "đăng kí", "subscribe", "chia sẻ", "kênh")  # CTA đã ĐỌC ở đuôi video


def qa_image_match(product_image: str, generated_image: str) -> dict:
    """So ảnh sinh ra với ảnh SP thật. Trả {passed, score, logo_legible, reasons, skipped}."""
    if settings.use_fake_clients or settings.image_provider == "mock":
        return {"passed": True, "skipped": True, "reasons": ["mock mode — bỏ kiểm vision"]}
    if not (product_image and os.path.exists(product_image)):
        return {"passed": False, "skipped": False, "reasons": ["thiếu ảnh sản phẩm gốc để so"]}
    if not looks_real_secret(settings.gemini_api_key or ""):
        return {"passed": False, "skipped": False, "reasons": ["thiếu GEMINI_API_KEY cho QA vision"]}
    try:
        verdict = _gemini_compare(product_image, generated_image)
    except Exception as exc:  # noqa: BLE001 — fail-closed: QA lỗi thì không cho qua
        logger.warning(f"[qa] vision lỗi → chặn (fail-closed): {exc}")
        return {"passed": False, "skipped": False, "reasons": [f"qa_error: {str(exc)[:200]}"]}
    # Fix 2026-06-13: score=null (Gemini trả thiếu) KHÔNG được coerce về 0.0 (rớt gate, loại oan SP
    # đúng). Verdict thiếu score → fail-closed có lý do RÕ thay vì "score 0.0 < ngưỡng" mập mờ.
    if verdict.get("score") is None:
        return {"passed": False, "skipped": False, "reasons": ["Gemini không trả score hợp lệ"]}
    score = float(verdict.get("score"))
    # Fix 2026-06-11 (job 20 fail oan): sản phẩm KHÔNG có logo/chữ in → logo_legible vô nghĩa
    # (Gemini trả false vì không có gì để đọc) → CHỈ xét logo_legible khi has_logo_text=true.
    has_logo_text = bool(verdict.get("has_logo_text", True))  # thiếu khóa → coi như có (an toàn cũ)
    logo_legible = bool(verdict.get("logo_legible", True))
    # Fix 2026-06-13 (job 36 fail oan): clip khớp SP RẤT CAO (score >= ngưỡng) thì logo/nhãn không
    # đọc được KHÔNG được hard-fail — vd áo da có nhãn TRONG cổ áo, bị che khi MẶC nên Gemini chấm
    # logo_legible=false dù sản phẩm ĐÚNG (score 0.95). score THẤP + logo mờ vẫn chặn (chống SP sai).
    logo_ok = logo_legible or not has_logo_text or score >= settings.qa_logo_legible_exception_score
    # same_product thiếu/null → mặc định True (đối xứng has_logo_text/logo_legible mặc định True):
    # score>=ngưỡng đã là tín hiệu khớp, KHÔNG để bool(None)=False loại oan SP đúng. Echo ra dict
    # để audit phân biệt fail do mismatch thật vs do Gemini bỏ khóa.
    same_product = bool(verdict.get("same_product", True))
    passed = same_product and score >= _MATCH_THRESHOLD and logo_ok
    return {
        "passed": passed,
        "skipped": False,
        "score": score,
        "same_product": same_product,
        "has_logo_text": has_logo_text,
        "logo_legible": logo_legible,  # giá trị THẬT từ Gemini (passed mới là quyết định cổng)
        "logo_waived_by_score": bool(has_logo_text and not logo_legible and logo_ok),
        "reasons": [str(r) for r in (verdict.get("reasons") or [])][:5],
    }


def qa_final_video(
    *,
    final_path: str,
    expected_seconds: float,
    aspect: str,
    product_image: str = "",
    check_product_match: bool = True,
    expected_texts: list[str] | None = None,
    text_scan_until: float | None = None,
    narration: str = "",
    expect_cta: bool = False,
) -> dict:
    """Cổng final. Trả {passed, reasons, probes, + 3 cờ QA v2}.

    V8.3-Q5: 3 check v2 (``text_scan_ok``/``audio_ok``/``duration_ok``) KHÔNG đổi
    ``passed`` (gate fidelity cũ — job tay vẫn READY để founder duyệt mắt); chúng chỉ
    chặn AUTO-APPROVE của autopilot (B5.2). Text scan lỗi LLM → False (fail-closed
    cho tự duyệt — không verify được thì không tự đăng).
    """
    reasons: list[str] = []
    probe = _ffprobe(final_path)
    if probe is None:
        return {"passed": False, "reasons": ["file không tồn tại hoặc ffprobe đọc không được"]}
    duration = probe["duration"]
    width, height = probe["width"], probe["height"]
    if duration < 3.0:
        reasons.append(f"thời lượng quá ngắn: {duration:.1f}s")
    if expected_seconds and abs(duration - expected_seconds) > max(3.0, expected_seconds * 0.5):
        reasons.append(f"thời lượng lệch nhiều: {duration:.1f}s vs đặt {expected_seconds}s")
    ratio = (width / height) if height else 0.0
    # aspect wired (long_narrative 16:9). Guard theo aspect → job product 9:16 giữ nguyên byte-identical.
    if aspect == "16:9":
        if width <= height or abs(ratio - (16 / 9)) > 0.02:
            reasons.append(f"không đúng tỷ lệ 16:9: {width}x{height}")
    else:
        if height <= width or abs(ratio - (9 / 16)) > 0.006:
            reasons.append(f"không đúng tỷ lệ 9:16: {width}x{height}")

    match_report: dict = {"skipped": True}
    if check_product_match and product_image:
        frame = final_path + ".qa_frame.png"
        if _extract_middle_frame(final_path, duration, frame):
            match_report = qa_image_match(product_image, frame)
            if os.path.exists(frame):
                os.remove(frame)
            if not match_report.get("passed"):
                reasons.append(
                    "khung hình giữa video không khớp sản phẩm: "
                    + "; ".join(match_report.get("reasons") or [])
                )
        else:
            reasons.append("không trích được khung hình để QA sản phẩm")

    audio_ok, audio_detail = _qa_audio(final_path)
    # V8.4: 'chấm lọc kĩ' giọng bằng ASR THẬT (Groq) — có lời người? đúng tiếng Việt? khớp
    # kịch bản? (bắt giọng câm/sai ngôn ngữ/garbled/đọc nhầm). None = không verify được → fail-open.
    voice_ok: bool | None = None
    voice_detail: dict = {"skipped": "no narration"}
    if narration:
        from video_engine.voice.asr import check_voice
        voice_ok, voice_detail = check_voice(final_path, narration)
    duration_ok = bool(
        expected_seconds
        and abs(duration - expected_seconds) <= max(1.0, expected_seconds * 0.10)
    )
    # CTA tái kiểm trên VIDEO THÀNH PHẨM (long_narrative): đuôi transcript THẬT có kêu gọi like/đăng ký/
    # chia sẻ không — bắt trường hợp beat CTA bị rớt/cụt khi render. None = không ASR được (fail-open).
    # Cờ v2 (KHÔNG đổi `passed`, giống text_scan_ok) — chỉ chặn auto-approve, job tay vẫn READY để duyệt mắt.
    cta_ok: bool | None = None
    if expect_cta:
        tail = (voice_detail.get("asr_text_tail") or "").lower() if isinstance(voice_detail, dict) else ""
        if tail:
            cta_ok = any(k in tail for k in _CTA_KW_FINAL)
        # voice_ok None (không ASR được) → cta_ok giữ None (không verify được, fail-open)
    report = {
        "passed": not reasons,
        "reasons": reasons,
        "probes": {"duration_s": duration, "width": width, "height": height},
        "product_match": match_report,
        "audio_ok": audio_ok,
        "audio_detail": audio_detail,
        "voice_ok": voice_ok,
        "voice_detail": voice_detail,
        "duration_ok": duration_ok,
        "cta_ok": cta_ok,
    }
    if expected_texts is not None:
        # text_scan_until (V8.3): có đuôi CTA → CHỈ soi clip chính (nơi Seedance có thể vẽ
        # bậy); tail là local deterministic + dùng nguyên ẢNH SP của shop (ảnh đó có chữ
        # marketing hợp lệ — soi vào là flag oan, bài học job 34).
        scan_window = min(duration, text_scan_until) if text_scan_until else duration
        report["text_scan_ok"], report["text_scan"] = _qa_text_scan(
            final_path, scan_window, expected_texts
        )
    return report


def _qa_audio(final_path: str) -> tuple[bool, dict]:
    """V8.3-Q5(b): volumedetect — mean ∈ [−22,−12] dB, max ≤ −0.3 dB, không câm ($0)."""
    try:
        proc = subprocess.run(
            ["ffmpeg", "-i", final_path, "-af", "volumedetect", "-f", "null", "-"],
            capture_output=True, text=True, timeout=300,
        )
        mean = max_v = None
        for line in proc.stderr.splitlines():
            if "mean_volume" in line:
                mean = float(line.split(":")[-1].replace("dB", "").strip())
            elif "max_volume" in line:
                max_v = float(line.split(":")[-1].replace("dB", "").strip())
        if mean is None or max_v is None:
            return False, {"error": "không parse được volumedetect"}
        ok = -22.0 <= mean <= -12.0 and max_v <= -0.3 and mean > -50.0
        return ok, {"mean_db": mean, "max_db": max_v}
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        return False, {"error": str(exc)[:150]}


def _qa_text_scan(final_path: str, duration: float, expected_texts: list[str]) -> tuple[bool, dict]:
    """V8.3-Q5(a): 3 frame → 1 call Gemini vision — chữ lỗi glyph / chữ LẠ ngoài danh sách
    (Seedance lén vẽ) → False. LLM lỗi → False (fail-closed cho auto-approve)."""
    frames: list[str] = []
    try:
        for i, ts in enumerate((1.5, duration / 2, max(0.5, duration - 1.5))):
            frame = f"{final_path}.scan{i}.jpg"
            proc = subprocess.run(
                ["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{ts:.2f}",
                 "-i", final_path, "-frames:v", "1", frame],
                capture_output=True, text=True, timeout=60,
            )
            if proc.returncode == 0 and os.path.exists(frame):
                frames.append(frame)
        if not frames:
            return False, {"error": "không trích được frame"}
        verdict = _gemini_text_scan(frames, expected_texts)
        ok = not bool(verdict.get("garbled")) and not bool(verdict.get("unexpected"))
        return ok, verdict
    except Exception as exc:  # noqa: BLE001 — không verify được = không cho tự duyệt
        logger.warning(f"[qa] text scan lỗi → text_scan_ok=False: {str(exc)[:150]}")
        return False, {"error": str(exc)[:150]}
    finally:
        for frame in frames:
            try:
                os.remove(frame)
            except OSError:
                pass


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=12), reraise=True)
def _gemini_text_scan(frames: list[str], expected_texts: list[str]) -> dict:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=settings.gemini_api_key)
    parts: list = []
    for path in frames:
        with open(path, "rb") as f:
            parts.append(types.Part.from_bytes(data=f.read(), mime_type="image/jpeg"))
    expected = json.dumps(expected_texts, ensure_ascii=False)
    parts.append(
        "Đây là 3 khung hình từ 1 video quảng cáo. DANH SÁCH CHỮ MONG ĐỢI (overlay đồ hoạ "
        f"được phép xuất hiện): {expected}. Chữ in sẵn trên BAO BÌ/NHÃN sản phẩm là bình "
        "thường — KHÔNG tính. Kiểm tra: (1) garbled = có chữ overlay nào lỗi glyph/sai dấu "
        "tiếng Việt/méo không đọc được? (2) unexpected = có chữ overlay đồ hoạ NGOÀI danh "
        "sách mong đợi (watermark, caption lạ, chữ AI tự vẽ)? "
        'Trả JSON: {"texts_seen": ["..."], "garbled": bool, "unexpected": bool}'
    )
    resp = client.models.generate_content(
        model=settings.gemini_model,
        contents=parts,
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    return _loads_lenient(resp.text or "")


# ── helpers ───────────────────────────────────────────────────────────
@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=12), reraise=True)
def _gemini_compare(product_image: str, generated_image: str) -> dict:
    """So 2 ảnh bằng Gemini vision (retry 503/transient — QA lỗi hẳn mới fail-closed)."""
    import mimetypes

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=settings.gemini_api_key)
    parts = []
    for label, path in (("ẢNH GỐC SẢN PHẨM", product_image), ("ẢNH SINH RA", generated_image)):
        mime = mimetypes.guess_type(path)[0] or "image/png"
        with open(path, "rb") as f:
            parts.append(types.Part.from_bytes(data=f.read(), mime_type=mime))
        parts.append(label)
    parts.append(
        "So sánh 2 ảnh: ẢNH SINH RA có đúng là CÙNG sản phẩm với ẢNH GỐC không "
        "(logo, màu sắc, hình dáng, chi tiết nhận diện)? "
        "has_logo_text: ẢNH GỐC có logo/chữ IN trên sản phẩm không (không có → false)? "
        "logo_legible: NẾU có logo/chữ thì trong ẢNH SINH RA có đọc được không "
        "(sản phẩm không có logo/chữ → logo_legible=true). "
        'Trả về JSON: {"same_product": bool, "score": 0..1, "has_logo_text": bool, '
        '"logo_legible": bool, "reasons": ["..."]}'
    )
    resp = client.models.generate_content(
        model=settings.gemini_model,
        contents=parts,
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    return _loads_lenient(resp.text or "")


def _ffprobe(path: str) -> dict | None:
    if not path or not os.path.exists(path) or shutil.which("ffprobe") is None:
        return None
    proc = subprocess.run(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height:format=duration",
            "-of", "json", path,
        ],
        capture_output=True, text=True, timeout=60,
    )
    if proc.returncode != 0:
        return None
    try:
        data = json.loads(proc.stdout)
        stream = (data.get("streams") or [{}])[0]
        return {
            "duration": float((data.get("format") or {}).get("duration") or 0.0),
            "width": int(stream.get("width") or 0),
            "height": int(stream.get("height") or 0),
        }
    except (ValueError, TypeError, KeyError):
        return None


def _extract_middle_frame(video_path: str, duration: float, out_path: str) -> bool:
    if shutil.which("ffmpeg") is None:
        return False
    midpoint = max(0.5, duration / 2)
    proc = subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error",
            "-ss", f"{midpoint:.2f}", "-i", video_path,
            "-frames:v", "1", out_path,
        ],
        capture_output=True, text=True, timeout=60,
    )
    return proc.returncode == 0 and os.path.exists(out_path)
