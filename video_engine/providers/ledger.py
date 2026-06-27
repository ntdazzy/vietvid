"""Budget gate ngày — nguồn sự thật DUY NHẤT là bảng ``provider_ledger`` (DB).

Luật: budget USD/ngày là luật CHÍNH (xét trước), ``video_max_per_day`` chỉ là trần
phụ chống spam. Reserve atomic bằng row-lock (``SELECT … FOR UPDATE`` trên Postgres;
SQLite bỏ qua FOR UPDATE nhưng được bảo vệ bởi write-lock của chính nó).
"""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from config.settings import settings
from core.database import db
from core.logger import logger
from core.models import ProviderLedger
from video_engine.providers.base import VideoBudgetError

# Provider gộp chung 1 sổ/ngày cho toàn engine (ảnh + video đều trừ vào đây).
LEDGER_PROVIDER = "video_engine"


def _today() -> str:
    # QA P1#4: ngày ngân sách theo MÚI GIỜ VẬN HÀNH (reset nửa đêm địa phương), không phải UTC
    # (UTC reset lúc 07:00 VN → card 'Chi phí hôm nay' hiện $0 dù vừa tiêu sáng nay). Fallback UTC nếu TZ hỏng.
    try:
        return datetime.now(ZoneInfo(settings.dispatch_timezone)).date().isoformat()
    except Exception:  # noqa: BLE001
        return datetime.now(timezone.utc).date().isoformat()


def _get_or_create_row(session, day: str, provider: str) -> ProviderLedger:
    row = session.scalar(
        select(ProviderLedger)
        .where(ProviderLedger.date == day, ProviderLedger.provider == provider)
        .with_for_update()
    )
    if row is not None:
        return row
    row = ProviderLedger(
        date=day,
        provider=provider,
        spent_usd=0.0,
        budget_usd=float(settings.video_daily_budget_usd or 0.0),
        jobs_count=0,
    )
    session.add(row)
    try:
        session.flush()
    except IntegrityError:
        # Worker khác vừa tạo row cùng (date, provider) → rollback flush, lock lại.
        session.rollback()
        row = session.scalar(
            select(ProviderLedger)
            .where(ProviderLedger.date == day, ProviderLedger.provider == provider)
            .with_for_update()
        )
        if row is None:  # pragma: no cover — không thể xảy ra sau IntegrityError
            raise VideoBudgetError("Không tạo/đọc được ledger ngày.") from None
    return row


def reserve_video_budget(
    est_usd: float,
    *,
    count_job: bool = True,
    provider: str = LEDGER_PROVIDER,
    daily_budget: float | None = None,
) -> tuple[float, str]:
    """Đặt chỗ ``est_usd`` cho 1 job. Vượt budget/trần → ``VideoBudgetError``.

    Trả về ``(số tiền đã reserve, ngày-UTC reserve)``. Caller PHẢI truyền lại ``day`` đó cho
    ``settle_video_budget`` để hoàn/điều chỉnh ĐÚNG ledger row — job chạy vắt qua nửa đêm
    UTC nếu settle theo ``_today()`` mới sẽ ghi nhầm sang ngày khác (reserve treo ở hôm qua).
    """
    budget = float(daily_budget if daily_budget is not None else (settings.video_daily_budget_usd or 0.0))
    max_jobs = int(settings.video_max_per_day or 0)
    if budget <= 0:
        raise VideoBudgetError(
            "VIDEO_DAILY_BUDGET_USD phải > 0 để chống phát sinh chi phí ngoài ý muốn."
        )
    est = max(0.0, float(est_usd))
    day = _today()
    with db.transaction() as session:
        row = _get_or_create_row(session, day, provider)
        row.budget_usd = budget  # cập nhật nếu founder đổi budget trong ngày
        # 1) Luật chính: ngân sách USD.
        if row.spent_usd + est > budget:
            raise VideoBudgetError(
                f"Hết ngân sách video ngày: đã tiêu ${row.spent_usd:.2f} "
                f"+ ước tính ${est:.2f} > budget ${budget:.2f}. Job xếp hàng mai."
            )
        # 2) Trần phụ: số job/ngày.
        if count_job and max_jobs > 0 and row.jobs_count >= max_jobs:
            raise VideoBudgetError(
                f"Đạt trần {max_jobs} video/ngày (trần phụ chống spam). Job xếp hàng mai."
            )
        row.spent_usd = round(row.spent_usd + est, 4)
        if count_job:
            row.jobs_count += 1
        logger.info(
            f"[video-budget] reserve ${est:.3f} → đã tiêu ${row.spent_usd:.3f}"
            f"/{budget:.2f} USD, jobs={row.jobs_count}"
        )
    return est, day


def settle_video_budget(
    reserved_usd: float,
    actual_usd: float,
    *,
    day: str | None = None,
    provider: str = LEDGER_PROVIDER,
) -> None:
    """Điều chỉnh sổ sau khi biết chi phí thật (hoàn phần reserve thừa/thiếu).

    ``day`` = ngày-UTC lúc reserve (do ``reserve_video_budget`` trả về). KHÔNG truyền →
    dùng ``_today()`` (chỉ đúng khi reserve+settle cùng ngày UTC).
    """
    delta = round(float(actual_usd) - float(reserved_usd), 4)
    if abs(delta) < 1e-9:
        return
    day = day or _today()
    with db.transaction() as session:
        row = _get_or_create_row(session, day, provider)
        row.spent_usd = max(0.0, round(row.spent_usd + delta, 4))
        logger.info(
            f"[video-budget] settle delta ${delta:+.3f} → đã tiêu ${row.spent_usd:.3f} USD"
        )


def ledger_snapshot(provider: str = LEDGER_PROVIDER) -> dict:
    """Trạng thái ngân sách hôm nay cho web/cost screen (provider mặc định video_engine — back-compat)."""
    day = _today()
    with db.transaction() as session:
        row = session.scalar(
            select(ProviderLedger).where(
                ProviderLedger.date == day, ProviderLedger.provider == provider
            )
        )
        budget = float(settings.video_daily_budget_usd or 0.0)
        if row is None:
            return {"date": day, "spent_usd": 0.0, "budget_usd": budget, "jobs_count": 0}
        return {
            "date": day,
            "spent_usd": row.spent_usd,
            "budget_usd": budget,
            "jobs_count": row.jobs_count,
        }
