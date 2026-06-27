"""Nạp "luật chủ đề kênh" từ tài liệu gốc (TAI-LIEU-GOC-KENH-CHIN-CHUN.md) vào prompt.

Trích các mục ĐỘC LẬP với việc job dùng KOL nào (niche, trụ cột nội dung, ràng buộc
pipeline, khử nét AI) — KHÔNG ép persona Chin/Chun để không chỏi khi job dùng KOL khác
hoặc product_only. Doc là nguồn sự thật duy nhất (sửa doc → video bám theo), tránh chép tay.

Fail-soft: thiếu file / đọc lỗi / rỗng → trả "" (Director chạy như cũ).
"""

from __future__ import annotations

from pathlib import Path

from config.settings import settings
from core.logger import logger

# Các mục trích (theo prefix tiêu đề trong doc). Đều là prose, độc lập nhân vật.
_TARGET_PREFIXES = ("## 4.", "## 8.", "### 18.5.", "### 18.6.")
_MAX_CHARS = 1800
# project root = .../affiliatebot (file này ở video_engine/director/channel_theme.py)
_PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Cache trong tiến trình theo (path, mtime) — đọc lại khi doc đổi.
_cache_key: tuple[str, float] | None = None
_cache_value: str = ""


def _resolve_doc_path(raw: str) -> Path:
    """Đường dẫn tuyệt đối; tương đối thì tính từ project root (KHÔNG dùng cwd —
    orchestrator/Task Scheduler chạy từ thư mục khác sẽ đọc trượt file)."""
    path = Path(raw).expanduser()
    return path if path.is_absolute() else _PROJECT_ROOT / path


def _extract_sections(content: str) -> str:
    """Trích các mục theo _TARGET_PREFIXES. Bỏ qua tiêu đề nằm TRONG code block
    (doc có ``` ở mục 18.1/18.2). Flush buffer mục cũ trước khi sang mục mới."""
    sections: list[str] = []
    buf: list[str] = []
    collecting = False
    in_code = False

    def _flush() -> None:
        if buf:
            sections.append("\n".join(buf).strip())
            buf.clear()

    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            if collecting:
                buf.append(line)
            continue
        is_heading = not in_code and stripped.startswith("#")
        if is_heading and any(stripped.startswith(p) for p in _TARGET_PREFIXES):
            _flush()  # đóng mục đang thu (vd 18.5 khi gặp 18.6 liền kề)
            collecting = True
            buf.append(line)
            continue
        if is_heading and collecting:
            collecting = False  # gặp tiêu đề KHÁC → kết thúc mục hiện tại
            _flush()
            continue
        if collecting:
            buf.append(line)
    _flush()

    combined = "\n\n".join(s for s in sections if s).strip()
    if len(combined) > _MAX_CHARS:
        combined = combined[:_MAX_CHARS].rstrip() + "\n… [cắt gọn chủ đề kênh]"
    return combined


def load_channel_theme() -> str:
    """Trả block "luật chủ đề kênh" (đã trích + cắt), cache theo mtime. "" nếu tắt/lỗi."""
    global _cache_key, _cache_value
    raw = (settings.channel_theme_doc or "").strip()
    if not raw:
        return ""
    doc_path = _resolve_doc_path(raw)
    try:
        mtime = doc_path.stat().st_mtime
    except OSError:
        logger.warning(f"[channel_theme] không thấy file chủ đề kênh: {doc_path}")
        return ""

    key = (str(doc_path), mtime)
    if _cache_key == key:
        return _cache_value

    try:
        content = doc_path.read_text(encoding="utf-8")
    except OSError as exc:
        logger.warning(f"[channel_theme] đọc file lỗi: {str(exc)[:160]}")
        return ""

    value = _extract_sections(content)
    _cache_key, _cache_value = key, value
    return value
