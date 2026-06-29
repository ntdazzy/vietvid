"""MB Bank transaction poller — "mini-SePay" tự host, MIỄN PHÍ, ~3-8s.

Service ĐỘC LẬP (chạy venv riêng): đăng nhập API MB Bank (lib cộng đồng `mbbank`),
poll lịch sử giao dịch mỗi vài giây, lọc giao dịch TIỀN VÀO mới → POST về backend Vyra
(/v1/billing/ipn/sepay) đúng format SePay → backend tự đối soát memo + cộng credit.

Vì sao service riêng: lib `mbbank` chưa hỗ trợ Python 3.14 (backend chạy 3.14). Poller này
chỉ cần `mbbank` + `requests`, chạy trên Python 3.11/3.12, KHÔNG import backend → cô lập,
phiên-bản-độc-lập, lỗi không làm sập API chính.

⚠️ BẢO MẬT: file này cần USER+PASS MB. KHUYẾN NGHỊ dùng 1 TÀI KHOẢN MB RIÊNG chỉ để thu
tiền nạp (rút định kỳ về TK chính). Đặt creds qua ENV, KHÔNG hardcode, KHÔNG commit.

Cài + chạy (venv Python 3.11/3.12):
    py -3.11 -m venv .venv-poller
    .venv-poller\\Scripts\\activate      (Windows)   |   source .venv-poller/bin/activate (mac/linux)
    pip install mbbank requests
    # đặt env (xem bên dưới) rồi:
    python scripts/mb_poller.py

ENV:
    MB_USERNAME           username đăng nhập MB
    MB_PASSWORD           password MB
    MB_ACCOUNT            số tài khoản nhận tiền
    VYRA_BACKEND_URL      vd http://127.0.0.1:8099  (hoặc domain prod)
    VYRA_WEBHOOK_TOKEN    = VIETVID_SEPAY_TOKEN của backend (mật khẩu chung tự đặt)
    MB_POLL_INTERVAL_S    mặc định 3
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import os
import re
import sys
import time
from pathlib import Path

import requests

log = logging.getLogger("mbpoller")

USERNAME = os.environ.get("MB_USERNAME", "")
PASSWORD = os.environ.get("MB_PASSWORD", "")
ACCOUNT = os.environ.get("MB_ACCOUNT", "")
BACKEND = os.environ.get("VYRA_BACKEND_URL", "http://127.0.0.1:8099").rstrip("/")
TOKEN = os.environ.get("VYRA_WEBHOOK_TOKEN", "")
INTERVAL = max(2, int(os.environ.get("MB_POLL_INTERVAL_S", "3")))
STATE_FILE = Path(__file__).with_name(".mb_poller_state.json")  # nhớ refNo đã xử lý


def _load_seen() -> set[str]:
    try:
        return set(json.loads(STATE_FILE.read_text("utf-8")))
    except Exception:  # noqa: BLE001
        return set()


def _save_seen(seen: set[str]) -> None:
    # giữ tối đa 2000 ref gần nhất để file không phình
    try:
        STATE_FILE.write_text(json.dumps(list(seen)[-2000:]), "utf-8")
    except Exception:  # noqa: BLE001
        log.warning("không ghi được state file")


def _to_vnd(raw) -> int:
    """Quy về số nguyên VND, đúng cho cả số (200000 / 200000.0) lẫn chuỗi ('200,000', '200.000', '200000.00')."""
    if isinstance(raw, (int, float)):
        return int(round(float(raw)))
    s = re.sub(r"[.,]\d{1,2}$", "", str(raw).strip())  # bỏ đuôi thập phân .0/.00/,00 (VND không có xu)
    digits = re.sub(r"[^\d]", "", s)                    # còn lại bỏ . , khoảng trắng (dấu phân nghìn)
    return int(digits) if digits else 0


def _tx_amount_in(tx: dict) -> int:
    """Số tiền GHI CÓ (tiền vào) của 1 giao dịch; 0 nếu là tiền ra / không đọc được."""
    # tiền ra (debit > 0) → bỏ ngay
    deb = tx.get("debitAmount")
    if deb not in (None, "", "0", 0) and _to_vnd(deb) > 0:
        return 0
    for key in ("creditAmount", "amount", "transactionAmount"):
        raw = tx.get(key)
        if raw in (None, "", "0", 0):
            continue
        val = _to_vnd(raw)
        if val > 0:
            return val
    return 0


def _tx_content(tx: dict) -> str:
    """Nội dung CK (chứa memo VYRA) — thử nhiều tên field."""
    for key in ("description", "addDescription", "transactionDesc", "remark", "content"):
        v = tx.get(key)
        if v:
            return str(v)
    return ""


def _tx_ref(tx: dict) -> str:
    for key in ("refNo", "transactionId", "id", "transactionRefNo"):
        v = tx.get(key)
        if v:
            return str(v)
    # fallback: hash thô từ nội dung+tiền+ngày
    return f"{tx.get('postingDate','')}-{_tx_content(tx)[:20]}-{_tx_amount_in(tx)}"


def _post_transfer(content: str, amount: int) -> str:
    """POST 1 giao dịch tiền-vào về backend (format SePay). Trả message backend."""
    r = requests.post(
        f"{BACKEND}/v1/billing/ipn/sepay",
        headers={"Authorization": f"Apikey {TOKEN}", "Content-Type": "application/json"},
        json={"transferType": "in", "content": content, "transferAmount": amount},
        timeout=15,
    )
    try:
        return r.json().get("message", str(r.status_code))
    except Exception:  # noqa: BLE001
        return f"HTTP {r.status_code}"


def fetch_recent(mb) -> list[dict]:
    """Lấy lịch sử GD ~3 ngày gần nhất. mbbank API: getTransactionAccountHistory."""
    today = dt.datetime.now()
    data = mb.getTransactionAccountHistory(
        accountNo=ACCOUNT,
        from_date=today - dt.timedelta(days=3),
        to_date=today,
    )
    # MB trả dict; danh sách GD ở 'transactionHistoryList' (tuỳ phiên bản)
    for key in ("transactionHistoryList", "transactionHistory", "historyList"):
        lst = data.get(key) if isinstance(data, dict) else None
        if isinstance(lst, list):
            return lst
    return []


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s mbpoller: %(message)s")
    if not (USERNAME and PASSWORD and ACCOUNT and TOKEN):
        log.error("Thiếu env: cần MB_USERNAME, MB_PASSWORD, MB_ACCOUNT, VYRA_WEBHOOK_TOKEN.")
        sys.exit(1)
    try:
        from mbbank import MBBank
    except ImportError:
        log.error("Chưa cài 'mbbank'. Tạo venv Python 3.11/3.12 rồi: pip install mbbank requests")
        sys.exit(1)

    seen = _load_seen()
    mb = None
    log.info("bắt đầu poll MB account=%s mỗi %ss → %s", ACCOUNT, INTERVAL, BACKEND)
    while True:
        try:
            if mb is None:
                mb = MBBank(username=USERNAME, password=PASSWORD)  # tự giải captcha + lấy token
                log.info("đăng nhập MB OK")
            txs = fetch_recent(mb)
            new_credited = 0
            for tx in txs:
                ref = _tx_ref(tx)
                if ref in seen:
                    continue
                amount = _tx_amount_in(tx)
                if amount <= 0:
                    seen.add(ref)  # tiền ra / không liên quan → đánh dấu để bỏ qua
                    continue
                content = _tx_content(tx)
                msg = _post_transfer(content, amount)
                seen.add(ref)
                log.info("GD ref=%s +%s → backend: %s", ref, amount, msg)
                if msg == "credited":
                    new_credited += 1
            if len(seen) > 4000:  # chặn phình RAM khi poller chạy 24/7 (idempotency vẫn là lưới chính)
                seen = set(list(seen)[-2000:])
            _save_seen(seen)
            if new_credited:
                log.info("đã cộng credit cho %s giao dịch", new_credited)
        except Exception as exc:  # noqa: BLE001 — lỗi mạng/session hết hạn → login lại vòng sau
            log.warning("vòng poll lỗi (%s) — sẽ đăng nhập lại", str(exc)[:120])
            mb = None
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
