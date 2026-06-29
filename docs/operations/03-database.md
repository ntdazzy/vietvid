# Cơ sở dữ liệu

Postgres là **sổ cái sự thật** của Vyra: ví tiền (credit), job render, tenant, thanh toán. Vì là tiền + đa-tenant nên hai thứ TUYỆT ĐỐI không được sai: **cách ly tenant (RLS)** và **không mất dữ liệu (backup/PITR)**. File này cầm tay chỉ việc: RLS hoạt động ra sao, bảng nào global/bảng nào tenant, chạy migration an toàn lúc deploy, và khôi phục khi sự cố.

**Trạng thái:** ⚙️ một phần — schema + RLS FORCE + migration pipeline đã build & verify trên dev (migrations 0001→0011). Backup/PITR **chưa bật** vì prod chưa dựng (phụ thuộc nhà cung cấp Postgres bạn chọn: Neon / Railway / Supabase).

**Liên quan:** [01-architecture.md](01-architecture.md) (RLS trong bức tranh tổng) · [02-infrastructure.md](02-infrastructure.md) (chọn Postgres managed) · [14-backup-dr-maintenance.md](14-backup-dr-maintenance.md) (DR chi tiết) · [15-security.md](15-security.md) (role app non-superuser) · [17-deployment-cicd.md](17-deployment-cicd.md) (migration trong CD) · [18-runbooks.md](18-runbooks.md) (sự cố DB)

---

## 1. Tổng quan nhanh

| Hạng mục | Giá trị thật trong code | File:dòng |
|---|---|---|
| Engine DB | PostgreSQL (psycopg2) | `app_api/config.py:36` |
| ORM | SQLAlchemy 2.0 (DeclarativeBase) | `app_api/models.py:31` |
| Đa-tenant | Row-Level Security **FORCE**, fail-closed | `alembic/versions/20260627_0001_baseline.py:57` |
| GUC RLS | `vietvid.current_org` | `app_api/config.py:50` |
| Migration tool | Alembic, head = **0011** | `alembic/versions/` |
| Extensions bắt buộc | `pgcrypto`, `citext` | baseline `:24` |
| Backup/PITR | 🔜 dùng tính năng managed của nhà cung cấp | — |

> ⚠️ **Số liệu chưa đo:** kích thước DB, số dòng, IOPS, dung lượng WAL cho PITR — Vyra mới ra mắt, chưa có prod. Mọi con số dạng "khoảng" trong file này là **ước lượng, cần đo thật** (cách đo ghi ngay tại chỗ).

---

## 2. Kết nối & cấu hình

DB URL đọc từ env, ưu tiên `VIETVID_DATABASE_URL` → `DATABASE_URL` → fallback local (`app_api/config.py:36-40`):

```
VIETVID_DATABASE_URL=postgresql+psycopg2://USER:PASS@HOST:5432/DBNAME?sslmode=require
```

- ✅ Dạng URL: `postgresql+psycopg2://...`. Nhà cung cấp managed (Neon/Railway/Supabase) cho sẵn chuỗi — chỉ cần thêm `?sslmode=require` nếu chưa có.
- ✅ **Secret không in ra log, không commit.** Đặt vào biến môi trường của PaaS (Railway/Vercel dashboard), local thì đọc từ file gitignored (xem [15-security.md](15-security.md)).
- ⚙️ `VIETVID_DB_APP_ROLE` (`config.py:43`) — khai báo sẵn để app `SET ROLE` xuống role non-superuser, **hiện chưa được wire vào db.py** (để rỗng = dùng role trong URL). Xem mục 3.4.

**Engine fork-safe** (`app_api/db.py:29-43`): mỗi PID 1 engine riêng (`pool_size=5, max_overflow=10, pool_pre_ping=True`). Khi worker fork (Arq), engine tự tạo lại — không dùng chung socket với tiến trình cha. Bạn không cần làm gì, chỉ cần biết: **đừng chia sẻ Session giữa các process**.

---

## 3. RLS — cách ly tenant (phần quan trọng nhất)

### 3.1 Nguyên lý fail-closed

Mỗi bảng tenant có cột `org_id`. RLS chặn ở tầng DB: nếu không set "org hiện tại" thì **đọc 0 dòng** (chứ không phải đọc tất cả). Predicate thật (`models.py:73`, baseline `:18`):

```sql
org_id = nullif(current_setting('vietvid.current_org', true), '')::uuid
```

- Chưa set GUC → `current_setting(..., true)` trả NULL → `nullif` → NULL → so sánh `org_id = NULL` luôn FALSE → **0 dòng**. Đây là "fail-closed": quên set org = không lộ data, không phải lộ hết.
- `FORCE ROW LEVEL SECURITY` (baseline `:60`) áp policy **cả với chủ bảng (table owner)**. Đây là lý do role app phải là **non-superuser** — superuser bỏ qua RLS.

### 3.2 `tenant_session()` — luôn dùng cái này cho data tenant

`app_api/db.py:66-83`. Mở transaction NGẮN, set GUC ngay đầu rồi mới query:

```python
from app_api.db import tenant_session

with tenant_session(org_id) as s:      # org_id = uuid string từ JWT đã xác thực
    s.execute(...)                      # RLS tự lọc về đúng org này
```

- `SET LOCAL vietvid.current_org = :org` chỉ sống trong transaction → an toàn với PgBouncer transaction-mode.
- **KHÔNG bọc cả request trong 1 transaction** (giữ lock khi gọi API render chậm). Mở/đóng quanh cụm query thôi.
- Bảng global (users/plans...) dùng `session_scope()` (`db.py:52-63`) — không set GUC.

### 3.3 Bảng global vs tenant (danh sách thật)

Nguồn duy nhất: `app_api/models.py`.

**TENANT_TABLES** (`models.py:630`) — có RLS FORCE + policy `org_isolation`:

```
wallets, ledger_entries, payments, jobs, job_events, videos, notifications, vv_webhooks
```

**GLOBAL_ORG_TABLES** (`models.py` ~`:636`) — CÓ cột `org_id` nhưng **cố ý không RLS** (truy cập pre-auth, trước khi biết org). Mỗi mục là quyết định có chủ đích, lọc `org_id` tường minh tại endpoint:

| Bảng | Vì sao global |
|---|---|
| `memberships`, `org_invitations` | lớp identity/join, dùng trước khi vào tenant |
| `vv_affiliate_links`, `vv_link_clicks` | redirect `/r/{code}` + ghi click chạy **pre-auth** (không có GUC) |
| `audit_log` | phải **sống sót cả khi org bị xoá** (điều tra/pháp lý) |
| `vv_api_keys` | tra cứu theo hash **trước khi biết org** (auth API key) |

**Bảng global thuần** (không `org_id`): `users`, `orgs`, `plans`, `credit_packs`, `vv_platform_config`.

⚠️ **Quy tắc khi thêm bảng tenant mới:** thêm vào `TENANT_TABLES` + bật RLS trong chính migration tạo bảng đó. Nếu bảng có `org_id` mà cố ý global → phải thêm vào `GLOBAL_ORG_TABLES`, nếu không CI sẽ đỏ (xem 3.5).

### 3.4 Role app non-superuser (bắt buộc cho FORCE RLS)

FORCE RLS **vô hiệu nếu app connect bằng superuser**. Trên prod:

1. Tạo role app riêng, KHÔNG superuser, KHÔNG `BYPASSRLS`:
   ```sql
   CREATE ROLE vyra_app LOGIN PASSWORD '...';
   GRANT CONNECT ON DATABASE vyra TO vyra_app;
   GRANT USAGE ON SCHEMA public TO vyra_app;
   GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO vyra_app;
   GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO vyra_app;
   ALTER DEFAULT PRIVILEGES IN SCHEMA public
     GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO vyra_app;
   ```
2. Dùng role này trong `VIETVID_DATABASE_URL`.
3. ✅ Neon/Railway/Supabase: role mặc định họ cấp **không phải superuser** → FORCE RLS hoạt động. Kiểm chứng:
   ```sql
   SELECT current_user, usesuper FROM pg_user WHERE usename = current_user;  -- usesuper phải = false
   ```
4. ⚠️ Migration cần quyền DDL (CREATE TABLE/EXTENSION). Hai lựa chọn: (a) chạy `alembic upgrade` bằng role owner riêng rồi app chạy bằng `vyra_app`; (b) cho `vyra_app` quyền tạo bảng. Quyết định khi dựng prod — xem [open question].

### 3.5 CI test giữ RLS không bị quên

`tests/test_rls_coverage.py` (✅ đã có): quét `information_schema` tìm MỌI bảng có cột `org_id`, loại trừ `GLOBAL_ORG_TABLES`, rồi assert từng bảng còn lại có `relrowsecurity=true`, `relforcerowsecurity=true`, và ≥1 policy. Thiếu = test đỏ = không merge được.

Chạy thủ công (cần DB thật/dev đang chạy):

```bash
PYTHONUTF8=1 /c/Python314/python -m pytest tests/test_rls_coverage.py -v
```

---

## 4. Migrations (Alembic)

### 4.1 Trạng thái thật

✅ Migrations trên đĩa: **0001 → 0011** (`alembic/versions/`):

| File | Nội dung |
|---|---|
| `20260627_0001_baseline` | M1: mọi bảng M1 + extensions + RLS FORCE + trigger ledger immutable + partial indexes |
| `..._0002_auth_tokens` | bảng auth_tokens |
| `..._0003_org_invitations` | lời mời org |
| `..._0004_billing_catalog` | plans, credit_packs (global) |
| `..._0005_content_tables` | templates / KOL persona / brand kit |
| `..._0006_affiliate` | affiliate links + clicks |
| `..._0007_notifications` | notifications |
| `..._0008_audit_log` | audit log |
| `..._0009_series_group` | series/group |
| `..._0010_api_keys_webhooks` | API keys + webhooks |
| `..._0011_platform_config` | vv_platform_config |

> Lưu ý: tài liệu [docs/designs/SYSTEM_DESIGN.md](../designs/SYSTEM_DESIGN.md) §1 mô tả **kế hoạch** chuỗi migration 0004+ (thiết kế ban đầu). Code thực tế đã đi xa hơn (head = 0011). Khi nghi ngờ, **tin file trên đĩa** (`alembic/versions/`), không tin plan cũ.

### 4.2 Quy ước viết migration (D1 — KHÔNG dùng autogen)

Quyết định kiến trúc D1 (SYSTEM_DESIGN `:555`): **bỏ `create_all`/autogen cho M2 trở đi**. Autogen KHÔNG sinh được RLS policy, `FORCE`, partial index (`WHERE`), trigger append-only, hay seed INSERT. Mỗi migration viết tay `op.create_table(...)` + `op.execute(...)` raw SQL cho RLS/index/trigger/seed.

⚠️ **Không bao giờ `alembic revision --autogenerate` rồi commit thẳng.** Autogen chỉ dùng làm bộ kiểm tra trôi schema trong CI (`alembic check`), không phải nguồn migration.

Khi thêm bảng tenant trong migration mới, lặp đúng loop baseline với danh sách LOCAL:

```python
_NEW_TENANT_TABLES = ("ten_bang_moi",)
_RLS = "org_id = nullif(current_setting('vietvid.current_org', true), '')::uuid"
for t in _NEW_TENANT_TABLES:
    op.execute(f"ALTER TABLE {t} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {t} FORCE ROW LEVEL SECURITY")
    op.execute(f"DROP POLICY IF EXISTS org_isolation ON {t}")
    op.execute(f"CREATE POLICY org_isolation ON {t} USING ({_RLS}) WITH CHECK ({_RLS})")
```

### 4.3 Chạy migration AN TOÀN lúc deploy

✅ Cách hiện tại — **Dockerfile chạy tự động khi container khởi động** (`Dockerfile:28`):

```sh
python -m alembic upgrade head && uvicorn app_api.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

Nghĩa là: deploy ảnh mới → migration chạy trước → nếu migration LỖI thì uvicorn không start (fail-fast, an toàn). Trên Railway/Render, đây là hành vi mặc định khi dùng Dockerfile này.

**Quy trình deploy migration an toàn (cầm tay):**

1. **Trước khi deploy lên prod, thử trên DB staging/copy.** Restore 1 bản backup gần nhất ra DB tạm rồi `alembic upgrade head`, xem có lỗi không.
2. **Backup ngay trước migration phá huỷ** (DROP COLUMN, ALTER TYPE...). Managed Postgres có snapshot 1-click — bấm trước khi deploy.
3. **Kiểm tra version hiện tại vs head:**
   ```bash
   PYTHONUTF8=1 /c/Python314/python -m alembic current   # version đang ở DB
   PYTHONUTF8=1 /c/Python314/python -m alembic heads      # version mới nhất trong code
   PYTHONUTF8=1 /c/Python314/python -m alembic history    # xem chuỗi
   ```
4. **Migration cộng dồn (additive) trước, phá huỷ sau.** Thêm cột nullable → deploy code dùng cột mới → migration sau mới xoá cột cũ. Tránh "deploy code mới + drop cột cũ" cùng lúc (rollback khó). Đây là pattern expand/contract.
5. **Một instance chạy migration tại một thời điểm.** Nếu Railway scale >1 replica, nhiều container cùng `alembic upgrade` lúc boot → có thể đua. Alembic có khoá ở bảng `alembic_version` nhưng an toàn nhất: tách bước migration thành **release command** chạy 1 lần trước khi rollout (Railway hỗ trợ pre-deploy command), KHÔNG để trong CMD khi >1 replica. Xem [17-deployment-cicd.md](17-deployment-cicd.md).
6. **Rollback:** `alembic downgrade -1` (lùi 1 bước). ⚠️ Downgrade migration phá huỷ thường **mất dữ liệu** — chỉ tin downgrade với migration additive. Khi đã DROP, rollback thật = restore từ backup.

```bash
# local / staging — chạy thủ công (alembic không trên PATH → dùng python -m)
PYTHONUTF8=1 /c/Python314/python -m alembic upgrade head
PYTHONUTF8=1 /c/Python314/python -m alembic downgrade -1   # lùi 1 bước nếu cần
```

---

## 5. Backup tự động + PITR

🔜 **Chưa bật** — phụ thuộc nhà cung cấp Postgres prod (chưa chốt; xem [02-infrastructure.md](02-infrastructure.md)). Đây là **việc bắt buộc làm trước khi nhận đồng tiền thật đầu tiên** — DB chứa sổ cái ví credit, mất là mất tiền khách.

### 5.1 Dùng tính năng managed (đừng tự dựng pg_dump cron lúc khởi đầu)

| Nhà cung cấp | Backup | PITR | Ghi chú |
|---|---|---|---|
| **Neon** | tự động | có (point-in-time restore theo "history retention") | free-tier retention ngắn; gói trả phí dài hơn — **cần kiểm tra số ngày thật** |
| **Railway Postgres** | snapshot | tuỳ gói | xác nhận tần suất + retention trong dashboard |
| **Supabase** | daily backup | PITR ở gói Pro+ | nếu đã dùng Supabase cho auth thì tiện gộp |

✅ **Việc cần làm:** bật backup + đặt **retention ≥ 7 ngày** (tối thiểu), bật PITR nếu gói cho phép. Ghi lại số ngày retention thật vào [14-backup-dr-maintenance.md](14-backup-dr-maintenance.md).

> **Số liệu chưa đo:** RPO (mất tối đa bao nhiêu phút dữ liệu) và RTO (khôi phục mất bao lâu) — phụ thuộc gói cụ thể. **Cách đo:** sau khi bật, đọc tài liệu gói về WAL retention, rồi làm 1 lần restore thử (mục 6) và bấm giờ.

### 5.2 Backup logic bổ sung (tự chủ, khuyến nghị thêm)

Ngoài snapshot của nhà cung cấp, nên có **1 bản `pg_dump` định kỳ** đẩy sang nơi KHÁC (vd Cloudflare R2) để không phụ thuộc 1 vendor:

```bash
# chạy từ máy có psql/pg_dump; URL đọc từ env, KHÔNG hardcode
pg_dump "$VIETVID_DATABASE_URL" -Fc -f "vyra_$(date +%F).dump"
# rồi upload lên R2 (xem 04-storage-media.md cho cấu hình S3-compatible)
```

⚙️ Chưa có script tự động trong repo — đây là gợi ý cho giai đoạn prod. Lịch chạy: dùng Railway cron / GitHub Actions schedule (xem [17-deployment-cicd.md](17-deployment-cicd.md)).

---

## 6. Cách restore (khôi phục)

### 6.1 PITR / snapshot (đường chính, dùng UI nhà cung cấp)

1. Vào dashboard Postgres → chọn snapshot/thời điểm cần khôi phục.
2. Restore ra **DB MỚI** (không ghi đè DB đang chạy — để còn so sánh + tránh mất thêm).
3. Đổi `VIETVID_DATABASE_URL` của app trỏ sang DB mới → redeploy.
4. Kiểm chứng tính toàn vẹn ví (mục 6.3) TRƯỚC khi cho user vào lại.

### 6.2 Restore từ `pg_dump`

```bash
createdb vyra_restore                     # hoặc tạo DB rỗng trên managed
pg_restore -d "postgresql://.../vyra_restore" -Fc vyra_2026-06-29.dump
```

⚠️ Sau restore, chạy lại migration nếu bản dump cũ hơn head: `alembic upgrade head`.

### 6.3 Kiểm chứng sau restore (BẮT BUỘC — đây là tiền)

Ledger là **append-only** (trigger chặn UPDATE/DELETE, baseline `:40-55`), nên số dư ví = tổng ledger. Sau restore, đối chiếu:

```sql
-- Số dư ví phải = tổng các bút toán ledger của org đó (nếu lệch → restore hỏng)
SELECT w.org_id, w.balance,
       (SELECT COALESCE(SUM(amount),0) FROM ledger_entries l WHERE l.org_id = w.org_id) AS ledger_sum
FROM wallets w;   -- chạy với role bypass RLS / hoặc set GUC từng org
```

> Lưu ý cột thật trong `wallets`/`ledger_entries` cần xác nhận lại theo `app_api/models.py` (mục Wallet `:449`, LedgerEntry `:466`) — câu trên là khung kiểm chứng, chỉnh tên cột cho khớp.

Kiểm chứng RLS vẫn FORCE sau restore (đừng để restore làm tắt RLS):

```bash
PYTHONUTF8=1 /c/Python314/python -m pytest tests/test_rls_coverage.py -v
```

---

## 7. Bẫy thường gặp (đọc trước khi gặp)

- **Quên set GUC → thấy 0 dòng, tưởng mất data.** Không mất — RLS đang fail-closed. Dùng `tenant_session(org_id)`, không phải `session_scope()`.
- **App connect bằng superuser → RLS không có tác dụng.** Kiểm tra `usesuper=false` (mục 3.4).
- **Chạy `alembic` trực tiếp báo "command not found".** Trên máy này alembic không trên PATH → `python -m alembic` (HANDOFF.md `:156, :301`).
- **Migration đua khi nhiều replica.** Tách thành release command (mục 4.3 bước 5).
- **Downgrade migration phá huỷ ≠ rollback an toàn.** Mất data thật. Restore từ backup mới là rollback thật.
- **Seed bảng global có org_id NULL bị FORCE RLS chặn.** Seed TRƯỚC khi ENABLE RLS trong migration (SYSTEM_DESIGN D6, `:585`).

---

## Việc cần làm (checklist)

- [ ] Chốt nhà cung cấp Postgres prod (Neon / Railway / Supabase) — ghi vào [02-infrastructure.md](02-infrastructure.md).
- [ ] Tạo role app **non-superuser** (`vyra_app`) + cấp quyền đúng; xác nhận `usesuper=false`.
- [ ] Quyết định ai chạy DDL migration (owner role vs app role) — mục 3.4 bước 4.
- [ ] Bật backup tự động + retention ≥ 7 ngày + PITR (nếu gói cho phép); ghi số ngày thật vào [14-backup-dr-maintenance.md](14-backup-dr-maintenance.md).
- [ ] **Đo RPO/RTO thật** bằng 1 lần restore thử có bấm giờ.
- [ ] Thiết lập `pg_dump` định kỳ đẩy sang R2 (backup ngoài vendor) — script + cron.
- [ ] Quyết định migration trong CD: giữ trong Dockerfile CMD (1 replica) hay tách release command (>1 replica) — [17-deployment-cicd.md](17-deployment-cicd.md).
- [ ] Wire `VIETVID_DB_APP_ROLE` vào `db.py` (`SET ROLE`) nếu muốn dùng 1 connection nhưng hạ quyền — hiện chưa wire.
- [ ] Viết runbook "restore khẩn cấp" trong [18-runbooks.md](18-runbooks.md), gồm câu SQL đối chiếu ví ở mục 6.3.
- [ ] Đặt CI chạy `tests/test_rls_coverage.py` trên mọi PR (xem [17-deployment-cicd.md](17-deployment-cicd.md)).
