"""Auth DUAL-MODE (mục 4, 7 plan + §11).

- **Supabase** (production): verify JWT do Supabase phát.
  - JWKS (khoá bất đối xứng RS256/ES256): set `SUPABASE_JWKS_URL` → fetch + cache khoá ký.
  - HS256 legacy: set `SUPABASE_JWT_SECRET` (project JWT secret).
- **dev** (chưa cấu hình Supabase): tự verify/phát HS256 bằng `DEV_JWT_SECRET` → verify lớp
  HTTP ngay trên Postgres thật, KHÔNG phụ thuộc Supabase. Cắm Supabase = chỉ set env.

`verify_token(token)` trả `Principal(user_id, email, claims)` hoặc raise `AuthError`.
Engine/ví KHÔNG biết gì về JWT — auth chỉ resolve danh tính, tenancy.py resolve org.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field

import jwt
from jwt import PyJWKClient

from app_api import config


class AuthError(Exception):
    """JWT thiếu/sai/hết hạn — router map sang 401."""


@dataclass(frozen=True)
class Principal:
    user_id: str            # uuid string = JWT `sub` (Supabase user id / dev user id)
    email: str
    claims: dict = field(default_factory=dict)


# ── JWKS client cache (1 client / URL, fetch + cache khoá; lazy) ──────────
_jwks_client: PyJWKClient | None = None
_jwks_url: str | None = None


def _get_jwks_client() -> PyJWKClient:
    global _jwks_client, _jwks_url
    url = config.SUPABASE_JWKS_URL
    if _jwks_client is None or _jwks_url != url:
        # PyJWKClient cache khoá trong RAM + tự refresh khi gặp kid lạ.
        _jwks_client = PyJWKClient(url, cache_keys=True, lifespan=3600)
        _jwks_url = url
    return _jwks_client


def _decode(token: str) -> dict:
    """Giải mã + verify chữ ký theo mode đang cấu hình. Raise jwt.* nếu sai."""
    mode = config.auth_mode()
    aud = config.SUPABASE_JWT_AUD or None
    common = dict(
        audience=aud,
        issuer=config.SUPABASE_JWT_ISSUER or None,
        options={
            "require": ["exp", "sub"],
            "verify_aud": bool(aud),
            "verify_iss": bool(config.SUPABASE_JWT_ISSUER),
        },
        leeway=30,  # cho lệch đồng hồ nhẹ
    )
    if mode == "supabase" and config.SUPABASE_JWKS_URL:
        signing_key = _get_jwks_client().get_signing_key_from_jwt(token)
        return jwt.decode(token, signing_key.key, algorithms=["RS256", "ES256"], **common)
    if mode == "supabase":  # HS256 legacy secret
        return jwt.decode(token, config.SUPABASE_JWT_SECRET, algorithms=["HS256"], **common)
    # dev mode
    return jwt.decode(token, config.DEV_JWT_SECRET, algorithms=["HS256"], **common)


def verify_token(token: str) -> Principal:
    if not token or not token.strip():
        raise AuthError("thiếu token")
    try:
        claims = _decode(token.strip())
    except jwt.ExpiredSignatureError as exc:
        raise AuthError("token hết hạn") from exc
    except jwt.InvalidTokenError as exc:
        raise AuthError(f"token không hợp lệ: {exc}") from exc
    except Exception as exc:  # noqa: BLE001 — JWKS fetch lỗi mạng, kid lạ, v.v.
        raise AuthError(f"không verify được token: {exc}") from exc

    sub = str(claims.get("sub") or "").strip()
    if not sub:
        raise AuthError("token thiếu sub")
    # Supabase nhét email ở top-level; một số provider để trong user_metadata.
    email = (
        claims.get("email")
        or (claims.get("user_metadata") or {}).get("email")
        or ""
    )
    return Principal(user_id=sub, email=str(email).strip().lower(), claims=claims)


# ── Dev token mint (CHỈ dev-mode) — dùng để verify lớp HTTP không cần Supabase ──
def mint_dev_token(user_id: str, email: str, *, ttl_seconds: int = 3600, extra: dict | None = None) -> str:
    """Phát HS256 token bằng DEV_JWT_SECRET. Chỉ hợp lệ khi app đang ở dev-mode."""
    now = _dt.datetime.now(tz=_dt.timezone.utc)
    payload = {
        "sub": str(user_id),
        "email": email,
        "aud": config.SUPABASE_JWT_AUD or "authenticated",
        "iat": int(now.timestamp()),
        "exp": int((now + _dt.timedelta(seconds=ttl_seconds)).timestamp()),
        **(extra or {}),
    }
    if config.SUPABASE_JWT_ISSUER:
        payload["iss"] = config.SUPABASE_JWT_ISSUER
    return jwt.encode(payload, config.DEV_JWT_SECRET, algorithm="HS256")
