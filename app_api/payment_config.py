"""Cấu hình thanh toán SỬA-ĐƯỢC-LÚC-CHẠY (admin UI) — lưu ở VvPlatformConfig.data['payment'].

Secret (token/key) mã hoá qua secrets_box trước khi lưu DB. env làm FALLBACK khi DB rỗng
→ setup hiện tại (đặt qua env) vẫn chạy. Admin GET trả secret dạng MASK (không lộ plaintext).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app_api import config, secrets_box
from app_api.models import VvPlatformConfig

_MASK = "••••••••"
# field bí mật: lưu SEALED, không bao giờ trả plaintext cho client.
_SECRET_FIELDS = {"webhook_token", "momo_access", "momo_secret", "vnpay_hash"}
# fallback env cho từng field (DB rỗng → đọc env). lambda để đọc giá trị env hiện tại.
_ENV = {
    "bank_bin": lambda: config.BANK_BIN,
    "bank_account": lambda: config.BANK_ACCOUNT_NUMBER,
    "bank_account_name": lambda: config.BANK_ACCOUNT_NAME,
    "bank_name": lambda: config.BANK_NAME,
    "webhook_token": lambda: config.SEPAY_API_TOKEN,
    "momo_partner": lambda: config.MOMO_PARTNER_CODE,
    "momo_access": lambda: config.MOMO_ACCESS_KEY,
    "momo_secret": lambda: config.MOMO_SECRET_KEY,
    "vnpay_tmn": lambda: config.VNPAY_TMN_CODE,
    "vnpay_hash": lambda: config.VNPAY_HASH_SECRET,
}
_FIELDS = list(_ENV.keys())
_ENABLED_DEFAULT = {"bank_qr": True, "momo": False, "vnpay": False}


def _raw(session: Session) -> dict:
    row = session.get(VvPlatformConfig, 1)
    return dict((row.data or {}).get("payment") or {}) if row else {}


def resolve(session: Session) -> dict:
    """Config PLAINTEXT để billing dùng: DB (giải mã secret) ⊕ env fallback."""
    raw = _raw(session)
    out: dict = {}
    for f in _FIELDS:
        v = raw.get(f, "")
        if f in _SECRET_FIELDS:
            v = secrets_box.unseal(v)
        if not v:  # DB rỗng → env
            v = _ENV[f]()
        out[f] = v or ""
    out["enabled"] = {**_ENABLED_DEFAULT, **(raw.get("enabled") or {})}
    return out


def masked(session: Session) -> dict:
    """Cho admin GET: secret → '••••' nếu đã có (DB sealed HOẶC env), rỗng nếu chưa; non-secret → giá trị thật."""
    raw = _raw(session)
    out: dict = {}
    for f in _FIELDS:
        if f in _SECRET_FIELDS:
            has = bool(secrets_box.unseal(raw.get(f, "")) or _ENV[f]())
            out[f] = _MASK if has else ""
        else:
            out[f] = raw.get(f) or _ENV[f]() or ""
    out["enabled"] = {**_ENABLED_DEFAULT, **(raw.get("enabled") or {})}
    out["secrets_storage"] = "encrypted" if secrets_box.configured() else "env-only"
    return out


def save(session: Session, patch: dict) -> dict:
    """Ghi patch. Secret: bỏ qua nếu = MASK/rỗng (không đổi), else seal (cần master key). Non-secret: ghi thẳng."""
    row = session.get(VvPlatformConfig, 1)
    if row is None:
        row = VvPlatformConfig(id=1, data={})
        session.add(row)
        session.flush()
    data = dict(row.data or {})
    pay = dict(data.get("payment") or {})
    for f in _FIELDS:
        if f not in patch:
            continue
        val = (str(patch[f]) if patch[f] is not None else "").strip()
        if f in _SECRET_FIELDS:
            if val in ("", _MASK):  # không đổi → giữ nguyên (không xoá vô tình)
                continue
            if not secrets_box.configured():
                raise RuntimeError("Chưa đặt VIETVID_CONFIG_SECRET — không lưu được secret qua UI. Đặt env rồi thử lại.")
            pay[f] = secrets_box.seal(val)
        else:
            pay[f] = val
    if isinstance(patch.get("enabled"), dict):
        pay["enabled"] = {**_ENABLED_DEFAULT, **(pay.get("enabled") or {}), **patch["enabled"]}
    data["payment"] = pay
    row.data = data
    session.flush()
    return masked(session)


def bank_ready(cfg: dict) -> bool:
    """Đủ thông tin nhận tiền bank-QR chưa (dùng resolve())."""
    return bool(cfg.get("bank_bin") and cfg.get("bank_account") and cfg.get("bank_account_name"))
