"""Lớp truy cập DB an toàn cho đa tiến trình.

BẪY QUAN TRỌNG: KHÔNG tạo engine ở tiến trình cha rồi truyền sang con. Sau ``fork``,
con kế thừa socket pool của cha → hai tiến trình ghi chung một socket → vỡ giao thức
Postgres. Vì vậy engine ở đây được tạo **lazy theo PID**: chỉ dựng ở lần dùng đầu tiên
*bên trong* mỗi tiến trình. Nếu phát hiện đã vượt ranh giới fork, engine kế thừa bị bỏ
bằng ``dispose(close=False)`` (không đóng vật lý socket của cha) rồi dựng lại.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from config.settings import settings
from core.logger import logger


class Database:
    def __init__(self, url: str) -> None:
        self._url = url
        self._engine: Engine | None = None
        self._sessionmaker: sessionmaker | None = None
        self._owner_pid: int | None = None

    def _is_sqlite(self) -> bool:
        return self._url.startswith("sqlite")

    def _build_engine(self) -> Engine:
        if self._is_sqlite():
            # timeout = busy_timeout giúp giảm "database is locked" khi nhiều tiến trình ghi.
            # NullPool: mỗi thao tác mở kết nối mới rồi đóng → không giữ connection cũ cache
            # schema lệch giữa các test (gốc lỗi "no such table" chập chờn khi reset schema).
            engine = create_engine(
                self._url,
                connect_args={"check_same_thread": False, "timeout": 30},
                poolclass=NullPool,
                future=True,
            )

            @event.listens_for(engine, "connect")
            def _sqlite_pragmas(dbapi_conn, _record):  # noqa: ANN001
                cur = dbapi_conn.cursor()
                cur.execute("PRAGMA journal_mode=WAL")
                cur.execute("PRAGMA synchronous=NORMAL")
                cur.close()

            return engine
        return create_engine(
            self._url, pool_size=5, max_overflow=10, pool_pre_ping=True, future=True
        )

    @property
    def engine(self) -> Engine:
        pid = os.getpid()
        if self._engine is None or self._owner_pid != pid:
            if self._engine is not None and self._owner_pid != pid:
                # Engine kế thừa từ tiến trình cha → bỏ rơi pool (không đóng socket của cha).
                self._engine.dispose(close=False)
            self._engine = self._build_engine()
            self._sessionmaker = sessionmaker(
                bind=self._engine, expire_on_commit=False, future=True
            )
            self._owner_pid = pid
            logger.debug(f"Tạo DB engine mới trong pid={pid}")
        return self._engine

    def session(self) -> Session:
        _ = self.engine  # bảo đảm engine + sessionmaker tồn tại cho PID hiện tại
        assert self._sessionmaker is not None
        return self._sessionmaker()

    @contextmanager
    def transaction(self) -> Iterator[Session]:
        """Transaction guard: tự commit khi thành công, rollback khi có lỗi."""
        session = self.session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def reset_for_fork(self) -> None:
        """Gọi ở đầu hàm chạy của tiến trình con để bỏ engine kế thừa từ cha."""
        if self._engine is not None:
            self._engine.dispose(close=False)
        self._engine = None
        self._sessionmaker = None
        self._owner_pid = None


# Singleton: import được trước fork; engine thực tế dựng lazy trong từng tiến trình.
db = Database(settings.database_url)
