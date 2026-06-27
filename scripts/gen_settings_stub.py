"""V8.3-W2.2b — Sinh `config/settings.pyi` từ registry (giữ IDE type-hint cho mức B).

Chạy lại MỖI KHI đổi config/registry.py:
    .venv/Scripts/python -m scripts.gen_settings_stub
"""

from __future__ import annotations

from pathlib import Path

from config.registry import REGISTRY

HEADER = '''"""Stub TỰ SINH từ config/registry.py — KHÔNG sửa tay.

Sinh lại: python -m scripts.gen_settings_stub
"""

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
'''

PROPERTIES = """
    @property
    def cors_origins(self) -> list[str]: ...
    @property
    def auto_sensitive_categories_list(self) -> list[str]: ...
    @property
    def scripts_dir(self) -> str: ...
    @property
    def audio_dir(self) -> str: ...
    @property
    def broll_dir(self) -> str: ...
    @property
    def music_dir(self) -> str: ...
    @property
    def output_dir(self) -> str: ...
    @property
    def score_weights(self) -> dict[str, float]: ...
    def render_format_specs(self) -> list[tuple[str, int, int]]: ...
    @property
    def category_weights_map(self) -> dict[str, dict[str, float]]: ...
    def score_weights_for_category(self, category: str | None) -> dict[str, float]: ...

settings: Settings
"""


def main() -> None:
    lines = [HEADER]
    for key in REGISTRY:
        if key.env_only:
            continue
        lines.append(f"    {key.name}: {key.type.__name__}")
    lines.append(PROPERTIES)
    out = Path("config/settings.pyi")
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"OK - sinh {out}")


if __name__ == "__main__":
    main()
