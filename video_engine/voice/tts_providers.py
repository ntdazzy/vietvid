"""TTS provider trả phí (Vbee) — fail-closed + sổ ngân sách ngày, theo khuôn motion.py.

edge-tts vẫn do TTSEngine xử lý; module này CHỈ cung cấp provider HTTP trả phí.
build_tts_provider() trả None khi tts_provider là edge/none → TTSEngine dùng đường cũ.
Fail-closed: bật provider trả phí mà thiếu key/voice/budget → raise RenderError (không giả lập giọng).
Endpoint thật có thể khác theo hợp đồng tài khoản → cần live-smoke khi go-live (như motion/FASHN).
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from datetime import datetime, timezone
from typing import Protocol

import httpx

from config.settings import settings
from core.config_checks import looks_real_secret
from core.exceptions import RenderError
from video_engine.compose.ffmpeg import FFmpegProcessor

_VBEE_POLL_INTERVAL_SECONDS = 2.0
_VBEE_POLL_MAX_ATTEMPTS = 30


class TTSProvider(Protocol):
    name: str

    def synthesize(self, text: str, out_path: str) -> float:
        """Sinh audio vào out_path, trả về thời lượng (giây)."""


# ── Sổ ngân sách ngày (mirror motion._reserve_budget) ─────────────────────────
def _read_tts_ledger() -> dict:
    path = settings.tts_budget_ledger_path
    if not path or not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as fh:
            payload = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_tts_ledger(payload: dict) -> None:
    path = settings.tts_budget_ledger_path
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2, sort_keys=True)
    os.replace(tmp, path)


def tts_budget_ready() -> bool:
    return (
        float(settings.tts_daily_budget_usd or 0.0) > 0
        and float(settings.tts_estimated_cost_per_call_usd or 0.0) > 0
    )


def _reserve_tts_budget(name: str) -> float:
    budget = float(settings.tts_daily_budget_usd or 0.0)
    cost = float(settings.tts_estimated_cost_per_call_usd or 0.0)
    if budget <= 0 or cost <= 0:
        raise RenderError(
            "TTS provider trả phí cần TTS_DAILY_BUDGET_USD và TTS_ESTIMATED_COST_PER_CALL_USD > 0 "
            "để tránh phát sinh chi phí ngoài ý muốn."
        )
    today = datetime.now(timezone.utc).date().isoformat()
    ledger = _read_tts_ledger()
    day = ledger.setdefault(today, {})
    spent = float(day.get(name, 0.0) or 0.0)
    if spent + cost > budget:
        raise RenderError(
            f"TTS budget vượt giới hạn ngày: spent={spent:.4f}, cost={cost:.4f}, budget={budget:.2f}."
        )
    day[name] = round(spent + cost, 4)
    _write_tts_ledger(ledger)
    return cost


# ── Providers ─────────────────────────────────────────────────────────────────
# V8.2 D3: ElevenLabs đã xoá — TTS trả phí còn vbee (fallback edge-tts free trong TTSEngine).
class VbeeProvider:
    """Vbee TTS (async job): POST /api/v1/tts (Bearer) → request_id → poll → tải audio_link."""

    name = "vbee"

    def __init__(self, app_id: str, api_token: str, voice_code: str) -> None:
        self.app_id = app_id
        self.api_token = api_token
        # V7-B4: VBEE_VOICE_CODE có thể là DANH SÁCH nhiều giọng (ngăn bởi dấu phẩy) — founder đặt
        # nhiều voice để tùy ngành. Tách list; truyền NGUYÊN chuỗi nhiều-mã cho Vbee = lỗi, nên
        # dùng giọng đầu làm mặc định. (Chọn-giọng-theo-ngành đầy đủ: follow-on, cần luồng category.)
        self.voice_codes = [v.strip() for v in (voice_code or "").split(",") if v.strip()]
        self.voice_code = self.voice_codes[0] if self.voice_codes else (voice_code or "").strip()
        self.base = "https://vbee.vn/api/v1"

    def voice_for(self, seed: str = "") -> str:
        """Chọn 1 giọng từ list theo seed (vd category sản phẩm) — deterministic; rỗng→giọng đầu."""
        if not self.voice_codes:
            return self.voice_code
        if not seed:
            return self.voice_codes[0]
        return self.voice_codes[sum(ord(c) for c in seed) % len(self.voice_codes)]

    def synthesize(self, text: str, out_path: str) -> float:
        _reserve_tts_budget(self.name)
        headers = {"Authorization": f"Bearer {self.api_token}"}
        callback_url = _validated_vbee_callback_url()
        # Audio v2 (2026-06-11): WAV không nén (mp3 vbee nén làm "lùng bùng" khi mix lại) +
        # speed_rate chỉnh nhịp đọc (1.0 = tự nhiên; founder tune VBEE_SPEED_RATE).
        create = httpx.post(
            f"{self.base}/tts",
            headers=headers,
            json={
                "app_id": self.app_id,
                "input_text": text,
                "voice_code": self.voice_code,
                "audio_type": "wav",
                "speed_rate": float(settings.vbee_speed_rate or 1.0),
                "callback_url": callback_url,
            },
            timeout=settings.tts_timeout_seconds,
        )
        create.raise_for_status()
        request_id = str((create.json().get("result") or {}).get("request_id") or "").strip()
        if not request_id:
            raise RenderError("Vbee không trả request_id hợp lệ.")
        audio_link = self._poll_audio_link(request_id, headers)
        # Vbee trả audio_link redirect 302 → S3 pre-signed; PHẢI follow redirect để tải mp3.
        download = httpx.get(
            audio_link, follow_redirects=True, timeout=settings.tts_timeout_seconds
        )
        download.raise_for_status()
        with open(out_path, "wb") as fh:
            fh.write(download.content)
        return FFmpegProcessor.probe_duration(out_path)

    def _poll_audio_link(self, request_id: str, headers: dict) -> str:
        for attempt in range(_VBEE_POLL_MAX_ATTEMPTS):
            try:
                status = httpx.get(
                    f"{self.base}/tts/{request_id}",
                    headers=headers,
                    timeout=settings.tts_timeout_seconds,
                )
            except httpx.HTTPError as exc:
                if attempt >= _VBEE_POLL_MAX_ATTEMPTS - 1:
                    raise RenderError(f"Vbee TTS lỗi mạng khi poll: {exc}") from exc
                time.sleep(_VBEE_POLL_INTERVAL_SECONDS)
                continue
            if 400 <= status.status_code < 500:
                raise RenderError(
                    f"Vbee TTS poll bị từ chối HTTP {status.status_code}; kiểm token/request_id."
                )
            if status.status_code >= 500:
                if attempt >= _VBEE_POLL_MAX_ATTEMPTS - 1:
                    raise RenderError(f"Vbee TTS poll lỗi server HTTP {status.status_code}.")
                time.sleep(_VBEE_POLL_INTERVAL_SECONDS)
                continue
            status.raise_for_status()
            result = status.json().get("result") or {}
            state = str(result.get("status") or "").upper()
            if state in {"SUCCESS", "DONE", "COMPLETED"}:
                link = str(result.get("audio_link") or "").strip()
                if link.startswith("https://"):
                    return link
                raise RenderError("Vbee trả status thành công nhưng thiếu audio_link HTTPS.")
            if state in {"FAILED", "ERROR", "FAILURE"}:
                raise RenderError(f"Vbee TTS thất bại sớm: status={state}.")
            if attempt < _VBEE_POLL_MAX_ATTEMPTS - 1:
                time.sleep(
                    _VBEE_POLL_INTERVAL_SECONDS
                )  # chờ job async, tránh nã 30 request tức thì
        raise RenderError("Vbee TTS quá hạn chờ (timeout poll).")


class GeminiTTSProvider:
    """Gemini 2.5 TTS — prosody tự nhiên, ra lệnh được phong cách đọc (V8.3-Q2).

    Giọng chọn theo gender NGAY LÚC BUILD (Kore nữ / Puck nam — đổi qua registry);
    PCM 24kHz 16-bit mono từ inline_data → wav → ffmpeg chuẩn hoá 48k mono cho Audio v2.
    """

    name = "gemini_tts"

    def __init__(self, api_key: str, model: str, voice: str, *, is_male: bool = False) -> None:
        self.api_key = api_key
        self.model = model
        self.voice = voice
        self.is_male = is_male

    def synthesize(self, text: str, out_path: str) -> float:
        _reserve_tts_budget(self.name)
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=self.api_key)
        # Style prompt PHẢI khớp giới tính giọng đã chọn (Puck nam / Autonoe nữ); trước đây ép
        # "con gái teen" cho cả giọng nam → mâu thuẫn, giọng nam bị bảo đọc như con gái.
        if self.is_male:
            style = (
                "Đọc bằng giọng CON TRAI Việt trẻ trung, năng động, tự tin thân thiện, "
                "nhịp nhanh tự nhiên như đang tám với hội bạn, nhấn nhá cảm xúc, KHÔNG đều đều: "
            )
        else:
            style = (
                "Đọc bằng giọng CON GÁI TEEN Việt dễ thương, trẻ trung, tươi vui nhí nhảnh, "
                "nhịp nhanh tự nhiên như đang tám với hội bạn, nhấn nhá cảm xúc, KHÔNG đều đều: "
            )
        resp = client.models.generate_content(
            model=self.model,
            contents=style + text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=self.voice)
                    )
                ),
            ),
        )
        try:
            pcm = resp.candidates[0].content.parts[0].inline_data.data
        except (AttributeError, IndexError, TypeError) as exc:
            raise RenderError(f"Gemini TTS không trả audio inline_data: {exc}") from exc
        raw = out_path + ".raw.wav"
        import wave

        # try/finally GỘP cả ghi wav + transcode → raw KHÔNG rò khi writeframes lỗi (disk full/OOM).
        try:
            with wave.open(raw, "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(24000)
                wav.writeframes(pcm)
            # voice_speed: atempo nói nhanh hơn (giữ cao độ; gemini không có tham số rate).
            speed = float(settings.voice_speed or 1.0)
            af = ["-filter:a", f"atempo={speed:.3f}"] if abs(speed - 1.0) > 0.01 else []
            proc = subprocess.run(
                ["ffmpeg", "-y", "-loglevel", "error", "-i", raw,
                 *af, "-ar", "48000", "-ac", "1", out_path],
                capture_output=True, text=True, timeout=120,
            )
            if proc.returncode != 0:
                raise RenderError(f"Gemini TTS transcode 48k lỗi: {proc.stderr[:200]}")
        finally:
            if os.path.exists(raw):
                os.remove(raw)
        return FFmpegProcessor.probe_duration(out_path)


class NotConfiguredTTSProvider:
    """Fail-closed: provider trả phí được bật nhưng thiếu cấu hình."""

    def __init__(self, name: str, missing: str) -> None:
        self.name = name
        self.missing = missing

    def synthesize(self, text: str, out_path: str) -> float:
        raise RenderError(
            f"TTS provider {self.name} chưa cấu hình {self.missing}; không giả lập giọng khi đã bật."
        )


def vbee_if_configured() -> VbeeProvider | None:
    """VbeeProvider khi đủ cấu hình — dùng cho TTS_PROVIDER=vbee VÀ fallback của gemini_tts.

    2026-06-13 (fix giọng rớt xuống edge monotone): chấp nhận khi CÓ bất kỳ kho giọng nào —
    VBEE_VOICE_CODE *hoặc* VBEE_VOICE_CODE_MALE/_FEMALE (founder thường chỉ set male/female).
    Gộp cả 3 thành danh sách → caller (_segment_engines/pick) chọn theo gender.
    """
    codes = ",".join(
        c.strip()
        for c in (settings.vbee_voice_code, settings.vbee_voice_code_male, settings.vbee_voice_code_female)
        if (c or "").strip()
    )
    if (
        looks_real_secret(settings.vbee_api_token, min_length=12)
        and (settings.vbee_app_id or "").strip()
        and codes
        and tts_budget_ready()
        and _vbee_callback_url_ready()
    ):
        return VbeeProvider(settings.vbee_app_id, settings.vbee_api_token, codes)
    return None


def build_tts_provider(gender: str = "") -> TTSProvider | None:
    """None → edge-tts do TTSEngine xử lý. Provider trả phí → fail-closed nếu thiếu cấu hình.

    ``gender`` ("nam"/"nữ"/"male"/"female") chỉ gemini_tts dùng — chọn giọng lúc build;
    vbee chọn giọng qua voice_code nên bỏ qua.
    """
    provider = (settings.tts_provider or "edge").strip().lower()
    if provider in {"", "edge", "none"}:
        return None
    if provider == "vbee":
        return vbee_if_configured() or NotConfiguredTTSProvider(
            "vbee",
            "VBEE_APP_ID + VBEE_API_TOKEN + VBEE_VOICE_CODE + VBEE_CALLBACK_URL thật "
            "+ TTS_DAILY_BUDGET_USD",
        )
    if provider == "gemini_tts":
        if looks_real_secret(settings.gemini_api_key, min_length=12) and tts_budget_ready():
            is_male = (gender or "").strip().lower() in {"nam", "male", "m"}
            voice = settings.gemini_tts_voice_male if is_male else settings.gemini_tts_voice_female
            return GeminiTTSProvider(
                settings.gemini_api_key, settings.gemini_tts_model, voice, is_male=is_male
            )
        return NotConfiguredTTSProvider(
            "gemini_tts", "GEMINI_API_KEY thật + TTS_DAILY_BUDGET_USD"
        )
    return NotConfiguredTTSProvider(provider, "TTS_PROVIDER=edge|vbee|gemini_tts")


def _vbee_callback_url_ready() -> bool:
    url = (settings.vbee_callback_url or "").strip()
    return url.startswith("https://") and "example.com" not in url


def _validated_vbee_callback_url() -> str:
    if not _vbee_callback_url_ready():
        raise RenderError("VBEE_CALLBACK_URL phải là HTTPS thật, không dùng example.com.")
    return settings.vbee_callback_url.strip()
