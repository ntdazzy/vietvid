"""Poller email báo-có MB Bank → tự cộng credit (thay SePay, MIỄN PHÍ, không giới hạn GD).

Đọc hòm mail nhận email "biến động số dư / báo có" của MB Bank qua IMAP bằng
APP-PASSWORD của email (KHÔNG phải mật khẩu ngân hàng). Mỗi email tiền-vào mới:
bóc số tiền + nội dung (chứa memo VYRAxxxxxxxx) → gọi billing.credit_bank_transfer
(logic đối soát + cộng credit DÙNG CHUNG với webhook). Idempotent — quét lại không cộng kép.

Chạy (cùng env với backend — VIETVID_DATABASE_URL, ... ):
    python -m app_api.bank_email_poller

Cấu hình (env):
    VIETVID_BANK_EMAIL_IMAP      (mặc định imap.gmail.com)
    VIETVID_BANK_EMAIL_USER      email nhận báo-có
    VIETVID_BANK_EMAIL_PASSWORD  APP-PASSWORD (Gmail: tạo ở Google Account → App passwords)
    VIETVID_BANK_EMAIL_SENDER    (tuỳ chọn) lọc người gửi, vd email báo-có của MB
    VIETVID_BANK_POLL_INTERVAL_S (mặc định 45)
"""

from __future__ import annotations

import email
import imaplib
import logging
import re
import time
from email.header import decode_header

from app_api import billing, config

log = logging.getLogger("vietvid.bankpoll")

# Dấu hiệu TIỀN VÀO (ghi có) — chỉ xử lý mail báo-có, bỏ qua tiền ra / mail khác.
# Bao cả có-dấu lẫn không-dấu (ghi có / ghi co, tiền vào / tien vao).
_INCOMING_RE = re.compile(
    r"\(\+\)|ghi\s*c[oó]|ti[eề]n\s*v[aà]o|nh[aậ]n\s*ti[eề]n|credit|\+\s*[\d]",
    re.IGNORECASE,
)
# Số tiền ghi-có: bắt số đứng sau dấu hiệu cộng / nhãn (+ , (+), GD:+, ghi có, số tiền).
_AMOUNT_RE = re.compile(
    r"(?:\(\+\)|\+|ghi\s*c[oó]|GD\s*:?\s*\+?|s[oố]\s*ti[eề]n)\s*:?\s*\+?\s*([\d][\d.,]*)\s*(?:VND|VN[ĐD]|đ)?",
    re.IGNORECASE,
)


def _to_int_vnd(s: str) -> int:
    digits = re.sub(r"[^\d]", "", s)  # bỏ dấu . , khoảng trắng
    return int(digits) if digits else 0


def parse_mb_email(subject: str, body: str) -> tuple[int, str] | None:
    """(số_tiền_vnd, nội_dung) nếu là email TIỀN VÀO đọc được; None nếu không phải.

    Trả nguyên text (subject + body) làm `nội_dung` để credit_bank_transfer bóc memo VYRA.
    Best-effort theo format MB phổ biến — dán 1 email MB thật vào test để tinh chỉnh regex.
    """
    text = f"{subject}\n{body}"
    if not _INCOMING_RE.search(text):
        return None  # không có dấu hiệu tiền vào
    m = _AMOUNT_RE.search(text)
    if not m:
        return None
    amount = _to_int_vnd(m.group(1))
    if amount <= 0:
        return None
    return amount, text


def _decode_subject(raw: str | None) -> str:
    try:
        return "".join(
            (b.decode(enc or "utf-8", "replace") if isinstance(b, bytes) else b)
            for b, enc in decode_header(raw or "")
        )
    except Exception:  # noqa: BLE001 — subject hỏng không được làm chết poller
        return str(raw or "")


def _email_text(msg: email.message.Message) -> str:
    """Trích text từ email (ưu tiên text/plain; text/html → strip thẻ)."""
    parts: list[str] = []
    targets = msg.walk() if msg.is_multipart() else [msg]
    for part in targets:
        ctype = part.get_content_type()
        if ctype not in ("text/plain", "text/html"):
            continue
        try:
            payload = part.get_payload(decode=True) or b""
            charset = part.get_content_charset() or "utf-8"
            text = payload.decode(charset, errors="replace")
        except Exception:  # noqa: BLE001
            continue
        if ctype == "text/html":
            text = re.sub(r"<[^>]+>", " ", text)
        parts.append(text)
    return " ".join(parts)


def process_once() -> int:
    """Một vòng quét hòm mail. Trả số giao dịch đã cộng credit."""
    imap = imaplib.IMAP4_SSL(config.BANK_EMAIL_IMAP_HOST)
    credited = 0
    try:
        imap.login(config.BANK_EMAIL_USER, config.BANK_EMAIL_PASSWORD)
        imap.select("INBOX")
        crit = ["UNSEEN", "FROM", config.BANK_EMAIL_SENDER] if config.BANK_EMAIL_SENDER else ["UNSEEN"]
        typ, data = imap.search(None, *crit)
        if typ != "OK" or not data or not data[0]:
            return 0
        for uid in data[0].split():
            typ, msg_data = imap.fetch(uid, "(RFC822)")
            if typ != "OK" or not msg_data or not msg_data[0]:
                continue
            msg = email.message_from_bytes(msg_data[0][1])
            parsed = parse_mb_email(_decode_subject(msg.get("Subject")), _email_text(msg))
            # Đánh dấu đã đọc dù xử lý được hay không → tránh quét lại vô hạn.
            # credit_bank_transfer idempotent (FOR UPDATE + status) nên không lo cộng kép.
            imap.store(uid, "+FLAGS", "\\Seen")
            if parsed is None:
                continue
            amount, content = parsed
            try:
                result = billing.credit_bank_transfer(content, amount)
            except Exception:  # noqa: BLE001 — 1 email lỗi không được làm chết vòng quét
                log.exception("bankpoll: lỗi cộng credit (uid=%s)", uid)
                continue
            log.info(
                "bankpoll: uid=%s amount=%s → %s (memo=%s)",
                uid.decode(errors="replace"), amount, result["status"], result.get("memo"),
            )
            if result["status"] == "credited":
                credited += 1
        return credited
    finally:
        try:
            imap.logout()
        except Exception:  # noqa: BLE001
            pass


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    if not config.bank_email_configured():
        log.error("Chưa cấu hình email báo-có (VIETVID_BANK_EMAIL_USER / _PASSWORD). Dừng.")
        raise SystemExit(1)
    interval = max(15, config.BANK_POLL_INTERVAL_S)
    log.info(
        "bankpoll: poll %s mỗi %ss (user=%s, sender=%s)",
        config.BANK_EMAIL_IMAP_HOST, interval, config.BANK_EMAIL_USER,
        config.BANK_EMAIL_SENDER or "(mọi người gửi)",
    )
    while True:
        try:
            n = process_once()
            if n:
                log.info("bankpoll: đã cộng credit cho %s giao dịch", n)
        except Exception:  # noqa: BLE001 — lỗi mạng/IMAP tạm thời → thử lại vòng sau
            log.exception("bankpoll: vòng quét lỗi, thử lại sau %ss", interval)
        time.sleep(interval)


if __name__ == "__main__":
    main()
