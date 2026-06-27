"""Gửi email (Sóng 1B). Dev (chưa cấu hình SMTP): ghi nội dung + link ra LOG để bạn lấy thử.
Prod (set VIETVID_SMTP_*): gửi thật qua SMTP STARTTLS.

Cố ý nhỏ gọn: text email, không template engine. Đủ cho reset/verify.
"""

from __future__ import annotations

import logging
import smtplib
from email.mime.text import MIMEText

from app_api import config

log = logging.getLogger("vietvid")


def send_email(to: str, subject: str, body: str) -> bool:
    """Gửi 1 email text. Trả True nếu đã gửi/đã log. Không bao giờ ném (best-effort)."""
    if not config.email_configured():
        # Dev: in ra log để lấy link reset/verify mà không cần SMTP.
        log.info("EMAIL (dev, chưa gửi thật) → %s | %s\n%s", to, subject, body)
        return True
    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = config.SMTP_FROM
        msg["To"] = to
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=15) as s:
            s.starttls()
            s.login(config.SMTP_USER, config.SMTP_PASSWORD)
            s.sendmail(config.SMTP_FROM, [to], msg.as_string())
        log.info("EMAIL đã gửi → %s | %s", to, subject)
        return True
    except Exception:  # noqa: BLE001 — gửi email lỗi không được làm sập request auth.
        log.exception("EMAIL gửi lỗi → %s", to)
        return False


def send_reset(to: str, raw_token: str) -> None:
    link = f"{config.APP_BASE_URL}/reset-password?token={raw_token}"
    send_email(
        to,
        "Đặt lại mật khẩu VietVid",
        f"Bạn vừa yêu cầu đặt lại mật khẩu.\n\nMở liên kết sau (hết hạn sau 1 giờ):\n{link}\n\n"
        f"Nếu không phải bạn, hãy bỏ qua email này.",
    )


def send_invite(to: str, raw_token: str, org_name: str) -> None:
    link = f"{config.APP_BASE_URL}/accept-invite?token={raw_token}"
    send_email(
        to,
        f"Lời mời tham gia workspace {org_name} trên VietVid",
        f"Bạn được mời tham gia workspace \"{org_name}\".\n\n"
        f"Chấp nhận lời mời (hết hạn sau 7 ngày):\n{link}\n\n"
        f"Nếu chưa có tài khoản, hãy đăng ký bằng đúng email này rồi mở lại liên kết.",
    )


def send_verify(to: str, raw_token: str) -> None:
    link = f"{config.APP_BASE_URL}/verify-email?token={raw_token}"
    send_email(
        to,
        "Xác minh email VietVid",
        f"Chào mừng tới VietVid!\n\nXác minh email của bạn (hết hạn sau 24 giờ):\n{link}\n\n"
        f"Sau khi xác minh, tài khoản của bạn được kích hoạt đầy đủ.",
    )
