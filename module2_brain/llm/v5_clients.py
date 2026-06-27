"""LLM cho đường V5 với fallback nhiều provider (chống rơi template / _safe_score).

Vấn đề thực tế (2026-06-09): Gemini có thể lỗi tạm thời — 429 ``limit:0`` (key chưa có quota
cho model đó, vd gemini-2.5-pro) hoặc 503 high-demand. Khi đó copywriter V5 rơi về **template**
(copy "lộ AI") và critic rơi về **_safe_score** (đếm field). Để giữ chất lượng + chạy 24/7 ổn,
ta thử lần lượt **Gemini (chất, theo model cấu hình) → Groq (free, llama-3.3-70b)** trước khi
caller buộc phải fallback. Chỉ raise khi TẤT CẢ provider lỗi.

Tái dùng `GeminiClient`/`GroqClient` + `run_coro_blocking` sẵn có, không thêm SDK/khái niệm mới.
"""

from __future__ import annotations

from config.settings import settings
from core.exceptions import LLMError
from core.logger import logger
from module2_brain.llm.base import BaseLLMClient

# Thứ tự thử: Gemini trước (chất, founder đã bật billing) → Groq (free, chống rơi template).
_PROVIDER_ORDER = ("gemini", "groq")


def _build_client(provider: str, gemini_model: str) -> BaseLLMClient:
    if provider == "groq":
        from module2_brain.llm.groq_client import GroqClient

        return GroqClient()
    from module2_brain.llm.gemini_client import GeminiClient

    return GeminiClient(model=gemini_model)


def complete_with_fallback(system: str, prompt: str, *, gemini_model: str) -> str:
    """Gọi LLM thử Gemini(gemini_model) → Groq. Trả raw text của provider đầu tiên chạy được.

    Raise ``LLMError`` nếu mọi provider lỗi (cấu hình thiếu hoặc runtime lỗi) → caller fallback.
    """
    from module2_brain.llm.runner import run_coro_blocking

    errors: list[str] = []
    for index, provider in enumerate(_PROVIDER_ORDER):
        try:
            client = _build_client(provider, gemini_model)
        except Exception as exc:  # noqa: BLE001 — provider chưa cấu hình (thiếu key) → bỏ qua
            errors.append(f"{provider}/config: {str(exc)[:120]}")
            continue
        try:
            result = run_coro_blocking(lambda c=client: c.complete(system, prompt))
        except Exception as exc:  # noqa: BLE001 — provider lỗi runtime → thử provider kế
            errors.append(f"{provider}: {str(exc)[:160]}")
            logger.warning(
                f"[brain-v5] LLM provider={provider} lỗi, thử provider kế: {str(exc)[:160]}"
            )
            continue
        if index > 0:
            # Đã phải TỤT khỏi provider chính ('{primary}') → chất lượng kịch bản/chấm có thể giảm
            # âm thầm. Báo MẠNH (Telegram, đã khử-trùng theo prefix nên không spam mỗi job).
            _alert_llm(
                "WARNING",
                f"LLM tụt provider: '{_PROVIDER_ORDER[0]}' lỗi → đang dùng '{provider}'. "
                f"Chất lượng có thể giảm. Lý do: {' | '.join(errors)[:200]}",
                dedupe_prefix="brain-v5:fallback",
            )
        return result
    # Mọi provider sập = Strategist/Critic/Analyzer fail-soft → video tụt về không-brief/không-chấm.
    _alert_llm(
        "CRITICAL",
        "MỌI provider LLM đều lỗi (Gemini+Groq). Strategist/Critic/Analyzer đang fail-soft "
        "→ kịch bản KHÔNG brief / KHÔNG chấm. Kiểm tra quota/khoá key ngay. "
        + " | ".join(errors)[:200],
        dedupe_prefix="brain-v5:all-down",
    )
    raise LLMError("Mọi provider LLM V5 đều lỗi: " + " | ".join(errors)[:400])


def _alert_llm(level: str, message: str, *, dedupe_prefix: str) -> None:
    """Cảnh báo MẠNH (Telegram + SystemEvent) khi LLM tụt provider/sập — fail-soft + khử-trùng
    (notify tự dedupe theo prefix). KHÔNG được làm hỏng luồng chính nếu kênh báo lỗi."""
    try:
        from dashboard.telegram_bot import notify

        notify(level, "brain-v5", message, dedupe_prefix=dedupe_prefix)
    except Exception:  # noqa: BLE001 — báo lỗi không được nghẽn pipeline
        logger.warning(f"[brain-v5] không gửi được cảnh báo fallback: {message[:120]}")
