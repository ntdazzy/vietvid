"""vieneu_client.py — cầu nối tới daemon giọng clone VieNeu (chạy ở venv RIÊNG, ngoài .venv prod).

Vì gói `vieneu` (+ onnxruntime, sea-g2p…) KHÔNG cài trong .venv prod (rủi ro xung đột numpy/onnx),
ta chạy nó như 1 daemon HTTP local: nạp model 1 LẦN, phục vụ per-block. Module này chỉ dùng httpx +
subprocess (có sẵn trong .venv prod) — KHÔNG import `vieneu`.

Daemon CỐ Ý sống dai (CPU nhẹ): các tiến trình prod sau reuse qua port file + /health. Daemon là tiến
trình ĐỘC LẬP (không phải child) nên thu hồi bằng PID file (identity-based kill), không phải kill-tree.

- `vieneu_ready()`        : đủ điều kiện dùng engine 'vieneu' (đã cài daemon dir + venv).
- `synth_via_daemon()`    : reuse daemon đang sống, hoặc spawn mới (kill bản kẹt trước), rồi POST /synth.
- `shutdown_vieneu_daemon()`: thu hồi daemon theo PID file (gọi khi muốn giải phóng; KHÔNG bắt buộc).
"""
from __future__ import annotations

import os
import subprocess
import time

import httpx

from config.settings import settings
from core.logger import logger

_DEFAULT_DIR = r"C:\Users\NTD\vieneu_tts"
# repo root = .../<repo>/video_engine/voice/vieneu_client.py → lên 3 cấp
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_state: dict = {"port": None, "logf": None}


def _daemon_dir() -> str:
    return (settings.voiceclone_daemon_dir or _DEFAULT_DIR).strip() or _DEFAULT_DIR


def _venv_python(d: str) -> str:
    return os.path.join(d, "venv", "Scripts", "python.exe")


def _script(d: str) -> str:
    return os.path.join(d, "vieneu_daemon.py")


def _port_file(d: str) -> str:
    return os.path.join(d, "daemon_port.txt")


def _pid_file(d: str) -> str:
    return os.path.join(d, "daemon_pid.txt")


def _log_file(d: str) -> str:
    return os.path.join(d, "daemon.log")


def _read(path: str) -> str | None:
    try:
        return (open(path, encoding="utf-8").read().strip() or None) if os.path.exists(path) else None
    except OSError:
        return None


def _health(port: str) -> bool:
    try:
        return bool(httpx.get(f"http://127.0.0.1:{port}/health", timeout=3).json().get("ok"))
    except Exception:  # noqa: BLE001 — health probe best-effort
        return False


def _log_tail(d: str, n: int = 14) -> str:
    try:
        lines = open(_log_file(d), encoding="utf-8", errors="replace").read().splitlines()
        return "\n".join(lines[-n:]) or "(daemon.log rỗng)"
    except OSError:
        return "(không đọc được daemon.log)"


def _kill_stale(d: str) -> None:
    """Kill daemon theo PID file (thu hồi bản kẹt/cũ) + xoá port/pid file."""
    pid = _read(_pid_file(d))
    if pid and pid.isdigit():
        try:
            subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True, timeout=10)
            logger.info(f"[vieneu] thu hồi daemon kẹt pid={pid}")
        except Exception:  # noqa: BLE001 — best-effort
            pass
    for f in (_port_file(d), _pid_file(d)):
        try:
            os.remove(f)
        except OSError:
            pass


def vieneu_ready() -> bool:
    """Đã cài daemon (venv + script) → cho phép chọn engine 'vieneu'."""
    d = _daemon_dir()
    return os.path.exists(_venv_python(d)) and os.path.exists(_script(d))


def _ensure_daemon() -> str:
    d = _daemon_dir()
    port = _state["port"] or _read(_port_file(d))
    if port and _health(port):       # daemon đang sống → reuse
        _state["port"] = port
        return port

    _kill_stale(d)                   # bản cũ/kẹt → thu hồi để giải phóng cổng
    py, script = _venv_python(d), _script(d)
    if not (os.path.exists(py) and os.path.exists(script)):
        raise RuntimeError(f"VieNeu daemon chưa cài tại {d} (thiếu venv hoặc vieneu_daemon.py)")

    flags = 0
    if os.name == "nt":  # nhường CPU cho web/DB prod + không bật cửa sổ console
        flags = subprocess.BELOW_NORMAL_PRIORITY_CLASS | subprocess.CREATE_NO_WINDOW
    env = dict(os.environ)
    env["VIENEU_PORT"] = str(settings.voiceclone_daemon_port or 8771)
    env["VIENEU_OUT_BASE"] = _REPO_ROOT     # daemon chỉ cho ghi file dưới repo root
    logf = open(_log_file(d), "a", encoding="utf-8")   # GIỮ log chẩn đoán (không DEVNULL)
    _state["logf"] = logf
    logger.info(f"[vieneu] spawn daemon: {d}")
    subprocess.Popen([py, "-u", script], cwd=d, env=env, creationflags=flags,
                     stdout=logf, stderr=subprocess.STDOUT)

    for i in range(90):   # chờ nạp model + bind (~7-15s); cap 90s
        port = _read(_port_file(d))
        if port and _health(port):
            _state["port"] = port
            logger.info(f"[vieneu] daemon ready on 127.0.0.1:{port}")
            return port
        if i and i % 15 == 0:
            logger.info(f"[vieneu] chờ daemon lên... {i}s")
        time.sleep(1)
    raise RuntimeError(f"VieNeu daemon không lên sau 90s. daemon.log:\n{_log_tail(d)}")


def synth_via_daemon(text: str, out_path: str, *, ref_audio: str, emotion: str, silence_p: float) -> str:
    """POST /synth → trả path WAV (VieNeu xuất 48k). Lỗi → raise để caller fallback."""
    port = _ensure_daemon()
    r = httpx.post(
        f"http://127.0.0.1:{port}/synth",
        json={"text": text, "out_path": out_path, "ref_audio": ref_audio,
              "emotion": emotion, "silence_p": silence_p},
        timeout=300,
    ).json()
    if not r.get("ok"):
        raise RuntimeError(f"VieNeu synth lỗi: {r}")
    return r["path"]


def shutdown_vieneu_daemon() -> None:
    """Thu hồi daemon theo PID file (identity-based). KHÔNG bắt buộc — daemon cố ý sống dai để reuse."""
    _kill_stale(_daemon_dir())
    _state["port"] = None
    f = _state.get("logf")
    if f is not None:
        try:
            f.close()
        except Exception:  # noqa: BLE001
            pass
    _state["logf"] = None
