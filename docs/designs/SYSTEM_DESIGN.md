# VietVid — System Design (M2+)

> Bản thiết kế hệ thống đầy đủ cho VietVid: SaaS đa-tenant tạo video AI giọng Việt, định vị vượt autovis.ai.
> Thiết kế dựa trên codebase thật (M1 đã xong: migrations 0001–0003, auth lifecycle, ví ACID, reaper, signed URLs, prod-safety).
> Sinh bởi 7 kiến trúc sư song song + tổng hợp. Đây là **build-spec** cho các Sóng còn lại.


_Lập: 2026-06-27 · 7 miền · 53 bảng mới · 66 endpoint mới_


## Mục lục

1. Data Model & Migrations (M2+): Complete Remaining Schema + Alembic Plan (0004→)
2. Job Pipeline, Queue & Media Infra
3. Billing, Payments & Subscriptions
4. Feature Modules — autovis parity + revenue-loop differentiators
5. Security, Multi-tenancy, RBAC & Compliance
6. Frontend Architecture & Complete Screen Map
7. Infrastructure, DevOps, Deployment & Observability

A. Phụ lục — Bảng mới · B. Endpoint mới · C. Module mới · D. Quyết định kiến trúc · E. Câu hỏi cần chốt · F. Lộ trình triển khai


---

# 1. Data Model & Migrations (M2+): Complete Remaining Schema + Alembic Plan (0004→)

## Data Model & Migrations (M2+)

This section designs every remaining table to reach a full multi-tenant SaaS, building **on** the verified M1 baseline (migrations 0001–0003). It reuses the exact existing conventions found in `app_api/models.py`: the `_PK()` (`gen_random_uuid()`) and `_TS()` helpers, `CITEXT` for email/slug, `BigInteger Identity()` PKs for append-only logs, status as `Text` + `CheckConstraint` (never native enums — "thêm trạng thái không cần ALTER"), `JSONB` with `'{}'::jsonb` defaults, and the RLS fail-closed model.

### 0. Conventions every new table inherits (non-negotiable)

**Tenant table (org_id + RLS):** any table holding org-owned business data gets:
1. `org_id UUID NOT NULL FK orgs.id` (ondelete per table below),
2. registration in the migration's local RLS loop so it gets `ENABLE` + **`FORCE`** ROW LEVEL SECURITY and the `org_isolation` policy using the *identical* predicate already in baseline:
   `org_id = nullif(current_setting('vietvid.current_org', true), '')::uuid`
   This is fail-closed: GUC unset → `nullif` → NULL → predicate false → zero rows. Reuse the `_RLS_USING` string constant from baseline verbatim (copy into 0004's module, or — preferred — extract it to `app_api/models.py` as `RLS_USING_PREDICATE` and import; see Decision D7).
3. Every query still filters `org_id` explicitly (RLS is the net, the WHERE is the index path — matches existing jobs/videos routers).

**Global table (no RLS):** reference/identity data not owned by a single tenant — `plans`, `credit_packs` (catalog), `coupons` (catalog), `webhook_events` (IPN arrives pre-auth, no GUC), `data_subject_requests` (may target a deleted org), `audit_log` (must survive org deletion → see D5). These get **no** `org_id`-RLS; access control lives in the router/RBAC layer.

**The `TENANT_TABLES` tuple** in `models.py` is the single source the baseline RLS loop reads. Each migration that adds tenant tables defines its **own local list** and runs the same `ENABLE/FORCE/POLICY` loop (do NOT mutate the baseline tuple's loop — baseline already ran). I do extend `TENANT_TABLES` in `models.py` to its full final set for documentation/test-assertion purposes (a test can assert "every table with an `org_id` column is in `TENANT_TABLES` AND has RLS enabled" — see D8), but the *enabling* happens per-migration.

---

### 1. Billing / Plans / Entitlements layer

#### `plans` — GLOBAL
Subscription tier catalog. Backs `orgs.plan_code` (currently a free-text column defaulting `'free'`; we add a soft FK — see D3).

| col | type | notes |
|---|---|---|
| `code` | `Text` PK | `'free'`, `'pro'`, `'business'`, `'enterprise'` — matches existing `orgs.plan_code` values |
| `name` | `Text NOT NULL` | display |
| `name_vi` | `Text NOT NULL default ''` | Vietnamese display |
| `monthly_price_vnd` | `BigInteger NOT NULL default 0` | |
| `yearly_price_vnd` | `BigInteger NOT NULL default 0` | |
| `monthly_credit_grant` | `BigInteger NOT NULL default 0` | credits refilled each cycle (the M1 TODO "reset hàng tháng = M2") |
| `max_concurrent_jobs` | `Integer NOT NULL default 1` | clamps in `validate.py` |
| `max_resolution` | `Text NOT NULL default '720p'` | feeds `validate_and_clamp` (already plan-aware) |
| `max_seconds` | `Integer NOT NULL default 15` | |
| `watermark_free` | `Boolean NOT NULL default false` | drives `videos.has_watermark` |
| `features` | `JSONB NOT NULL default '{}'` | open-ended entitlement bag |
| `is_active` | `Boolean NOT NULL default true` | hide retired plans |
| `sort_order` | `Integer NOT NULL default 0` | |
| `created_at/updated_at` | `_TS()` | |

PK `code`. No FK in. Seeded in the migration (insert `free`/`pro`/`business`) so `orgs.plan_code='free'` resolves.

#### `subscriptions` — TENANT (org_id + RLS)
One active subscription per org (multiple rows over time for history).

| col | type | notes |
|---|---|---|
| `id` | `_PK()` | |
| `org_id` | `UUID NOT NULL FK orgs.id ondelete=CASCADE` | |
| `plan_code` | `Text NOT NULL FK plans.code ondelete=RESTRICT` | |
| `status` | `Text NOT NULL default 'ACTIVE'` | `ACTIVE/PAST_DUE/CANCELLED/EXPIRED` (check) |
| `billing_cycle` | `Text NOT NULL default 'monthly'` | `monthly/yearly` (check) |
| `current_period_start` | `timestamptz NOT NULL` | |
| `current_period_end` | `timestamptz NOT NULL` | cron grants monthly credits at rollover |
| `cancel_at_period_end` | `Boolean NOT NULL default false` | |
| `provider` | `Text default ''` | vnpay/momo recurring ref (manual renew in VN context) |
| `provider_sub_ref` | `Text default ''` | |
| `last_grant_at` | `timestamptz` | dedupe monthly grant (only grant once per period) |
| `created_at/updated_at` | `_TS()` | |

Indexes: `ix_subscriptions_org (org_id)`; **partial unique** `uq_subscription_active_org ON subscriptions(org_id) WHERE status='ACTIVE'` (one live sub per org — hand-written in migration like baseline's partial indexes). `ix_subscriptions_period_end (current_period_end) WHERE status='ACTIVE'` for the renewal cron sweep.
Check: `status IN (...)`, `billing_cycle IN ('monthly','yearly')`.

#### `entitlements` — TENANT (org_id + RLS)
Per-org overrides / add-ons that diverge from the plan (e.g. a one-off "extra 5 concurrent jobs" grant, or a comped feature). Keeps `plans` clean and avoids per-org plan clones.

| col | type | notes |
|---|---|---|
| `id` | `_PK()` | |
| `org_id` | `UUID NOT NULL FK orgs.id ondelete=CASCADE` | |
| `key` | `Text NOT NULL` | `'max_concurrent_jobs'`, `'watermark_free'`, ... |
| `value` | `JSONB NOT NULL` | typed bag (`{"int":10}` / `{"bool":true}`) |
| `source` | `Text NOT NULL default 'manual'` | `manual/plan/promo/support` |
| `expires_at` | `timestamptz` | nullable = permanent |
| `created_at` | `_TS()` | |

Unique `uq_entitlement_org_key (org_id, key)`. Resolution order in code: entitlement override → plan default. Index `ix_entitlements_org (org_id)`.

#### `credit_packs` — GLOBAL — **backs `payments.credit_pack_id`**
Replaces the hardcoded `PACKS` dict in `billing.py`. The reserved column `payments.credit_pack_id UUID` (no FK today) gets a real FK here.

| col | type | notes |
|---|---|---|
| `id` | `_PK()` | |
| `code` | `Text NOT NULL` | `'starter'/'popular'/'pro'` — matches existing dict keys for migration continuity |
| `name` | `Text NOT NULL` | `name_vi` analog: keep `name` Vietnamese as the dict does (`"Khởi đầu"`) |
| `amount_vnd` | `BigInteger NOT NULL` | matches dict |
| `credits` | `BigInteger NOT NULL` | base + bonus, matches dict semantics |
| `bonus_credits` | `BigInteger NOT NULL default 0` | optional split for display |
| `is_active` | `Boolean NOT NULL default true` | |
| `sort_order` | `Integer NOT NULL default 0` | |
| `created_at/updated_at` | `_TS()` | |

Unique `uq_credit_pack_code (code)`. Check `amount_vnd > 0`, `credits > 0`. Seeded with the 3 existing packs (same code/amount/credits) so live `payments.credit_pack_id` references resolve and `billing.get_packs()` switches from dict to a `SELECT`.

#### Backing the reserved FK on `payments.credit_pack_id` (safe online add)
The column already exists (`UUID`, nullable, no FK) with possibly-NULL live data. Add the constraint **NOT VALID** then **VALIDATE** to avoid a full-table `ACCESS EXCLUSIVE` scan-lock:
```sql
ALTER TABLE payments
  ADD CONSTRAINT fk_payments_credit_pack
  FOREIGN KEY (credit_pack_id) REFERENCES credit_packs(id)
  ON DELETE SET NULL NOT VALID;
ALTER TABLE payments VALIDATE CONSTRAINT fk_payments_credit_pack;
```
`ON DELETE SET NULL` — a deleted pack must not orphan a real payment record. Existing NULLs pass (FK allows NULL). This runs in **migration 0005** *after* `credit_packs` is created and seeded in 0004 (ordering matters — see §9).

---

### 2. Invoicing / Refunds / Promos / Payment audit

#### `invoices` — TENANT (org_id + RLS)
VN VAT/hóa đơn record. One per successful `payment` (top-up) or per subscription period.

| col | type | notes |
|---|---|---|
| `id` | `_PK()` | |
| `org_id` | `UUID NOT NULL FK orgs.id ondelete=RESTRICT` | RESTRICT — financial record, never silently cascade-deleted (mirrors `payments.org_id`) |
| `invoice_no` | `Text NOT NULL` | sequential human number `VV-2026-000123` |
| `payment_id` | `UUID FK payments.id ondelete=SET NULL` | |
| `subscription_id` | `UUID FK subscriptions.id ondelete=SET NULL` | |
| `status` | `Text NOT NULL default 'ISSUED'` | `DRAFT/ISSUED/PAID/VOID/REFUNDED` (check) |
| `currency` | `Text NOT NULL default 'VND'` | |
| `subtotal_vnd` | `BigInteger NOT NULL` | |
| `vat_rate` | `Numeric(5,4) NOT NULL default 0.10` | VN VAT 10% |
| `vat_vnd` | `BigInteger NOT NULL default 0` | |
| `total_vnd` | `BigInteger NOT NULL` | |
| `buyer_name` | `Text default ''` | hóa đơn fields |
| `buyer_tax_code` | `Text default ''` | MST (mã số thuế) |
| `buyer_address` | `Text default ''` | |
| `buyer_email` | `CITEXT` | |
| `issued_at` | `timestamptz` | |
| `meta` | `JSONB default '{}'` | e-invoice provider payload (Viettel/MISA later) |
| `created_at` | `_TS()` | |

Unique `uq_invoice_no (invoice_no)`. Index `ix_invoices_org_created (org_id, created_at)`. Check `status IN (...)`, `total_vnd >= 0`.
**Sequence:** `invoice_no` from a global `Sequence` `invoice_no_seq` (created in migration), formatted in app code. Global sequence (not per-org) because tax authorities expect monotonic issuer-wide numbering.

#### `invoice_lines` — TENANT (org_id + RLS)
| col | type | notes |
|---|---|---|
| `id` | `BigInteger Identity() PK` | append-style line items |
| `org_id` | `UUID NOT NULL FK orgs.id ondelete=RESTRICT` | denormalized for RLS (every tenant table needs its own org_id for the policy) |
| `invoice_id` | `UUID NOT NULL FK invoices.id ondelete=CASCADE` | |
| `description` | `Text NOT NULL` | |
| `quantity` | `Numeric(12,3) NOT NULL default 1` | |
| `unit_price_vnd` | `BigInteger NOT NULL` | |
| `amount_vnd` | `BigInteger NOT NULL` | |
| `credit_pack_id` | `UUID FK credit_packs.id ondelete=SET NULL` | |
| `created_at` | `_TS()` | |

Index `ix_invoice_lines_invoice (invoice_id)`. Note `org_id` is required even though `invoice_id` implies the org — RLS policies operate per-table, so the policy column must be local.

#### `refunds` — TENANT (org_id + RLS)
Distinct from the ledger `REFUND` entry (which is credit-side). This is **money-side** refund tracking (a customer gets VND back), linked to the credit reversal.

| col | type | notes |
|---|---|---|
| `id` | `_PK()` | |
| `org_id` | `UUID NOT NULL FK orgs.id ondelete=RESTRICT` | |
| `payment_id` | `UUID NOT NULL FK payments.id ondelete=RESTRICT` | |
| `invoice_id` | `UUID FK invoices.id ondelete=SET NULL` | |
| `amount_vnd` | `BigInteger NOT NULL` | |
| `credits_reversed` | `BigInteger NOT NULL default 0` | |
| `ledger_entry_id` | `BigInteger` | the `REFUND` ledger row (no FK — ledger PK is BigInt, mirrors `payments.ledger_entry_id` which is also FK-less) |
| `reason` | `Text NOT NULL default ''` | |
| `status` | `Text NOT NULL default 'PENDING'` | `PENDING/PROCESSED/FAILED` (check) |
| `requested_by` | `UUID FK users.id` | |
| `processed_at` | `timestamptz` | |
| `provider_ref` | `Text default ''` | gateway refund id |
| `created_at` | `_TS()` | |

Index `ix_refunds_org_created (org_id, created_at)`, `ix_refunds_payment (payment_id)`. Check `amount_vnd > 0`.

#### `coupons` — GLOBAL (catalog) + `coupon_redemptions` — TENANT
`coupons` GLOBAL — a promo code is platform-issued, not org-owned:

| col | type | notes |
|---|---|---|
| `id` | `_PK()` | |
| `code` | `CITEXT NOT NULL` | case-insensitive entry (`TET2026`) |
| `kind` | `Text NOT NULL` | `PERCENT/FIXED_VND/BONUS_CREDITS` (check) |
| `value` | `BigInteger NOT NULL` | percent (0–100) or VND or credits per kind |
| `max_redemptions` | `Integer` | null = unlimited |
| `max_per_org` | `Integer NOT NULL default 1` | |
| `redeemed_count` | `Integer NOT NULL default 0` | atomic `UPDATE ... SET redeemed_count=redeemed_count+1 WHERE redeemed_count < max_redemptions` |
| `min_amount_vnd` | `BigInteger NOT NULL default 0` | |
| `applies_to` | `Text NOT NULL default 'topup'` | `topup/subscription/any` |
| `starts_at` / `expires_at` | `timestamptz` | |
| `is_active` | `Boolean NOT NULL default true` | |
| `created_at/updated_at` | `_TS()` | |

Unique `uq_coupon_code (code)`. Check `kind IN (...)`, `value >= 0`.

`coupon_redemptions` — TENANT (org_id + RLS): who used what, enforces `max_per_org`.

| col | type | notes |
|---|---|---|
| `id` | `_PK()` | |
| `org_id` | `UUID NOT NULL FK orgs.id ondelete=CASCADE` | |
| `coupon_id` | `UUID NOT NULL FK coupons.id ondelete=RESTRICT` | |
| `payment_id` | `UUID FK payments.id ondelete=SET NULL` | |
| `redeemed_by` | `UUID FK users.id` | |
| `amount_discounted_vnd` | `BigInteger NOT NULL default 0` | |
| `credits_granted` | `BigInteger NOT NULL default 0` | |
| `created_at` | `_TS()` | |

Unique `uq_coupon_redemption_org (coupon_id, org_id)` enforces `max_per_org=1` at DB level (the common case); the `max_per_org>1` case relaxes to app-checked count. Index `ix_coupon_redemptions_org (org_id)`.

#### `webhook_events` — GLOBAL — **IPN idempotency + audit**
Hardens the existing `apply_topup` idempotency (which today relies on `payments.ext_ref` UNIQUE + `FOR UPDATE`). This table records **every** inbound gateway callback (VNPay IPN, MoMo, future USDT) for replay-dedup and forensics — IPNs arrive **unauthenticated** (no JWT, no org GUC) so this **must be GLOBAL, no RLS**.

| col | type | notes |
|---|---|---|
| `id` | `_PK()` | |
| `provider` | `Text NOT NULL` | `vnpay/momo/usdt` |
| `event_type` | `Text NOT NULL default 'ipn'` | |
| `dedup_key` | `Text NOT NULL` | provider txn id / `vnp_TxnRef` + response code |
| `payment_id` | `UUID FK payments.id ondelete=SET NULL` | resolved after match |
| `signature_valid` | `Boolean NOT NULL default false` | result of HMAC verify (`verify_vnpay_ipn`) |
| `processed` | `Boolean NOT NULL default false` | set true after `apply_topup` ran |
| `http_status_returned` | `Integer` | what we replied to gateway |
| `payload` | `JSONB NOT NULL default '{}'` | raw params (audit) |
| `received_at` | `_TS()` | |
| `processed_at` | `timestamptz` | |

**Unique `uq_webhook_dedup (provider, dedup_key)`** — the hard idempotency net: a replayed IPN hits this constraint, code catches `IntegrityError` → no double-credit. This is the second line of defense behind `payments` FOR UPDATE; together they make double-credit impossible even under concurrent retries. Index `ix_webhook_events_payment (payment_id)`, `ix_webhook_events_received (received_at)`.

---

### 3. Creative assets — **backs the 3 reserved `jobs` FKs**

The reserved columns `jobs.template_id`, `jobs.kol_persona_id`, `jobs.brand_kit_id` (all `UUID`, nullable, no FK) get real tables + FKs in **migration 0006** (after the tables exist in 0006's create step).

#### `templates` — TENANT (org_id + RLS), with a GLOBAL-template carve-out
Reusable video recipes. Supports **platform templates** (org-less, curated) AND **org templates** — handled by making `org_id` nullable + a NULL-friendly RLS policy (see D6).

| col | type | notes |
|---|---|---|
| `id` | `_PK()` | |
| `org_id` | `UUID FK orgs.id ondelete=CASCADE` | **nullable** — NULL = platform-global template |
| `name` | `Text NOT NULL` | |
| `name_vi` | `Text NOT NULL default ''` | |
| `category` | `Text NOT NULL default 'product_ad'` | matches `jobs.kind` vocabulary |
| `spec` | `JSONB NOT NULL default '{}'` | the clamped spec_input shape consumed by `validate_and_clamp` |
| `aspect/resolution/seconds` | mirror `jobs` cols | defaults from a job spec |
| `thumbnail_url` | `Text default ''` | |
| `is_public` | `Boolean NOT NULL default false` | |
| `created_by` | `UUID FK users.id` | |
| `created_at/updated_at` | `_TS()` | |

Index `ix_templates_org (org_id)`, `ix_templates_public (category) WHERE is_public AND org_id IS NULL`.
**RLS (D6):** policy `USING (org_id IS NULL OR org_id = nullif(current_setting('vietvid.current_org', true),'')::uuid)` — org sees its own + globals. `WITH CHECK` is the strict org-only predicate (you can't write a global template via normal path; seeding globals runs as table owner which FORCE-RLS still applies to — so seed globals in the migration with a `SET LOCAL row_security = off` or via a superuser/owner bypass; see D6 note).

#### `kol_personas` — TENANT (org_id + RLS, same nullable-global pattern)
Vietnamese KOL / voice persona presets (drives `edge-tts` voice + visual style).

| col | type | notes |
|---|---|---|
| `id` | `_PK()` | |
| `org_id` | `UUID FK orgs.id ondelete=CASCADE` | nullable = platform persona |
| `name` | `Text NOT NULL` | |
| `gender` | `Text default ''` | |
| `voice_id` | `Text NOT NULL default ''` | edge-tts voice (`vi-VN-HoaiMyNeural` etc.) |
| `voice_style` | `Text default ''` | |
| `speaking_rate` | `Numeric(4,2) default 1.0` | |
| `appearance_prompt` | `Text default ''` | Gemini image conditioning |
| `reference_image_url` | `Text default ''` | |
| `sample_audio_url` | `Text default ''` | |
| `is_public` | `Boolean default false` | |
| `created_by` | `UUID FK users.id` | |
| `created_at/updated_at` | `_TS()` | |

Index `ix_kol_personas_org (org_id)`. Same nullable-global RLS as templates.

#### `brand_kits` — TENANT (org_id + RLS) — org-only (no global variant)
| col | type | notes |
|---|---|---|
| `id` | `_PK()` | |
| `org_id` | `UUID NOT NULL FK orgs.id ondelete=CASCADE` | strictly org-owned |
| `name` | `Text NOT NULL default 'Default'` | |
| `logo_url` | `Text default ''` | |
| `primary_color/secondary_color` | `Text default ''` | hex |
| `font_family` | `Text default ''` | |
| `watermark_url` | `Text default ''` | |
| `cta_text` | `Text default ''` | |
| `brand_voice` | `Text default ''` | tone notes |
| `assets` | `JSONB default '{}'` | extra brand assets |
| `is_default` | `Boolean NOT NULL default false` | |
| `created_by` | `UUID FK users.id` | |
| `created_at/updated_at` | `_TS()` | |

Index `ix_brand_kits_org (org_id)`; partial unique `uq_brand_kit_default ON brand_kits(org_id) WHERE is_default` (one default kit/org). Standard org-only RLS (the baseline predicate).

#### Backing the 3 reserved `jobs` FKs (online, NOT VALID + VALIDATE)
In **migration 0007**, after templates/kol_personas/brand_kits exist:
```sql
ALTER TABLE jobs ADD CONSTRAINT fk_jobs_template
  FOREIGN KEY (template_id) REFERENCES templates(id) ON DELETE SET NULL NOT VALID;
ALTER TABLE jobs ADD CONSTRAINT fk_jobs_kol_persona
  FOREIGN KEY (kol_persona_id) REFERENCES kol_personas(id) ON DELETE SET NULL NOT VALID;
ALTER TABLE jobs ADD CONSTRAINT fk_jobs_brand_kit
  FOREIGN KEY (brand_kit_id) REFERENCES brand_kits(id) ON DELETE SET NULL NOT VALID;
ALTER TABLE jobs VALIDATE CONSTRAINT fk_jobs_template;
ALTER TABLE jobs VALIDATE CONSTRAINT fk_jobs_kol_persona;
ALTER TABLE jobs VALIDATE CONSTRAINT fk_jobs_brand_kit;
```
`ON DELETE SET NULL` — deleting a template/persona/kit must not destroy historical jobs that used it. **RLS interaction:** `jobs` is itself RLS-tenant; these FKs point at tables that have global (NULL-org) rows. A job referencing a global template is fine — FK validation runs as table owner and the referenced row exists regardless of GUC. But beware: when a tenant session reads `templates` via a join, the templates RLS policy applies; that's why the nullable-global policy (D6) exists.

---

### 4. Media storage (R2/S3) — backs `STORAGE_*` config + `media.py`

#### `media_assets` — TENANT (org_id + RLS)
First-class storage records for **all** files (source uploads, generated images, intermediate clips, final videos, thumbnails). Today `videos.storage_url` is a bare string and `routers/uploads.py` returns raw local paths; this normalizes storage and is the join target for R2 lifecycle/GC.

| col | type | notes |
|---|---|---|
| `id` | `_PK()` | |
| `org_id` | `UUID NOT NULL FK orgs.id ondelete=CASCADE` | |
| `job_id` | `UUID FK jobs.id ondelete=SET NULL` | nullable: uploads exist before a job |
| `kind` | `Text NOT NULL` | `source_image/gen_image/clip/video/thumbnail/poster/audio` (check) |
| `storage_backend` | `Text NOT NULL default 'local'` | `local/s3/r2` (matches `storage_configured()`) |
| `bucket` | `Text default ''` | |
| `object_key` | `Text NOT NULL` | R2 key OR local path |
| `public_url` | `Text default ''` | CDN base + key (`STORAGE_PUBLIC_BASE`) |
| `content_type` | `Text default ''` | |
| `size_bytes` | `BigInteger NOT NULL default 0` | |
| `width/height` | `Integer default 0` | |
| `duration_s` | `Numeric(8,3) default 0` | |
| `checksum_sha256` | `Text default ''` | dedup/integrity |
| `status` | `Text NOT NULL default 'PENDING'` | `PENDING/UPLOADED/READY/DELETED` (check) |
| `uploaded_by` | `UUID FK users.id` | |
| `expires_at` | `timestamptz` | lifecycle GC (mirrors `videos.expires_at`) |
| `meta` | `JSONB default '{}'` | |
| `created_at` | `_TS()` | |

Indexes: `ix_media_assets_org_created (org_id, created_at)`, `ix_media_assets_job (job_id)`, `ix_media_assets_gc (expires_at) WHERE status='READY' AND expires_at IS NOT NULL` (GC sweep). Unique `uq_media_object (storage_backend, bucket, object_key)`.
**Non-breaking adoption:** `videos.storage_url` stays as-is; add nullable `videos.media_asset_id UUID FK media_assets.id ondelete=SET NULL` (additive `ALTER`) so videos can point at the normalized asset without a destructive migration. Code writes both during transition.

#### `asset_versions` — TENANT (org_id + RLS)
Immutable history of an asset (re-renders, watermark-removed variant, format transcodes). Lets "remove watermark" (existing `videos.watermark_removed_at`) produce a new version instead of mutating.

| col | type | notes |
|---|---|---|
| `id` | `BigInteger Identity() PK` | |
| `org_id` | `UUID NOT NULL FK orgs.id ondelete=CASCADE` | |
| `media_asset_id` | `UUID NOT NULL FK media_assets.id ondelete=CASCADE` | |
| `version_no` | `Integer NOT NULL` | |
| `object_key` | `Text NOT NULL` | |
| `variant` | `Text NOT NULL default 'original'` | `original/no_watermark/transcode_h264/...` |
| `size_bytes` | `BigInteger default 0` | |
| `meta` | `JSONB default '{}'` | |
| `created_at` | `_TS()` | |

Unique `uq_asset_version (media_asset_id, version_no)`. Index `ix_asset_versions_org (org_id)`.

---

### 5. Audit, notifications, API keys, analytics, support, compliance, moderation

#### `audit_log` — GLOBAL (append-only) — see D5
Security/compliance trail (who did what). GLOBAL + **no RLS** so it survives org deletion and is queryable by platform admins across tenants; `org_id` kept as a plain (FK-less) column so a cascade org-delete doesn't wipe the audit trail.

| col | type | notes |
|---|---|---|
| `id` | `BigInteger Identity() PK` | append-only |
| `org_id` | `UUID` | plain column, **no FK** (survives org delete) |
| `actor_user_id` | `UUID` | plain, no FK (survive user delete) |
| `action` | `Text NOT NULL` | `auth.login`, `billing.topup`, `job.create`, `member.invite`, `dsr.export` |
| `resource_type` | `Text default ''` | |
| `resource_id` | `Text default ''` | |
| `ip` | `Text default ''` | |
| `user_agent` | `Text default ''` | |
| `detail` | `JSONB default '{}'` | |
| `created_at` | `_TS()` | |

Append-only trigger (reuse the `ledger_immutable()` pattern → a generic `audit_immutable()` blocking UPDATE/DELETE). Indexes `ix_audit_org_created (org_id, created_at)`, `ix_audit_action (action, created_at)`.

#### `notifications` — TENANT (org_id + RLS)
In-app notifications (job ready, payment succeeded, low credits).

| col | type | notes |
|---|---|---|
| `id` | `_PK()` | |
| `org_id` | `UUID NOT NULL FK orgs.id ondelete=CASCADE` | |
| `user_id` | `UUID FK users.id ondelete=CASCADE` | null = org-wide |
| `type` | `Text NOT NULL` | `job_ready/job_failed/payment_succeeded/low_credits/invite` |
| `title` | `Text NOT NULL` | |
| `body` | `Text default ''` | |
| `link` | `Text default ''` | |
| `channels` | `JSONB default '["inapp"]'` | which channels fired |
| `read_at` | `timestamptz` | |
| `created_at` | `_TS()` | |

Index `ix_notifications_user_unread (user_id, created_at) WHERE read_at IS NULL`, `ix_notifications_org (org_id)`.

#### `notification_prefs` — TENANT (org_id + RLS)
| col | type | notes |
|---|---|---|
| `id` | `_PK()` | |
| `org_id` | `UUID NOT NULL FK orgs.id ondelete=CASCADE` | |
| `user_id` | `UUID NOT NULL FK users.id ondelete=CASCADE` | |
| `email_enabled` | `Boolean default true` | |
| `inapp_enabled` | `Boolean default true` | |
| `event_prefs` | `JSONB default '{}'` | per-type toggles |
| `updated_at` | `_TS()` | |

Unique `uq_notif_pref_org_user (org_id, user_id)`.

#### `api_keys` — TENANT (org_id + RLS)
Programmatic access (B2B/agency). Stores **hash only** (mirrors `auth_tokens` discipline — "Chỉ lưu HASH").

| col | type | notes |
|---|---|---|
| `id` | `_PK()` | |
| `org_id` | `UUID NOT NULL FK orgs.id ondelete=CASCADE` | |
| `name` | `Text NOT NULL` | |
| `key_prefix` | `Text NOT NULL` | first 8 chars shown in UI (`vv_live_xxxx`) |
| `key_hash` | `Text NOT NULL` | sha256, never raw |
| `scopes` | `JSONB default '[]'` | |
| `created_by` | `UUID FK users.id` | |
| `last_used_at` | `timestamptz` | |
| `expires_at` | `timestamptz` | |
| `revoked_at` | `timestamptz` | |
| `created_at` | `_TS()` | |

Unique `uq_api_key_hash (key_hash)` (global uniqueness of the secret; on a TENANT table that's fine — uniqueness is enforced regardless of RLS). Index `ix_api_keys_org (org_id) WHERE revoked_at IS NULL`, `ix_api_keys_prefix (key_prefix)`.
**Lookup caveat:** verifying an API key at request time happens **before** an org GUC is set (the key *resolves* the org). So the lookup-by-`key_hash` path must run in `session_scope()` (no RLS) — but `api_keys` is RLS-FORCED. Resolution: either (a) keep `api_keys` **GLOBAL** like `auth_tokens`/`org_invitations` (which are global precisely because they're consulted pre-tenant-resolution), or (b) keep it tenant and do the unauthenticated lookup via a dedicated `SECURITY DEFINER` function. **Decision D4: make `api_keys` GLOBAL** (no RLS), consistent with `auth_tokens`/`org_invitations` — it carries `org_id` as a column but isn't RLS-scoped, because it's the thing that *establishes* the tenant. Listing keys in the dashboard filters `org_id` explicitly in the router (already the codebase norm).

#### `analytics_events` — TENANT (org_id + RLS)
Product analytics (page views, wizard steps, funnel). High-volume append.

| col | type | notes |
|---|---|---|
| `id` | `BigInteger Identity() PK` | |
| `org_id` | `UUID NOT NULL FK orgs.id ondelete=CASCADE` | |
| `user_id` | `UUID` | plain, no FK (volume) |
| `event_name` | `Text NOT NULL` | `wizard.step`, `job.created`, `video.downloaded` |
| `properties` | `JSONB default '{}'` | |
| `session_id` | `Text default ''` | |
| `created_at` | `_TS()` | |

Index `ix_analytics_org_created (org_id, created_at)`, `ix_analytics_event (event_name, created_at)`. **Partitioning note (D9):** declare as a candidate for monthly `PARTITION BY RANGE (created_at)` later; ship non-partitioned now (premature partitioning is the speculative-flexibility CLAUDE.md warns against), but keep `created_at` leading the index so converting later is cheap.

#### `usage_rollup` — TENANT (org_id + RLS)
Pre-aggregated daily usage per org (jobs run, credits spent, seconds rendered) — powers dashboard charts without scanning `ledger_entries`/`jobs`.

| col | type | notes |
|---|---|---|
| `id` | `BigInteger Identity() PK` | |
| `org_id` | `UUID NOT NULL FK orgs.id ondelete=CASCADE` | |
| `day` | `Date NOT NULL` | |
| `jobs_created` | `Integer default 0` | |
| `jobs_succeeded` | `Integer default 0` | |
| `credits_spent` | `BigInteger default 0` | |
| `credits_topped_up` | `BigInteger default 0` | |
| `seconds_rendered` | `Integer default 0` | |
| `usd_cost` | `Numeric(12,6) default 0` | |
| `updated_at` | `_TS()` | |

Unique `uq_usage_rollup_org_day (org_id, day)` (upsert target). Index `ix_usage_rollup_org_day (org_id, day)`.

#### `support_tickets` — TENANT (org_id + RLS) + `support_messages`
| `support_tickets` col | type | notes |
|---|---|---|
| `id` | `_PK()` | |
| `org_id` | `UUID NOT NULL FK orgs.id ondelete=CASCADE` | |
| `created_by` | `UUID FK users.id` | |
| `subject` | `Text NOT NULL` | |
| `category` | `Text default 'general'` | `billing/bug/feature/abuse` |
| `status` | `Text NOT NULL default 'OPEN'` | `OPEN/PENDING/RESOLVED/CLOSED` (check) |
| `priority` | `Text default 'normal'` | |
| `job_id` | `UUID FK jobs.id ondelete=SET NULL` | optional context |
| `last_message_at` | `timestamptz` | |
| `created_at/updated_at` | `_TS()` | |

`support_messages` — TENANT (org_id + RLS): `id _PK`, `org_id FK orgs CASCADE`, `ticket_id UUID FK support_tickets ondelete=CASCADE`, `author_user_id UUID FK users`, `is_staff Boolean default false`, `body Text NOT NULL`, `attachments JSONB default '[]'`, `created_at _TS()`. Index `ix_support_messages_ticket (ticket_id, created_at)`.
Index on tickets: `ix_support_tickets_org_status (org_id, status)`.

#### `data_subject_requests` — GLOBAL (PDPD / GDPR)
Vietnam PDPD (Nghị định 13/2023) + GDPR data-subject requests (export/delete). GLOBAL + no RLS — a deletion request may **outlive** the org/user it targets and must be processed by platform admins; RLS-scoping would hide it once the org is gone.

| col | type | notes |
|---|---|---|
| `id` | `_PK()` | |
| `org_id` | `UUID` | plain, no FK |
| `user_id` | `UUID` | plain, no FK |
| `subject_email` | `CITEXT NOT NULL` | |
| `request_type` | `Text NOT NULL` | `EXPORT/DELETE/RECTIFY/RESTRICT` (check) |
| `status` | `Text NOT NULL default 'RECEIVED'` | `RECEIVED/VERIFYING/PROCESSING/COMPLETED/REJECTED` (check) |
| `verification_token_hash` | `Text default ''` | confirm identity (hash only) |
| `export_url` | `Text default ''` | signed link to export bundle |
| `due_at` | `timestamptz` | SLA (PDPD timelines) |
| `processed_by` | `UUID` | admin |
| `detail` | `JSONB default '{}'` | |
| `created_at` | `_TS()` | |
| `completed_at` | `timestamptz` | |

Index `ix_dsr_status_due (status, due_at)`, `ix_dsr_email (subject_email)`.

#### `moderation_events` — TENANT (org_id + RLS)
Backs the existing `videos.moderation_status`/`moderation_detail` with a full audit trail (each scan/decision is a row). Append-style.

| col | type | notes |
|---|---|---|
| `id` | `BigInteger Identity() PK` | |
| `org_id` | `UUID NOT NULL FK orgs.id ondelete=CASCADE` | |
| `subject_type` | `Text NOT NULL` | `video/image/text` |
| `subject_id` | `UUID NOT NULL` | video.id / media_asset.id (polymorphic, no FK — mixed targets) |
| `job_id` | `UUID FK jobs.id ondelete=SET NULL` | |
| `provider` | `Text default ''` | moderation provider / `internal` |
| `decision` | `Text NOT NULL` | matches `ModerationStatus`: `PENDING/APPROVED/FLAGGED/BLOCKED` (check, reuse constant) |
| `categories` | `JSONB default '[]'` | flagged categories + scores |
| `score` | `Numeric(5,4) default 0` | |
| `reviewed_by` | `UUID FK users.id` | null = automated |
| `notes` | `Text default ''` | |
| `created_at` | `_TS()` | |

Index `ix_moderation_org_created (org_id, created_at)`, `ix_moderation_subject (subject_type, subject_id)`. Check reuses the existing moderation vocabulary so it lines up with `videos.moderation_status`.

---

### 6. Migration ordering & the `create_all` audit risk

**Audit risk (explicit fix).** Baseline 0001 used `Base.metadata.create_all(bind)`. That means `target_metadata = Base.metadata` in `alembic/env.py` reflects the **full** current models module — so any `alembic revision --autogenerate` run *today* would already see the M1 tables as "existing in metadata, existing in DB" (no drift) but would try to **emit CREATE for every new M2 model the moment we add it to `models.py`**, mixing all new tables into one autogen blob with no FORCE-RLS, no partial indexes, no triggers, no seed data, and unpredictable ordering. **Autogen cannot produce a correct migration for this schema** (it never emits RLS policies, `FORCE`, partial/`WHERE` indexes, append-only triggers, `NOT VALID`/`VALIDATE` FK adds, or seed INSERTs). 

**Decision D1 — abandon `create_all`/autogen for M2; use explicit `op.create_table` + raw `op.execute`.** Each M2 migration explicitly creates its tables via `op.create_table(...)` (or `Model.__table__.create(bind, checkfirst=True)` for pure global tables, the pattern already used in 0002/0003), then runs hand-written `op.execute` for partial indexes, RLS enable/force/policy, triggers, and seeds — exactly as baseline 0001 did for the M1 tenant tables. This keeps RLS/index/trigger intent **in the migration, reviewable**, not implicit in `create_all`. Autogen stays available only as a *diff-checker in CI* (D8): run `alembic check` / autogen-to-/dev/null and assert "no changes" to catch model-vs-migration drift, but never commit its output blindly.

**Proposed migration chain (each `down_revision` = prior):**

| rev | adds | tenant tables (RLS in same migration) | reserved-FK work |
|---|---|---|---|
| `20260628_0004_plans_billing` | `plans` (G), `subscriptions` (T), `entitlements` (T), `credit_packs` (G) + **seed** plans & 3 credit packs | subscriptions, entitlements | — |
| `20260628_0005_invoicing_promos` | `invoices` (T), `invoice_lines` (T), `refunds` (T), `coupons` (G), `coupon_redemptions` (T), `webhook_events` (G) + `invoice_no_seq` | invoices, invoice_lines, refunds, coupon_redemptions | **FK `payments.credit_pack_id`→credit_packs (NOT VALID+VALIDATE)** |
| `20260628_0006_creative_assets` | `templates` (T*), `kol_personas` (T*), `brand_kits` (T) + **seed** global templates/personas | templates, kol_personas, brand_kits (templates/kol use nullable-global policy) | — |
| `20260628_0007_jobs_asset_fks` | (constraints only) | — | **3 FKs `jobs.template_id/kol_persona_id/brand_kit_id` (NOT VALID+VALIDATE)** |
| `20260628_0008_media_storage` | `media_assets` (T), `asset_versions` (T) + `ALTER videos ADD media_asset_id` | media_assets, asset_versions | additive `videos.media_asset_id` FK |
| `20260628_0009_audit_notif_apikeys` | `audit_log` (G, immutable trigger), `notifications` (T), `notification_prefs` (T), `api_keys` (G) | notifications, notification_prefs | — |
| `20260628_0010_analytics_support` | `analytics_events` (T), `usage_rollup` (T), `support_tickets` (T), `support_messages` (T) | all four | — |
| `20260628_0011_compliance_moderation` | `data_subject_requests` (G), `moderation_events` (T) | moderation_events | — |

Ordering rules enforced: a table is created **before** any migration adds an FK to it (credit_packs in 0004 → FK in 0005; templates/personas/kits in 0006 → FKs in 0007; media_assets in 0008 → `videos.media_asset_id` same migration). Global catalog tables (`plans`, `credit_packs`, `coupons`) seed in the same migration that creates them so dependent FKs resolve against real rows.

**Per-migration RLS loop (copy of baseline, local list):**
```python
_RLS_USING = "org_id = nullif(current_setting('vietvid.current_org', true), '')::uuid"
_NEW_TENANT_TABLES = ("subscriptions", "entitlements")  # per migration
for t in _NEW_TENANT_TABLES:
    op.execute(f"ALTER TABLE {t} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {t} FORCE ROW LEVEL SECURITY")
    op.execute(f"DROP POLICY IF EXISTS org_isolation ON {t}")
    op.execute(f"CREATE POLICY org_isolation ON {t} USING ({_RLS_USING}) WITH CHECK ({_RLS_USING})")
```
Downgrades reverse: drop policy, disable RLS, `op.drop_table` in reverse dependency order, drop sequences/triggers.

### 7. Seeding globals under FORCE RLS (templates/personas)
`templates`/`kol_personas` are FORCE-RLS but hold global (NULL-`org_id`) rows. FORCE RLS applies to the table owner too, and a NULL `org_id` fails the strict `WITH CHECK`. Two safe options in the migration: (a) seed **before** enabling RLS on that table (create table → INSERT globals → then ENABLE/FORCE), or (b) wrap the seed INSERTs in `SET LOCAL row_security = off` (allowed for the migration's superuser/owner connection). **Choose (a)** — create + seed + then enable RLS, simplest and review-obvious. The nullable-global RLS policy (D6) governs runtime reads only.

### 8. `models.py` changes
Add the new mapped classes following existing style (`_PK()`, `_TS()`, status constant classes, `__table_args__` with `CheckConstraint`/`Index`/`UniqueConstraint`). Extend the `TENANT_TABLES` tuple to the full final tenant set (used by D8's test). Add real `ForeignKey(...)` to the three reserved `jobs` columns and `payments.credit_pack_id` **in the model** at the same time as the migration adds the DB constraint (model and DB stay in lockstep; the `NOT VALID/VALIDATE` is migration-only — SQLAlchemy just sees a normal FK).


---

# 2. Job Pipeline, Queue & Media Infra

## Job Pipeline, Queue & Media Infra

This is the durable-execution layer that turns the M1 in-process `BackgroundTasks` runner into a crash-safe, multi-tenant, fair-shared render farm with real object storage and provider fallback. **Nothing in the M1 contract changes**: `POST /v1/jobs` still does `create_job` (HOLD + insert) in one short tenant txn, commits, then calls `executor.submit_job(...)` *after* commit. The only thing that changes behind that seam is where the work runs.

The design has five tracks. Each maps to concrete files under `app_api/` and `video_engine/`. I deliberately reuse the proven mechanics already on disk (`piapi_task_id` stamping in `sink_queue.QueueSink`, the seedance `on_created`/`resume_task_id` resume path, the reaper's per-org RLS loop, the `media.py` HMAC signer) rather than reinventing them.

---

### 1. Arq + Redis durable queue

#### 1.1 The seam (already correct — fill it in, don't move it)

`app_api/executor.py:submit_job` already branches on `config.JOB_EXECUTION_MODE`. The `queue` branch raises `RuntimeError` today. The whole change is local:

```python
# app_api/executor.py  (queue branch)
if mode == "queue":
    from app_api.queue import enqueue_render
    enqueue_render(org_id, job_id)   # picks lane from job.kind, returns immediately
    return
```

`enqueue_render` is the only new call the router path needs. The router's existing post-commit `try/except` around `submit_job` (`routers/jobs.py:112-120`) already does `release_hold` if enqueue throws — so a Redis outage at enqueue time refunds the HOLD and 500s cleanly. That safety net is reused verbatim; **do not** duplicate it inside `enqueue_render`.

#### 1.2 New module: `app_api/queue.py` (Arq client + settings)

```python
# app_api/queue.py
from arq import create_pool
from arq.connections import RedisSettings

def _redis_settings() -> RedisSettings:
    return RedisSettings.from_dsn(config.REDIS_URL)   # redis://host:6379/0

_LANE_OF = {  # job.kind -> queue name
    "premium": "q_slow", "long_narrative": "q_slow", "film_recap": "q_slow",
}
def lane_for(kind: str) -> str:
    return _LANE_OF.get(kind, "q_fast")

async def _enqueue(org_id, job_id, lane):
    pool = await create_pool(_redis_settings())
    try:
        await pool.enqueue_job(
            "render_job_task", str(org_id), str(job_id),
            _queue_name=lane,
            _job_id=f"render:{job_id}",          # Arq dedup key = idempotent enqueue
            _defer_by=0,
        )
    finally:
        await pool.close()

def enqueue_render(org_id, job_id) -> None:
    kind = _kind_of(job_id)                      # 1 short tenant_session read
    asyncio.run(_enqueue(org_id, job_id, lane_for(kind)))
```

Key decisions:
- **`_job_id=f"render:{job_id}"`** makes Arq's enqueue idempotent. If the router retries enqueue (or a duplicate `POST` slips the `(org_id, idempotency_key)` unique constraint race), Arq collapses it to one queued task. This is the queue-side mirror of the DB-side idempotency already enforced by `uq_jobs_org_idem`.
- `asyncio.run` wrapper because the FastAPI route handler is sync (`def create_job`, runs in threadpool). Keeping the enqueue sync avoids leaking an event loop into the sync handler. Acceptable: enqueue is a sub-millisecond Redis `RPUSH`.

#### 1.3 q_fast / q_slow split

Two Arq queues on one Redis, drained by **separate worker pools** so a 1.75h `long_narrative` render never head-of-line-blocks a 12s `product_ad`. Lane is derived from `job.kind` (mirrors the proven `slow_modes` lane logic in the legacy `video_engine/worker.py:_pick_next_job`):

| Lane | Kinds | Concurrency default | Timeout | Rationale |
|---|---|---|---|---|
| `q_fast` | product_ad, product_only, kol_full, draft, premium-short | `WORKER_FAST_CONCURRENCY=4` | `ARQ_FAST_TIMEOUT=1800s` | money jobs, sub-2-min renders |
| `q_slow` | long_narrative, film_recap | `WORKER_SLOW_CONCURRENCY=1` | `ARQ_SLOW_TIMEOUT=9000s` | heavy renders, isolated pool |

(`premium` stays in `q_fast` — `route_video` caps it at 720p/15s, still sub-2-min. Only the genuinely-long modes go slow.)

#### 1.4 New module: `app_api/queue_worker.py` (the Arq task + WorkerSettings)

The Arq task is a *thin async wrapper around the existing sync `worker.run_job`* — the render itself is unchanged. Arq gives us the durable envelope (retry, ack-after-success, dead-letter) for free.

```python
# app_api/queue_worker.py
async def render_job_task(ctx, org_id: str, job_id: str) -> None:
    # run_job is sync + blocking (httpx poll, ffmpeg) -> thread, never block the loop
    await asyncio.to_thread(worker.run_job, org_id, job_id)

class FastWorker:
    functions = [func(render_job_task, name="render_job_task")]
    queue_name = "q_fast"
    redis_settings = _redis_settings()
    max_jobs = int(config.WORKER_FAST_CONCURRENCY)        # 4
    job_timeout = int(config.ARQ_FAST_TIMEOUT)            # 1800
    max_tries = int(config.ARQ_MAX_TRIES)                 # 3
    retry_delay = backoff_seconds                          # see 1.5
    keep_result = 0                                        # result is in Postgres, not Redis
    on_startup = _warm                                     # ensure_wallet pool / engine ping
    health_check_interval = 30

class SlowWorker(FastWorker):
    queue_name = "q_slow"
    max_jobs = int(config.WORKER_SLOW_CONCURRENCY)        # 1
    job_timeout = int(config.ARQ_SLOW_TIMEOUT)            # 9000
```

`worker.run_job` needs **two surgical changes** to be retry-safe (today it is crash-safe by accident via the reaper, but not retry-aware):

1. **Idempotent terminal guard.** Add a status check at the top so an Arq retry of an already-`READY`/`CANCELLED` job is a no-op instead of a double-SETTLE. `complete_job` already guards `CANCELLED`; extend the guard to all terminal states and move it into `run_job`'s first short txn:
   ```python
   if job.status in TERMINAL_STATES:   # READY, FAILED, REFUNDED, CANCELLED, QA_FAIL
       return None
   ```
2. **Distinguish retryable vs. terminal failure.** `run_job` currently returns a `RenderResult` and `complete_job` decides SETTLE/REFUND. For Arq retry we need *system* faults (provider 5xx, network) to `raise Retry(defer=...)` BEFORE settling, while *input* faults settle-and-stop. Thread the existing `result.fault_class` (`"system"`/`"input"`) out of `render`:
   ```python
   result = render(spec, sink)
   if result.status == FAILED and result.fault_class == "system" and ctx["job_try"] < max_tries:
       raise Retry(defer=backoff_seconds(ctx["job_try"]))   # HOLD stays, no settle yet
   with tenant_session(org_id) as s:
       complete_job(s, org_id, job_id, result)              # final attempt -> settle/refund
   ```
   This is why `render_service` already returns `fault_class` — it was built for exactly this fork. **Crucially the HOLD is not released on a retryable failure**; it stays HELD across retries, and only the reaper (or final-attempt `complete_job`) ever releases it. No double-refund window.

#### 1.5 Retry-with-backoff + dead-letter

- **Backoff:** `backoff_seconds(try_n) = min(BACKOFF_BASE * 2**(try_n-1), BACKOFF_CAP) + jitter`, defaults `BACKOFF_BASE=15s`, `BACKOFF_CAP=600s`, jitter `±20%`. Arq's `Retry(defer=...)` re-enqueues with this delay.
- **Dead-letter:** Arq has no native DLQ, so on the *final* failed try we don't silently drop. The final-attempt `complete_job` already writes `FAILED` + `error` + REFUND (system fault) / SETTLE (input fault). For observability we add one row to a new **`job_retries`** ledger table (see schema) capturing `(job_id, attempt, fault_class, error, provider, ts)` — this IS the dead-letter record, queryable per-tenant under RLS. A nightly `bin/vietvid-dlq-report` (cron) summarizes `FAILED + fault_class='system'` jobs for the founder.
- **Poison-pill cap:** `ARQ_MAX_TRIES=3`. After 3 system-fault tries, force-terminal `FAILED` + REFUND. Prevents a provider-down storm from re-billing budget forever.

#### 1.6 Crash-safe reclaim (the load-bearing reuse)

Arq acks a job only after the coroutine returns. If a worker is `SIGKILL`ed mid-render, Arq's `max_jobs` in-flight tracking + the job's `_job_id` mean the task is **not** lost (Arq re-queues abandoned in-progress jobs on the next worker poll via its `health_check` + `re-enqueue on restart` semantics). When the reclaim fires, `render` re-runs — and the **already-stamped `piapi_task_id`** (persisted by `QueueSink.merge_params` the instant the seedance task was created) makes the seedance provider `resume_task_id` poll the *existing* PiAPI task instead of paying for a new i2v generation. That path already exists and is tested (`seedance_piapi.py:63-74`). The worker design adds nothing here except *not breaking it* — `run_job`'s first txn must NOT clear `params.piapi_task_id`.

The existing `reaper.py` stays as the **belt-and-suspenders** layer: if Redis itself is wiped (not just a worker crash), Arq loses the task entirely, but the DB job is stuck `RUNNING`. The reaper still catches it (older_than `REAPER_STUCK_MINUTES`) and refunds. So we keep the reaper running in `main.py` lifespan *and* in queue mode. One change: in queue mode the reaper should **re-enqueue** an orphaned `RUNNING`/`QUEUED` job (mirroring `video_engine/worker.py:_requeue_orphan_running`) rather than cancel it, IF its `piapi_task_id` is stamped (cheap resume available) and it's under the stuck cutoff×2. Add a `REAPER_REQUEUE_IN_QUEUE_MODE=true` knob.

#### 1.7 Worker process + Dockerfile / topology

Separate process, not part of the API. Two new entrypoints:

```
# Dockerfile.worker  (sibling of the API image)
FROM python:3.12-slim
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*
COPY requirements.txt . && pip install -r requirements.txt   # + arq, boto3
COPY . /app
WORKDIR /app
ENV JOB_EXECUTION_MODE=queue
# fast worker (scale this replica count)
CMD ["arq", "app_api.queue_worker.FastWorker"]
```

Topology (docker-compose / Render services):
- `api` (N replicas) — `JOB_EXECUTION_MODE=queue`, never renders.
- `worker-fast` (M replicas) — `arq app_api.queue_worker.FastWorker`.
- `worker-slow` (1 replica) — `arq app_api.queue_worker.SlowWorker`.
- `redis` (managed: Upstash / Render Redis) — `REDIS_URL`.
- `reaper` runs inside `api` lifespan (already wired) — keep it; it's idempotent and per-org.

ffmpeg lives only in the worker image (API doesn't render). Workers need the same `VIETVID_DATABASE_URL` + storage + provider keys.

---

### 2. Concurrency: per-tenant + global limits, fair-share

Arq's `max_jobs` gives **global** concurrency per worker pool (q_fast=4×replicas, q_slow=1). What it does NOT give is **per-tenant fairness** — one org submitting 50 jobs would monopolize all 4 fast slots and starve everyone else. Three layers:

1. **Per-tenant in-flight cap (admission control at enqueue).** Before enqueue, `enqueue_render` checks a Redis counter `inflight:{org_id}` (INCR/DECR around task execution). If `>= MAX_INFLIGHT_PER_ORG` (default 2 fast / 1 slow, plan-scaled), the job is enqueued with `_defer_by` = a short re-check delay and tagged `status=QUEUED` (already its state) — it waits in Redis but doesn't burn a worker slot. Counter is decremented in the task's `finally`. Use a Lua script (`limits.lua`) for atomic check-and-incr to avoid TOCTOU.
   - Plan-scaling: `tenancy.org_plan_code(org_id)` already exists; map `free=1, pro=3, business=6` via `PLAN_INFLIGHT_JSON`.
2. **Fair-share dispatch.** Instead of strict FIFO (which lets a burst-org dominate), the worker's job-pick is naturally round-robined by the per-org cap: an org at its cap can't have a 3rd job pulled, so the next *different* org's job runs. This is weighted-fair-queueing-lite, achieved purely by the admission counter — no custom scheduler needed. (Proven pattern: same shape as the legacy lane logic, generalized to per-tenant.)
3. **Global cost circuit-breaker** = the daily budget gate (track 4). Even if concurrency allows, the budget gate stops spend.

New module: `app_api/concurrency.py` — `acquire_slot(org_id, lane) -> bool`, `release_slot(org_id, lane)`, backed by Redis. Falls back to no-op (always-acquire) when `REDIS_URL` unset (inline mode) so M1 behavior is unchanged.

---

### 3. Object storage abstraction + lifecycle

#### 3.1 New module: `app_api/storage.py`

Single abstraction, two backends, selected by the **already-defined** `config.storage_configured()`:

```python
# app_api/storage.py
class Storage(Protocol):
    def put(self, local_path: str, key: str, *, content_type: str) -> str: ...   # returns storage_url
    def url_for(self, key: str) -> str: ...        # CDN/public or s3:// internal ref
    def delete(self, key: str) -> None: ...
    def presign_get(self, key: str, ttl: int) -> str: ...

def get_storage() -> Storage:
    return S3Storage() if config.storage_configured() else LocalStorage()
```

- **`LocalStorage`** (MVP/dev fallback): copies into `VIETVID_MEDIA_ROOT` (default `./storage/vietvid`), returns a filesystem path → exactly today's `Video.storage_url` semantics. Zero behavior change when `STORAGE_*` unset.
- **`S3Storage`** (boto3, R2-compatible): uses the existing `config.STORAGE_*` knobs (`STORAGE_ENDPOINT` for R2/MinIO, `STORAGE_REGION='auto'`). Key layout: `org/{org_id}/jobs/{job_id}/final.mp4`. `put` does multipart upload for the ~2-20MB MP4. Returns either the `STORAGE_PUBLIC_BASE` CDN URL (if set) or an `s3://` internal marker.

#### 3.2 Upload on complete (wire into the worker, not the engine)

The engine (`render_service.render`) stays storage-agnostic — it writes `final.mp4` to `workdir` and returns the local path in `RenderResult.path`. **The upload happens in `worker.run_job` step 3, before `complete_job`**, so the engine never learns about S3:

```python
# app_api/worker.py  (step 3, before complete_job)
if result.status == JobStatus.READY and result.path:
    storage = get_storage()
    key = f"org/{org_id}/jobs/{job_id}/final.mp4"
    result.path = storage.put(result.path, key, content_type="video/mp4")  # local path -> storage_url
    # also upload poster/thumbnail if present (track 5)
with tenant_session(org_id) as s:
    complete_job(s, org_id, job_id, result)   # writes Video.storage_url = result.path (unchanged)
```

`complete_job` already writes `Video.storage_url = result.path` and sets `file_size_bytes`/`width`/`height` (those columns exist, are currently 0 — populate them from the local file before upload via `ffprobe`, which the QA stage already runs).

#### 3.3 Signed CDN delivery (extend, don't replace media.py)

`media.py` HMAC signing + `routers/media.py:serve_video` already handle both cases: local path → `FileResponse`, `http(s)://` → `RedirectResponse`. Two extensions:

- For `S3Storage` with **no** public CDN base, `serve_video` should `presign_get(key, ttl)` and redirect to the time-limited S3/R2 URL instead of storing a bare `s3://` that can't be served. Add: if `url.startswith("s3://")` → `RedirectResponse(storage.presign_get(...))`. The HMAC token (our auth) gates *issuance* of the presigned URL; the presigned URL gates *delivery*. Two independent TTLs (`MEDIA_URL_TTL` for our token, a separate `STORAGE_PRESIGN_TTL` for the S3 URL).
- For R2 with a public CDN base (`STORAGE_PUBLIC_BASE`), `storage_url` is already the CDN URL → existing redirect path works untouched.

#### 3.4 Lifecycle / TTL + workdir cleanup (the real bug: unbounded tmp growth)

**Audit finding — confirmed unbounded growth.** `worker.run_job` creates `tempfile.gettempdir()/vietvid_jobs/{job_id}` and **never deletes it**. `render` *also* mkdtemps when `spec.workdir` is empty (it isn't here, but the engine path can leak). Every render leaves clean-plate PNGs, clip.mp4, voice.wav, final.mp4 on disk. On a long-lived worker this fills the disk and eventually fails renders with `ENOSPC`. Two fixes:

1. **Per-job workdir cleanup in `worker.run_job` `finally`.** After upload (success) or terminal failure, `shutil.rmtree(workdir, ignore_errors=True)`. Gate with `KEEP_WORKDIR=false` (set `true` in dev for debugging). This is the primary fix.
   - **Subtlety:** must NOT delete before the `piapi_task_id`-resumable retry window if upload failed. Rule: rmtree only on **terminal** outcome (READY uploaded OK, or terminal FAILED/QA_FAIL/CANCELLED). On a retryable system fault we keep the workdir so the next attempt can reuse the already-downloaded clip. A separate **boot-time + periodic sweeper** (`storage.sweep_orphan_workdirs`) removes any `vietvid_jobs/*` dir whose job is terminal or older than `WORKDIR_TTL_HOURS=6` — catches workdirs orphaned by SIGKILL. Wire into the reaper loop in `main.py` (it already runs periodically).
2. **Object-storage lifecycle for `Video`.** The `videos.expires_at` column already exists (currently unused). Set it on insert for non-paid/watermarked previews (`expires_at = now + VIDEO_PREVIEW_TTL_DAYS`, paid/watermark-removed = NULL = keep forever). Two enforcement paths:
   - **S3/R2 native lifecycle rule** (set once via `bin/vietvid-storage-init`): expire objects under a `previews/` prefix after N days — cheapest, no compute.
   - **DB sweeper** (`storage.sweep_expired_videos`, per-org under RLS, in reaper loop): for `videos WHERE expires_at < now()`, `storage.delete(key)` + null the `storage_url` (keep the row for ledger/audit; mark `error='expired'`). Mirrors the existing per-org reaper loop exactly.

---

### 4. Provider routing / fallback + per-job cost ceiling

#### 4.1 Fallback (today: single provider, no fallback)

`routing.route_video` returns one `VideoRoute` from one `settings.video_provider`. Production needs a fallback chain so a PiAPI outage doesn't fail every job. Extend `routing.py` with an ordered candidate list (no engine-pipeline change — `render` already wraps `video_provider.generate` in a retry for `ProviderRejectedError`; we widen that to provider-level fallback):

```python
# video_engine/providers/routing.py
def route_video_chain(mode, purpose, resolution) -> list[VideoRoute]:
    primary = route_video(mode, purpose, resolution)          # seedance via PiAPI (unchanged)
    chain = [primary]
    for alt in _parse_fallback(settings.video_fallback_providers):   # e.g. "seedance_piapi,kling_piapi"
        if alt != primary.provider:
            chain.append(replace(primary, provider=alt, model_id=_alt_model(alt, primary)))
    return chain
```

In `render`, wrap the `video_provider.generate` call: on `ProviderNotConfiguredError` or a *system* `VideoEngineError` (NOT `ProviderRejectedError` — moderation reject is content, fallback won't help), advance to the next route. **Resume safety:** `piapi_task_id` is provider-specific, so a fallback to a different provider clears `resume_task_id` (start fresh on the new provider); a retry on the *same* provider keeps it. Cost is only counted for the provider that actually produced the clip (the existing `if video_provider.name != "mock"` guard generalizes to per-attempt cost accumulation).

#### 4.2 Per-job cost ceiling (`max_cost_usd`)

Already half-built: `render` computes `max_cost_usd = estimate["total_usd"] * 1.5` and passes it to `sink.update_job`, and `estimate_hold` HOLDs `ceil(est_credits * 1.5)`. Wire it to actually **abort** a runaway job: before each paid provider call, assert `actual_cost + next_call_est <= max_cost_usd`; if exceeded, raise `VideoBudgetError` → job goes `QUEUED_BUDGET` (no charge beyond what ran). This caps blast radius if a provider's per-second price is misconfigured. The HOLD (1.5×) is the credit-side ceiling; this is the USD-side ceiling. Both already exist as numbers; this connects the USD one to a guard.

#### 4.3 Daily budget gate (`VIDEO_DAILY_BUDGET`) — port to app_api's DB

The legacy `video_engine/providers/ledger.py` budget gate uses `core.database.db` (the old monolith), which `app_api` does NOT connect to. The M0 `render_service` explicitly dropped budget reserve/settle. For production we re-introduce it **in the app_api DB world** so it shares the same Postgres + RLS-exempt global ledger:

- New **global** table `provider_budget_ledger` (NOT tenant-scoped — it's a platform-wide cost fuse, like the founder's daily spend cap, not per-org). `(date, provider)` unique, `spent_usd`, `budget_usd`, `jobs_count`. Reserve with `SELECT ... FOR UPDATE` (identical algorithm to the proven `ledger.py:reserve_video_budget`, just pointed at `app_api/db.session_scope`).
- New module `app_api/budget.py`: `reserve_video_budget(est_usd) -> (reserved, day)` / `settle_video_budget(reserved, actual, day)`. Called by `worker.run_job` *before* render (reserve) and *after* (settle delta). On `VideoBudgetError`, job → `QUEUED_BUDGET`, HOLD stays HELD, and the queue retries it next day (the `q_fast` worker's blocked-job retry loop, ported from `video_engine/worker.py:_pick_next_job` as an Arq cron that re-enqueues `QUEUED_BUDGET` jobs every `BUDGET_RETRY_MINUTES=5`).
- Reset is midnight in `dispatch_timezone` (Asia/Ho_Chi_Minh) — reuse the exact `_today()` logic so the founder's "spent today" matches local day, not UTC.

`QUEUED_BUDGET` must be added to the `JobStatus` class and the `ck_jobs_status` CHECK constraint (it's referenced by `render_service` but missing from `app_api/models.py:JobStatus` — latent bug today; a render that hits budget would write an invalid status and the INSERT/UPDATE would violate the check). Migration alters the constraint.

---

### 5. Progress streaming (DB-poll today → add SSE)

Today the frontend polls `GET /v1/jobs/{id}` which reads `job_events` (written live by `QueueSink._event`). This works but is chatty (1-3s poll × every open job card). Add an **SSE endpoint that tails `job_events`** without changing the writer:

- New route `GET /v1/jobs/{job_id}/events/stream` (authed, tenant-scoped) in `routers/jobs.py`. Returns `text/event-stream`. Server loop: every `SSE_POLL_MS` (default 1000ms) reads `job_events WHERE id > last_seen_id` under a short `tenant_session`, emits each as an SSE `data:` frame, advances `last_seen_id`. Closes when job reaches a terminal status (emit a final `event: done`).
- **Why poll-backed SSE, not Redis pub/sub:** `QueueSink` runs in the *worker* process and writes to Postgres; the SSE endpoint runs in the *API* process. The durable source of truth is already `job_events` in Postgres. A Redis pub/sub channel (`progress:{job_id}`) is an optional latency optimization (worker PUBLISHes on each `_event`, API SUBSCRIBEs) — design it as a **fast-path layered on top of** the DB poll (fall back to poll if Redis is down), never as the source of truth. Mirrors the "gbrain enhances, file is reliable" principle. Ship DB-poll-SSE first; pub/sub is a `PROGRESS_PUBSUB=true` opt-in.
- The existing `GET /v1/jobs/{id}` poll stays as the no-SSE fallback (proxies/old browsers). SSE is additive.
- Reuse the `_event` detail shape already emitted (`stage`, `event_type`, `provider`, `cost_usd`, `asset_url`, `detail.qa`) — the SSE frame is just the existing `JobEventOut` serialized, so the frontend's event renderer is unchanged.

---

### Module-change summary (concrete)

| File | Change |
|---|---|
| `app_api/executor.py` | fill `queue` branch → `enqueue_render` |
| `app_api/queue.py` | **new** — Arq pool, `enqueue_render`, lane routing, idempotent `_job_id` |
| `app_api/queue_worker.py` | **new** — `render_job_task`, `FastWorker`/`SlowWorker` settings |
| `app_api/worker.py` | terminal-guard, fault-class retry fork, storage upload, workdir cleanup `finally`, budget reserve/settle |
| `app_api/concurrency.py` | **new** — per-org Redis admission counter + fair-share |
| `app_api/storage.py` | **new** — `Storage` protocol, `LocalStorage`, `S3Storage` (boto3/R2) |
| `app_api/budget.py` | **new** — daily budget reserve/settle ported to app_api DB |
| `app_api/reaper.py` | add re-enqueue-in-queue-mode, call workdir + expired-video sweepers |
| `app_api/routers/jobs.py` | add `GET /{job_id}/events/stream` (SSE) |
| `app_api/routers/media.py` | add `s3://` → `presign_get` redirect branch |
| `app_api/models.py` | add `QUEUED_BUDGET` to `JobStatus`; new `JobRetry`, `ProviderBudgetLedger` models |
| `app_api/config.py` | add `REDIS_URL`, `WORKER_*`, `ARQ_*`, `BACKOFF_*`, `MAX_INFLIGHT_PER_ORG`, `VIDEO_MEDIA_ROOT`, `WORKDIR_TTL_HOURS`, `VIDEO_PREVIEW_TTL_DAYS`, `STORAGE_PRESIGN_TTL`, `SSE_POLL_MS`, fallback knobs |
| `video_engine/providers/routing.py` | add `route_video_chain` for provider fallback |
| `video_engine/render_service.py` | provider-level fallback loop around `video_provider.generate`; wire `max_cost_usd` USD ceiling guard |
| `alembic/versions/20260627_0004_*.py` | **new** — `provider_budget_ledger` (global), `job_retries` (tenant+RLS), `QUEUED_BUDGET` CHECK alter, `videos.expires_at` index |
| `Dockerfile.worker`, `docker-compose.yml` | **new** — worker image + topology |
| `bin/vietvid-storage-init`, `bin/vietvid-dlq-report` | **new** — one-time R2 lifecycle rule, nightly DLQ summary |


---

# 3. Billing, Payments & Subscriptions

## Billing, Payments & Subscriptions

This extends the existing ACID wallet (`wallet.py`), append-only ledger (`ledger_entries`), idempotent top-up (`billing.apply_topup`), and the `payments` table. Nothing here re-designs the credit invariants — every money movement still routes through `wallet.hold/settle/refund/topup/grant_once` inside a `tenant_session(org_id)`, and every grant/charge/refund lands as a ledger row. We add the **gateway layer**, **data-driven plans/packs**, **subscription lifecycle**, **invoices/VAT**, **money-refund lifecycle**, and **coupons/referral**.

The single biggest correctness gap today: the VNPay IPN verifies the HMAC signature and resolves the org, but **never checks `vnp_Amount` against `payments.amount_vnd`** (`billing.verify_vnpay_ipn` returns only `(sig_ok and paid, txn_ref)`). A signed-but-tampered callback, or a stale sandbox replay with a different amount, would credit the pack's full `credits_granted` regardless of money actually moved. We fix this with a mandatory reconciliation step in a generic adapter contract.

---

### 1. Payment gateway abstraction (`app_api/payments/`)

Today VNPay logic is inlined in `billing.py`. As we add MoMo, ZaloPay, and VietQR/Napas, that file becomes a 600-line switch. Extract a thin adapter protocol and one module per provider. Keep `billing.py` as the **orchestrator** (create payment row, dispatch to adapter, call `apply_topup`); move provider crypto into adapters.

New package layout:

```
app_api/payments/
  __init__.py        # registry: PROVIDERS = {"vnpay": VNPayAdapter(), "momo": ..., ...}
  base.py            # PaymentAdapter protocol + ReconcileResult dataclass
  vnpay.py           # move existing _sign/_query/build_vnpay_url/verify here, ADD amount check
  momo.py            # MoMo AIO v2 (HMAC-SHA256), ipnUrl + redirectUrl
  zalopay.py         # ZaloPay v2 (HMAC-SHA256 on mac), callback + app_trans_id
  vietqr.py          # VietQR / Napas247 static+dynamic QR via bank/PSP webhook (addInfo match)
  dev.py             # instant-topup (no real gateway) — gated by BILLING_DEV_ENABLED
```

`base.py` protocol — every adapter implements the same shape so `billing.py` and the IPN router are provider-agnostic:

```python
@dataclass(frozen=True)
class ReconcileResult:
    ok: bool                 # signature valid AND paid AND amount reconciled
    ext_ref: str             # our payment.ext_ref (TxnRef / orderId / app_trans_id / addInfo code)
    paid_amount_vnd: int | None   # amount the gateway says it captured (None if unknown)
    provider_txn_id: str = ""     # gateway-side transaction id, persisted for support/refund
    reason: str = ""              # human reason on failure (logged, never shown raw to user)

class PaymentAdapter(Protocol):
    name: str
    def configured(self) -> bool: ...
    def build_redirect(self, payment: Payment, *, client_ip: str, return_url: str) -> str: ...
    def parse_callback(self, params: dict) -> ReconcileResult: ...      # signature + paid only
    def build_refund(self, payment: Payment, amount_vnd: int, *, reason: str) -> RefundRequest | None: ...
```

**Amount reconciliation (fixes the audit flag).** The orchestrator, NOT the adapter, owns the amount comparison so the rule is enforced uniformly for every provider:

```python
def confirm_payment(session, *, provider, params) -> ConfirmOutcome:
    res = PROVIDERS[provider].parse_callback(params)
    if not res.ok or not res.ext_ref:
        return ConfirmOutcome.REJECT
    p = lock_payment(session, provider, res.ext_ref)   # SELECT ... FOR UPDATE
    if p is None:
        return ConfirmOutcome.NOT_FOUND
    if p.status == PaymentStatus.SUCCEEDED:
        return ConfirmOutcome.ALREADY            # idempotent replay
    # AUDIT FIX: gateway-captured amount MUST equal what we asked for.
    if res.paid_amount_vnd is not None and int(res.paid_amount_vnd) != int(p.amount_vnd):
        mark_failed(session, p, reason=f"amount_mismatch want={p.amount_vnd} got={res.paid_amount_vnd}")
        log_payment_event(session, p, kind="AMOUNT_MISMATCH", payload=params)
        return ConfirmOutcome.AMOUNT_MISMATCH    # -> alert, do NOT credit
    billing.apply_topup(session, provider=provider, ext_ref=res.ext_ref)  # existing idempotent path
    p.provider_txn_id = res.provider_txn_id
    return ConfirmOutcome.CONFIRMED
```

`apply_topup` stays exactly as-is (it already does FOR UPDATE + `status == SUCCEEDED` short-circuit). We only gate the call behind reconciliation.

**Webhook idempotency at the transport layer.** `payments(provider, ext_ref)` UNIQUE already de-dupes credit application, but we want an **audit trail of every raw IPN hit** (replays, tampered sigs, amount mismatches) for support and fraud review. Add a `webhook_events` table (tenant-scoped) that records each inbound callback keyed by `(provider, provider_event_id)` UNIQUE — insert-first, and if the insert conflicts we know it's a replay and return the cached response without re-running `confirm_payment`. This is the standard "idempotency receiver" pattern and means an at-least-once gateway can hammer us safely.

Per-provider `ext_ref` embedding (org resolution for unauthenticated IPN) follows the existing VNPay trick (`org_from_vnpay_txnref` reads org UUID from the first 32 hex of TxnRef, trustworthy *after* signature verify). MoMo `orderId`, ZaloPay `app_trans_id`, and VietQR `addInfo` all get the same `org.hex + random` construction in `billing.create_topup` so the IPN can `tenant_session(org_id)` without a session.

New/changed endpoints (router stays `routers/billing.py`, IPN handlers generalized):

| Method | Path | Purpose |
|---|---|---|
| POST | `/v1/billing/topup` | unchanged contract; `provider` now `dev\|vnpay\|momo\|zalopay\|vietqr`; returns `pay_url` or `qr_payload` |
| GET/POST | `/v1/billing/ipn/{provider}` | generic IPN: `webhook_events` insert → `confirm_payment` → provider-shaped ack body |
| GET | `/v1/billing/return/{provider}` | browser redirect landing (display-only; never the source of truth — IPN is) |

Each `/ipn/{provider}` returns the gateway's required ack shape (VNPay `{RspCode, Message}`, MoMo `{resultCode}`, ZaloPay `{return_code}`) via an adapter `ack(outcome)` method so we keep the wire contract each gateway demands.

---

### 2. Plans & subscriptions vs one-off credit packs (data-driven)

Today packs are hardcoded in `billing.PACKS` and plan limits in `validate._PLAN_LIMITS`; `orgs.plan_code` is a free-text column read by `tenancy.org_plan_code`. Promote both to tables so pricing/limits change without a deploy, and add a real subscription record.

**`plans`** (global, no RLS — like `users`/`orgs`). Replaces the hardcoded `_PLAN_LIMITS` + adds monetization fields:

| column | type | notes |
|---|---|---|
| `code` | text PK | `free`, `creator`, `pro`, `agency` |
| `name` | text | display |
| `price_vnd_month` | bigint | 0 for free |
| `price_vnd_year` | bigint | annual (proration/discount) |
| `monthly_credits` | bigint | granted each cycle |
| `carryover_cap_credits` | bigint | max unused credits that roll over (0 = expire all) |
| `max_seconds` / `max_resolution` | int / text | feeds `validate.validate_and_clamp` (replaces `_PLAN_LIMITS`) |
| `watermark_free` | bool | gates `videos.has_watermark` default |
| `concurrent_jobs` | int | future queue gate (item-2 worker) |
| `features` | jsonb | misc flags (api_access, priority_queue) |
| `sort` / `is_active` | int / bool | ordering + soft-retire |

**`credit_packs`** (global). Backs the reserved `payments.credit_pack_id` FK (currently UUID, no table). Replaces `billing.PACKS`:

| column | type | notes |
|---|---|---|
| `id` | uuid PK | now FK target for `payments.credit_pack_id` |
| `code` | text UNIQUE | `starter`/`popular`/`pro` |
| `name` | text | |
| `amount_vnd` | bigint | price |
| `credits` | bigint | includes bonus |
| `bonus_credits` | bigint | split out for UI "+X thưởng" |
| `is_active` / `sort` | bool / int | |

**`subscriptions`** (tenant-scoped → `org_id` + RLS). One active row per org (partial UNIQUE on `org_id WHERE status IN ('ACTIVE','TRIALING','PAST_DUE')`):

| column | type | notes |
|---|---|---|
| `id` | uuid PK | |
| `org_id` | uuid FK orgs | RLS isolation |
| `plan_code` | text FK plans | |
| `status` | text | `TRIALING`/`ACTIVE`/`PAST_DUE`/`CANCELED`/`EXPIRED` |
| `billing_cycle` | text | `month`/`year` |
| `current_period_start` / `current_period_end` | timestamptz | grant window |
| `cancel_at_period_end` | bool | cancel-at-period-end flag |
| `canceled_at` | timestamptz | |
| `grace_until` | timestamptz | dunning grace deadline |
| `provider` / `provider_sub_ref` | text | for gateway-managed recurring (most VN gateways are not true recurring → we re-charge from a stored token or re-prompt) |
| `last_grant_period` | text | `YYYY-MM` idempotency key for monthly grant |
| `created_at` / `updated_at` | timestamptz | |

**Monthly credit grant + carryover/expiry.** `wallet.grant_once` explicitly warns it is once-per-lifetime; monthly needs a period key. Add `wallet.grant_for_period(session, org_id, credits, *, period: str, kind=BONUS, note)`:

```python
def grant_for_period(session, org_id, credits, *, period, kind=LedgerKind.BONUS, note=""):
    # period e.g. "2026-07". Idempotent per (org, kind, period) via ledger metadata + FOR UPDATE.
    w = _lock(session, org_id)                         # serialize concurrent cron + manual
    if _has_period_grant(session, org_id, kind, period):   # SELECT on metadata->>'period'
        return 0
    w.balance_credits += credits
    session.add(LedgerEntry(org_id=org_id, entry_type=kind, delta_credits=credits,
        balance_after=w.balance_credits, ref_group=uuid4(),
        note=note, extra={"period": period, "source": "plan_grant"}))
    return credits
```

Idempotency key is `metadata->>'period'` on the ledger row (cheap partial index `ix_ledger_period ON ledger_entries ((metadata->>'period')) WHERE metadata ? 'period'`). This means a cron double-fire, or a manual re-run, never double-grants.

**Carryover/expiry** runs at renewal *before* the new grant. Plan `carryover_cap_credits` decides how much of the *granted* (plan, not purchased) balance survives. We must NOT expire purchased TOPUP credits — only plan-granted ones. Two clean options; recommend **(A)**:

- **(A) Bucketed expiry (recommended):** at renewal, compute expiring plan credits = `min(balance_attributable_to_plan_grants, balance)` and if it exceeds `carryover_cap`, write an `EXPIRE` ledger row (`delta = -(excess)`) before granting the new cycle. "Attributable to plan grants" = sum of unconsumed BONUS-with-source=plan_grant, tracked via a lightweight FIFO over ledger metadata. EXPIRE kind already exists in the CHECK constraint and the frontend `META` map.
- **(B) Full reset:** expire ALL non-purchased credits each cycle (simpler, harsher). Reject — it punishes light users and reads as a money grab against autovis.

**Proration.** On upgrade mid-cycle: charge `(new_price - old_price) * days_remaining / cycle_days` as a one-off VNPay/MoMo payment, then immediately grant the credit delta `(new_monthly - old_monthly)` for the remaining period via `grant_for_period` with a `period` suffix `-prorate`. On downgrade: take effect at `current_period_end` (set `plan_code` change as pending in `subscriptions.features.pending_plan`), no refund of difference (standard SaaS).

**Dunning / grace / cancel-at-period-end.** A scheduled task (`app_api/subscriptions.py::run_renewals`, wired into the existing `lifespan` periodic loop next to the reaper) processes due subscriptions:

```
For each ACTIVE/PAST_DUE sub where current_period_end <= now:
  1. attempt charge (recurring token or queue a "renew" payment + notify)
  2. on success  -> apply carryover/expiry, grant_for_period, advance period, status=ACTIVE
  3. on failure  -> status=PAST_DUE, set grace_until = now + GRACE_DAYS, send dunning email (T+0,3,7)
  4. if PAST_DUE and now > grace_until -> downgrade org to 'free' plan, status=EXPIRED
  5. if cancel_at_period_end -> status=CANCELED, no grant, downgrade to free at period_end
```

`orgs.plan_code` becomes a **denormalized cache** of `subscriptions.plan_code` (kept in sync on every status transition) so `tenancy.org_plan_code` and `validate.validate_and_clamp` need no change to their call sites — they keep reading `orgs.plan_code`, which now reflects the live subscription.

Endpoints (new `routers/subscriptions.py`):

| Method | Path | Purpose |
|---|---|---|
| GET | `/v1/plans` | public: list active plans from `plans` (replaces hardcoded) |
| GET | `/v1/billing/packs` | now reads `credit_packs` table |
| GET | `/v1/subscription` | current org subscription + period + next grant |
| POST | `/v1/subscription` | subscribe/upgrade → creates payment, sets/changes plan |
| POST | `/v1/subscription/cancel` | sets `cancel_at_period_end=true` |
| POST | `/v1/subscription/resume` | clears cancel flag before period end |

---

### 3. Invoices + Vietnamese VAT e-invoice (hoa-don dien tu)

Vietnam mandates electronic VAT invoices (Decree 123/2020, Circular 78/2021) issued through a tax-authority-registered provider. We don't talk to the GDT directly — we integrate a licensed e-invoice provider (VNPT-Invoice, Viettel S-Invoice, or MISA meInvoice) over their API. Design the **internal invoice record** now, integrate the provider behind an adapter (same shape as payments).

**`invoices`** (tenant-scoped → `org_id` + RLS):

| column | type | notes |
|---|---|---|
| `id` | uuid PK | |
| `org_id` | uuid FK | RLS |
| `payment_id` | uuid FK payments | the money event being invoiced (nullable for sub renewals batched) |
| `subscription_id` | uuid FK subscriptions, null | for recurring invoices |
| `number` | text | our sequential `VV-2026-000123`; provider returns its own `einvoice_no` |
| `subtotal_vnd` / `vat_rate` / `vat_vnd` / `total_vnd` | bigint / numeric / bigint / bigint | VAT default 10% (8% windows possible) |
| `buyer_name` / `buyer_tax_code` / `buyer_address` / `buyer_email` | text | from `billing_profiles` |
| `status` | text | `DRAFT`/`ISSUED`/`SIGNED`/`SENT`/`VOID`/`ADJUSTED` |
| `einvoice_provider` / `einvoice_no` / `einvoice_lookup_code` / `einvoice_pdf_url` | text | provider artifacts (lookup code = tra-cuu code on provider portal) |
| `issued_at` | timestamptz | |
| `meta` | jsonb | provider raw response |

**`billing_profiles`** (tenant-scoped, one per org) — VAT buyer details, needed before issuing a company invoice:

| column | type | notes |
|---|---|---|
| `org_id` | uuid PK FK | RLS |
| `legal_name` / `tax_code` / `address` / `email` | text | `tax_code` = MST; validated 10/13-digit |
| `invoice_default` | bool | auto-issue on every payment |

Flow: on `ConfirmOutcome.CONFIRMED`, enqueue an invoice job → create `invoices` row (`DRAFT`) → call e-invoice provider adapter `issue(invoice)` → store `einvoice_no` + `lookup_code` + signed PDF URL (in our R2 via the existing `media.py` signing) → email it. VAT is computed inclusive: `total = amount_vnd` (price shown is VAT-inclusive, standard for VN consumer), `vat = round(total * rate / (1 + rate))`, `subtotal = total - vat`. Refunds issue an **adjustment invoice** (`ADJUSTED`), never delete the original (legal requirement).

Endpoints (`routers/invoices.py`):

| Method | Path | Purpose |
|---|---|---|
| GET | `/v1/invoices` | list org invoices |
| GET | `/v1/invoices/{id}` | detail + signed PDF URL |
| POST | `/v1/billing/profile` | upsert VAT buyer details |
| GET | `/v1/billing/profile` | read |

E-invoice provider creds are infra-blocked (mark for user): `VIETVID_EINVOICE_PROVIDER`, `_API_URL`, `_USER`, `_PASS`, `_TEMPLATE`, `_SERIES`. Until configured, invoices stay `DRAFT` and we serve a non-VAT receipt PDF.

---

### 4. Refund-to-money flow + PaymentStatus lifecycle + stale-PENDING expiry

`PaymentStatus.FAILED` and `REFUNDED` exist in the model + CHECK constraint but are **never set today**. Wire the full state machine.

**Payment state machine** (column `payments.status`):

```
PENDING ──confirm(amount ok)──> SUCCEEDED ──refund(money)──> REFUNDED
   │                                 │
   ├─confirm(amount mismatch)──> FAILED (alert)
   ├─gateway fail / user cancel─> FAILED
   └─stale > TTL (cron)─────────> FAILED   (expire_stale_payments)
```

**Stale-PENDING expiry.** Mirror the orphan-job reaper (`reaper.py`). New `app_api/billing_reaper.py::expire_stale_payments()` wired into `lifespan` periodic loop: any `PENDING` payment older than `BILLING_PENDING_TTL_MIN` (default 30) → set `FAILED` with note `"timeout"`. Critical safety: only PENDING rows are touched, and `apply_topup`'s FOR UPDATE means a late IPN racing the reaper either finds SUCCEEDED (already credited) or PENDING (credits, wins) — the reaper can't expire a row mid-confirm because it also takes FOR UPDATE and skips non-PENDING.

**Money-refund flow.** Credit refunds (`wallet.refund`) already exist for *jobs*. **Money** refunds (return VND to the buyer) are new and distinct — they reverse a TOPUP. Two ledger effects must both happen atomically in one `tenant_session`:

1. Reverse the granted credits: `wallet.topup(session, org_id, -credits, kind=ADJUST, note="refund clawback")` — but only if the balance can absorb it. If the user already spent the credits, we **cannot** claw back below zero (the `ck_wallet_balance_nonneg` CHECK forbids it). Policy: money refund is only allowed when `balance >= credits_granted` of that payment; otherwise require manual review (partial refund of remaining credits). This is the honest constraint and protects against refund-fraud (top up, spend, refund).
2. Call the gateway refund API (`adapter.build_refund` → POST). On gateway success set `payments.status = REFUNDED`, write a `refunds` row, issue the adjustment invoice.

**`refunds`** (tenant-scoped → `org_id` + RLS):

| column | type | notes |
|---|---|---|
| `id` | uuid PK | |
| `org_id` | uuid FK | RLS |
| `payment_id` | uuid FK payments | |
| `amount_vnd` | bigint | full or partial |
| `credits_clawed` | bigint | credits removed via ADJUST ledger |
| `ledger_entry_id` | bigint | the ADJUST row |
| `status` | text | `REQUESTED`/`GATEWAY_OK`/`GATEWAY_FAIL`/`DONE` |
| `provider_refund_id` | text | gateway ref |
| `reason` | text | |
| `requested_by` | uuid FK users | |
| `created_at` / `settled_at` | timestamptz | |

Endpoints (owner-only via `require_owner`):

| Method | Path | Purpose |
|---|---|---|
| POST | `/v1/billing/payments/{id}/refund` | request money refund (owner) → validates balance, calls gateway |
| GET | `/v1/billing/refunds` | list refunds |

`apply_topup` is reused for nothing here; refund-clawback is a separate ADJUST so the ledger reads honestly (TOPUP +N at purchase, ADJUST -N at refund, net zero, both visible).

---

### 5. Coupons / referral credits (BONUS ledger)

All promotional credit lands as `BONUS` ledger entries (kind already exists and is rendered "Tặng" in the frontend `META` map), so wallet invariants and audit hold automatically.

**`coupons`** (global, no RLS — codes are shared catalog):

| column | type | notes |
|---|---|---|
| `id` | uuid PK | |
| `code` | text UNIQUE (CITEXT) | case-insensitive like emails |
| `kind` | text | `CREDIT` (flat credits) / `PERCENT_OFF` (on next pack/sub) / `PLAN_TRIAL` |
| `value` | bigint | credits, or basis points for percent |
| `applies_to` | text | `topup`/`subscription`/`any` |
| `max_redemptions` / `redeemed_count` | int | global cap |
| `per_org_limit` | int | usually 1 |
| `min_amount_vnd` | bigint | floor for percent coupons |
| `starts_at` / `expires_at` | timestamptz | |
| `is_active` | bool | |

**`coupon_redemptions`** (tenant-scoped → `org_id` + RLS, UNIQUE `(coupon_id, org_id)` when `per_org_limit=1`):

| column | type | notes |
|---|---|---|
| `id` | uuid PK | |
| `org_id` | uuid FK | RLS |
| `coupon_id` | uuid FK coupons | |
| `payment_id` | uuid FK payments, null | set when a PERCENT_OFF discount was applied |
| `credits_granted` | bigint | for CREDIT coupons |
| `ledger_entry_id` | bigint | the BONUS row |
| `redeemed_by` | uuid FK users | |
| `created_at` | timestamptz | |

`CREDIT` coupon redemption: in `tenant_session`, `wallet.grant_once`-style guard (lock wallet, check redemption row absent, insert redemption + BONUS ledger) — concurrency-safe by the same lock-then-check pattern already proven in `grant_once`. Increment `coupons.redeemed_count` with a `WHERE redeemed_count < max_redemptions` guarded UPDATE (atomic cap).

**Referral.** A referral is a self-issued coupon pair. `referrals` (tenant-scoped):

| column | type | notes |
|---|---|---|
| `org_id` | uuid FK | referrer org (RLS) |
| `code` | text UNIQUE | shareable (e.g. `VV-AB12CD`) |
| `referred_org_id` | uuid, null | filled on signup attribution |
| `referrer_bonus` / `referee_bonus` | bigint | credits each side gets |
| `status` | text | `PENDING`/`QUALIFIED`/`PAID` — referee must complete first paid top-up to qualify (anti-abuse) |
| `qualified_at` | timestamptz | |

On referee's first SUCCEEDED payment, the renewal/confirm path checks for a PENDING referral, sets `QUALIFIED`, and grants both BONUS entries (one in each org's `tenant_session`). Gating on first *paid* event (not signup) stops self-referral credit farming, which is the obvious attack against a 300-credit free grant.

Endpoints (`routers/promo.py`):

| Method | Path | Purpose |
|---|---|---|
| POST | `/v1/billing/coupon/redeem` | redeem a CREDIT coupon → BONUS ledger |
| POST | `/v1/billing/topup` | accepts optional `coupon_code` for PERCENT_OFF (applied to `amount_vnd` before payment) |
| GET | `/v1/referral` | org's referral code + stats |

---

### Migrations (Alembic, following the model-driven + raw-SQL-RLS style)

Three new revisions chained off `20260627_0003`:

- **`0004_billing_catalog`** — `plans`, `credit_packs`, `billing_profiles`; backfill `plans` from current `validate._PLAN_LIMITS` + `billing.PACKS`; add real FK `payments.credit_pack_id → credit_packs.id` (now that the table exists). `plans`/`credit_packs` are global → no RLS. `billing_profiles` is tenant → add to a local RLS loop.
- **`0005_subscriptions_invoices`** — `subscriptions`, `invoices`, `refunds`, `webhook_events`; all tenant-scoped → `ENABLE/FORCE ROW LEVEL SECURITY` + `org_isolation` policy reusing the `_RLS_USING` clause from baseline. Add `payments.provider_txn_id`, `payments.failed_reason`, `payments.coupon_id` columns.
- **`0006_promo`** — `coupons` (global), `coupon_redemptions` + `referrals` (tenant). Partial unique `uq_coupon_redemption_org ON coupon_redemptions (coupon_id, org_id)`; `ix_ledger_period` partial index for monthly-grant idempotency.

Every tenant table added here must be appended to the RLS application in its migration (the baseline `TENANT_TABLES` loop only covers M1 tables — new tables get their own `ENABLE/FORCE/POLICY` in their migration, matching how the schema enforces fail-closed isolation).

### Config knobs (extend `config.py`)

```
MOMO_PARTNER_CODE / MOMO_ACCESS_KEY / MOMO_SECRET_KEY / MOMO_ENDPOINT
ZALOPAY_APP_ID / ZALOPAY_KEY1 / ZALOPAY_KEY2 / ZALOPAY_ENDPOINT
VIETQR_BANK_BIN / VIETQR_ACCOUNT / VIETQR_PSP_WEBHOOK_SECRET
BILLING_PENDING_TTL_MIN = 30
SUBSCRIPTION_GRACE_DAYS = 7
VAT_RATE = 0.10
EINVOICE_PROVIDER / EINVOICE_API_URL / EINVOICE_USER / EINVOICE_PASS / EINVOICE_SERIES
```

Extend `startup_checks.validate_prod_config`: if `IS_PROD` and any subscription plan has `price_vnd_month > 0`, require at least one real payment gateway `configured()` (else paying users can't pay) — same fail-fast spirit as the existing dev-gate checks.


---

# 4. Feature Modules — autovis parity + revenue-loop differentiators

## Feature Modules — autovis parity + revenue-loop differentiators

### 0. The one architectural decision everything hangs on

There are **two model layers** in this repo and the design respects both:

| Layer | Module | Tenancy | Role |
|---|---|---|---|
| Engine catalog (legacy) | `core/models.py` | global, int PK, no `org_id` | seed library: `kol_characters` (6 seed KOLs), `ad_formats` (9 formats), `scene_presets`, `prompt_templates` (autovis import) |
| SaaS multi-tenant | `app_api/models.py` | `org_id` + RLS+FORCE, UUID PK | `jobs`, `videos`, `wallets`, ... |

The engine seam is already perfect for plug-in features. `build_job_spec` (`app_api/jobs.py:79`) does `JobSpec.from_dict(job.params)` — **`params` JSONB IS the JobSpec**. And `pipeline.run_job` already:
- dispatches on `snapshot["mode"]` (`product_ad|premium|kol_full|long_narrative|film_recap`),
- reads `scene_prompt` (= `ScenePreset.image_prompt`) and `structure_reference` (= `PromptTemplate.prompt_vi/en`),
- reads `kol` (`character_sheet` + `voice_id`) and `format_key`.

**So every feature below resolves a catalog/asset row into `params` / `scene_prompt` / `structure_reference` / `format_key` / `kol` at job-create time. The engine is NOT modified.** All new code lives under `app_api/features/` and `app_api/routers/`. The single new server-side function is `app_api/features/resolve.py::resolve_feature_inputs(spec_input, *, template, persona, brand_kit)` called inside `jobs_svc.create_job` before the HOLD.

The three reserved FK columns (`jobs.template_id/kol_persona_id/brand_kit_id`, all UUID, no FK today) get backed by **new tenant tables** (not the int-PK catalog), so a saved template / custom face / brand kit is RLS-isolated exactly like jobs. System defaults are **copy-on-remix** into a tenant row.

---

### 1. Templates / storyboard library + remix → backs `jobs.template_id`

**Data.** New `vv_templates` (tenant, RLS). System catalog stays in `core.prompt_templates` (global, read-only). `GET /v1/templates` merges both (system rows tagged `is_system:true`, no `org_id`). Remix = copy-on-write: `POST /v1/templates/{id}/remix` clones either a system row or another org row into a new `vv_templates` row owned by the caller, carrying `source_template_id` (lineage) and `system_source_id` (catalog origin).

**Engine reuse.** On job create with `template_id`, `resolve.py` copies the template's `storyboard`, `format_key`, `structure_reference`, `scene_prompt`, `aspect`, `seconds` into `spec_input`. No render change — `structure_reference` already flows to the Director.

**Screens.** `apps/web/src/app/app/templates/page.tsx` (gallery, system + mine tabs, electric-violet cards), `templates/[id]/page.tsx` (storyboard editor + "Remix to my library" + "Use in wizard" → `/app/create?template=<id>`).

```sql
-- 0004 (sketch)
CREATE TABLE vv_templates (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id uuid NOT NULL REFERENCES orgs(id) ON DELETE CASCADE,
  source_template_id uuid, system_source_id text,
  name text NOT NULL, category text DEFAULT '', format_key text DEFAULT '',
  mode text DEFAULT 'product_ad', aspect text DEFAULT '9:16', seconds int DEFAULT 15,
  scene_prompt text DEFAULT '', structure_reference text DEFAULT '',
  storyboard jsonb DEFAULT '[]'::jsonb, overlay_policy text DEFAULT 'allow',
  thumb_url text DEFAULT '', is_archived boolean DEFAULT false,
  created_by uuid, created_at timestamptz DEFAULT now(), updated_at timestamptz DEFAULT now()
);
ALTER TABLE vv_templates ENABLE ROW LEVEL SECURITY; ALTER TABLE vv_templates FORCE ROW LEVEL SECURITY;
CREATE POLICY org_isolation ON vv_templates USING (org_id = current_setting('vietvid.current_org')::uuid);
CREATE INDEX ix_vv_templates_org ON vv_templates(org_id, is_archived);
```

---

### 2. KOL / avatar gallery + custom face + voice profiles → backs `jobs.kol_persona_id`

**Data.** `vv_kol_personas` (tenant, RLS). Origin lineage `seed_kol_id` → `core.kol_characters`. Mirrors the proven legacy `KolCharacter` columns (`character_sheet`, `voice_id`, `consent_status`, `image_source`) so resolution is a direct field copy into `JobSpec.kol`.

**Buildable now:** create persona from a seed KOL (copy `character_sheet`/`voice_id`) or from text; pick `voice_id` (edge-tts Vietnamese voices already wired in `routers/voice.py`).

**External-gated (ship as stub):**
- `POST /v1/kol-personas/{id}/face` — custom face upload + **mandatory consent flag** → `face_status=PENDING_REVIEW`. The engine deliberately *text-describes* faces (see `director/__init__` `_VIDEO_PROMPT_RULES`: "KHÔNG gửi ảnh mặt vào model video") to dodge deepfake moderation, so face-swap needs an external model + a legal call. Column + UI ship; render path no-ops until wired.
- `POST /v1/kol-personas/{id}/voice-clone` — sample upload → `voice_clone_status=REQUESTED`. Needs a VN clone provider; falls back to standard `voice_id` until ready.

**Screens.** `personas/page.tsx` (face grid, "Custom face — cần xét duyệt" badge), `personas/[id]/page.tsx` (character sheet editor + voice picker + sample player).

---

### 3. Brand kits — logo / colors / watermark / disclosure → backs `jobs.brand_kit_id`

**Data.** `vv_brand_kits` (tenant, RLS), partial-unique `is_default` per org. `disclosure_text` is the affiliate-compliance line (e.g. "Tiếp thị liên kết — có thể nhận hoa hồng").

**Engine reuse.** `compose/overlays.py` already burns text/logos; `resolve.py` injects `params.brand = {logo_url, palette, watermark_policy, disclosure_text, cta_url}`. The video model `videos.has_watermark` + `watermark_removed_at` already exist — `watermark_policy=paid_off` flips `has_watermark` for paid plans. At job create, if no `brand_kit_id` passed and an org default exists, it's auto-attached.

**Screen.** `brand-kits/page.tsx` (logo upload via existing `/v1/uploads`, color pickers, watermark toggle, live preview overlay).

---

### 4. Auto-series — 1 brief → N variants (A/B) → `vv_series`

**Data.** `vv_series` (tenant). Children are normal `jobs` with `params.series_id` set; one **batch HOLD** under `batch_ref_group` (reuses the wallet HOLD/SETTLE/REFUND in `wallet.py`, one ledger group for N jobs). `series_expand.py` takes `axes` (cartesian of `hook[] × format_key[] × kol_persona_id[]`, clamped to `variant_count`) and emits N `JobCreateRequest`-equivalents through the SAME `create_job` path (idempotency keys `<series_id>:<variant_idx>`).

**A/B.** `GET /v1/series/{id}` joins child videos → `vv_shares.view_count` + `vv_link_clicks` → per-variant CTR. Winner logic = open question (CTR now, conversion later).

**Screens.** `series/page.tsx` (brief + axis chips + "tạo N biến thể"), `series/[id]/page.tsx` (variant grid, A/B leaderboard).

---

### 5. All-tools hub → `tools_manifest.py` over existing pipelines

`features.ts` already lists the menu. The hub is a **thin preset layer** — `GET /v1/tools` returns a manifest mapping each tool to engine settings; `POST /v1/tools/{key}/run` is a sugar alias over `POST /v1/jobs`:

| Tool (features.ts key) | Engine path (exists) | Preset injected |
|---|---|---|
| `product_ad` / `image_to_video` / `seedance` | `pipeline` mode=`product_ad` | i2v from uploaded frame |
| `text_to_video` | `pipeline` mode=`product_ad`, `frameMode=ai` | clean-plate skipped, Gemini frame |
| `lookbook` / `review` / `expert_review` | mode=`kol_full` + `format_key` | persona + format prompt |
| clean-plate (internal) | `image_stage/clean_plate.py::generate_clean_plate` | runs inside pipeline already |
| product-hero | `compose/product_hero.py::prepend_product_hero` | `params.product_hero=true` |
| recap | mode=`film_recap` → `film_recap/runner.py::render_film_recap` | source URL/file |
| long-narrative | mode=`long_narrative` → `long_narrative/runner.py::render_long_narrative` | script brief + visual_mode |

No new rendering — the hub only fills `mode`/`format_key`/`scene_prompt`/`params`. `tools.ts` (web) drives `app/app/tools/page.tsx`.

---

### 6. Public share page + embeds → `vv_shares`

Signed URLs already exist (`media.py` HMAC + `/v1/jobs/{id}/video-url`). `POST /v1/videos/{id}/share` mints a global-unique `slug`. **Public read** `GET /s/{slug}` and `GET /embed/{slug}` resolve by slug via a `SECURITY DEFINER` Postgres function (bypasses RLS for the single-row public read only; owner-side list/edit stays RLS-protected). The public page server-mints a short-TTL signed media URL so the mp4 plays without a Bearer token, and renders the brand-kit disclosure + tracked CTA. Web: `app/s/[slug]/page.tsx` (public, no auth guard).

---

### 7. Onboarding + first-video flow → `org.settings.onboarding`

No new table — state lives in the existing `orgs.settings` JSONB. `GET /v1/onboarding` returns the next step: `verify_email` (column exists) → `pick_persona` → `first_brief` → `first_video`. First video uses a curated system template + seed KOL so a new user ships one video in <2 min on the free 300 credits (see memory: free grant > cheapest HOLD). Web: `app/app/onboarding/page.tsx` + a dashboard checklist card.

---

### 8. Differentiators that beat autovis (revenue loop)

autovis stops at "make the video." VietVid closes to **revenue**, all buildable on current infra except conversion ingest.

**8a. Affiliate-link auto-attach + click tracking.** `vv_affiliate_links` (short `code`) + append-only `vv_link_clicks`. Public `GET /r/{code}` 302-redirects and inserts a click via a `SECURITY DEFINER` function (public endpoint, no tenant session — function sets `org_id` from the link row). `cta_tail.py` already composes a CTA tail clip; `resolve.py` burns the `/r/{code}` URL + brand-kit disclosure into it. Pure-build, no external API.

**8b. Revenue attribution.** `sub_id` on the link carries into the affiliate network; `POST /v1/affiliate-links/conversions` (webhook or CSV per network) matches `sub_id` → link → job/video/series and rolls up `revenue_vnd`. `attribution.py` is one adapter per network (Shopee/Lazada/TikTok — first network is an open question). Series A/B can then optimize on revenue, not just views.

**8c. Landing-page generator.** `vv_landing_pages` served public at `GET /p/{slug}` — video hero (signed URL) + headline + brand-kit CTA + tracked affiliate link + disclosure. Template-based (`template_key`), generated from `landing_render.py`. autovis has no landing pages; this turns one video into a conversion surface.

---

### Migrations (3, additive, RLS-correct)

- **0004 `feature_tables`** — `vv_templates`, `vv_kol_personas`, `vv_brand_kits`, `vv_series`, `vv_shares` (+ ENABLE/FORCE RLS + `org_isolation` policy mirroring the 6 existing tenant tables; `vv_shares` adds the `SECURITY DEFINER` public-by-slug read fn).
- **0005 `back_reserved_fks`** — add FK `jobs.template_id→vv_templates(id)`, `jobs.kol_persona_id→vv_kol_personas(id)`, `jobs.brand_kit_id→vv_brand_kits(id)` (all `ON DELETE SET NULL`) + supporting indexes; `payments.credit_pack_id→vv_credit_packs(id)` (billing domain owns that table).
- **0006 `affiliate_attribution`** — `vv_affiliate_links`, `vv_link_clicks`, `vv_landing_pages` + RLS + `SECURITY DEFINER` click-insert / redirect-resolve / landing-resolve fns for the public `/r`, `/s`, `/p` routes.

### What needs external infra (flagged, not blocking)

| Feature | External dep | Until then |
|---|---|---|
| Custom face swap | face model + consent/legal | text-persona only (engine default) |
| Voice clone (VN) | clone provider | standard `voice_id` |
| Auto-post TikTok/YT | OAuth + content-API approval | share page + manual download |
| Conversion ingest | network webhook/CSV creds | clicks/CTR tracked now, revenue later |
| Public `/s` `/p` at scale | R2 signed URLs (config exists) | local FileResponse in dev |


---

# 5. Security, Multi-tenancy, RBAC & Compliance

## Security, Multi-tenancy, RBAC & Compliance

This extends the verified M1 security spine (RLS+FORCE via `vietvid.current_org` GUC, fail-closed `nullif(...)::uuid`, dual-mode JWT, `role_in_org` RBAC, in-proc rate limit, HMAC media tokens). Nothing here re-designs that spine; every addition reuses its primitives. The whole section is enforceable: real columns, real policy SQL, real `deps.py` factories, real module paths.

---

### 1. RLS strategy for ALL new tenant tables — the pattern + checklist

The M1 baseline already proves the pattern: `TENANT_TABLES` tuple in `models.py` drives a loop in the migration that does `ENABLE` + `FORCE RLS` + `CREATE POLICY org_isolation USING (org_id = nullif(current_setting('vietvid.current_org', true), '')::uuid)`. The single failure mode is **a new tenant table added to `models.py` but forgotten in the RLS loop** — it would silently leak cross-org. We close that with a generated migration helper + a CI tripwire, not human discipline.

**The canonical pattern (every new tenant-scoped table):**

1. Column: `org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False)` — never nullable, never defaultable. `CASCADE` for child data (templates, brand kits, assets), `RESTRICT` for financial rows (mirrors `payments`/`ledger_entries` which use `RESTRICT` so money rows can't vanish on org delete).
2. Index: every tenant table gets `Index("ix_<t>_org_created", "org_id", "created_at")` — `org_id` MUST lead the index because every RLS-filtered query carries `org_id = <guc>` as the most selective predicate.
3. Add the table name to `TENANT_TABLES` in `models.py` (this is the single source of truth the migration reads).
4. The migration applies RLS via a shared helper so the policy SQL is written once.

**Refactor the RLS application into a reusable helper** at `alembic/helpers.py` so 0001's inline loop and every future migration share one definition:

```python
# alembic/helpers.py
RLS_USING = "org_id = nullif(current_setting('vietvid.current_org', true), '')::uuid"

def enable_org_rls(op, table: str) -> None:
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
    op.execute(f"DROP POLICY IF EXISTS org_isolation ON {table}")
    op.execute(
        f"CREATE POLICY org_isolation ON {table} "
        f"USING ({RLS_USING}) WITH CHECK ({RLS_USING})"
    )
```

Each new-table migration ends with `for t in NEW_TENANT_TABLES: enable_org_rls(op, t)`.

**RLS migration checklist (paste into every PR that adds a tenant table):**
- [ ] `org_id` NOT NULL FK to `orgs.id` present
- [ ] table name added to `TENANT_TABLES` in `models.py`
- [ ] migration calls `enable_org_rls(op, "<table>")`
- [ ] `(org_id, created_at)` composite index exists
- [ ] no global-scope query path writes/reads this table without `tenant_session(org_id)`
- [ ] CI drift test passes (see below)

**CI tripwire — `tests/test_rls_coverage.py`** (the real enforcement; not a checklist humans skip). At runtime, query Postgres catalog and assert every table that has an `org_id` column has RLS enabled+forced and an `org_isolation` policy, and that `set(TENANT_TABLES)` exactly equals the set of org-scoped tables:

```sql
-- tables with org_id but missing RLS = a leak
SELECT c.relname FROM pg_class c
JOIN pg_attribute a ON a.attrelid=c.oid AND a.attname='org_id'
WHERE c.relkind='r' AND c.relnamespace='public'::regnamespace
  AND (NOT c.relrowsecurity OR NOT c.relforcerowsecurity
       OR NOT EXISTS (SELECT 1 FROM pg_policy p WHERE p.polrelid=c.oid AND p.polname='org_isolation'));
```

If that query returns any row, the test fails — a forgotten table can't reach prod. Also assert the `org_isolation` policy `USING` clause text matches `RLS_USING` byte-for-byte (catches a hand-edited policy that drops the `nullif` fail-closed guard).

**New tenant tables introduced by other domains all follow this** (templates, kol_personas, brand_kits, credit_packs is global, video_assets, share_links, usage_counters). My domain owns the *enforcement mechanism*; their migrations own the per-table application.

---

### 2. Full RBAC — role + permission model

Today: only `owner` / `member`, enforced by `require_role(*roles)` reading `tenant.role` (a single membership column). That doesn't scale to a SaaS with finance, support, and a platform admin. The decision: **roles are coarse buckets stored on `memberships.role`; permissions are fine-grained scopes resolved code-side from a static matrix.** No permission table for tenant roles (it's a small fixed set; a DB table is over-engineering and adds a query per request). A DB table *is* warranted only for the platform-admin layer (audited, mutable) — covered in §4.

**Roles (per-org, stored in `memberships.role`):**

| Role | Intent |
|---|---|
| `owner` | full control incl. billing, member management, org delete. Exactly one+ per org. |
| `admin` | manage members/content/jobs, NOT billing payment methods or org delete |
| `editor` | create/run jobs, manage templates/brand kits, view videos |
| `viewer` | read-only: list jobs/videos, no create, no spend |
| `finance` | billing + payments + ledger + invoices; NO content/job create |
| `support` | read-only across content + read members; for internal CX seats invited into a customer org |

**Platform super-admin (`platform_admin`) is NOT a membership role** — it lives in a separate global table (§4) because it crosses orgs and must never be grantable via the normal invite flow.

**Permission matrix (resource × action → allowed roles).** Defined once in a new module `app_api/permissions.py`:

```python
# app_api/permissions.py
# scope string = "<resource>:<action>"
PERMISSIONS: dict[str, frozenset[str]] = {
    "job:create":      frozenset({"owner", "admin", "editor"}),
    "job:read":        frozenset({"owner", "admin", "editor", "viewer", "finance", "support"}),
    "job:cancel":      frozenset({"owner", "admin", "editor"}),
    "job:delete":      frozenset({"owner", "admin"}),
    "video:read":      frozenset({"owner", "admin", "editor", "viewer", "support"}),
    "video:delete":    frozenset({"owner", "admin"}),
    "video:share":     frozenset({"owner", "admin", "editor"}),
    "billing:read":    frozenset({"owner", "finance"}),
    "billing:topup":   frozenset({"owner", "finance"}),
    "wallet:read":     frozenset({"owner", "admin", "finance"}),
    "ledger:read":     frozenset({"owner", "finance"}),
    "member:read":     frozenset({"owner", "admin", "support"}),
    "member:invite":   frozenset({"owner", "admin"}),
    "member:remove":   frozenset({"owner", "admin"}),
    "member:setrole":  frozenset({"owner"}),       # only owner re-roles
    "template:write":  frozenset({"owner", "admin", "editor"}),
    "brandkit:write":  frozenset({"owner", "admin", "editor"}),
    "org:settings":    frozenset({"owner", "admin"}),
    "org:delete":      frozenset({"owner"}),
}

def role_can(role: str, scope: str) -> bool:
    allowed = PERMISSIONS.get(scope)
    return bool(allowed) and role in allowed  # unknown scope = deny (fail-closed)
```

**Enforcement — extend `deps.py` with `require_perm`** (keep `require_role`/`require_owner` for back-compat; migrate routers incrementally):

```python
# app_api/deps.py  (additive)
from app_api.permissions import role_can

def require_perm(scope: str):
    def _dep(tenant: Tenant = Depends(get_tenant)) -> Tenant:
        if not role_can(tenant.role, scope):
            raise HTTPException(status_code=403, detail=f"Thiếu quyền: {scope}")
        return tenant
    return _dep
```

Routers change from `Depends(require_owner)` to e.g. `Depends(require_perm("billing:topup"))`. The scope string in the route is self-documenting and the matrix is unit-testable (`tests/test_permissions.py` asserts every scope used in a router exists in `PERMISSIONS` — a grep-based test prevents typo-scopes that fail-closed silently to 403).

**Migration `0004`**: relax the `memberships.role` server-side — there is currently no CHECK on role, so no ALTER needed, but add `CheckConstraint("role IN ('owner','admin','editor','viewer','finance','support')", name="ck_membership_role")` to lock the vocabulary and add an index isn't needed (already `ix_memberships_org`/`_user`). Backfill: existing `'member'` rows → `'editor'` (closest capability match; one-line `UPDATE memberships SET role='editor' WHERE role='member'`).

---

### 3. audit_log — events, tamper-evidence, retention

New **tenant-scoped, append-only** table `audit_logs` (mirrors `ledger_entries` immutability exactly). RLS applies (it's org data the customer can view), plus platform-admin cross-org read via §4.

```python
class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orgs.id", ondelete="RESTRICT"), nullable=False)
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))  # null = system/reaper
    actor_role: Mapped[str] = mapped_column(Text, server_default=text("''"))
    action: Mapped[str] = mapped_column(Text, nullable=False)      # "member.role_changed", "billing.topup", "job.deleted"
    resource_type: Mapped[str] = mapped_column(Text, server_default=text("''"))
    resource_id: Mapped[str] = mapped_column(Text, server_default=text("''"))
    ip: Mapped[str] = mapped_column(Text, server_default=text("''"))
    user_agent: Mapped[str] = mapped_column(Text, server_default=text("''"))
    detail: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))  # before/after diff, redacted
    prev_hash: Mapped[str] = mapped_column(Text, server_default=text("''"))
    row_hash: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = _TS()
    __table_args__ = (
        Index("ix_audit_org_created", "org_id", "created_at"),
        Index("ix_audit_org_action", "org_id", "action"),
    )
```

**What gets logged** (security-relevant state changes only — NOT reads, NOT every API call; that's what `observability.py` request logging is for): auth events surfaced from `routers/auth.py` (login success/fail, password change, token reset), member lifecycle (`member.invited/joined/removed/role_changed`), billing (`billing.topup`, `payment.succeeded/refunded`), spend-authorizing actions (`job.created/cancelled/deleted`), moderation decisions (`video.flagged/blocked/approved`), org settings + delete, and every platform-admin cross-org access (§4).

**Tamper-evidence — hash chain per org** (cheaper + simpler than per-row signatures, and verifiable). `row_hash = sha256(prev_hash || org_id || actor || action || resource || created_at || canonical(detail))`. `prev_hash` = the previous row's `row_hash` for that org (fetched FOR UPDATE on the org's wallet row to serialize, reusing the lock the action already holds where possible; else a tiny per-org advisory lock `pg_advisory_xact_lock(hashtext('audit:'||org_id))`). A `verify_chain(org_id)` admin endpoint re-walks the chain and reports the first broken link. Append-only enforced by the **same trigger pattern as ledger** — reuse `ledger_immutable()`:

```sql
CREATE TRIGGER trg_audit_no_update BEFORE UPDATE ON audit_logs
  FOR EACH ROW EXECUTE FUNCTION ledger_immutable();
CREATE TRIGGER trg_audit_no_delete BEFORE DELETE ON audit_logs
  FOR EACH ROW EXECUTE FUNCTION ledger_immutable();
```

DELETE being blocked means **retention is enforced by partition drop, not row delete.** Range-partition `audit_logs` by month (`PARTITION BY RANGE (created_at)`); retention = `DETACH PARTITION` + archive to R2 cold storage, then `DROP TABLE` the detached partition (the trigger only fires on row UPDATE/DELETE, not partition DROP). Default retention 24 months hot (Vietnam e-commerce records obligation), then cold archive. A monthly Arq cron (`audit_partition_roll`) pre-creates next month's partition and rolls old ones.

**Writer module** `app_api/audit.py` exposes `log(session, *, org_id, actor, action, ...)` called inside the existing `tenant_session` of the action (same transaction → audit row commits atomically with the change it records; no orphan/missing audit on rollback).

---

### 4. Admin / super-admin cross-org access — RLS bypass strategy

This is the sharpest risk: an admin path that crosses orgs must NOT defeat RLS globally. **Decision: NO superuser DB role, NO `BYPASSRLS` grant on the app role.** The app role stays non-superuser+RLS-forced (as M1 already requires via `DB_APP_ROLE`). Cross-org access uses **explicit per-org iteration with the GUC set per org**, exactly like `reaper.py` already does — the GUC is set, queried, reset, one org at a time, with each access audited.

**Platform admin identity** — new global table (no RLS; it's not org data):

```python
class PlatformAdmin(Base):
    __tablename__ = "platform_admins"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    level: Mapped[str] = mapped_column(Text, server_default=text("'support'"))  # support | admin | superadmin
    granted_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = _TS()
```

Seeded only via a CLI (`scripts/grant_platform_admin.py`) run by infra, never via API — a platform admin can never be created through HTTP. `deps.get_platform_admin(principal)` checks membership in this table; `require_platform(level)` gates `/v1/admin/*` routes.

**The bypass mechanism** — a dedicated context manager `admin_session(org_id)` in `db.py` that is *identical* to `tenant_session` (sets the GUC to a specific org) but callable only after the `require_platform` gate, and it forces an `audit.log(action="admin.cross_org_access", ...)` write into that org's chain. For cross-org *aggregate* reads (e.g. abuse dashboard), use a small set of explicitly-defined **SECURITY DEFINER** functions owned by a separate `vietvid_admin` role (not the app role), each one narrow (e.g. `admin_org_summary()` returning counts only, never raw PII), so the bypass surface is auditable SQL, not a blanket role flag. The app connection calls these functions; it never gets `BYPASSRLS` itself.

`scripts/grant_platform_admin.py` + the `vietvid_admin` SECURITY DEFINER functions are the *only* two RLS-bypass surfaces in the system, both enumerable and both audited. New admin endpoints: `GET /v1/admin/orgs`, `GET /v1/admin/orgs/{id}`, `POST /v1/admin/orgs/{id}/suspend`, `GET /v1/admin/abuse/signals`, `POST /v1/admin/moderation/{video_id}/decision`, `GET /v1/admin/audit/verify/{org_id}`.

---

### 5. Content moderation pipeline

`videos.moderation_status` (PENDING/APPROVED/FLAGGED/BLOCKED) + `moderation_detail` JSONB already exist. Wire a real pipeline. **Two gates, both pre-publish:** (a) input-prompt moderation at `job:create` time, (b) output-frame moderation after compose, before `READY`.

New tenant table `moderation_events` (audit trail of every automated/human decision, RLS-scoped):

```python
class ModerationEvent(Base):
    __tablename__ = "moderation_events"
    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False)
    video_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    stage: Mapped[str] = mapped_column(Text, nullable=False)        # "prompt" | "frame" | "human"
    provider: Mapped[str] = mapped_column(Text, server_default=text("''"))  # "gemini_safety" | "manual"
    verdict: Mapped[str] = mapped_column(Text, nullable=False)      # APPROVED|FLAGGED|BLOCKED
    categories: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))  # {sexual:0.02,...}
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = _TS()
    __table_args__ = (Index("ix_moderation_org_created", "org_id", "created_at"),)
```

**Flow** in new module `app_api/moderation.py`:
1. **Prompt gate** (`screen_prompt(text) -> verdict`): the job's Vietnamese marketing prompt runs through a category classifier (Gemini already in-stack has safety ratings; reuse the same client). BLOCKED → job never enters the engine, HOLD refunded, `402`-style `422` to user with category. FLAGGED → proceeds but `videos.moderation_status` defaults to FLAGGED for human review before watermark removal/share.
2. **Frame gate** (`screen_frames(video_id)`): on compose completion, sample N keyframes (the engine already extracts frames for QA), classify. BLOCKED → video stored but `moderation_status=BLOCKED`, NOT served (media endpoint checks status), job marked READY-but-withheld, owner notified. APPROVED → `moderation_status=APPROVED`.
3. **Serve gate**: `routers/media.py` and the signed-URL issuer (`/v1/jobs/{id}/video-url`) MUST refuse to mint/serve when `moderation_status IN ('BLOCKED')` and require APPROVED (or owner-only preview) for `FLAGGED`. This is a real added check at the existing media egress, not a new service.
4. **Human review queue**: platform-admin endpoint `POST /v1/admin/moderation/{video_id}/decision` writes a `human` moderation_event and updates status; logged to `audit_logs`.

Moderation thresholds in config: `MODERATION_BLOCK_THRESHOLD=0.85`, `MODERATION_FLAG_THRESHOLD=0.5`, `MODERATION_ENABLED` (default on in prod, off in dev so local iteration isn't gated).

---

### 6. Abuse defense

**6.1 Redis-backed rate limiting (multi-instance).** The current `ratelimit.py` is honest in-proc fixed-window — correct for 1-box, wrong for N instances (each box has its own counter → N× the real limit). Keep the middleware + bucket logic + config knobs **exactly as-is**; swap only the `_allow` backend behind a strategy. New module `app_api/ratelimit_redis.py` implementing the same `(allowed, retry)` contract via a Redis sliding-window (Lua INCR+PEXPIRE or sorted-set ZADD/ZREMRANGEBYSCORE for true sliding window). Selection by config:

```python
# config.py additions
RATE_LIMIT_BACKEND = _str("VIETVID_RL_BACKEND", "memory")  # memory | redis
REDIS_URL = _str("VIETVID_REDIS_URL")  # shared with Arq queue (item-2 infra)
```

`ratelimit.py` picks the backend at startup; `redis` requires `REDIS_URL` or `startup_checks.validate_prod_config()` blocks boot in prod (add a problem entry: "VIETVID_RL_BACKEND=memory in prod with >1 instance leaks rate limits"). **Blocked on user infra: Redis** — design is drop-in, flips on when Redis exists (same Redis as the Arq queue).

**Add tiered limits by principal, not just IP.** Today buckets key on IP only — a farmer behind one IP is throttled, but a botnet of IPs each gets full quota for free-credit farming. Add a per-`user_id` and per-`org_id` bucket for authed expensive routes (job create): `expensive` limit also checked against `(org_id, "expensive_org")` so one org can't fan out across IPs. New knob `RATE_LIMIT_EXPENSIVE_ORG=200/3600`.

**6.2 Signup / free-credit farming.** This is the real money leak: `FREE_GRANT_CREDITS=300` (>1 paid job) granted per *org*, and `bootstrap_tenant` creates an org per user. Defenses, layered:
- **Email-verify gating on spend** (not on signup): a user can register and look around, but `job:create` and `billing` require `users.email_verified=true`. Enforced in `deps.py` via a new `require_verified` mixed into `require_perm("job:create")`. Returns `403 EMAIL_NOT_VERIFIED`. This kills throwaway-email farming because the free grant is unusable until a real inbox is proven.
- **Grant gated on verification, not signup.** Move the `grant_once(FREE_GRANT_CREDITS)` from `bootstrap_tenant` to fire on first email-verify (in `routers/auth.py` verify handler), so unverified orgs hold zero spendable credit. (Free grant vs min-hold invariant from memory still holds — grant still 300, still > cheapest HOLD ~105.)
- **Disposable-domain + signup-velocity check** at register: new module `app_api/abuse.py` with `is_disposable_email(domain)` (static blocklist, refreshable) and a Redis counter `signup:ip:<ip>` (cap N signups/IP/day, default 5). Tripping it → require email verify *and* flag the org `settings.abuse_review=true` (no auto-grant). Recorded to `audit_logs` (system actor).
- **Device/fingerprint soft-signal** stored in `users.signup_meta` JSONB (IP, UA, accept-language) for the admin abuse dashboard — not a hard block (too many false positives), a signal for `GET /v1/admin/abuse/signals`.

**6.3 Email-verify gating summary**: verification is the linchpin — it gates the *grant* and gates *spend*, so a farmer must solve a real inbox per 300 credits, collapsing the economics of farming.

---

### 7. PDPD / GDPR — export, deletion, consent

Vietnam's PDPD (Decree 13/2023) is the binding regime; GDPR-shaped controls satisfy both. Three obligations: data subject **access/export**, **erasure**, **consent**.

**7.1 Export** — `POST /v1/me/export` (authed, self-service). New Arq job `export_user_data` assembles a ZIP: profile (`users` row, redacted hash), all orgs the user owns + memberships, jobs+videos metadata (signed URLs, not re-hosted bytes), ledger + payments for owned orgs, audit_logs where `actor_user_id = me`. Cross-org assembly uses per-org `tenant_session` iteration (never a bypass). Delivered as a signed R2 URL (reuse `media.py` HMAC signer), TTL 24h, emailed. Rate-limited to 1/day/user. Logged to `audit_logs`.

**7.2 Account deletion / erasure** — `DELETE /v1/me` (authed, requires password re-auth or fresh token). Two-phase to respect the append-only financial/audit ledger (you legally CANNOT hard-delete payment/ledger records — Vietnam tax retention; PDPD allows retaining what law requires):
- **Phase 1 (immediate, soft):** `users.status='DELETED'` (kill-switch in `deps.get_principal` already enforces this → instant logout everywhere), revoke all `auth_tokens`, anonymize PII in `users` (email → `deleted-<uuid>@deleted.local`, full_name/avatar cleared), set owned orgs `status='DELETED'`. A grace window (`DELETION_GRACE_DAYS=14`) allows recovery.
- **Phase 2 (after grace, Arq cron `purge_deleted_accounts`):** hard-delete recoverable content (videos from R2, jobs params with prompts), but PRESERVE financial rows with PII stripped (ledger/payments keep amounts + org_id, drop any name/email in `raw_payload` via a redaction pass — the `lib/redact-engine` pattern). Audit_logs are retained per §3 retention but the actor PII column is anonymized. A `deletions` global table records the request + completion for compliance proof:

```python
class DeletionRequest(Base):
    __tablename__ = "deletion_requests"
    id: Mapped[uuid.UUID] = _PK()
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    requested_at: Mapped[datetime] = _TS()
    purge_after: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    scope: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
```

**7.3 Consent** — new columns on `users`: `tos_accepted_at`, `tos_version`, `privacy_accepted_at`, `marketing_consent` (bool, default false), `marketing_consent_at`. Register flow records ToS/privacy version accepted (the terms/privacy screens already exist in frontend). A `consents` event log isn't needed at M2 scale — versioned columns on `users` plus the `audit_logs` `consent.updated` action give the audit trail. `PATCH /v1/me/consent` toggles marketing consent (PDPD requires granular, withdrawable consent for marketing). Migration `0005` adds these columns (global table, no RLS).

---

### 8. Secrets management

Current state: secrets read directly from env in `config.py` (`DEV_JWT_SECRET`, `VNPAY_HASH_SECRET`, `STORAGE_SECRET_KEY`, `SMTP_PASSWORD`, future provider keys). `startup_checks.py` already fail-closes on placeholder `DEV_JWT_SECRET` in prod — extend that gate, don't replace the env model (12-factor env is correct; a secrets manager is infra, not code).

**Concrete hardening:**
- **Separate the media-signing secret from the JWT secret.** `media.py` and `media-url-issuer` currently fall back to `DEV_JWT_SECRET` — a single secret signing both auth tokens and media URLs means a media-secret leak forges auth. Add `MEDIA_SIGNING_KEY = _str("VIETVID_MEDIA_KEY")`, fall back to `DEV_JWT_SECRET` ONLY in dev; `startup_checks` requires a distinct real `MEDIA_SIGNING_KEY` in prod.
- **Secret presence + strength gate at boot.** Extend `validate_prod_config()`: when `vnpay_configured()` / `storage_configured()` / `email_configured()` are true, assert the corresponding secret passes `looks_real_secret()` (the helper already exists in `core/config_checks`). When false, the feature route returns "not configured" (existing pattern) — never a half-configured live secret.
- **Key rotation for signing secrets**: support `MEDIA_SIGNING_KEY` + `MEDIA_SIGNING_KEY_PREV` so `verify_media_token` tries current then previous (dual-key window) — rotate without invalidating live share links. Same dual-key pattern documented for `DEV_JWT_SECRET` rotation.
- **Never log secrets**: `observability.py` structured logging + the existing `lib/redact-engine` taxonomy already cover egress; add a config dump guard (`/health` MUST NOT echo any `*_SECRET`/`*_KEY`/`*_PASSWORD` — assert in a test).
- **Deployment**: secrets injected as platform env vars (Render/Vercel/Neon secret stores — blocked on user deploy infra), never committed; `.env` git-ignored (already is). Document a `secrets-checklist.md` enumerating every secret, its rotation owner, and rotation cadence.

---

### Build order (low-risk → high-value)

1. `0004` RBAC migration + `permissions.py` + `require_perm` + role CHECK + RLS-coverage CI test (no infra dep, immediate hardening).
2. `audit.py` + `audit_logs` table + hash chain + triggers (reuses ledger pattern).
3. Moderation pipeline (`moderation.py`, `moderation_events`, serve-gate in `media.py`).
4. Platform-admin layer (`platform_admins`, `require_platform`, `admin_session`, `/v1/admin/*`).
5. PDPD: consent columns, export/delete endpoints + Arq purge cron.
6. Redis rate-limit backend + farming defenses (flips on when Redis lands — blocked on infra).
7. Secrets split (`MEDIA_SIGNING_KEY`) + startup gate extensions.


---

# 6. Frontend Architecture & Complete Screen Map

## Frontend Architecture & Complete Screen Map

This designs the REMAINING frontend on top of the verified Next.js 14 App Router base (21 screens, TanStack Query, Zustand wizard, dark + electric-violet token system in `tailwind.config.ts` + `globals.css`). It does NOT redesign what is built; it specifies the additions concretely against the actual files.

### 0. What's already there (baseline, do not redesign)

- **Route tree built**: `/` (landing), `/pricing`, `/login`, `/forgot-password`, `/reset-password`, `/verify-email`, `/accept-invite`, `/terms`, `/privacy`, `/billing/return`, and the `/app/*` group (`/app`, `/app/create`, `/app/library`, `/app/billing`, `/app/settings`, `/app/team`, `/app/reports`, `/app/audio`, `/app/image-gen`, `/app/compose`, `/app/v/[id]`), plus `error.tsx` + `not-found.tsx`.
- **Data layer**: `lib/api/client.ts` (fetch + `withRefresh` auto-401-retry in dev mode), `lib/api/endpoints.ts` (typed `api.*`), `lib/api/types.ts` (mirror of `schemas.py`), `lib/query/hooks.ts` + `mutations.ts` (query keys: `["me"]`, `["wallet"]` 20s poll, `["jobs"]`, `["job", id]` 2.5s poll-until-terminal, `["ledger"]`, `["estimate", ...]`), `providers.tsx` (`QueryClient`, staleTime 15s, retry 1, no refetch-on-focus).
- **Shell**: `app/app/layout.tsx` → `AuthGate` (client redirect to `/login`) + `SiteHeader authed` (fixed mega-menu, the real nav). NOTE: `components/shell/sidebar.tsx` exists but is **unused** — the app navigates via `SiteHeader`. New app screens hang off the mega-menu in `lib/features.ts`, not a sidebar.
- **UI kit**: `ui/button.tsx` (cva: primary/glass/ghost/outline), `ui/field.tsx` (`Field`, `inputCls`, `ChipGroup`), `ui/glass-card.tsx`, `ui/badge.tsx`, `ui/skeleton.tsx`, `ui/credit-value.tsx`. Wizard in `store/wizard.ts` (5-step, sessionStorage-persisted). i18n strings in `lib/i18n/vi.ts`.

The gaps this section fills: a **public** (non-auth) share page, an **admin** console, the **new feature screens** (templates, KOL gallery, brand-kit editor, scene/timeline editor, analytics, invoice history, onboarding), the **missing UI primitives** (Modal, Toast, Table, EmptyState, ErrorState, Tabs, Drawer, Select/Combobox), and the **cross-cutting** strategy (query-key contract, optimistic updates, responsive/i18n/a11y/SEO).

---

### 1. Complete route tree / screen map

Legend: ✅ built · �driority to-build · 🔒 admin-gated · 🌐 public (no auth).

#### 1a. Marketing / public (route group `(marketing)` — extract from current flat root)

| Path | File | Purpose | State |
|---|---|---|---|
| `/` | `app/(marketing)/page.tsx` | Landing hero + features + pricing teaser + FAQ | ✅ (move) |
| `/pricing` | `app/(marketing)/pricing/page.tsx` | Credit packs, per-video cost calculator | ✅ (move) |
| `/features/[slug]` | `app/(marketing)/features/[slug]/page.tsx` | SEO landing per feature (lookbook, review, product-ad…) from `lib/features.ts` keys; OG per page | �Build |
| `/templates` | `app/(marketing)/templates/page.tsx` | Public template gallery (SEO funnel; "use this template" → `/login?next=/app/create?template=`) | �Build |
| `/blog`, `/blog/[slug]` | `app/(marketing)/blog/...` | MDX content marketing (optional M3) | �Build later |
| `/terms`, `/privacy` | existing | Legal | ✅ (move) |
| `/share/[token]` 🌐 | `app/share/[token]/page.tsx` | **Public** video share page (no auth, signed media). SSR for OG. | �Build (§7) |

#### 1b. Auth (route group `(auth)`)

| Path | File | Purpose | State |
|---|---|---|---|
| `/login` | `app/(auth)/login/page.tsx` | Login + register tabs + dev quick-login + Google (Supabase) | ✅ (move) |
| `/register` | `app/(auth)/register/page.tsx` | Dedicated register (split from login tab for SEO + `?next=`) | �Build |
| `/forgot-password`, `/reset-password`, `/verify-email`, `/accept-invite` | existing | Lifecycle | ✅ (move) |
| `/onboarding` | `app/(auth)/onboarding/page.tsx` | First-run 3-step: brand kit → first KOL/voice → "make first video" CTA. Gated by `me.onboarded` flag (see new endpoint). | �Build (§5) |

#### 1c. App (authenticated, route group `app/app/*`)

| Path | File | Purpose | State |
|---|---|---|---|
| `/app` | existing | Dashboard: quick-create + recent jobs rail | ✅ |
| `/app/create` | existing | 5-step wizard | ✅ (extend for template/KOL/brand presets) |
| `/app/library` | existing | All videos grid + filters | ✅ (add filter bar, bulk select) |
| `/app/v/[id]` | existing | Video detail (auth) + "Share" action → mints `/share/[token]` | ✅ (add share modal) |
| `/app/billing` | existing | Wallet + topup packs | ✅ |
| `/app/billing/invoices` | `app/app/billing/invoices/page.tsx` | Invoice/payment history table + receipt download | �Build (§5) |
| `/app/templates` | `app/app/templates/page.tsx` | In-app template gallery → seed wizard | �Build (§5) |
| `/app/kols` | `app/app/kols/page.tsx` | KOL persona gallery (CRUD personas, consent) | �Build (§5) |
| `/app/kols/[id]` | `app/app/kols/[id]/page.tsx` | KOL persona editor (face ref, voice, style, consent) | �Build (§5) |
| `/app/brand-kits` | `app/app/brand-kits/page.tsx` | Brand kit list | �Build (§5) |
| `/app/brand-kits/[id]` | `app/app/brand-kits/[id]/page.tsx` | Brand kit editor (logo, palette, fonts, watermark, CTA) | �Build (§5) |
| `/app/projects/[id]/editor` | `app/app/projects/[id]/editor/page.tsx` | Scene/timeline editor (per-scene prompt, duration, reorder, voice line) | �Build (§5) |
| `/app/analytics` | `app/app/analytics/page.tsx` | Usage/spend/render-time dashboards (replaces thin `/app/reports`) | �Build (§5) |
| `/app/settings` | existing | Profile, password, default voice, members link, API keys placeholder | ✅ |
| `/app/team` | existing | Members + invites | ✅ |
| `/app/audio`, `/app/image-gen`, `/app/compose` | existing | Standalone tool surfaces | ✅ |

#### 1d. Admin (route group `app/admin/*`, 🔒 role `admin`)

| Path | File | Purpose | State |
|---|---|---|---|
| `/admin` | `app/admin/layout.tsx` + `page.tsx` | Admin shell + KPI overview (MRR, active orgs, jobs/day, refund rate) | �Build (§4) |
| `/admin/orgs` | `app/admin/orgs/page.tsx` | Tenant list, search, credit adjust, suspend | �Build (§4) |
| `/admin/orgs/[id]` | `app/admin/orgs/[id]/page.tsx` | Org detail: wallet, ledger, jobs, members | �Build (§4) |
| `/admin/jobs` | `app/admin/jobs/page.tsx` | Global job monitor (filter by status, retry/refund, stuck-job triage) | �Build (§4) |
| `/admin/payments` | `app/admin/payments/page.tsx` | Payment reconciliation (VNPay IPN status, manual settle) | �Build (§4) |
| `/admin/users` | `app/admin/users/page.tsx` | User search, account-status kill-switch toggle | �Build (§4) |
| `/admin/templates`, `/admin/kols` | `app/admin/...` | Curate global (system) templates + KOL presets | �Build (§4) |

---

### 2. State & data-fetching strategy

#### 2a. Query-key contract (extend `lib/query/keys.ts` — new file, single source of truth)

Today keys are inline string arrays scattered across `hooks.ts`/`mutations.ts`. As the surface grows, centralize a **key factory** to prevent invalidation drift:

```ts
// apps/web/src/lib/query/keys.ts
export const qk = {
  me: ['me'] as const,
  wallet: ['wallet'] as const,
  ledger: (limit: number) => ['ledger', limit] as const,
  jobs: (filter?: JobFilter) => ['jobs', filter ?? 'all'] as const,
  job: (id: string) => ['job', id] as const,
  estimate: (p: EstimateRequest) => ['estimate', p.mode, p.purpose, p.seconds, p.resolution] as const,
  templates: (scope: 'org' | 'system') => ['templates', scope] as const,
  template: (id: string) => ['template', id] as const,
  kols: () => ['kols'] as const,
  kol: (id: string) => ['kol', id] as const,
  brandKits: () => ['brand-kits'] as const,
  brandKit: (id: string) => ['brand-kit', id] as const,
  invoices: (limit: number) => ['invoices', limit] as const,
  analytics: (range: string) => ['analytics', range] as const,
  // admin namespace prefixed to never collide with tenant cache
  admin: {
    overview: ['admin', 'overview'] as const,
    orgs: (q: string) => ['admin', 'orgs', q] as const,
    org: (id: string) => ['admin', 'org', id] as const,
    jobs: (status: string) => ['admin', 'jobs', status] as const,
  },
};
```

Migrate existing hooks to `qk.*` (mechanical, behavior-preserving). New hooks for the new screens (`useTemplates`, `useKols`, `useBrandKit`, `useInvoices`, `useAnalytics`, `useAdminOverview`) follow the existing `useQuery` pattern in `hooks.ts`.

#### 2b. Polling & live state (keep existing pattern)

- `useJob` already polls 2.5s until terminal via `refetchInterval` callback — **keep**; reuse it in the timeline editor's render preview.
- `useWallet` 20s poll — **keep**; additionally invalidate `qk.wallet` after job create/topup (already wired in `mutations.ts`).
- For the **render timeline**, the current `useJob` + `job_events` polling is sufficient for inline mode. When Arq+Redis lands (blocked on infra), upgrade to **SSE**: add `lib/query/use-job-stream.ts` subscribing to `GET /v1/jobs/{id}/stream` (EventSource), `setQueryData(qk.job(id), …)` on each event, falling back to polling if `EventSource` errors. Design the hook now, gate behind `NEXT_PUBLIC_JOB_STREAM=1`.

#### 2c. Optimistic updates

Today only invalidation-on-success is used (correct for credit-sensitive paths — never optimistically guess a balance). Add **true optimistic** updates only where the server is authoritative-but-slow and cheap to roll back:

- **Job delete/cancel** (`/app/library`): `onMutate` → snapshot `qk.jobs()`, remove the row, `onError` rollback, `onSettled` invalidate. Gives instant grid feedback.
- **KOL/template/brand-kit rename + delete**: optimistic list mutation, rollback on error.
- **NEVER optimistic** for: topup, job create, credit adjust — these touch the wallet/ledger; always invalidate `qk.wallet`+`qk.ledger` from the server response (the source of truth is the append-only ledger).

#### 2d. Auth-on-401 (already added — extend)

`client.ts:withRefresh` retries once on 401 in dev mode after `refreshSession()`. Two extensions:
1. **Supabase mode**: also retry on 401 by forcing `sb.auth.refreshSession()` (currently only dev refreshes). Add a branch so both auth modes self-heal.
2. **Hard 401 (refresh failed)**: dispatch a global event `window.dispatchEvent(new Event('vietvid:unauthorized'))`; a listener in `AuthGate`/top-level calls `clearSession()` + `router.replace('/login?next=' + pathname)`. Today a dead session silently fails requests until the next `AuthGate` mount.

#### 2e. Wizard Zustand (extend `store/wizard.ts`)

Keep the 5-step shape. Add three preset-seeding fields so the new galleries can drive the wizard without breaking the existing `?feature=` preset path:
- `templateId: string`, `kolPersonaId: string`, `brandKitId: string` (map 1:1 to the reserved `jobs.template_id/kol_persona_id/brand_kit_id` FK columns).
- `/app/create` reads `?template=`, `?kol=`, `?brand=` query params (mirror the existing `?feature=` handler) and patches these. `handleCreate` adds them to `JobCreateRequest` (the backend FK columns already exist).
- Add a separate `store/timeline.ts` for the scene editor (array of `{ id, prompt, seconds, voiceLine, order }`), persisted to `localStorage` keyed by project id (drafts survive reload).

---

### 3. Design-system tokens + component library plan

Keep the existing token system verbatim (`tailwind.config.ts`: `bg.*`, `violet.*`, `ink.*`, `success/hold/refund/danger`, `grad-brand`, `glow-*` shadows; `globals.css`: `.glass`, `.glass-bordered`, `.mesh-bg`, `.grain`, `.text-gradient`). No new colors. The component plan **fills the missing primitives** — everything below lives under `components/ui/`:

| Component | File | Why needed | Pattern |
|---|---|---|---|
| `Modal` / `Dialog` | `ui/modal.tsx` | Share, confirm-delete, invite, credit-adjust | Framer Motion fade+scale, focus-trap, `Esc`/backdrop close, `role="dialog" aria-modal`, portal |
| `Drawer` | `ui/drawer.tsx` | Mobile filters, scene properties panel | Slide-in, same a11y contract |
| `Toast` + `ToastProvider` | `ui/toast.tsx` | Replace ad-hoc inline `text-success`/`text-danger` msgs (settings, billing) | Context + queue, top-right, auto-dismiss, `aria-live="polite"` |
| `Table` / `DataTable` | `ui/table.tsx` | Ledger, invoices, admin lists, team | Sticky header, `tabular` nums, empty/loading/error slots |
| `EmptyState` | `ui/empty-state.tsx` | Factor out the repeated empty-card markup (dashboard, library) | Icon + title + CTA |
| `ErrorState` | `ui/error-state.tsx` | Standard query-error card with retry | Icon + message + `onRetry` |
| `Tabs` | `ui/tabs.tsx` | Login (login/register), settings sections, analytics ranges | Roving tabindex, `aria-selected` |
| `Select` / `Combobox` | `ui/select.tsx` | Voice/engine/resolution pickers beyond `ChipGroup`, KOL search | Keyboard nav, `listbox` semantics |
| `Tooltip` | `ui/tooltip.tsx` | Credit-cost hints, stage explanations | `aria-describedby` |
| `Switch`, `Slider` | `ui/switch.tsx`, `ui/slider.tsx` | Consent toggle, scene duration | Native-input-backed for a11y |
| `Avatar`, `Stat`, `ProgressBar` | `ui/avatar.tsx`, `ui/stat.tsx`, `ui/progress.tsx` | Team, analytics KPI cards, render progress | — |

**Reusable form pattern**: keep `Field`/`inputCls`/`ChipGroup`. Add a thin `useForm`-less validation helper `lib/forms/validate.ts` (pure functions, Vietnamese error strings via `vi.ts`) — no heavy form lib; the existing controlled-input style is fine and matches the codebase.

**Query-state pattern (standardize)**: every data screen renders `isLoading → <Skeleton/>`, `isError → <ErrorState onRetry={refetch}/>`, `empty → <EmptyState/>`, else content. Factor a tiny `<QueryBoundary query={...} skeleton={...} empty={...}>` wrapper in `components/ui/query-boundary.tsx` so screens stop re-implementing the `dashboard/page.tsx` triple-branch by hand.

---

### 4. Admin dashboard UI architecture

- **Gate**: new role `admin` (today RBAC only has `owner`/`member`). `app/admin/layout.tsx` calls `useMe()`; if `me.role !== 'admin'` → `router.replace('/app')`. Backend mirror: `deps.require_role('admin')` on `/v1/admin/*`. Admin reads cross-tenant data, so those endpoints run with **RLS bypass via a service path** (a dedicated `admin` DB role / session that does not set `vietvid.current_org`), not the tenant principal — flag clearly for the backend domain; the frontend just calls `/v1/admin/*`.
- **Shell**: distinct from the marketing `SiteHeader`. `components/admin/admin-shell.tsx` = left rail (Overview, Orgs, Jobs, Payments, Users, Curate) + topbar with a "Viewing as admin" banner so it's never confused with the tenant app. Reuse `Sidebar`-style nav (the unused `shell/sidebar.tsx` is the visual reference).
- **Screens**: all are `DataTable` + filter bar + detail drawer. `/admin` = grid of `Stat` cards (`useAdminOverview`). `/admin/jobs` = the highest-value screen: live job monitor (poll 5s), columns status/org/stage/age/cost, row actions retry/refund (calls `/v1/admin/jobs/{id}/retry|refund`). `/admin/payments` = VNPay reconciliation (IPN received? settled? manual-settle action). Mutations invalidate the `qk.admin.*` namespace only.
- **Safety**: every destructive admin action (suspend org, force-refund, kill-switch user) goes through the new `Modal` confirm with a typed-confirmation for high-impact ones (type the org slug). No optimistic updates in admin — always server-confirmed.

---

### 5. New feature screens

**Templates gallery** (`/app/templates`, `/app/templates` marketing mirror): masonry of `GlassCard` template tiles (thumbnail, name, category, est-credit badge). System templates (curated by admin) + org templates ("Save as template" from a finished job). Click → `router.push('/app/create?template=<id>')` which seeds the wizard via the new `templateId` field. Hook `useTemplates('system'|'org')`. Backs the reserved `jobs.template_id` FK.

**KOL gallery + editor** (`/app/kols`, `/app/kols/[id]`): grid of persona cards (face thumbnail, name, voice tag, consent ✓). Editor: face reference upload (reuse `api.uploadImage`), voice gender/style `ChipGroup`, persona style brief, **mandatory consent toggle** (reuse the wizard's consent gate logic). New endpoints `/v1/kols` CRUD. Backs `jobs.kol_persona_id`. Wizard reads `?kol=<id>`.

**Brand-kit editor** (`/app/brand-kits`, `/app/brand-kits/[id]`): logo upload, color palette picker (constrained to brand tokens + custom), font choice, watermark on/off + position, default CTA text, default voice. Live preview pane. New endpoints `/v1/brand-kits` CRUD. Backs `jobs.brand_kit_id`.

**Scene / timeline editor** (`/app/projects/[id]/editor`): horizontal filmstrip of scenes (reuse the `render-timeline.tsx` film-strip visual language). Each scene = card with per-scene prompt, duration `Slider`, voice line, and reorder (drag via Framer Motion `Reorder.Group`). Right `Drawer` = scene properties. "Render" composes scenes into a `JobCreateRequest` (maps to `scene_prompt`/`params` already in `JobCreateRequest`). State in `store/timeline.ts`. This is the "pro" surface autovis lacks: granular per-scene control.

**Analytics dashboards** (`/app/analytics`, replacing thin `/app/reports`): `Tabs` for range (7d/30d/90d). KPI `Stat` cards (videos made, credits spent, avg render time, success rate). Charts: spend-over-time, credit burn-down, per-feature usage, render-time-by-stage (from `job.stage_timings`). Use a lightweight chart lib (`recharts`, ~tree-shakeable) or hand-rolled SVG bars to avoid bundle bloat — decide at build. Hook `useAnalytics(range)` → new `/v1/analytics/usage`.

**Billing / invoice history** (`/app/billing/invoices`): `DataTable` of payments (date, pack, amount VND, credits, provider, status, receipt). Receipt download → `/v1/billing/payments/{id}/receipt`. Hook `useInvoices`. Complements the existing wallet/ledger screen.

**Onboarding** (`/onboarding`): 3-step `Stepper` (reuse `create/stepper.tsx`): (1) optional brand kit quick-create, (2) pick/confirm default voice, (3) "make your first video" → `/app/create`. Gated by a new `me.onboarded` boolean; skip if true. Sets `onboarded=true` via `PATCH /v1/auth/me`.

---

### 6. Mobile/responsive + i18n + a11y

- **Responsive**: the app already uses `max-w-6xl` + `lg:` breakpoints and a mobile mega-menu in `SiteHeader`. New screens follow: grids `grid-cols-2 sm:grid-cols-3 lg:grid-cols-4`, tables collapse to stacked cards under `sm`, filters move into the `Drawer` on mobile. The timeline editor is desktop-first with a read-only mobile fallback (drag-reorder is impractical on touch — show "edit on desktop" hint).
- **i18n**: everything Vietnamese via `lib/i18n/vi.ts`. The dict is currently shallow; **expand it into namespaces** (`vi.templates`, `vi.kol`, `vi.brand`, `vi.analytics`, `vi.admin`, `vi.errors`) and route ALL new copy through it — no inline Vietnamese in new components (the existing components have some inline strings; leave them, but new code is dict-only so a future EN locale is a drop-in). Keep `lang="vi"` in root layout. Format VND/credits/dates via `lib/format.ts` helpers (`Intl.NumberFormat('vi-VN')`).
- **a11y**: the new primitives bake in the contract (focus-trap modals, `aria-live` toasts, `listbox` selects, roving-tabindex tabs, visible focus rings already in `button.tsx`). Audit checklist per screen: every interactive element keyboard-reachable, every icon-only button has `aria-label` (the header already does this), color is never the sole status signal (pair `Badge` tone with text — already the pattern), `prefers-reduced-motion` already handled in `globals.css`. Target WCAG 2.1 AA contrast (the `ink.*` ramp on `bg.*` passes).

---

### 7. Public share page + SEO/OG

- **Route**: `app/share/[token]/page.tsx` — **outside** the `/app` auth group, **server component** (SSR for crawlable OG). The current `/app/v/[id]` is auth-gated and client-only; the share page is the public twin.
- **Token, not job id**: `/app/v/[id]` adds a "Share" action → `POST /v1/jobs/{id}/share` returns a public `share_token` (random, revocable, stored in a new `video_shares` table). The share page resolves token → signed media URL server-side (reuse `media.py` HMAC signing) and renders the player without exposing the raw job/org id. Revoke from the detail page.
- **SEO/OG**: `generateMetadata({ params })` fetches share meta server-side → sets `og:title`, `og:description`, `og:video`, `og:image` (poster frame), `twitter:card=player`. Add `app/sitemap.ts` (marketing + `/features/[slug]` + `/templates`), `app/robots.ts` (allow marketing/share, disallow `/app`, `/admin`), and per-feature OG on `/features/[slug]`. Landing/pricing/feature pages become server components where possible for crawlability (today they're client `'use client'` — split the static shell from the interactive islands).
- **Watermark/branding policy**: free-tier shares carry a small "Made with VietVid" badge on the share page (growth loop); paid orgs can toggle it via brand kit.

---

### Cross-cutting build order (suggested)

1. UI primitives (`Modal`, `Toast`, `Table`, `EmptyState`, `ErrorState`, `Tabs`, `QueryBoundary`) + `lib/query/keys.ts` migration + `lib/format.ts` — unblocks everything, zero backend dependency.
2. Route-group refactor (`(marketing)`, `(auth)`) + onboarding — pure frontend.
3. Share page + SEO/OG — needs one new endpoint + `video_shares` table.
4. Templates / KOL / brand-kit galleries+editors — need CRUD endpoints + 3 tables (the FK columns already exist).
5. Analytics + invoices — need 2 read endpoints.
6. Admin console — needs the `admin` role + `/v1/admin/*` + RLS-bypass service path.
7. Scene/timeline editor — most complex; last.


---

# 7. Infrastructure, DevOps, Deployment & Observability

## Infrastructure, DevOps, Deployment & Observability

This section designs the production delivery layer that turns the verified M1 app (`app_api/`, `video_engine/`, `apps/web/`) into a deployable, observable, recoverable, multi-instance SaaS. It builds **on** what exists — the Dockerfile, `infra/docker-compose.yml`, `observability.py`, `startup_checks.py`, `reaper.py`, the `executor.submit_job` queue seam, and the rich cost-attribution columns already on `jobs`/`ledger_entries`/`job_events`. Nothing already-built is redesigned.

The audit's three P0s drive priority order:
1. **ZERO tests** — biggest production risk. The credit ledger is real money and has no automated proof it holds invariants under concurrency.
2. **Multi-instance migrate race** — the Dockerfile's `CMD` runs `alembic upgrade head` on every boot; Render scaling to N replicas runs N concurrent migrations.
3. **Inline executor doesn't survive redeploy cleanly** — a 90s render in a FastAPI `BackgroundTask` gets SIGTERM'd on every deploy; the reaper refunds it, but the user's job silently dies. Needs the real Arq worker.

---

### 1. Deployment topology

**Target: split web / API / worker, managed data plane, VN/SEA edge.** autovis runs everything in one box; VietVid wins on a clean tier split that scales the expensive render path independently and keeps the financial DB on PITR-backed managed Postgres.

```
                    Cloudflare (DNS + WAF + CDN, SG/HKG edge)
                              │
        ┌─────────────────────┼──────────────────────────┐
        │                     │                           │
   app.vietvid.vn        api.vietvid.vn            media.vietvid.vn
   Vercel (Next.js)      Render Web Service        Cloudflare R2 (custom domain)
   Edge: sin1/hkg        Region: Singapore          + Cache Rules (signed URLs)
        │                     │
        │              ┌──────┴───────┐
        │              │              │
        │         API service    Worker service (Render Background Worker)
        │         (web, N=2)      arq worker (q_fast / q_slow), N=1→burst
        │              │              │
        │              └──────┬───────┘
        │                     │
        │         ┌───────────┼────────────┐
        │         │           │            │
        │     Neon Postgres  Upstash Redis  R2
        │     (Singapore,    (queue +       (media,
        │      PITR on)       ratelimit)     lifecycle)
```

**Why this split (Layer-3 reasoning, not cargo-culting):**

- **Web on Vercel** — already the documented path (`docs/DEPLOY.md` §4, `apps/web` root dir). Static + SSR at the edge; nothing to change. Vercel's `sin1`/`hkg` regions serve VN/SEA users sub-50ms.
- **API and worker as SEPARATE Render services from ONE image.** The current Dockerfile builds a single backend image. Keep it — split by `CMD` override, not by building two images:
  - API service: `web` type, `CMD` runs migrate-with-lock then `uvicorn`.
  - Worker service: `worker` type (no port), `CMD` runs `arq app_api.arq_worker.WorkerSettings`.
  This is the cheapest correct split: same artifact, same deps (ffmpeg/opencv already baked in layer), independent scaling and independent OOM/CPU budgets. The render path needs 2-4GB RAM + CPU burst; the API needs 512MB. Co-locating them means a heavy render starves request handling — the exact failure mode the inline executor has today.
- **Postgres on Neon, Singapore region, PITR enabled.** Already documented. Neon's default role is non-superuser so `FORCE RLS` stays effective (DEPLOY.md §1 already calls this out). Neon gives branch-per-PR DBs for the CI migration-smoke job (see §3).
- **Redis on Upstash (Singapore).** Serverless Redis, pay-per-command, TLS by default. Backs both the Arq queue AND the distributed rate limiter (replacing the in-proc `ratelimit.py` dict for multi-instance correctness). `rediss://` URL into the existing unused `REDIS_URL` knob.
- **Object storage R2 + Cloudflare CDN.** Render's ephemeral disk loses `/tmp` media on every deploy (DEPLOY.md §"Giới hạn MVP" already flags this). R2 has zero egress fees — decisive for a video product where egress would otherwise dwarf compute. Custom domain `media.vietvid.vn` fronted by Cloudflare cache rules; signed-URL access via the EXISTING `media.py` HMAC tokens (no change to the token scheme, just the backing store).

**GPU burst** is deferred infra, not core: today's video path is **PiAPI/Seedance (external API)** — VietVid does not run GPUs for i2v. The only GPU need is the optional VieNeu voice clone (`TTS_VIENEU_URL` over a tunnel). Scaling path for that is a separate Fly.io GPU machine behind the existing tunnel knob — designed in §6, not built now.

---

### 2. Environments, IaC, secrets

**Three environments, one Dockerfile, env-only differences** (the codebase already keys everything off `VIETVID_ENV` + env vars via `app_api/config.py`):

| Env | Web | API+Worker | Postgres | Redis | Storage | Auth | Billing |
|-----|-----|-----------|----------|-------|---------|------|---------|
| **dev** | localhost:3000 | localhost:8099, `JOB_EXECUTION_MODE=inline` | docker-compose pg | docker-compose redis (idle) | MinIO (compose) | dev HS256 | dev instant-topup |
| **staging** | Vercel preview | Render (free/starter), `=queue` | Neon branch `staging` | Upstash free db | R2 `vietvid-staging` | Supabase staging project | VNPay **sandbox** |
| **prod** | Vercel prod | Render standard, `=queue` | Neon `main` + PITR | Upstash prod | R2 `vietvid-prod` | Supabase prod | VNPay **live** |

**IaC choice: `render.yaml` Blueprint at repo root** (declarative, in-repo, free) + **Terraform for Cloudflare/R2/Upstash** (`infra/terraform/`). Rationale: Render Blueprints natively express the multi-service-one-image split and env-group wiring; using Terraform for everything would fight Render's model. Keep the boundary clean:

- `render.yaml` — declares `vietvid-api` (web) + `vietvid-worker` (worker) + a shared `envVars` group, both `fromDockerfile`.
- `infra/terraform/` — R2 buckets + lifecycle rules, Cloudflare DNS/cache rules/WAF, Upstash DB. State in R2 backend.
- `infra/docker-compose.yml` — **already exists, unchanged** for local dev (pg/redis/minio).

**Secrets:** never in repo (`.dockerignore` already excludes `.env*`). Source of truth per platform: Render env groups (API+worker share `vietvid-prod-env`), Vercel env vars, GitHub Actions secrets (for CI deploy hooks + migration-smoke DB URL). `.env.production.example` stays the documented contract. Add a `scripts/check_env.py` that asserts the prod-required set is present and fails CI/boot — this complements `startup_checks.validate_prod_config()` which already gates auth/CORS/dev-port safety but does NOT yet assert storage/redis presence when `JOB_EXECUTION_MODE=queue`. **Extend `validate_prod_config()`** to add: "if `JOB_EXECUTION_MODE=queue` then `REDIS_URL` required" and "if prod then `storage_configured()` required" — fail-closed, matching the file's existing pattern.

---

### 3. CI/CD — GitHub Actions

No `.github/` exists at repo root today (confirmed). A sibling worktree has a `ci.yml` for the *engine* modules — reuse its proven shape (Python 3.12, ruff pinned, ffmpeg apt, advisory mypy/bandit) but retarget at `app_api`. New file: **`.github/workflows/ci.yml`**.

**Pipeline (PR → merge → deploy):**

```yaml
# .github/workflows/ci.yml  (on: pull_request, push to main)
jobs:
  lint:        # ruff format --check + ruff check app_api core video_engine (pinned 0.15.16)
  typecheck:   # mypy app_api  (continue-on-error: advisory, matches engine CI)
  test:        # pytest -m "not paid"  against a Postgres 18 service container
  migration-smoke:  # the audit's race fix lives here — see below
  build:       # docker build (cache-from gha) — proves the image compiles
```

**`test` job** spins a `postgres:18` service container (mirrors compose), runs `alembic upgrade head`, then `pytest -m "not paid"` (the real-op tier — §7). Redis via a `redis:7-alpine` service for queue/ratelimit tests.

**`migration-smoke` job — directly addresses the multi-instance migrate race audit:**
```
1. Create a fresh Neon branch (or pg service container) at main's schema.
2. Run `alembic upgrade head` then `alembic downgrade -1 && alembic upgrade head` (proves reversibility of the new revision).
3. Run `alembic check` (autogen drift: models vs migrations must match).
4. CONCURRENCY TEST: launch `alembic upgrade head` ×3 in parallel against the
   SAME db; assert exactly one acquires the lock, others wait, final schema is correct,
   no "DuplicateTable"/"relation already exists" error. This is the regression test
   for the advisory-lock fix below.
```

**The advisory-lock fix (the core deliverable of the race audit).** Today migration runs inline in the container `CMD` — every Render replica races. Fix in **`alembic/env.py`** `run_migrations_online()`: wrap the migration in a Postgres session advisory lock so concurrent boots serialize, the loser sees head-is-current and no-ops.

```python
# alembic/env.py — run_migrations_online(), inside connection scope, BEFORE run_migrations()
_MIGRATION_LOCK_KEY = 0x7669657476696431  # crc of "vietvid1", stable int64
with connectable.connect() as connection:
    connection.exec_driver_sql("SELECT pg_advisory_lock(%s)", (_MIGRATION_LOCK_KEY,))
    try:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
    finally:
        connection.exec_driver_sql("SELECT pg_advisory_unlock(%s)", (_MIGRATION_LOCK_KEY,))
```
Session-level (not xact-level) lock so it spans the whole `run_migrations()` regardless of internal transactions; `NullPool` (already set) means one real connection holds it. This is the Layer-1 tried-and-true pattern (Django/Rails both ship migration locks) — search-before-building confirms Postgres `pg_advisory_lock` is the built-in, no external coordination needed.

**Deploy stage.** On push to `main` after CI green: trigger Render deploy hooks (`vietvid-api` then, on success, `vietvid-worker`) and Vercel auto-deploys on its own git integration. Migration runs ONCE via the API container's locked `CMD`; the worker container's `CMD` does NOT migrate (it only runs arq) — so only one service is the migration driver. **This is a deliberate change to the worker `CMD`**: API migrates, worker waits. Document the ordering in `render.yaml` (worker `dependsOn`-equivalent: deploy API first).

**Rollback.** Render keeps prior images — one-click rollback of `vietvid-api`/`vietvid-worker` to the last green deploy. The hard part is **schema rollback**: forward migrations must be backward-compatible (expand/contract) so an app rollback doesn't hit a schema it can't read. Document the rule in `docs/DEPLOY.md`: additive columns nullable-or-defaulted, never drop-in-same-release. `migration-smoke`'s `downgrade -1` check enforces every new revision is reversible.

---

### 4. Observability — metrics, traces, errors, alerting

Structured logs are **done** (`observability.py`: request-id contextvar, JSON formatter, access log, global exception handler). The gaps are metrics, traces, error aggregation, and alerting. Design adds them without disturbing the existing middleware stack.

**Metrics (Prometheus) — new module `app_api/metrics.py`.** Use `prometheus-client` (add to `requirements.txt`). Expose `GET /metrics` (gated to internal/bearer in prod). Instrument the money-and-render path, not vanity counters:

| Metric | Type | Labels | Why |
|--------|------|--------|-----|
| `vietvid_http_requests_total` | Counter | method, path_template, status | golden-signals traffic/errors |
| `vietvid_http_request_seconds` | Histogram | path_template | latency SLO |
| `vietvid_jobs_total` | Counter | status (READY/FAILED/QA_FAIL/REFUNDED), kind | render success rate |
| `vietvid_job_duration_seconds` | Histogram | kind, speed_tier | render time regression |
| `vietvid_queue_depth` | Gauge | queue (q_fast/q_slow) | scaling signal (§6) |
| `vietvid_provider_cost_usd_total` | Counter | provider (seedance/gemini/piapi) | spend tracking |
| `vietvid_wallet_hold_settle_total` | Counter | op (HOLD/SETTLE/REFUND) | ledger health |
| `vietvid_provider_errors_total` | Counter | provider, kind | provider outage detection |

Wire the HTTP metrics in a thin middleware added next to `RequestContextMiddleware`. Wire job/cost/wallet metrics at the exact points that already emit data: `worker.run_job` (duration, status), `complete_job` (settle/refund), `QueueSink.add_asset` (provider cost — it already carries `provider`+`cost_usd`).

**Traces (OpenTelemetry) — optional, behind `OTEL_EXPORTER_OTLP_ENDPOINT`.** Use `opentelemetry-instrumentation-fastapi` + `-sqlalchemy` for auto-spans across HTTP → DB. One custom span around the render pipeline stages (the engine already has `stage_timings`). Export to a free Grafana Cloud / Honeycomb tier. Trace propagation reuses the existing `X-Request-Id` as the correlation key (set it as the OTel trace baggage so logs ↔ traces join).

**Error aggregation (Sentry).** Add `sentry-sdk[fastapi]`, init in `main.py` lifespan gated on `SENTRY_DSN`. Critically: the existing global exception handler in `observability.install_exception_handlers` swallows tracebacks into a safe 500 — Sentry must capture BEFORE that returns. Init Sentry's FastAPI integration so it hooks the ASGI layer (captures even handled-500s) and scrub PII (email, tokens) via `before_send`. Also init in the **worker** process (renders fail there, not in the API). Tag every event with `org_id` + `request_id` from the contextvar.

**Uptime + alerting.** Better Stack (or UptimeRobot free) pings `GET /health/ready` (already returns 503 on DB-down). Alert routes (Slack/email):
- **Availability:** `/health/ready` 503 for >2 checks → page.
- **Error rate:** `vietvid_http_requests_total{status=~"5.."}` ratio >2% over 5m.
- **Job failure:** `vietvid_jobs_total{status="FAILED"}` rate spike, or QA_FAIL ratio >20% (provider quality drop).
- **Provider:** `vietvid_provider_errors_total` >N/5m (PiAPI/Gemini outage).
- **Spend guardrail:** `vietvid_provider_cost_usd_total` increase >$X/hour → page (runaway render loop = real money). This is the single most important alert for a credit-backed product and maps 1:1 to the `usd_cost` already snapshotted into every ledger row.
- **Queue depth:** `vietvid_queue_depth{queue="q_slow"}` > threshold for 5m → scale signal.

---

### 5. Backups / PITR + restore drill (financial source of truth)

The credit ledger (`ledger_entries`, append-only trigger) is the money source of truth. A wallet balance is reconstructable by summing `delta_credits`; `balance_after` is the materialized check. Backup strategy must make this **provably restorable**.

**Backup layers:**
1. **Neon PITR** — continuous WAL, configurable retention (set 7d staging / 30d prod). RPO ≈ seconds, RTO = minutes (branch from timestamp). This is the primary mechanism, already available on the chosen provider.
2. **Daily logical dump of financial tables** to R2 (`vietvid-backups/`), defense-in-depth against provider-side loss or a bad migration that corrupts the schema PITR would faithfully reproduce. New job: **`scripts/backup_ledger.py`** → `pg_dump -t wallets -t ledger_entries -t payments -t orgs` (orgs for FK integrity), gzip, upload to R2 with object-lock/immutability + lifecycle (keep 90d). Run via Render Cron Job (declared in `render.yaml`).
3. **R2 media** — `videos` rows reference R2 objects; R2 versioning + a lifecycle rule. Media is regenerable (re-render) so lower tier than the ledger.

**Restore drill (the part teams skip — make it a scheduled, scripted, asserted procedure).** New file **`scripts/restore_drill.py`** + a `migration-smoke`-style CI/cron job `restore-drill.yml` (monthly):
```
1. Spin a Neon branch from PITR at T-1h (or load latest R2 ledger dump into a scratch db).
2. Run reconciliation assertions on the restored ledger:
   a. For every wallet: balance == SUM(delta_credits) for that org  (ledger integrity).
   b. balance_after on the latest row per org == wallet.balance  (materialized check).
   c. No ledger row violates ck_ledger_balance_after_nonneg.
   d. Every HOLD has a matching SETTLE or REFUND in the same ref_group, OR the job is
      still non-terminal  (no orphaned holds — same invariant the reaper enforces live).
   e. payments.credits_granted sums reconcile against TOPUP ledger entries by ref_group.
3. Assert restored row counts within tolerance of live.
4. Emit a PASS/FAIL report; FAIL pages on-call.
```
This drill doubles as the **reconciliation test** that proves the append-only trigger + ACID wallet logic hold over real history — exactly the confidence a money system needs and that "we have backups" alone never gives.

---

### 6. Cost model + scaling path

**Cost is already attributable in the schema** — no new tables needed for the model itself. Per render: `jobs.actual_cost_usd` (and `est_cost_usd`), `jobs.provider_video`/`provider_image`/`model_id`; per stage: `job_events.cost_usd`+`provider`; per credit movement: `ledger_entries.usd_cost`+`fx_usd_vnd`+`credit_price_vnd` snapshot. Unit economics fall straight out of these.

**Per-provider monthly cost drivers (the real spend):**

| Provider | Unit | Scales with | Where it lands |
|----------|------|-------------|----------------|
| PiAPI/Seedance (i2v) | per clip-second | render volume × seconds | dominant variable cost; `job_events.cost_usd` provider=seedance |
| Gemini (images) | per image | scenes per render | `provider_image=gemini` cost |
| Groq (script LLM) | per token | ~flat per render | small |
| edge-tts (voice) | free | — | $0 (VieNeu only if clone enabled) |
| Neon | compute-hours + storage | DB load + retention | ~flat, steps with PITR window |
| Upstash | per command | queue ops + ratelimit | low |
| R2 | storage + Class-A ops | media GB stored; **egress $0** | grows with retained videos |
| Render | instance-hours | API replicas + worker burst | second-largest fixed cost |
| Vercel | bandwidth/builds | web traffic | low |

**Per-tenant cost model.** A tenant's marginal infra cost is dominated by render spend, fully captured by `SUM(jobs.actual_cost_usd) WHERE org_id=?`. The platform margin per render = `usd_to_credits(actual_cost_usd) × CREDIT_PRICE_VND` charged vs `actual_cost_usd × USD_TO_VND` paid — both already computed by `app_api/pricing.py`. Surface this as an **admin reporting view** (no new table): a materialized/query view `org_cost_summary` rolling up `jobs` + `ledger_entries` by org+month for the existing `apps/admin` surface. The `est_cost_usd` vs `actual_cost_usd` gap per provider is the calibration signal for repricing credits.

**Scaling path (queue-depth driven):**
1. **API replicas** scale on CPU/latency (Render autoscale). Stateless after the rate-limiter moves to Redis (§2) — required, since the in-proc `ratelimit.py` dict is per-instance and under-counts with N replicas.
2. **Worker scaling on `vietvid_queue_depth`.** Arq pulls from `q_fast` (drafts/short) and `q_slow` (full renders) — the two-queue split the executor seam already anticipates (`executor.py` comment names `q_fast/q_slow`). Add worker replicas when `q_slow` depth > threshold. Each render is external-API-bound (PiAPI), so a worker is mostly waiting — high concurrency per worker (`arq` `max_jobs` tuned to PiAPI rate limits, not CPU).
3. **PiAPI is the real throughput ceiling**, not our compute — concurrency limited by PiAPI account rate limits + spend cap. The scaling lever is the spend guardrail alert (§4), not more workers. Document: scaling renders = raising the PiAPI cap, gated on the cost alert.
4. **GPU burst (VieNeu voice clone only, deferred):** a Fly.io GPU machine behind the existing `TTS_VIENEU_URL` tunnel knob, scale-to-zero, woken by the worker when a job requests clone voice. Not built now — the edge-tts fallback already works.

---

### 7. Test strategy — the ZERO-tests P0

This is the highest-leverage deliverable. **Today there are no tests** (no `pytest.ini`/`conftest.py`/`tests/` at root). The verify harness referenced in MEMORY is a real-op script, not an automated suite. Design a `pytest` real-op tiered suite plus what CI runs.

**Tiering (pytest markers in a new `pyproject.toml` `[tool.pytest.ini_options]`):**

| Marker | What | Backing | Runs in CI | Speed |
|--------|------|---------|-----------|-------|
| `unit` | pure logic: `pricing.usd_to_credits`, `media` token sign/verify, config parsing | none | every PR | <1s |
| `db` (real-op) | **real Postgres**: wallet HOLD/SETTLE/REFUND, ledger append-only trigger, RLS isolation, idempotency, reaper | pg service container | every PR | ~10s |
| `api` (real-op) | FastAPI TestClient against real pg: auth lifecycle, RBAC, job submit→complete (mock provider), billing IPN idempotency | pg + app | every PR | ~30s |
| `queue` (real-op) | Arq enqueue→worker→complete round-trip | pg + redis | every PR | ~20s |
| `paid` | real Gemini/PiAPI render end-to-end | live keys | manual/nightly only | minutes, $ |

**The must-have real-op tests (financial correctness — the reason this is P0):**

- **RLS isolation:** two orgs, org A's `tenant_session` cannot SELECT/UPDATE org B's wallet/jobs/ledger. Proves `FORCE RLS` + the `vietvid.current_org` GUC actually fences tenants (the entire multi-tenant safety claim).
- **Ledger append-only:** `UPDATE`/`DELETE` on `ledger_entries` raises (trigger). Proves immutability of the money log.
- **Wallet ACID under concurrency:** N parallel HOLDs on a wallet with budget for K<N never oversell; balance never goes negative (`ck_ledger_balance_after_nonneg` holds); exactly K succeed. This is the test that catches the double-spend class.
- **Idempotency:** duplicate `idempotency_key` on `POST /jobs` and duplicate VNPay IPN (`apply_topup`) each apply exactly once.
- **Reaper:** a job stuck RUNNING past `REAPER_STUCK_MINUTES` gets HOLD refunded + CANCELLED, and the refund is exactly the held amount (no leak, no double-refund).
- **Migration round-trip:** `upgrade head` from empty == models metadata (`alembic check`), `downgrade -1/upgrade` clean.

**Test infra files (new):**
- `pyproject.toml` — pytest markers, ruff config (retire the per-module path lists; target `app_api core video_engine`).
- `tests/conftest.py` — fixtures: `pg_engine` (truncate-between-tests against the service container, NOT mocks), `client` (FastAPI TestClient), `org_factory`, `auth_headers`, `redis` (fakeredis for `unit`, real for `queue`). Real Postgres is non-negotiable for the `db`/`api` tiers — RLS and the append-only trigger are Postgres behaviors that SQLite/mocks cannot reproduce.
- `tests/test_wallet.py`, `tests/test_rls.py`, `tests/test_ledger_trigger.py`, `tests/test_jobs_api.py`, `tests/test_billing_idempotency.py`, `tests/test_reaper.py`, `tests/test_migrations.py`, `tests/test_queue_roundtrip.py`.
- `requirements-dev.txt` — `pytest`, `pytest-asyncio`, `httpx` (have it), `fakeredis`, `arq` (move from commented to required once queue ships).

**What CI runs:** `lint` + `typecheck` + `test (unit+db+api+queue)` + `migration-smoke` + `build` on every PR; `paid` and `restore-drill` on schedule. Gate merge on the non-paid suite.

---

### Sequenced build order (each step independently shippable, verified by real-op)

1. **Advisory-lock in `alembic/env.py`** + `migration-smoke` CI job → verify: 3 concurrent `alembic upgrade head` serialize cleanly.
2. **pytest real-op suite + `conftest.py`** + CI `test` job → verify: ledger/RLS/wallet/idempotency tests pass against real pg. (Closes the ZERO-tests P0.)
3. **Arq worker** (`app_api/arq_worker.py` + `app_api/queue.py`, wire `executor.submit_job` queue branch) + Upstash + Redis rate limiter → verify: job survives an API redeploy (no longer SIGTERM-killed mid-render).
4. **R2 storage backend** (`app_api/storage.py`, wire the unused `STORAGE_*` knobs + `media.py`) → verify: video persists across deploy, served via signed CDN URL.
5. **metrics.py + Sentry + OTel + alerts** → verify: spend + job-fail + availability alerts fire on injected faults.
6. **render.yaml + terraform + backup/restore-drill crons** → verify: monthly restore drill reconciles the ledger.


---

# Phụ lục A — Bảng dữ liệu mới (hợp nhất)

| Bảng | Tenant/RLS | Khoá chính/cột chính | Mục đích | Miền |
|---|---|---|---|---|
| `plans` | 🌐 global | code PK, monthly_credit_grant, max_concurrent_jobs, max_resolution, watermark_fr | Subscription tier catalog backing orgs.plan_code; feeds plan-aware cla | data |
| `subscriptions` | 🔒 tenant+RLS | id PK, org_id FK, plan_code FK plans, status, current_period_end, last_grant_at; | Per-org active subscription + billing period; renewal cron grants mont | data |
| `entitlements` | 🔒 tenant+RLS | id PK, org_id FK, key, value jsonb, expires_at; unique(org_id,key) | Per-org overrides/add-ons over plan defaults without cloning plans. | data |
| `credit_packs` | 🌐 global | id PK, code unique, amount_vnd, credits, bonus_credits, is_active | Backs reserved payments.credit_pack_id; replaces hardcoded PACKS dict  | data |
| `invoices` | 🔒 tenant+RLS | id PK, org_id FK RESTRICT, invoice_no unique (global seq), payment_id FK, vat_ra | VN VAT hoa-don per top-up/subscription; financial record (RESTRICT del | data |
| `invoice_lines` | 🔒 tenant+RLS | id BigInt Identity PK, org_id FK, invoice_id FK CASCADE, amount_vnd, credit_pack | Line items for invoices; org_id local for RLS policy. | data |
| `refunds` | 🔒 tenant+RLS | id PK, org_id FK RESTRICT, payment_id FK RESTRICT, amount_vnd, credits_reversed, | Money-side refund tracking linked to ledger REFUND credit reversal. | data |
| `coupons` | 🌐 global | id PK, code CITEXT unique, kind, value, max_redemptions, redeemed_count, expires | Platform-issued promo code catalog (percent/fixed/bonus credits). | data |
| `coupon_redemptions` | 🔒 tenant+RLS | id PK, org_id FK, coupon_id FK RESTRICT, payment_id FK, unique(coupon_id,org_id) | Per-org redemption record enforcing max_per_org; audits discounts/bonu | data |
| `webhook_events` | 🌐 global | id PK, provider, dedup_key, unique(provider,dedup_key), payment_id FK, signature | GLOBAL (IPN arrives pre-auth) IPN idempotency net + audit; unique dedu | data |
| `templates` | 🔒 tenant+RLS | id PK, org_id FK CASCADE (nullable=global), category, spec jsonb, is_public; nul | Backs reserved jobs.template_id; reusable video recipes, org-owned + c | data |
| `kol_personas` | 🔒 tenant+RLS | id PK, org_id FK CASCADE (nullable=global), voice_id, voice_style, appearance_pr | Backs reserved jobs.kol_persona_id; Vietnamese KOL/voice presets (edge | data |
| `brand_kits` | 🔒 tenant+RLS | id PK, org_id FK CASCADE NOT NULL, logo_url, colors, watermark_url, partial-uniq | Backs reserved jobs.brand_kit_id; org-only brand assets. | data |
| `media_assets` | 🔒 tenant+RLS | id PK, org_id FK CASCADE, job_id FK SET NULL, kind, storage_backend, object_key, | Normalized storage records (R2/S3/local) for all files; GC + lifecycle | data |
| `asset_versions` | 🔒 tenant+RLS | id BigInt Identity PK, org_id FK, media_asset_id FK CASCADE, version_no, variant | Immutable asset version history (no-watermark variant, transcodes, re- | data |
| `audit_log` | 🌐 global | id BigInt Identity PK, org_id (plain no FK), actor_user_id (plain), action, reso | GLOBAL immutable security/compliance trail surviving org/user deletion | data |
| `notifications` | 🔒 tenant+RLS | id PK, org_id FK CASCADE, user_id FK CASCADE (null=org-wide), type, read_at; par | In-app notifications (job ready, payment, low credits). | data |
| `notification_prefs` | 🔒 tenant+RLS | id PK, org_id FK, user_id FK, email_enabled, inapp_enabled, event_prefs jsonb; u | Per-user notification channel/event preferences. | data |
| `api_keys` | 🌐 global | id PK, org_id (column, no RLS), key_prefix, key_hash unique, scopes jsonb, revok | GLOBAL like auth_tokens (consulted pre-tenant-resolution to ESTABLISH  | data |
| `analytics_events` | 🔒 tenant+RLS | id BigInt Identity PK, org_id FK CASCADE, user_id (plain), event_name, propertie | High-volume product analytics; created_at-leading index for future mon | data |
| `usage_rollup` | 🔒 tenant+RLS | id BigInt Identity PK, org_id FK, day, jobs_created, credits_spent, seconds_rend | Pre-aggregated daily usage for dashboard charts without scanning ledge | data |
| `support_tickets` | 🔒 tenant+RLS | id PK, org_id FK CASCADE, created_by FK, subject, status, job_id FK SET NULL | Customer support tickets, optionally tied to a job. | data |
| `support_messages` | 🔒 tenant+RLS | id PK, org_id FK, ticket_id FK CASCADE, author_user_id FK, is_staff, body, attac | Threaded messages on a support ticket. | data |
| `data_subject_requests` | 🌐 global | id PK, org_id (plain), user_id (plain), subject_email CITEXT, request_type, stat | GLOBAL PDPD (NĐ 13/2023)/GDPR export/delete requests surviving org del | data |
| `moderation_events` | 🔒 tenant+RLS | id BigInt Identity PK, org_id FK CASCADE, subject_type/subject_id (polymorphic), | Append audit trail behind videos.moderation_status; per-scan decisions | data |
| `provider_budget_ledger` | 🌐 global | date (text, local-tz day), provider (text), spent_usd (numeric12,4), budget_usd  | Platform-wide daily USD spend fuse for video providers (VIDEO_DAILY_BU | pipeline |
| `job_retries` | 🔒 tenant+RLS | id (bigint identity), org_id (uuid, RLS), job_id (uuid FK->jobs CASCADE), attemp | Dead-letter / retry audit trail. One row per failed render attempt (Ar | pipeline |
| `billing_profiles` | 🔒 tenant+RLS | org_id (PK+FK+RLS), legal_name, tax_code (MST), address, email, invoice_default | Vietnamese VAT buyer details required before issuing a company e-invoi | billing |
| `referrals` | 🔒 tenant+RLS | org_id (FK+RLS, referrer), code (UNIQUE), referred_org_id, referrer_bonus, refer | Referral program tied to BONUS ledger; qualifies only on referee's fir | billing |
| `vv_templates` | 🔒 tenant+RLS | id uuid pk, org_id uuid (RLS), source_template_id uuid null (remix lineage), sys | Backs jobs.template_id. Org-owned editable storyboard/remix. System ca | features |
| `vv_kol_personas` | 🔒 tenant+RLS | id uuid pk, org_id uuid (RLS), seed_kol_id int null (origin in core.kol_characte | Backs jobs.kol_persona_id. Per-org avatar/face gallery + voice profile | features |
| `vv_brand_kits` | 🔒 tenant+RLS | id uuid pk, org_id uuid (RLS), name text, logo_url text, palette jsonb (hex[]),  | Backs jobs.brand_kit_id. Logo/colors/watermark/affiliate-disclosure ap | features |
| `vv_series` | 🔒 tenant+RLS | id uuid pk, org_id uuid (RLS), brief text, axes jsonb (hook[]/format_key[]/kol_p | Auto-series 1-brief->N-variants A/B parent. Child jobs reference serie | features |
| `vv_shares` | 🔒 tenant+RLS | id uuid pk, org_id uuid (RLS), video_id uuid fk->videos, slug citext unique-glob | Public share/embed page for a video. Reused signed media URLs (media.p | features |
| `vv_affiliate_links` | 🔒 tenant+RLS | id uuid pk, org_id uuid (RLS), code citext unique-global, target_url text, netwo | Tracked short link backing /r/{code}. sub_id is the join key for conve | features |
| `vv_link_clicks` | 🔒 tenant+RLS | id bigint identity pk, org_id uuid (RLS), link_id uuid fk->vv_affiliate_links, s | Append-only click stream for revenue attribution + A/B CTR. Org-scoped | features |
| `vv_landing_pages` | 🔒 tenant+RLS | id uuid pk, org_id uuid (RLS), slug citext unique-global, video_id uuid fk, bran | Generated affiliate landing page (video hero + CTA + disclosure). Serv | features |
| `audit_logs` | 🔒 tenant+RLS | id (bigint identity PK), org_id (FK orgs RESTRICT), actor_user_id, actor_role, a | Tamper-evident (hash-chained) append-only audit of security-relevant s | security |
| `platform_admins` | 🌐 global | user_id (FK users PK), level (support/admin/superadmin), granted_by, created_at | Global cross-org platform staff identity; seeded only via CLI, never v | security |
| `deletion_requests` | 🌐 global | id (uuid PK), user_id, requested_at, purge_after, completed_at, scope jsonb | PDPD/GDPR erasure proof: records soft-delete + grace window + hard-pur | security |
| `video_shares` | 🔒 tenant+RLS | id uuid pk, org_id uuid (RLS), job_id uuid fk->jobs, share_token text unique (ra | Public revocable share tokens for the /share/[token] page so a video c | frontend |

_41 bảng mới (đã khử trùng)._


---

# Phụ lục B — API endpoint mới


**Job Pipeline, Queue & Media Infra**

- `GET /v1/jobs/{job_id}/events/stream` — SSE stream tailing job_events for live render progress (replaces chatty 1-3s polling of GET /v1/jobs/{id}). Authed, tenant-scoped, emits each new job_event as it lands, closes with event:done on terminal status. Poll-of-Postgres backed; optional Redis pub/sub fast-path.

**Billing, Payments & Subscriptions**

- `GET /v1/plans` — List active subscription plans from the plans table (data-driven, replaces hardcoded)
- `GET /v1/subscription` — Current org subscription: plan, status, period window, next monthly grant date
- `POST /v1/subscription` — Subscribe/upgrade/downgrade: creates proration payment, sets plan, grants prorated credits
- `POST /v1/subscription/cancel` — Set cancel_at_period_end=true (keep access until period end)
- `POST /v1/subscription/resume` — Clear the cancel-at-period-end flag before period end
- `GET /v1/billing/ipn/{provider}` — Generic IPN receiver (GET+POST): webhook_events idempotency -> confirm_payment with amount reconciliation -> provider-shaped ack; replaces VNPay-only /ipn/vnpay
- `POST /v1/billing/ipn/{provider}` — Same generic IPN handler for providers that POST (MoMo, ZaloPay, VietQR/Napas)
- `GET /v1/billing/return/{provider}` — Browser redirect landing per provider (display-only; IPN remains source of truth)
- `POST /v1/billing/payments/{id}/refund` — Owner-only money refund: validate balance can absorb clawback, ADJUST ledger, call gateway refund, set payments.status=REFUNDED
- `GET /v1/billing/refunds` — List refund records for the org
- `GET /v1/billing/profile` — Read VAT billing profile (tax code, legal name, address)
- `POST /v1/billing/profile` — Upsert VAT billing profile for company e-invoices
- `GET /v1/invoices` — List org invoices
- `GET /v1/invoices/{id}` — Invoice detail + signed PDF URL + e-invoice lookup code
- `POST /v1/billing/coupon/redeem` — Redeem a CREDIT coupon -> BONUS ledger entry (concurrency-safe lock-then-check)
- `GET /v1/referral` — Org referral code + referral stats (pending/qualified/paid)

**Feature Modules**

- `GET /v1/templates` — List templates visible to org: system catalog (from core.prompt_templates) + org-owned vv_templates. Filters: category, format_key, q. Read-only catalog merge.
- `POST /v1/templates` — Create/save a tenant template (org_id, RLS). Body = storyboard JSON + default format_key/seconds/aspect/scene_prompt/structure_reference.
- `POST /v1/templates/{id}/remix` — Clone a system OR org template into a NEW editable vv_templates row for this org (copy-on-write), returning the new template id for the wizard.
- `PATCH /v1/templates/{id}` — Edit an org-owned template (rename, tweak storyboard/overlay_policy). 403 on system rows.
- `DELETE /v1/templates/{id}` — Delete an org-owned template (jobs.template_id SET NULL via FK).
- `GET /v1/kol-personas` — List personas: seed/global kol_characters + org-owned vv_kol_personas (custom faces, saved voice profiles).
- `POST /v1/kol-personas` — Create a tenant persona from a global KOL (copy character_sheet/voice_id) or from scratch (text persona). org_id + RLS.
- `POST /v1/kol-personas/{id}/face` — Attach custom face: presigned upload + REQUIRES consent flag. Sets face_status=PENDING_REVIEW; external face-swap not yet wired (stub).
- `POST /v1/kol-personas/{id}/voice-clone` — Request a cloned Vietnamese voice from an uploaded sample. Sets voice_clone_status=REQUESTED; needs external clone provider (stub).
- `GET /v1/brand-kits` — List org brand kits (logo, palette, watermark, affiliate disclosure text, default CTA).
- `POST /v1/brand-kits` — Create a brand kit (logo upload ref, hex colors, watermark policy, disclosure_text). org_id + RLS.
- `PATCH /v1/brand-kits/{id}` — Update brand kit; set is_default to apply automatically to new jobs.
- `POST /v1/series` — Auto-series: 1 brief -> N variants. Body = brief + variant axes (hook[], format_key[], kol_persona_id[]) + count. Server expands to N child jobs under one HOLD batch.
- `GET /v1/series/{id}` — Series detail: child jobs, per-variant status, aggregate spend, and A/B metrics (views/CTR/conversions) joined from share + click tables.
- `GET /v1/tools` — All-tools hub manifest: each tool -> {mode, default params, required inputs, credit estimate hint} mapping features.ts keys to engine pipelines.
- `POST /v1/tools/{tool_key}/run` — Thin alias over POST /v1/jobs that injects the tool's preset (mode/scene_prompt/format_key) so clean-plate/product-hero/recap/long-narrative reuse the job path.
- `POST /v1/videos/{video_id}/share` — Create a public share page: mint slug + signed-URL-backed public view; optional embed. Writes vv_shares (org_id, RLS) but exposes a tokenless public read.
- `GET /s/{slug}` — PUBLIC share/watch page data (no auth): resolves slug -> signed media URL + brand-kit disclosure + affiliate CTA. SECURITY DEFINER read, RLS-bypassing by slug only.
- `GET /embed/{slug}` — PUBLIC oEmbed/iframe payload for the share (poster + signed mp4 + tracked CTA).
- `POST /v1/affiliate-links` — Create a tracked short link (target URL + network + optional product). Returns code for /r/{code}. org_id + RLS.
- `GET /r/{code}` — PUBLIC redirector: 302 to target, append-only insert into vv_link_clicks (ts, ua, ref, geo, video_id, share_slug). No auth.
- `POST /v1/affiliate-links/conversions` — Ingest conversions (webhook or CSV) from Shopee/Lazada/TikTok affiliate; matches sub_id back to link/job for revenue attribution.
- `POST /v1/landing-pages` — Generate a landing page from a video + brand kit + affiliate link (template-based). Writes vv_landing_pages; served at /p/{slug}.
- `GET /v1/onboarding` — Onboarding state machine: returns next step (verify email, pick persona, first brief) + first-video CTA. Reads org.settings.onboarding JSON.

**Security, Multi-tenancy, RBAC & Compliance**

- `POST /v1/admin/orgs/{id}/suspend` — Platform-admin suspends an abusive org (audited cross-org action)
- `GET /v1/admin/orgs` — Platform-admin org list via narrow SECURITY DEFINER summary (counts only, no raw PII)
- `GET /v1/admin/abuse/signals` — Abuse dashboard: signup velocity, disposable-email flags, farming signals
- `POST /v1/admin/moderation/{video_id}/decision` — Human moderation override; writes moderation_event + audit_log, updates videos.moderation_status
- `GET /v1/admin/audit/verify/{org_id}` — Re-walk an org's audit hash chain and report first broken link (tamper detection)
- `POST /v1/me/export` — PDPD/GDPR self-service data export; Arq job assembles ZIP, signed R2 URL TTL 24h, 1/day
- `DELETE /v1/me` — Account erasure: phase-1 soft-delete+anonymize+token-revoke, phase-2 cron hard-purge after grace, financial rows preserved PII-stripped
- `PATCH /v1/me/consent` — Granular withdrawable marketing consent toggle (PDPD requirement)

**Frontend Architecture & Screen Map**

- `POST /v1/jobs/{id}/share` — Mint a public revocable share_token for a READY job; inserts into video_shares. Returns {share_token}. Called from /app/v/[id] Share action.
- `DELETE /v1/jobs/{id}/share` — Revoke the active share token (sets revoked=true).
- `GET /v1/share/{token}` — Public (no-auth) resolver: token -> {video signed-url, poster, title, made_with_badge}. Used by SSR generateMetadata + the share page. Reads video_shares by token via a service path that does not require vietvid.current_org.
- `GET /v1/templates` — List system (org_id NULL) + current-org templates for the gallery. Query ?scope=system|org.
- `POST /v1/templates` — Create an org template ('Save as template' from a finished job).
- `GET /v1/kols` — List org KOL personas for the gallery.
- `POST /v1/kols` — Create a KOL persona (face ref + voice + mandatory consent_at).
- `PATCH /v1/kols/{id}` — Update a KOL persona; DELETE /v1/kols/{id} to remove.
- `GET /v1/brand-kits` — List org brand kits; POST creates, PATCH /{id} updates, DELETE /{id} removes.
- `GET /v1/billing/payments` — Paginated payment/invoice history for /app/billing/invoices table.
- `GET /v1/billing/payments/{id}/receipt` — Download a receipt (PDF/HTML) for one payment.
- `GET /v1/analytics/usage` — Aggregated usage/spend/render-time metrics for /app/analytics. Query ?range=7d|30d|90d.
- `PATCH /v1/auth/me` — EXTEND existing endpoint to accept onboarded:boolean so /onboarding can mark completion (no new route).
- `GET /v1/admin/overview` — Cross-tenant KPI summary (MRR, active orgs, jobs/day, refund rate) for /admin. Requires role=admin + RLS-bypass service path.
- `GET /v1/admin/jobs` — Global job monitor list (filter by status) for /admin/jobs; POST /v1/admin/jobs/{id}/retry and /refund for triage actions.

**Infra, DevOps, Deployment & Observability**

- `GET /metrics` — Prometheus scrape endpoint (HTTP/job/cost/wallet/queue metrics). Bearer/internal-gated in prod.
- `GET /health/live` — Liveness probe (process up, no DB dependency) to complement existing /health/ready DB-liveness — lets the load balancer distinguish process-dead from DB-degraded.

---

# Phụ lục C — File/module mới


**Data Model & Migrations**
- `c:\Users\NTD\Desktop\vietvid\alembic\versions\20260628_0004_plans_billing.py`
- `c:\Users\NTD\Desktop\vietvid\alembic\versions\20260628_0005_invoicing_promos.py`
- `c:\Users\NTD\Desktop\vietvid\alembic\versions\20260628_0006_creative_assets.py`
- `c:\Users\NTD\Desktop\vietvid\alembic\versions\20260628_0007_jobs_asset_fks.py`
- `c:\Users\NTD\Desktop\vietvid\alembic\versions\20260628_0008_media_storage.py`
- `c:\Users\NTD\Desktop\vietvid\alembic\versions\20260628_0009_audit_notif_apikeys.py`
- `c:\Users\NTD\Desktop\vietvid\alembic\versions\20260628_0010_analytics_support.py`
- `c:\Users\NTD\Desktop\vietvid\alembic\versions\20260628_0011_compliance_moderation.py`

**Job Pipeline, Queue & Media Infra**
- `app_api/queue.py`
- `app_api/queue_worker.py`
- `app_api/concurrency.py`
- `app_api/storage.py`
- `app_api/budget.py`
- `Dockerfile.worker`
- `docker-compose.yml`
- `bin/vietvid-storage-init`
- `bin/vietvid-dlq-report`
- `alembic/versions/20260627_0004_queue_storage_budget.py`

**Billing, Payments & Subscriptions**
- `app_api/payments/__init__.py`
- `app_api/payments/base.py`
- `app_api/payments/vnpay.py`
- `app_api/payments/momo.py`
- `app_api/payments/zalopay.py`
- `app_api/payments/vietqr.py`
- `app_api/payments/dev.py`
- `app_api/subscriptions.py`
- `app_api/invoices.py`
- `app_api/einvoice.py`
- `app_api/promo.py`
- `app_api/billing_reaper.py`
- `app_api/routers/subscriptions.py`
- `app_api/routers/invoices.py`
- `app_api/routers/promo.py`
- `alembic/versions/20260627_0004_billing_catalog.py`
- `alembic/versions/20260627_0005_subscriptions_invoices.py`
- `alembic/versions/20260627_0006_promo.py`
- `apps/web/src/app/app/subscription/page.tsx`
- `apps/web/src/app/app/invoices/page.tsx`

**Feature Modules**
- `app_api/routers/templates.py`
- `app_api/routers/personas.py`
- `app_api/routers/brandkits.py`
- `app_api/routers/series.py`
- `app_api/routers/tools.py`
- `app_api/routers/share.py`
- `app_api/routers/affiliate.py`
- `app_api/routers/landing.py`
- `app_api/routers/onboarding.py`
- `app_api/features/__init__.py`
- `app_api/features/resolve.py`
- `app_api/features/tools_manifest.py`
- `app_api/features/series_expand.py`
- `app_api/features/shortlink.py`
- `app_api/features/attribution.py`
- `app_api/features/landing_render.py`
- `app_api/feature_models.py`
- `alembic/versions/20260627_0004_feature_tables.py`
- `alembic/versions/20260627_0005_back_reserved_fks.py`
- `alembic/versions/20260627_0006_affiliate_attribution.py`
- `apps/web/src/app/app/templates/page.tsx`
- `apps/web/src/app/app/templates/[id]/page.tsx`
- `apps/web/src/app/app/personas/page.tsx`
- `apps/web/src/app/app/personas/[id]/page.tsx`
- `apps/web/src/app/app/brand-kits/page.tsx`
- `apps/web/src/app/app/series/page.tsx`
- `apps/web/src/app/app/series/[id]/page.tsx`
- `apps/web/src/app/app/tools/page.tsx`
- `apps/web/src/app/app/links/page.tsx`
- `apps/web/src/app/app/onboarding/page.tsx`
- `apps/web/src/app/s/[slug]/page.tsx`
- `apps/web/src/app/p/[slug]/page.tsx`
- `apps/web/src/lib/tools.ts`
- `apps/web/src/lib/api/features.ts`

**Security, Multi-tenancy, RBAC & Compliance**
- `app_api/permissions.py`
- `app_api/audit.py`
- `app_api/moderation.py`
- `app_api/abuse.py`
- `app_api/ratelimit_redis.py`
- `app_api/routers/admin.py`
- `app_api/routers/me.py`
- `alembic/helpers.py`
- `scripts/grant_platform_admin.py`
- `tests/test_rls_coverage.py`
- `tests/test_permissions.py`
- `alembic/versions/20260701_0004_rbac_audit.py`
- `alembic/versions/20260702_0005_pdpd_consent.py`

**Frontend Architecture & Screen Map**
- `apps/web/src/lib/query/keys.ts`
- `apps/web/src/lib/query/use-job-stream.ts`
- `apps/web/src/lib/format.ts`
- `apps/web/src/lib/forms/validate.ts`
- `apps/web/src/store/timeline.ts`
- `apps/web/src/components/ui/modal.tsx`
- `apps/web/src/components/ui/drawer.tsx`
- `apps/web/src/components/ui/toast.tsx`
- `apps/web/src/components/ui/table.tsx`
- `apps/web/src/components/ui/empty-state.tsx`
- `apps/web/src/components/ui/error-state.tsx`
- `apps/web/src/components/ui/tabs.tsx`
- `apps/web/src/components/ui/select.tsx`
- `apps/web/src/components/ui/tooltip.tsx`
- `apps/web/src/components/ui/switch.tsx`
- `apps/web/src/components/ui/slider.tsx`
- `apps/web/src/components/ui/avatar.tsx`
- `apps/web/src/components/ui/stat.tsx`
- `apps/web/src/components/ui/progress.tsx`
- `apps/web/src/components/ui/query-boundary.tsx`
- `apps/web/src/components/admin/admin-shell.tsx`
- `apps/web/src/app/share/[token]/page.tsx`
- `apps/web/src/app/(auth)/onboarding/page.tsx`
- `apps/web/src/app/(auth)/register/page.tsx`
- `apps/web/src/app/(marketing)/features/[slug]/page.tsx`
- `apps/web/src/app/(marketing)/templates/page.tsx`
- `apps/web/src/app/app/templates/page.tsx`
- `apps/web/src/app/app/kols/page.tsx`
- `apps/web/src/app/app/kols/[id]/page.tsx`
- `apps/web/src/app/app/brand-kits/page.tsx`
- `apps/web/src/app/app/brand-kits/[id]/page.tsx`
- `apps/web/src/app/app/projects/[id]/editor/page.tsx`
- `apps/web/src/app/app/analytics/page.tsx`
- `apps/web/src/app/app/billing/invoices/page.tsx`
- `apps/web/src/app/admin/layout.tsx`
- `apps/web/src/app/admin/page.tsx`
- `apps/web/src/app/admin/orgs/page.tsx`
- `apps/web/src/app/admin/orgs/[id]/page.tsx`
- `apps/web/src/app/admin/jobs/page.tsx`
- `apps/web/src/app/admin/payments/page.tsx`
- `apps/web/src/app/admin/users/page.tsx`
- `apps/web/src/app/sitemap.ts`
- `apps/web/src/app/robots.ts`

**Infra, DevOps, Deployment & Observability**
- `app_api/metrics.py`
- `app_api/queue.py`
- `app_api/arq_worker.py`
- `app_api/storage.py`
- `scripts/backup_ledger.py`
- `scripts/restore_drill.py`
- `scripts/check_env.py`
- `pyproject.toml`
- `requirements-dev.txt`
- `tests/conftest.py`
- `tests/test_wallet.py`
- `tests/test_rls.py`
- `tests/test_ledger_trigger.py`
- `tests/test_jobs_api.py`
- `tests/test_billing_idempotency.py`
- `tests/test_reaper.py`
- `tests/test_migrations.py`
- `tests/test_queue_roundtrip.py`
- `.github/workflows/ci.yml`
- `.github/workflows/restore-drill.yml`
- `render.yaml`
- `infra/terraform/main.tf`
- `infra/terraform/r2.tf`
- `infra/terraform/cloudflare.tf`

---

# Phụ lục D — Quyết định kiến trúc


### Data Model & Migrations
- **D1 — Abandon Base.metadata.create_all / autogen for all M2 migrations; use explicit op.create_table + raw op.execute for tables, indexes, RLS, triggers, and seeds.** — Baseline 0001 used create_all, and env.py targets Base.metadata, so any autogenerate run after adding M2 models would emit one undifferentiated CREATE blob with NO FORCE-RLS, NO partial/WHERE indexes, NO append-only triggers, NO NOT VALID/VALIDATE FK adds, NO seed INSERTs, and unpredictable ordering. Autogen structurally cannot produce a correct migration for this schema. Explicit migrations keep RLS/index/trigger intent reviewable, matching how baseline already hand-wrote those for M1 tenant tables.
- **D2 — Add reserved FKs (payments.credit_pack_id; jobs.template_id/kol_persona_id/brand_kit_id) via ALTER ... ADD CONSTRAINT ... NOT VALID then VALIDATE CONSTRAINT, all ON DELETE SET NULL, in a migration AFTER the referenced table is created+seeded.** — NOT VALID skips the full-table ACCESS EXCLUSIVE scan-lock on add; VALIDATE then checks existing rows under a weaker lock. Existing NULLs pass. SET NULL preserves historical jobs/payments when a pack/template/persona/kit is later deleted (never destroy financial or job history). Ordering (pack created in 0004 → FK in 0005; assets in 0006 → FKs in 0007) guarantees the referenced rows exist.
- **D3 — orgs.plan_code becomes a soft reference to plans.code (seed plans first); keep it as Text, optionally add FK later.** — orgs is a GLOBAL table already populated with plan_code='free'. Seeding plans with code='free'/'pro'/'business' in 0004 makes the reference resolvable. A hard FK on orgs.plan_code is optional (orgs is global, low-churn) and can be added NOT VALID later; not forcing it now avoids touching the verified orgs table.
- **D4 — api_keys is GLOBAL (no RLS), carrying org_id as a plain column, consistent with auth_tokens and org_invitations.** — API-key verification resolves the org from the key hash BEFORE any tenant GUC is set, so the lookup must run outside RLS (session_scope). auth_tokens/org_invitations are global for exactly this 'consulted before tenant resolution' reason. Dashboard listing filters org_id explicitly in the router, which is already the codebase norm even on RLS tables.
- **D5 — audit_log, data_subject_requests, and webhook_events are GLOBAL with org_id/user_id as plain FK-less columns; audit_log gets an append-only trigger reusing the ledger_immutable pattern.** — Audit and compliance records must SURVIVE org/user deletion (a CASCADE would erase the very trail needed for forensics/legal). webhook_events records unauthenticated IPNs that have no GUC. RLS-scoping these would hide them once the tenant is gone. FK-less columns avoid cascade wipes; the immutable trigger mirrors the proven append-only ledger guard.
- **D6 — templates and kol_personas use a nullable org_id + relaxed RLS policy: USING (org_id IS NULL OR org_id = current GUC), strict org-only WITH CHECK; globals seeded before RLS is enabled on the table.** — Platform-curated templates/personas (org_id NULL) must be visible to every tenant while each org still sees only its own custom rows. The relaxed USING grants read of globals + own; the strict WITH CHECK prevents a tenant from writing global rows. Seeding globals before ENABLE RLS sidesteps the FORCE-RLS-applies-to-owner problem without needing SET LOCAL row_security=off.
- **D7 — Extract the RLS predicate string (org_id = nullif(current_setting('vietvid.current_org', true),'')::uuid) to a shared constant and reuse verbatim in every migration's RLS loop.** — Baseline already defines _RLS_USING inline; duplicating the literal across 8 migrations risks a typo that silently breaks fail-closed isolation. One source of truth (importable constant or copied _RLS_USING per migration) keeps the fail-closed semantics identical everywhere.
- **D8 — Keep TENANT_TABLES in models.py updated to the full final tenant set and add a CI/test invariant: every table with an org_id column is in TENANT_TABLES AND has RLS+FORCE enabled; run alembic autogen-as-check (no-op assertion) to catch model/migration drift.** — The create_all baseline means model-vs-DB drift is otherwise invisible. A test asserting RLS coverage prevents the catastrophic class of bug where a new tenant table ships without a policy (cross-tenant leak). autogen-as-check (never autogen-as-author) turns the abandoned autogen path into a drift detector.
- **D9 — Ship analytics_events and moderation_events non-partitioned now, but lead their indexes with created_at and keep BigInteger Identity PKs so monthly RANGE partitioning is a cheap later migration.** — Premature partitioning is the speculative flexibility CLAUDE.md warns against; volume isn't proven yet. But choosing created_at-leading indexes and append-only Identity PKs now makes the future PARTITION BY RANGE (created_at) conversion non-destructive, so we pay nothing today and keep the door open.

### Job Pipeline, Queue & Media Infra
- **Arq task is a thin async wrapper (asyncio.to_thread) around the existing sync worker.run_job; the render code is unchanged.** — run_job and render are already crash-safe (piapi_task_id stamping) and battle-tested. Arq only adds the durable envelope: ack-after-success, retry-with-backoff, dead-letter. Rewriting render as native-async would be a large, risky change for zero functional gain and would break the proven resume path.
- **Keep the reaper running in BOTH inline and queue mode as belt-and-suspenders, not just Arq's reclaim.** — Arq reclaim handles worker crash (task survives in Redis). But if Redis itself is wiped, the task is gone while the DB job is stuck RUNNING. The reaper's per-org RLS scan still catches that and refunds the HOLD. Two independent failure domains need two independent safety nets.
- **Storage upload happens in worker.run_job (app_api layer), not in render_service (engine layer).** — The engine is deliberately stateless and storage-agnostic (writes final.mp4 to workdir, returns local path). Pushing S3 knowledge into the engine would couple it to app_api infra and break the M0 stateless contract. The worker is the right seam: it already owns the local->DB handoff in step 3.
- **Per-tenant fairness via a Redis admission counter (cap in-flight per org), not a custom scheduler.** — Arq's max_jobs is global-only; one burst-org would starve others. A per-org INCR/DECR cap achieves weighted-fair-queueing-lite for free: an org at its cap can't pull more slots, so a different org's job runs next. Same shape as the proven legacy lane logic, generalized. A bespoke scheduler is overcomplicated for this.
- **HOLD stays HELD across retryable (system-fault) failures; only final-attempt complete_job or the reaper ever releases it.** — Releasing/re-holding on each retry opens a double-refund / double-charge window and races the ledger's append-only invariant. Keeping the HOLD pinned through the retry chain means credits are reserved exactly once for the whole attempt sequence, matching the existing ACID wallet semantics.
- **Provider-level fallback advances only on system/config faults, never on ProviderRejectedError (moderation).** — Moderation rejects are content problems; a different provider will reject the same content. Falling back wastes money and time. Only infra faults (5xx, network, not-configured) should try the next provider. Resume task_id is provider-specific so it is cleared on cross-provider fallback, kept on same-provider retry.
- **Daily budget ledger ported into the app_api Postgres as a GLOBAL table, reusing the proven SELECT...FOR UPDATE reserve algorithm.** — The legacy ledger.py lives in the old core.database monolith that app_api doesn't connect to. The budget fuse is platform-wide (founder's cost cap), not tenant data, so it's global/no-RLS. Reusing the exact reserve/settle/local-tz-day logic avoids re-deriving a concurrency-correct cost gate.
- **Workdir cleanup runs on terminal outcome only (not on retryable failure), plus a boot+periodic orphan sweeper.** — Confirmed unbounded /tmp growth: run_job never deletes vietvid_jobs/{job_id}. But deleting on a retryable fault would throw away the already-downloaded clip the resume path reuses. So rmtree only when terminal; a TTL sweeper in the existing reaper loop catches workdirs orphaned by SIGKILL.
- **SSE progress is Postgres-poll-backed; Redis pub/sub is an opt-in fast-path layered on top, never the source of truth.** — QueueSink writes job_events to Postgres from the worker process; the SSE endpoint lives in the API process. The durable record is already in Postgres. Pub/sub only cuts latency. Making it the source of truth would lose events on a Redis blip. Ship DB-poll-SSE first, enhance with pub/sub behind a flag.

### Billing, Payments & Subscriptions
- **Amount reconciliation lives in the billing.py orchestrator (confirm_payment), not in each adapter, and gates apply_topup** — Fixes the audit flag (VNPay IPN never checked vnp_Amount) once, uniformly, for every current and future gateway. apply_topup stays untouched so the proven FOR UPDATE + status-check idempotency is preserved; we only refuse to call it when paid_amount != amount_vnd, marking the payment FAILED and alerting.
- **All promotional/plan credit routes through existing BONUS/ADJUST/EXPIRE ledger kinds; no new ledger kind** — The CHECK constraint and frontend META map already cover TOPUP/HOLD/SETTLE/REFUND/ADJUST/EXPIRE/BONUS. Monthly grants and coupons = BONUS, money-refund clawback = ADJUST, carryover expiry = EXPIRE. Wallet invariants, append-only audit, and the wallet=ledger reconciliation cron all keep working with zero changes to the money core.
- **Add wallet.grant_for_period(period='YYYY-MM') keyed on ledger metadata->>'period' instead of reusing grant_once** — grant_once explicitly documents it is once-per-lifetime (correct for signup) and would block every monthly grant after the first. A period-keyed guard with the same lock-then-check concurrency pattern makes cron double-fires and manual re-runs idempotent without a new table.
- **orgs.plan_code stays as a denormalized cache of subscriptions.plan_code, synced on every status transition** — tenancy.org_plan_code and validate.validate_and_clamp already read orgs.plan_code. Keeping it as the live mirror means the entire job-creation clamp path needs no change; subscriptions become the source of truth while the read path stays stable.
- **Money refund is only allowed when wallet balance >= the payment's credits_granted; otherwise manual/partial** — ck_wallet_balance_nonneg forbids clawing credits below zero. Refusing full refund after the credits were spent is the honest constraint and is the primary defense against top-up-spend-refund fraud against the free-grant economy.
- **Referral and coupon credit gate on the referee's first PAID payment, not on signup** — With a 300-credit free grant, signup-triggered referral credit is an obvious self-referral farming vector. Qualifying on first SUCCEEDED payment ties the reward to real revenue and neutralizes the attack.
- **Each new tenant table gets its own ENABLE/FORCE/org_isolation RLS block in its migration, reusing the baseline _RLS_USING clause** — The baseline TENANT_TABLES loop only covers M1 tables. New tenant tables (subscriptions, invoices, refunds, webhook_events, billing_profiles, coupon_redemptions, referrals) must carry the same fail-closed nullif()-based policy or they would leak cross-tenant. Global catalog tables (plans, credit_packs, coupons) correctly get no RLS, matching users/orgs.
- **webhook_events table as an idempotency receiver keyed on (provider, provider_event_id) on top of the existing payments(provider, ext_ref) UNIQUE** — payments-UNIQUE de-dupes credit application but discards the raw callback. An explicit event log makes at-least-once gateway delivery safe to replay, gives support/fraud a full audit of tampered sigs and amount mismatches, and lets us return a cached ack without re-running confirm_payment.

### Feature Modules
- **Features resolve catalog rows into the existing job params JSONB / scene_prompt / structure_reference / format_key / kol fields; the engine (pipeline.run_job, build_job_spec) is NOT modified.** — build_job_spec already passes params straight through to JobSpec.from_dict, and pipeline.run_job already dispatches on params.mode and reads scene_prompt (ScenePreset) and structure_reference (PromptTemplate). Templates/KOL/brand-kit just need to WRITE those fields at job-create time. This reuses rendering instead of reinventing it and keeps the engine single-tenant and stateless.
- **Tenant-owned feature entities go in NEW app_api tables with org_id + RLS+FORCE (vv_templates, vv_kol_personas, vv_brand_kits, vv_series, vv_affiliate_links, vv_link_clicks, vv_landing_pages, vv_shares). The existing global core.models catalog (kol_characters, ad_formats, scene_presets, prompt_templates) is surfaced READ-ONLY as the system/seed library.** — The reserved FK columns jobs.template_id/kol_persona_id/brand_kit_id are UUIDs, but core.models uses int PKs and has no org_id. A user's saved template / custom face / brand kit is tenant data and must be RLS-isolated like jobs/videos. System defaults (6 seed KOLs, 9 formats, autovis templates) stay global and are copied-on-remix into a tenant row. This cleanly separates shared catalog from per-org assets without touching the verified RLS model.
- **Back the three reserved FKs now: add real FK constraints jobs.template_id -> vv_templates.id, jobs.kol_persona_id -> vv_kol_personas.id, jobs.brand_kit_id -> vv_brand_kits.id (all ON DELETE SET NULL), and payments.credit_pack_id -> vv_credit_packs.id (credit_packs is the billing domain's table; we only reference it).** — The columns already exist nullable with no FK (intentional M2 reservation). Adding FK + index now gives referential integrity and lets job detail join the persona/template/brand-kit that produced it. SET NULL (not CASCADE) so deleting a saved template never deletes historical jobs.
- **Custom-face upload, voice-clone, auto-post (TikTok/YT), and motion-copy are gated as external-API features and shipped as 'request + status' stubs, while remix, brand kits, auto-series, the all-tools hub, share pages, affiliate links, and landing pages are fully buildable now on the existing engine.** — Custom face = deepfake-consent + face-swap model (not in engine; engine deliberately text-describes faces to dodge moderation). Voice-clone needs a clone provider. Auto-post needs TikTok/YT OAuth + content API approval. Everything else maps onto generate_clean_plate / product_hero / long_narrative / film_recap / edge-tts / ffmpeg that already exist, plus signed media URLs that already exist.
- **Affiliate-link auto-attach + click tracking + revenue attribution is built as a first-class differentiator: a short-link redirector (GET /r/{code}) writes append-only vv_link_clicks, CTA tail overlay (compose/cta_tail.py exists) burns the short URL into the video, and a daily reconcile maps clicks+conversions back to the originating job/video/series.** — autovis stops at 'make the video.' VietVid closes the loop to revenue. The redirector and click table are pure-build (no external API). Conversion ingest is a thin webhook/CSV importer per network (Shopee/Lazada/TikTok affiliate) the user configures later. cta_tail.py already composes a CTA tail clip, so attaching the tracked URL reuses existing compose code.

### Security, Multi-tenancy, RBAC & Compliance
- **Roles are coarse buckets on memberships.role; permissions are a static code-side matrix (permissions.py), NOT a DB table for tenant roles** — Six fixed roles is a small closed set; a permission table adds a query per request and mutability nobody needs. Static matrix is unit-testable, fail-closed on unknown scope, zero-latency. A DB table IS used for platform_admins because that layer is mutable, audited, and cross-org.
- **NO BYPASSRLS / superuser DB role for the app; cross-org admin access uses per-org GUC iteration (like reaper) + narrow SECURITY DEFINER functions, every access audited** — A blanket RLS-bypass role is the single biggest tenancy footgun — one bug leaks every org. Per-org iteration keeps FORCE RLS intact and makes the bypass surface exactly two enumerable, audited mechanisms instead of an always-on flag.
- **audit_logs reuses the ledger append-only trigger + a per-org sha256 hash chain; retention via month-partition DROP, never row DELETE** — The ledger immutability pattern is already proven in 0001; reusing ledger_immutable() means one tested mechanism. Hash chain gives tamper-evidence without per-row signing keys. Partition drop is the only way to expire rows when DELETE is trigger-blocked.
- **Move FREE_GRANT_CREDITS from signup to first email-verify, and gate job:create + billing on email_verified** — 300 free credits per auto-created org is the real money leak. Granting only on verified email and blocking spend until verified collapses throwaway-email farming economics — a farmer must solve a real inbox per 300 credits — while preserving the free-grant-vs-min-hold invariant.
- **RLS coverage is enforced by a runtime CI test querying pg_class/pg_policy, not by a PR checklist alone** — A new tenant table added to models.py but forgotten in the RLS loop silently leaks cross-org. A catalog query that fails CI when any org_id table lacks ENABLE+FORCE+org_isolation makes the leak unshippable, removing reliance on human discipline.
- **Split media-signing secret (MEDIA_SIGNING_KEY) from DEV_JWT_SECRET, with dual-key rotation window** — media.py currently signs share URLs with the same secret that verifies auth JWTs — a media-secret leak would forge auth tokens. Distinct keys contain blast radius; PREV-key fallback allows rotation without breaking live share links.

### Frontend Architecture & Screen Map
- **Navigation stays mega-menu-driven (SiteHeader), not the unused shell/sidebar.tsx — admin gets its own admin-shell sidebar.** — The app layout (app/app/layout.tsx) already renders SiteHeader with the full feature mega-menu from lib/features.ts; components/shell/sidebar.tsx exists but is wired nowhere. Matching the live pattern avoids a confusing dual-nav. Admin is a genuinely separate surface, so it gets a distinct sidebar shell to prevent admin/tenant confusion.
- **New galleries seed the existing 5-step wizard via query params + new Zustand fields (templateId/kolPersonaId/brandKitId), not a new creation flow.** — store/wizard.ts and /app/create already handle ?feature= presets, and jobs already has reserved template_id/kol_persona_id/brand_kit_id FK columns. Mirroring the proven preset path reuses the entire wizard + estimate + HOLD pipeline instead of forking it.
- **Public share page is a server component at /share/[token] using a revocable token + video_shares table, separate from the auth-gated /app/v/[id].** — OG/SEO needs SSR (current detail page is client-only and auth-gated). A random revocable token avoids leaking job/org ids and lets the media.py HMAC signer stay the auth boundary. This is the growth loop autovis-style products rely on.
- **No optimistic updates on wallet/ledger/topup/job-create; optimistic only on list mutations (delete/cancel/rename).** — The append-only ledger is the source of truth and credit holds are money-adjacent — guessing a balance client-side risks showing wrong credits. Existing mutations.ts already invalidates wallet/ledger from server responses; keep that and only add optimism where rollback is cheap and non-financial.
- **Centralize query keys in lib/query/keys.ts with an admin namespace, and standardize the loading/error/empty triple via a QueryBoundary component.** — Keys are currently inline arrays scattered across hooks.ts/mutations.ts; as 15+ new screens land, a key factory prevents invalidation drift and the admin prefix guarantees cross-tenant admin caches never collide with tenant caches. QueryBoundary stops every screen re-implementing the dashboard's hand-rolled triple-branch.
- **Extend withRefresh to also self-heal Supabase-mode 401s and emit a global vietvid:unauthorized event on hard failure.** — client.ts:withRefresh today only retries in dev mode; a Supabase access-token expiry silently fails until the next AuthGate mount. A global unauthorized event gives one consistent redirect-to-login-with-next path across both auth modes.

### Infra, DevOps, Deployment & Observability
- **Fix the multi-instance migrate race with a Postgres session advisory lock (pg_advisory_lock) inside alembic/env.py run_migrations_online(), not by changing the deploy choreography to a separate one-shot migrate job.** — The audit flags N Render replicas racing `alembic upgrade head` from the container CMD. pg_advisory_lock is the Layer-1 built-in (same pattern Django/Rails ship); it serializes concurrent boots with zero external coordination, the losers no-op on head-is-current. Keeping it in env.py means it works identically in CI, local, and prod, and is testable via a concurrency smoke test. A separate migrate job would still need a lock and adds deploy-ordering fragility.
- **Split API and worker into two Render services from ONE Docker image, differing only by CMD; only the API container runs migrations.** — The Dockerfile already builds a single backend image with ffmpeg/opencv baked in. A 90s render in a FastAPI BackgroundTask starves request handling and dies on every deploy SIGTERM (the inline executor's core flaw). Same artifact + CMD override is the cheapest correct split — independent RAM/CPU budgets, independent scaling — without a second build. Making only the API migrate avoids two services both driving migrations.
- **Real Postgres + real Redis in the pytest real-op tiers (db/api/queue), never SQLite or mocks for those tiers.** — The two highest-value invariants — FORCE RLS tenant isolation via the vietvid.current_org GUC, and the append-only ledger trigger — are Postgres-specific behaviors that SQLite and mocks cannot reproduce. Testing them against anything but real Postgres would give false green. This directly closes the ZERO-tests P0 for the financial source of truth.
- **No new tables for cost model, spend tracking, or backups — reuse existing columns (jobs.actual_cost_usd/provider_*, job_events.cost_usd/provider, ledger_entries.usd_cost/fx_usd_vnd) and pricing.usd_to_credits.** — The M1 schema already snapshots per-render, per-stage, and per-credit-movement USD cost with provider attribution and FX. Unit economics and per-tenant cost roll straight out of aggregation queries. Adding cost tables would duplicate the source of truth and risk drift. Surface via an admin reporting view (org_cost_summary), not new tenant tables.
- **Make the ledger restore drill a scheduled, scripted, asserted reconciliation job (scripts/restore_drill.py + monthly CI), not just 'enable PITR'.** — Backups you never restore are theater. The credit ledger is real money; a monthly drill that branches Neon from PITR and asserts wallet==SUM(delta_credits), balance_after consistency, no orphaned HOLDs, and TOPUP/payment reconciliation proves both that backups work AND that the ACID wallet + append-only trigger held over real history. It doubles as the reconciliation test a money system must have.
- **Replace the in-process rate limiter with a Redis-backed limiter once multi-instance, reusing the existing config knobs.** — ratelimit.py is an explicit in-proc dict (the file even says 'Prod đa-instance nên chuyển sang Redis'). With N API replicas each instance under-counts by 1/N, defeating the brute-force/credit-farm protection. Upstash Redis is already in the topology for the queue; INCR+EXPIRE keeps the N/window semantics with the same config keys.

---

# Phụ lục E — Câu hỏi cần chốt (quyết định sản phẩm)


### Data Model & Migrations
- Plans & pricing: confirm the actual tier lineup (free/pro/business/enterprise) and their VND prices, monthly_credit_grant, max_concurrent_jobs, max_resolution, max_seconds, and watermark_free — these seed values drive real entitlement clamps and revenue.
- VN e-invoicing: which hóa đơn điện tử provider (Viettel, MISA, VNPT) will invoices integrate with, and is invoice_no expected to be issuer-wide monotonic (global sequence) or per-period? This affects the sequence design and the meta payload shape.
- Subscriptions in VN context: is recurring auto-charge actually available via VNPay/MoMo, or are subscriptions effectively manual-renew (invoice + re-topup)? Determines whether provider_sub_ref/cancel_at_period_end carry real semantics or are vestigial.
- DSR/PDPD retention: what is the legal retention window for audit_log and for completed data_subject_requests, and does a DELETE request require hard-deleting media_assets/videos object storage (R2 lifecycle) vs soft-delete? This shapes the deletion pipeline and GC.
- API keys scope: is programmatic API access (api_keys) actually in scope for the first paid launch, or deferred? If deferred, drop it from 0009 to avoid building auth surface no plan sells yet.

### Job Pipeline, Queue & Media Infra
- Provider fallback chain: is there a second real video provider available (e.g. Kling via PiAPI, or a non-PiAPI vendor) to fall back to, or is the chain effectively seedance-only-with-retry until a second vendor is contracted? This determines whether route_video_chain ships with real alternates or just same-provider retry on day one.
- VIDEO_DAILY_BUDGET default: is the $5/day registry default the intended production cap, or a dev placeholder? At ~$1.21/render that's ~4 paid renders/day platform-wide, which would QUEUE_BUDGET nearly every job in production. Need the real daily spend ceiling tied to revenue economics.
- Preview/video retention policy: should free/watermarked preview videos auto-expire (VIDEO_PREVIEW_TTL_DAYS) to bound R2 storage cost, and at what TTL? Paid (watermark-removed) videos kept forever is assumed but should be confirmed against the billing/plan model.
- Per-plan in-flight concurrency caps (free=1, pro=3, business=6 assumed): confirm these against the actual plan tiers and what concurrency each paid tier promises, since this is a user-visible throughput guarantee.

### Billing, Payments & Subscriptions
- Plan pricing and credit allotments: confirm VND prices and monthly_credits for Free/Creator/Pro/Agency, and the annual discount (e.g. 2 months free) — these are product/pricing calls, not engineering.
- Carryover policy per plan: how many unused plan-granted credits roll over (carryover_cap_credits) vs expire each cycle? Recommend cap-based bucketed expiry, but the cap values are a monetization decision.
- Gateway launch priority: which of VNPay / MoMo / ZaloPay / VietQR ships first for real payments? Most VN gateways are not true recurring — confirm whether subscriptions re-charge from a stored token, re-prompt the user each cycle, or are sold only as annual one-off.
- E-invoice provider choice: VNPT-Invoice vs Viettel S-Invoice vs MISA meInvoice — affects the einvoice.py adapter and the merchant tax registration. Is per-payment auto-issuing required, or only on request for company buyers?
- VAT rate handling: lock to 10%, or support the periodic 8% reduction windows and 0% for certain exports? Affects vat_rate storage and invoice math.
- Refund policy: full refund window (e.g. 7 days, unspent only) and whether partial refunds of remaining unspent credits are offered when the user already consumed some.
- Referral economics: referrer_bonus / referee_bonus credit amounts and any global cap, balanced against the 300 free-grant to keep CAC sane.

### Feature Modules
- Affiliate conversion source: which networks first (Shopee / Lazada / TikTok Shop affiliate)? Each has a different conversion-ingest path (webhook vs daily CSV vs API). This decides the attribution.py adapter we build first.
- Custom-face policy: do we allow user-uploaded real faces (deepfake risk + consent/moderation liability) or restrict to AI-generated personas only? The engine deliberately text-describes faces today; enabling face-swap is a legal + provider decision, not just engineering.
- Voice-clone provider for Vietnamese (VieNeu/ElevenLabs/other) and whether cloned voices are a paid add-on credit SKU or a plan-gated feature.
- Auto-post scope: is TikTok/YT auto-publish in-scope for this phase? It needs OAuth + content-API approval (weeks of platform review) and changes the share-page priority.
- Series A/B 'winner' definition: optimize on CTR (click table, buildable now) or on conversion/revenue (needs network ingest)? Determines whether auto-series ships its A/B verdict in phase 1 or phase 2.
- Landing-page hosting: serve /p/{slug} from the Next.js app (Vercel) or a separate edge function? Affects whether landing pages get custom domains.

### Security, Multi-tenancy, RBAC & Compliance
- Content moderation provider: reuse Gemini safety ratings (already in-stack, zero new vendor) vs a dedicated moderation API (e.g. AWS Rekognition / Hive) for Vietnamese-context nudity/violence accuracy? Affects cost-per-video and false-positive rate on legitimate marketing content.
- Audit log hot retention: 24 months proposed for Vietnam e-commerce record obligations — confirm the actual legal retention requirement for your business category, since it sets cold-storage cost.
- Free-credit farming tolerance: hard-block on disposable domains + signup velocity, or soft-flag for manual review (fewer false-positive lockouts of real users on shared NAT/corporate IPs)? Trades farming loss against legit-user friction.
- Support-seat model: should 'support' role be an internal VietVid staff seat invited INTO a customer org, or strictly the platform_admin path? Determines whether CX agents appear in customer member lists.
- Deletion grace window (proposed 14 days) and what exactly is hard-purged vs PII-stripped-but-retained — confirm against your tax/accounting retention obligations for payment records.

### Frontend Architecture & Screen Map
- Should admin cross-tenant access run as a separate Postgres role that bypasses RLS, or as a dedicated 'platform' org with explicit grants? This is a security boundary decision that the DB/RLS domain owns; the frontend only needs role=admin gating and /v1/admin/* endpoints.
- Charting library for /app/analytics: recharts (richer, ~heavier bundle) vs hand-rolled SVG bars (zero dep, more work). Pick based on how rich the v1 analytics needs to be.
- Free-tier 'Made with VietVid' watermark badge on public share pages — is the growth-loop branding desired, or should shares be unbranded from day one? Affects share-page design and brand-kit watermark toggle scope.
- Does the scene/timeline editor ship in the first frontend wave or as a later 'pro' tier feature? It is the most complex screen and depends on backend support for multi-scene job composition beyond the current single scene_prompt field.
- Should templates support a public marketing gallery (/templates SEO funnel) in v1, or only the in-app /app/templates gallery first? The marketing mirror needs SSR + public read of system templates.

### Infra, DevOps, Deployment & Observability
- Provider priority for production payments: VNPay-only at launch, or also MoMo/bank-QR/USDT (payments table already models crypto fields)? Determines which merchant creds and IPN endpoints to wire first.
- Media retention policy for R2: how long are generated videos kept before lifecycle deletion (cost vs. user expectation)? Drives R2 lifecycle rules and the storage cost line.
- PITR retention window: 7d vs 30d on Neon prod (cost steps with retention) — and is a 30d window sufficient for financial dispute resolution, or is the daily R2 logical dump (90d) the system of record for disputes?
- PiAPI account spend cap and rate limits for production: these set the real render-throughput ceiling and the threshold for the runaway-spend alert. Needs the actual PiAPI plan numbers.
- Staging fidelity: full mirror of prod (separate Supabase project + Upstash + R2 bucket + Neon branch, ~doubles fixed cost) or a lean staging that shares some infra? Affects the environments matrix and monthly cost.
- Hosting choice lock-in: Render is the documented target, but Fly.io gives SG-region GPU machines for the optional VieNeu clone and finer worker scale-to-zero. Confirm Render for API/worker now, Fly only for the deferred GPU voice path?

---

# Phụ lục F — Lộ trình triển khai (Sóng)


Bám theo các Sóng đã thống nhất, ánh xạ thiết kế này:

- **Sóng 5 (đang tới) — Test + CI:** pytest vận hành thật cho ví/ledger/auth/reaper + GitHub Actions. (Phụ lục: infra)
- **Sóng 4 — Mở rộng tính năng + admin:** migrations 0004+ (plans/credit_packs/templates/kol/brand_kit/audit_log/notifications...), admin panel, templates/KOL gallery, auto-series, analytics. (Phụ lục: data, features, security, frontend)
- **Sóng 2 (mở khoá) — Arq+Redis + lưu R2:** khi có Redis + khoá R2. (Phụ lục: pipeline)
- **Sóng 3 — Thanh toán thật + gói cước + hoá đơn:** khi có mã merchant. (Phụ lục: billing)
- **Hạ tầng prod:** deploy topology, observability, backup. (Phụ lục: infra)

Mỗi bảng tenant mới BẮT BUỘC kèm `org_id` + ENABLE/FORCE RLS + policy `org_isolation` trong migration (xem Phụ lục D / miền security).
