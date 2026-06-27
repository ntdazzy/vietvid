"""V8.2 Phase 3 — Formula Bank: chọn công thức viral (script_formulas) làm few-shot cho Director.

36 row autovis — chấm trùng keyword đơn giản là đủ (không cần embedding).
Fail-open: không có formula khớp → [] (Director vẫn chạy không few-shot).
"""

from __future__ import annotations

import re

from sqlalchemy import select

from core.database import db
from core.logger import logger
from core.models import ScriptFormula

# ~1000 token ≈ 4000 ký tự cho mẫu tiếng Việt/Anh trộn.
_MAX_CHARS_PER_FORMULA = 4000


def _tokens(text: str) -> set[str]:
    return {w.lower() for w in re.findall(r"[\wÀ-ỹ-]+", text or "") if len(w) > 2}


def pick_formulas(
    format_key: str, category: str, product_name: str, k: int = 2
) -> list[ScriptFormula]:
    """Top-k formula ACTIVE: ưu tiên trùng keyword với (category + tên SP), cùng format trước.

    Rỗng theo keyword → top-k theo format; vẫn rỗng → [] (fail-open).
    """
    want = _tokens(category) | _tokens(product_name)
    with db.transaction() as session:
        rows = list(
            session.scalars(select(ScriptFormula).where(ScriptFormula.status == "ACTIVE"))
        )
        for row in rows:
            session.expunge(row)
    if not rows:
        return []

    def _score(f: ScriptFormula) -> tuple[int, int]:
        kw = {t.strip().lower() for t in (f.product_keywords or "").split(",") if t.strip()}
        kw |= _tokens(f.title)
        overlap = len(want & kw)
        same_format = 1 if (format_key and f.format_key == format_key) else 0
        return (same_format, overlap)

    # V8.3-Q7.2: formula THẮNG (doanh thu thật) ưu tiên TRƯỚC keyword — học liên tục.
    def _rank(f: ScriptFormula) -> tuple[int, float, int, int]:
        same_format, overlap = _score(f)
        return (int(f.wins or 0), float(f.revenue_usd or 0.0), same_format, overlap)

    ranked = sorted(rows, key=_rank, reverse=True)
    eligible = [f for f in ranked if sum(_score(f)) > 0 or (f.wins or 0) > 0]
    picked = eligible[:k]
    if not picked and format_key:
        picked = [f for f in ranked if f.format_key == format_key][:k]
    # Explore/exploit — chừa 1 slot để THỬ công thức CHƯA dùng (uses=0, wins=0), nếu không thì
    # trend mới không bao giờ được dùng → không tích wins → vòng tự-học kẹt chicken-egg. Kích hoạt khi:
    #  (a) top-k toàn công thức đã chứng minh (cần khám phá để có dữ liệu mới), HOẶC
    #  (b) có TREND chưa thử (founder vừa duyệt → cho thử SỚM, kể cả khi autovis cũng chưa có uses).
    # Trong nhóm chưa thử, ưu tiên trend-source trước (giữ thứ hạng _rank trong từng nhóm).
    def _is_trend(f) -> bool:
        return str(getattr(f, "source", "") or "").startswith("trend_")

    if len(picked) >= 2:
        chosen = {f.key for f in picked}
        untried = [
            f for f in eligible
            if (f.uses or 0) == 0 and (f.wins or 0) == 0 and f.key not in chosen
        ]
        untried.sort(key=lambda f: 0 if _is_trend(f) else 1)  # stable → trend lên đầu
        top_all_proven = all((f.uses or 0) > 0 or (f.wins or 0) > 0 for f in picked)
        if untried and (top_all_proven or _is_trend(untried[0])):
            picked = picked[: k - 1] + [untried[0]]
            logger.info(f"[formula_bank] explore: thử công thức MỚI '{untried[0].key}'")
    if picked:
        logger.info(
            f"[formula_bank] chọn {[f.key for f in picked]} cho format={format_key} cat={category}"
        )
        _bump_uses([f.key for f in picked])
    return picked


def _bump_uses(keys: list[str]) -> None:
    """Đếm số lần công thức được CHỌN (để explore/exploit biết cái nào chưa thử). Best-effort."""
    if not keys:
        return
    try:
        with db.transaction() as session:
            for f in session.scalars(select(ScriptFormula).where(ScriptFormula.key.in_(keys))):
                f.uses = (f.uses or 0) + 1
    except Exception:  # noqa: BLE001 — đếm uses lỗi không được chặn việc chọn formula
        logger.exception("[formula_bank] bump uses lỗi")


def format_for_prompt(formulas: list[ScriptFormula]) -> str:
    """Block few-shot nhét vào prompt Director — cắt ~1000 token/mẫu, nhãn chống copy."""
    if not formulas:
        return ""
    parts = []
    for i, f in enumerate(formulas, 1):
        body = (f.prompt_vi or f.prompt_en or "")[:_MAX_CHARS_PER_FORMULA]
        parts.append(
            f"MẪU THAM CHIẾU #{i} ({f.title} · {f.duration}s) — BẮT CHƯỚC CẤU TRÚC/NHỊP/TIMECODE, "
            f"KHÔNG copy tên/chi tiết sản phẩm trong mẫu:\n{body}"
        )
    return "\n\n".join(parts)
