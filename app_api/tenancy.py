"""Tenancy — resolve danh tính JWT → org + bootstrap idempotent (mục 7, 8.2 plan).

Bảng users/orgs/memberships là GLOBAL (không RLS) → thao tác trong `session_scope`.
Bảng wallets/ledger_entries là TENANT (RLS) → thao tác trong `tenant_session(org_id)`.

bootstrap_tenant: lần đầu tạo user+org(owner)+membership+wallet + tặng FREE_GRANT_CREDITS
(BONUS ledger), idempotent (gọi lại = trả org cũ, KHÔNG tặng thêm). slug org suy diễn từ
user-id (deterministic) → 2 request đồng thời sinh CÙNG slug → UNIQUE(slug) chốt 1 lần.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app_api import config, wallet
from app_api.db import session_scope, tenant_session
from app_api.models import LedgerKind, Membership, Org, User

_NS = uuid.NAMESPACE_URL


def principal_uuid(sub: str) -> uuid.UUID:
    """JWT sub → users.id. Supabase sub là uuid (dùng thẳng); sub lạ → uuid5 deterministic."""
    try:
        return uuid.UUID(str(sub))
    except (ValueError, AttributeError, TypeError):
        return uuid.uuid5(_NS, f"vietvid-user:{sub}")


def _get_or_create_user(session, uid: uuid.UUID, email: str, provider: str) -> User:
    u = session.get(User, uid)
    if u is not None:
        if email and u.email != email:
            u.email = email
        return u
    u = User(id=uid, email=email or f"{uid}@dev.local", auth_provider=provider, email_verified=True)
    session.add(u)
    try:
        session.flush()
    except IntegrityError:
        # race: PID khác vừa tạo (PK uid hoặc email UNIQUE) → rollback + lấy lại.
        session.rollback()
        u = session.get(User, uid)
        if u is None:  # đụng UNIQUE(email) khác uid
            u = session.execute(select(User).where(User.email == email)).scalar_one()
    return u


def _get_owner_org(session, uid: uuid.UUID) -> Org | None:
    return session.execute(
        select(Org)
        .join(Membership, Membership.org_id == Org.id)
        .where(Membership.user_id == uid, Membership.role == "owner")
        .order_by(Org.created_at.asc())
        .limit(1)
    ).scalar_one_or_none()


def bootstrap_tenant(principal) -> dict:
    """Idempotent: đảm bảo user có org riêng + ví + free credit. Trả tóm tắt tenant."""
    uid = principal_uuid(principal.user_id)
    email = principal.email or ""
    provider = (principal.claims.get("app_metadata") or {}).get("provider") or config.auth_mode()

    created = False
    # 1) user + org(owner) + membership — bảng global.
    with session_scope() as s:
        _get_or_create_user(s, uid, email, str(provider))
        org = _get_owner_org(s, uid)
        if org is None:
            slug = f"u-{uid.hex[:12]}"          # deterministic → idempotent qua UNIQUE(slug)
            name = (email.split("@")[0] if email else "workspace") or "workspace"
            org = Org(name=name, slug=slug, owner_user_id=uid, plan_code="free")
            s.add(org)
            try:
                s.flush()
                s.add(Membership(org_id=org.id, user_id=uid, role="owner"))
                s.flush()
                created = True
            except IntegrityError:
                # request song song đã tạo org+membership → lấy lại bản đã commit.
                s.rollback()
                org = _get_owner_org(s, uid)
                if org is None:  # cực hiếm: slug bị chiếm bởi org khác → tạo slug ngẫu nhiên
                    org = Org(name=name, slug=f"u-{uuid.uuid4().hex[:12]}",
                              owner_user_id=uid, plan_code="free")
                    s.add(org)
                    s.flush()
                    s.add(Membership(org_id=org.id, user_id=uid, role="owner"))
                    s.flush()
                    created = True
        org_id = org.id

    # 2) ví + free grant — bảng tenant (RLS GUC). grant_once khóa ví FOR UPDATE → cấp BONUS đúng
    #    MỘT lần kể cả 2 bootstrap song song (fix đua cấp-2-lần). ensure_wallet ON CONFLICT an toàn.
    with tenant_session(org_id) as s:
        wallet.ensure_wallet(s, org_id)
        granted = wallet.grant_once(
            s, org_id, config.FREE_GRANT_CREDITS, kind=LedgerKind.BONUS, note="signup free grant"
        )
        bal = wallet._balance(s, org_id)

    return {
        "org_id": str(org_id),
        "user_id": str(uid),
        "created": created,
        "granted_credits": granted,
        "balance_credits": bal,
    }


# ── helpers cho deps.py (resolve org từ principal) ───────────────────────
def get_default_org_id(uid: uuid.UUID) -> str | None:
    """Org mặc định của user = org sở hữu (owner); fallback membership đầu tiên."""
    with session_scope() as s:
        org = _get_owner_org(s, uid)
        if org is not None:
            return str(org.id)
        m = session_first_membership(s, uid)
        return str(m.org_id) if m else None


def session_first_membership(session, uid: uuid.UUID) -> Membership | None:
    return session.execute(
        select(Membership)
        .where(Membership.user_id == uid, Membership.status == "ACTIVE")
        .order_by(Membership.created_at.asc())
        .limit(1)
    ).scalar_one_or_none()


def org_plan_code(org_id: str) -> str:
    """plan_code của org (free/pro/...) — quyết định giới hạn clamp. orgs là bảng global."""
    with session_scope() as s:
        org = s.get(Org, uuid.UUID(str(org_id)))
        return (org.plan_code if org else "free") or "free"


def role_in_org(uid: uuid.UUID, org_id: str) -> str | None:
    """Role của user trong org (None nếu không phải thành viên active)."""
    with session_scope() as s:
        m = s.execute(
            select(Membership).where(
                Membership.user_id == uid,
                Membership.org_id == uuid.UUID(str(org_id)),
                Membership.status == "ACTIVE",
            )
        ).scalar_one_or_none()
        return m.role if m else None
