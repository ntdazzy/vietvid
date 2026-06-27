"""Cổng cấu hình (V7-B3): hệ thống CHỜ khi chưa đủ key/cookie để vận hành.

Founder nhập cookie + key vào web → đủ thì hệ thống tự chạy; thiếu → các loop tự động CHỜ
+ web báo "chưa cấu hình". Tối thiểu để chạy vòng V7 (input → video):
- LLM (Gemini HOẶC Groq) cho bộ não viết kịch bản.
- Shopee CDP (SHOPEE_CDP_URL local + provider shopee_cdp) cho input + tạo link.
Việc đăng-nhập-thật của Chrome được kiểm ở khâu ingest (login-wall), không ở đây (chỉ check
config tĩnh có mặt).
"""

from __future__ import annotations

from dataclasses import dataclass

from config.settings import settings
from core.config_checks import looks_real_secret
from core.logger import logger


@dataclass(frozen=True)
class ConfigStatus:
    ready: bool
    missing: list[str]  # nhãn thiếu, hiển thị trên web/banner

    def reason_text(self) -> str:
        return "; ".join(self.missing) if self.missing else "đã cấu hình đủ"


def operational_config_ready() -> ConfigStatus:
    """Đủ cấu hình tối thiểu để vận hành vòng V7 chưa? (không kiểm login Chrome — ingest lo)."""
    missing: list[str] = []

    if getattr(settings, "use_fake_clients", True):
        missing.append("USE_FAKE_CLIENTS=false để dùng dữ liệu/model thật")

    if not getattr(settings, "input_gate_enabled", False):
        missing.append("INPUT_GATE_ENABLED=true để chặn sản phẩm thiếu dữ liệu")

    gemini_ok = looks_real_secret(getattr(settings, "gemini_api_key", "") or "")
    groq_ok = looks_real_secret(getattr(settings, "groq_api_key", "") or "")
    if not (gemini_ok or groq_ok):
        missing.append("Khoá LLM (GEMINI_API_KEY hoặc GROQ_API_KEY)")

    cdp_url = (getattr(settings, "shopee_cdp_url", "") or "").lower()
    if "127.0.0.1" not in cdp_url and "localhost" not in cdp_url:
        missing.append("Shopee CDP (SHOPEE_CDP_URL = http://127.0.0.1:<port>)")

    if (getattr(settings, "affiliate_link_provider", "") or "") != "shopee_cdp":
        missing.append("AFFILIATE_LINK_PROVIDER=shopee_cdp")

    # SCRAPER_IMPORT_SECRET CHỈ cần cho đường EXTENSION import (dashboard/routers/scraper_import.py
    # tự kiểm secret tại endpoint). KHÔNG thuộc tối thiểu input→video — CDP ingest + brain + render
    # KHÔNG dùng nó → KHÔNG gate ở đây (P1 fix 2026-06-10: trước đây gate này khiến brain WAITING_CONFIG oan).

    tts_provider = (getattr(settings, "tts_provider", "") or "").strip().lower()
    if tts_provider == "vbee":
        if not looks_real_secret(getattr(settings, "vbee_app_id", "") or ""):
            missing.append("VBEE_APP_ID cho giọng đọc Vbee")
        if not looks_real_secret(getattr(settings, "vbee_api_token", "") or ""):
            missing.append("VBEE_API_TOKEN cho giọng đọc Vbee")
        callback_url = (getattr(settings, "vbee_callback_url", "") or "").strip()
        if not callback_url or callback_url == "https://example.com/vbee-callback":
            missing.append("VBEE_CALLBACK_URL thật, không dùng example.com")
    elif tts_provider == "gemini_tts":
        # V8.3-Q2: nhánh Gemini TTS — cần GEMINI_API_KEY (chuỗi fallback gemini→vbee→edge).
        if not looks_real_secret(getattr(settings, "gemini_api_key", "") or ""):
            missing.append("GEMINI_API_KEY cho giọng đọc Gemini TTS")
    elif tts_provider != "edge":
        # V8.2 D2/D3: kokoro + elevenlabs đã xoá. V8.3-Q2: thêm gemini_tts.
        missing.append("TTS_PROVIDER=edge|vbee|gemini_tts")

    if getattr(settings, "dispatch_provider", "mock") != "mock":
        missing.append("DISPATCH_PROVIDER=mock trong Phase A để không đăng thật")
    if getattr(settings, "revenue_provider", "mock") != "mock":
        missing.append("REVENUE_PROVIDER=mock trong Phase A để không gọi doanh thu thật")
    if getattr(settings, "youtube_privacy_status", "private") != "private":
        missing.append("YOUTUBE_PRIVACY_STATUS=private khi test")

    status = ConfigStatus(ready=not missing, missing=missing)
    if missing:
        logger.debug(f"[config-gate] chưa đủ cấu hình để chạy: {status.reason_text()}")
    return status


def video_engine_config_ready() -> ConfigStatus:
    """V8: đủ cấu hình cho engine video AI chưa? (job thiếu → WAITING_CONFIG).

    Mock provider (test không tốn tiền) thì không cần key thật.
    """
    missing: list[str] = []
    image_provider = (getattr(settings, "image_provider", "") or "").strip().lower()
    video_provider = (getattr(settings, "video_provider", "") or "").strip().lower()
    fake = bool(getattr(settings, "use_fake_clients", True))

    if not fake and image_provider == "gemini":
        if not looks_real_secret(getattr(settings, "gemini_api_key", "") or ""):
            missing.append("GEMINI_API_KEY cho image stage (ảnh KOL/sản phẩm)")
    if not fake and video_provider == "seedance_piapi":
        if not looks_real_secret(getattr(settings, "piapi_api_key", "") or ""):
            missing.append("PIAPI_API_KEY cho video stage (Seedance)")
    if float(getattr(settings, "video_daily_budget_usd", 0.0) or 0.0) <= 0:
        missing.append("VIDEO_DAILY_BUDGET_USD > 0 (cầu chì ngân sách ngày)")

    status = ConfigStatus(ready=not missing, missing=missing)
    if missing:
        logger.debug(f"[video-config-gate] thiếu: {status.reason_text()}")
    return status
