"""V8.3-W2.3b — Sinh `.env.example` từ config/registry.py (section theo group + note).

Chạy lại MỖI KHI đổi registry:
    .venv/Scripts/python -m scripts.sync_env_example
"""

from __future__ import annotations

from pathlib import Path

from config.registry import GROUP_META, REGISTRY

HEADER = """# ============================================================================
# AffiliateBot — .env.example (TỰ SINH từ config/registry.py — KHÔNG sửa tay)
# Copy thành `.env` rồi điền giá trị. Sinh lại: python -m scripts.sync_env_example
# Key bỏ trống = dùng default trong registry. KHÔNG để dòng `KEY=` rỗng cho key
# có default — sẽ đè default thành chuỗi rỗng (bài học V8.3-W1 job 500).
# ============================================================================
"""


def _fmt(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def main() -> None:
    lines = [HEADER]
    for gid, (title, description) in GROUP_META.items():
        keys = [k for k in REGISTRY if k.group == gid]
        if not keys:
            continue
        lines.append(f"# ── {title} " + "─" * max(1, 60 - len(title)))
        if description:
            lines.append(f"# {description}")
        for key in keys:
            if key.note:
                lines.append(f"# {key.note}")
            lines.append(f"{key.name.upper()}={_fmt(key.default)}")
        lines.append("")
    Path(".env.example").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"OK - sinh .env.example ({len(REGISTRY)} key)")


if __name__ == "__main__":
    main()
