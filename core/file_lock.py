"""Khoá file đa nền tảng — fcntl (Unix) / msvcrt (Windows). V8.3-W1.2.

Dùng chung cho mọi chỗ cần khoá file giữa các tiến trình (alert dedupe,
browser profile lock...). Thống nhất kiểu lỗi: tranh khoá non-blocking
thất bại → BlockingIOError trên CẢ HAI nền tảng.
"""

from __future__ import annotations

try:
    import fcntl

    _HAS_FCNTL = True
except ImportError:  # Windows
    import msvcrt

    _HAS_FCNTL = False


def lock_exclusive(fh, *, blocking: bool = True) -> None:
    """Khoá độc quyền file đang mở. blocking=False → BlockingIOError nếu đang bị giữ.

    Windows: khoá 1 byte đầu file (msvcrt khoá theo vùng từ vị trí hiện tại —
    seek(0) trước để mọi tiến trình tranh CÙNG một vùng; vùng ngoài EOF vẫn hợp lệ).
    """
    if _HAS_FCNTL:
        flags = fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB)
        fcntl.flock(fh.fileno(), flags)
        return
    fh.seek(0)
    mode = msvcrt.LK_LOCK if blocking else msvcrt.LK_NBLCK
    try:
        msvcrt.locking(fh.fileno(), mode, 1)
    except OSError as exc:
        raise BlockingIOError(str(exc)) from exc


def unlock(fh) -> None:
    """Nhả khoá (best-effort — file sắp đóng thì bỏ qua lỗi)."""
    if _HAS_FCNTL:
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        except OSError:
            pass
        return
    try:
        fh.seek(0)
        msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
    except OSError:
        pass
