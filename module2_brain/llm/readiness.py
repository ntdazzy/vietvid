"""Shared LLM configuration readiness checks."""

from __future__ import annotations

from dataclasses import dataclass

from config.settings import settings
from core.config_checks import looks_real_secret


@dataclass(frozen=True)
class LLMProviderConfig:
    provider: str
    api_key: str
    key_name: str
    model: str
    model_name: str


def provider_config(provider: str) -> LLMProviderConfig:
    if provider == "groq":
        return LLMProviderConfig(
            provider="groq",
            api_key=settings.groq_api_key,
            key_name="GROQ_API_KEY",
            model=settings.groq_model,
            model_name="GROQ_MODEL",
        )
    if provider == "gemini":
        return LLMProviderConfig(
            provider="gemini",
            api_key=settings.gemini_api_key,
            key_name="GEMINI_API_KEY",
            model=settings.gemini_model,
            model_name="GEMINI_MODEL",
        )
    raise ValueError(f"Provider LLM không hợp lệ: {provider}")


def llm_config_issues(provider: str) -> list[str]:
    cfg = provider_config(provider)
    issues: list[str] = []
    if not looks_real_secret(cfg.api_key):
        issues.append(f"{cfg.key_name} thieu hoac con placeholder")
    if not looks_real_secret(cfg.model, min_length=4):
        issues.append(f"{cfg.model_name} thieu hoac con placeholder")
    return issues


def llm_config_ready(provider: str) -> bool:
    return not llm_config_issues(provider)
