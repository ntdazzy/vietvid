# 17 — Triển khai & CI/CD

Cách đưa Vyra từ máy dev lên prod một cách lặp lại được: Git flow, deploy backend lên Railway + web lên Vercel từng bước, chạy migration lúc deploy, biến môi trường prod, preview env, rollback, và checklist "go-live" lần đầu.

**Trạng thái:** ⚙️ một phần — Dockerfile backend ✅ đã có (`Dockerfile`), CI ✅ đã có (`.github/workflows/ci.yml`), docker-compose dev ✅ (`infra/docker-compose.yml`); **railway.json / vercel.json 🔜 chưa tạo**; queue worker 🔜 chưa nối (xem [05](05-queue-worker-rendering.md)). Chưa từng deploy lên prod thật.

**Liên quan:** [02-infrastructure.md](02-infrastructure.md) (chọn PaaS) · [03-database.md](03-database.md) (Postgres + migration) · [04-storage-media.md](04-storage-media.md) (R2) · [05-queue-worker-rendering.md](05-queue-worker-rendering.md) (worker) · [10-payments.md](10-payments.md) (env bank/SePay) · [13-monitoring-uptime.md](13-monitoring-uptime.md) (`/health`) · [15-security.md](15-security.md) (secrets + startup gate) · [18-runbooks.md](18-runbooks.md) (sự cố deploy).

> ⚠️ **Quy tắc bất di bất dịch (gotcha #1 của repo):** **TUYỆT ĐỐI không chạy `next build` khi `next dev` đang chạy** → hỏng thư mục `.next`, CSS 404, trang trắng. Build prod chạy TRÊN nền tảng (Railway/Vercel), KHÔNG chạy tay khi đang dev local. Nếu lỡ: `kill` dev → `rm -rf apps/web/.next` → `bun run dev` lại. (Xem [HANDOFF.md §6](../HANDOFF.md).)

---

## 1. Bức tranh tổng thể: cái gì deploy ở đâu

Vyra tách làm 2 phần deploy độc lập (đã chốt ở consultation 2026-06-29):

| Thành phần | Code | Deploy lên | Vì sao |
|---|---|---|---|
| **Backend API** (FastAPI) | `app_api/` + `video_engine/` | **Railway** (container từ `Dockerfile`) | Có sẵn Dockerfile; Railway chạy Python + worker + cho Postgres/Redis cùng chỗ |
| **Worker render** | cùng image, lệnh khác | **Railway** (service thứ 2) | Khi bật queue mode — xem [05](05-queue-worker-rendering.md). Hiện inline nên CHƯA cần |
| **Web** (Next.js 14) | `apps/web/` | **Vercel** | Next.js chạy tốt nhất trên Vercel (edge, preview env, geo header cho i18n) |
| **Postgres** | — | **Railway Postgres** hoặc **Neon** (free khởi đầu) | Sổ cái tiền — KHÔNG chạy ở nhà ([03](03-database.md)) |
| **Redis** (queue) | — | **Railway Redis** hoặc **Upstash** (free khởi đầu) | Chỉ cần khi bật queue mode |
| **Video storage** | — | **Cloudflare R2** | Egress 0đ ([04](04-storage-media.md)) |

> Máy laptop i7-13700H/16GB = **MÁY DEV thôi**. KHÔNG chạy prod ở nhà (uptime, mất sổ cái tiền, bảo mật). Lý do đầy đủ: [02](02-infrastructure.md).

**Sơ đồ deploy:**
```
Người dùng
   │
   ├──► web.vyra.vn ──────► Vercel (Next.js)  ──┐
   │                                            │ gọi API qua NEXT_PUBLIC_API_BASE
   └──► api.vyra.vn ──────► Railway (FastAPI) ◄─┘
                               │
                               ├─► Railway/Neon Postgres (RLS + ví)
                               ├─► Railway/Upstash Redis (queue — khi bật)
                               └─► Cloudflare R2 (final.mp4)
```

---

## 2. Git flow (đơn giản, hợp solo founder)

Chỉ cần 1 nhánh chính + nhánh tính năng:

- `main` — nhánh deploy. Mọi commit vào `main` → tự deploy prod (Railway + Vercel theo dõi `main`).
- `master` — nhánh làm việc hiện tại của repo (xem `git status`). **Lưu ý:** base nhánh là `main` nhưng đang làm trên `master`. Trước go-live cần thống nhất: hoặc đổi nhánh deploy thành `master`, hoặc merge `master` → `main`. → ghi vào checklist cuối file.
- `feat/<tên>` — nhánh tính năng. Tạo PR vào `main` → Vercel tự dựng **preview URL** (mục 7) để xem trước khi merge.

Lệnh thật:
```bash
cd /c/Users/NTD/Desktop/vietvid
git checkout -b feat/queue-mode        # tạo nhánh tính năng
# ... code ...
git add app_api/executor.py app_api/queue.py   # add TỪNG path (CẤM git add . — có secret + binary)
git commit -m "feat(queue): nối Arq enqueue_render

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
git push -u origin feat/queue-mode
gh pr create --base main --fill        # tạo PR → CI chạy + Vercel dựng preview
```

> Quy tắc commit của repo (xem [HANDOFF.md §8](../HANDOFF.md)): mỗi commit 1 thay đổi logic, `git add` từng path tường minh, chỉ commit khi được phép rõ.

---

## 3. CI — chạy gì khi push (✅ đã có)

File: `.github/workflows/ci.yml`. Chạy trên mỗi `push` vào `main`/`master` + mọi PR. GitHub Actions, runner `ubuntu-latest`, Python 3.12.

Các bước CI hiện tại:
1. Dựng Postgres service (`postgres:16`, DB `vietvid_test`).
2. `pip install -r requirements.txt`.
3. **Chạy migration bằng owner** (`postgresql+...@localhost/vietvid_test`).
4. **Tạo role non-superuser `vietvid_app`** + cấp quyền (để FORCE RLS có hiệu lực — owner bypass RLS).
5. **Chạy test** bằng role non-superuser: `python -m pytest tests` (xác minh ví ACID / RLS / auth bằng DB thật).
6. Lint `ruff` — advisory (không fail build).

> ⚠️ **RULES.md của repo (worktree) nói pytest đã gỡ — kiểm thử CHỈ bằng `/real-qa`.** Nhưng `.github/workflows/ci.yml` ở repo gốc VẪN chạy `pytest tests`. Đây là điểm cần làm rõ trước go-live (CI gốc dùng pytest, nội quy worktree cấm pytest). → ghi checklist. Trạng thái thực: **CI chạy pytest** (sự thật theo file YAML).

**Bắt buộc trước khi merge vào `main`:** CI xanh + (theo nội quy dự án) `tsc --noEmit` sạch ở `apps/web` + live QA Playwright màn liên quan. CI hiện KHÔNG tự chạy `tsc` cho web → chạy tay:
```bash
cd /c/Users/NTD/Desktop/vietvid/apps/web && bunx tsc --noEmit
```

---

## 4. Deploy BACKEND lên Railway (cầm tay từng bước)

Backend đóng gói bằng `Dockerfile` ở gốc repo. Đọc lại nội dung thật:
- Base `python:3.12-slim` + cài `ffmpeg` (cần cho render/compose).
- Copy `app_api/ video_engine/ core/ config/ module2_brain/ alembic/ alembic.ini`.
- Set `VIETVID_ENV=production`, `EXPOSE 8000`.
- **CMD chạy migration rồi mới uvicorn:** `python -m alembic upgrade head && uvicorn app_api.main:app --host 0.0.0.0 --port ${PORT:-8000}` → **migration tự chạy mỗi lần deploy** (idempotent). Xem mục 5.

### Bước 4.1 — Tạo project + dịch vụ
1. Đăng ký https://railway.app (GitHub login). Plan **Hobby** (~$5/tháng credit) đủ khởi đầu.
2. **New Project → Deploy from GitHub repo** → chọn repo Vyra → nhánh `main`.
3. Railway tự phát hiện `Dockerfile` ở gốc → build bằng nó (KHÔNG cần Nixpacks). Nếu nó chọn Nixpacks nhầm: Settings → Build → **Builder: Dockerfile**.

### Bước 4.2 — Thêm Postgres
- **New → Database → Add PostgreSQL.** Railway tạo `DATABASE_URL` tự động.
- ⚠️ Code đọc `VIETVID_DATABASE_URL` trước, fallback `DATABASE_URL` (xem `config.py:36-40`). Railway cấp `DATABASE_URL` dạng `postgresql://...` — **cần prefix driver `+psycopg2`**. Cách an toàn: tự set `VIETVID_DATABASE_URL` = chuỗi của Railway nhưng đổi `postgresql://` → `postgresql+psycopg2://`.
- ⚠️ **FORCE RLS áp cả owner.** Role Railway cấp mặc định là owner DB → RLS sẽ bị bypass (mất cách ly tenant). Trước go-live PHẢI tạo role non-superuser cho app (giống CI bước 4) và trỏ `VIETVID_DATABASE_URL` vào role đó. Chi tiết: [03-database.md](03-database.md) + [15-security.md](15-security.md). → checklist.

### Bước 4.3 — Set biến môi trường prod
Railway → service backend → **Variables**. Dán các key ở mục 6 (KHÔNG commit secret vào repo). Bắt buộc tối thiểu để boot:
```
VIETVID_ENV=production
VIETVID_DATABASE_URL=postgresql+psycopg2://<app_role>:<pass>@<host>:5432/<db>
DEV_JWT_SECRET=<chuỗi-ngẫu-nhiên-≥32-ký-tự>     # hoặc cắm SUPABASE_* thay thế
CORS_ORIGINS=https://web.vyra.vn                 # KHÔNG để "*"
```
> **Startup gate sẽ TỪ CHỐI boot** nếu prod mà: `DEV_JWT_SECRET` còn placeholder/yếu (mà không có Supabase), `CORS_ORIGINS=*`, hoặc `VIETVID_DEV_AUTH`/`VIETVID_BILLING_DEV` còn bật. Logic thật: `app_api/startup_checks.py:validate_prod_config`. Đây là tính năng — đừng vô hiệu hoá nó.

### Bước 4.4 — Healthcheck + domain
- Railway → Settings → **Healthcheck Path: `/health`** (endpoint có sẵn, dùng `db_healthy()` — `startup_checks.py:60`). Railway chỉ chuyển traffic khi `/health` xanh.
- Settings → **Networking → Generate Domain** (vd `vyra-api.up.railway.app`) hoặc gắn custom `api.vyra.vn` (thêm CNAME ở DNS).
- ⚠️ Railway tự cấp `PORT` qua env — Dockerfile đã dùng `${PORT:-8000}`, không sửa gì.

### Bước 4.5 — Deploy + xác minh THẬT
Mỗi `git push origin main` → Railway tự build + deploy. Sau khi xanh:
```bash
curl -s https://api.vyra.vn/health          # mong: {"status":"ok",...} + db healthy
curl -s https://api.vyra.vn/docs            # FastAPI docs mở được (nếu chưa tắt)
```
Kiểm log boot: phải thấy `startup: cấu hình prod hợp lệ.` (`startup_checks.py:57`). Nếu thấy `Cấu hình prod không an toàn:` → sửa env theo thông báo rồi redeploy.

> Trạng thái: **🔜 chưa deploy lần nào** — các bước trên là quy trình, chưa chạy thật.

---

## 5. Chạy migration lúc deploy

**Cơ chế hiện tại (✅ đã có trong Dockerfile):** CMD chạy `python -m alembic upgrade head` TRƯỚC khi khởi uvicorn. Mỗi lần container start → migration tự áp (alembic idempotent: revision đã chạy thì bỏ qua). Migrations hiện tới `0011` (`alembic/versions/`).

**Cảnh báo khi có nhiều instance:** nếu chạy ≥2 replica backend, cả hai cùng chạy `alembic upgrade` lúc boot → đua nhau. Alembic có lock nhưng an toàn hơn là **tách migration thành bước riêng**:

Cách an toàn cho prod đa-instance (Railway "Pre-deploy command"):
1. Railway → service backend → Settings → **Pre-deploy Command:** `python -m alembic upgrade head`
2. Sửa Dockerfile CMD bỏ phần alembic, chỉ còn `uvicorn ...`.
→ Railway chạy pre-deploy 1 lần trước khi swap instance mới. Trạng thái: 🔜 chưa làm (hiện inline trong CMD là đủ cho 1 instance MVP).

**Chạy migration tay (khi cần, vd hotfix schema):**
```bash
# từ máy dev, trỏ vào DB prod (cẩn thận — đây là DB thật)
export VIETVID_DATABASE_URL="postgresql+psycopg2://<owner>:<pass>@<host>:5432/<db>"
PYTHONUTF8=1 /c/Python314/python -m alembic upgrade head
```
> Migration prod chạy bằng **role owner** (để tạo bảng/policy), nhưng app connect bằng **role non-superuser** (để RLS có hiệu lực). Hai role khác nhau — giống pattern CI. Xem [03](03-database.md).

**Migration phá vỡ (drop cột, đổi kiểu):** luôn backup trước (`pg_dump`, xem [14](14-backup-dr-maintenance.md)) + ưu tiên migration "expand → migrate → contract" để không downtime.

---

## 6. Biến môi trường prod (tham chiếu đầy đủ)

Nguồn sự thật: `app_api/config.py`. Tất cả đọc từ `os.environ`. **KHÔNG có file `.env` trong repo** — set thẳng trên Railway/Vercel. Đánh dấu trạng thái:

### Bắt buộc để boot an toàn (backend)
| Env | Giá trị prod | Trạng thái | Ghi chú |
|---|---|---|---|
| `VIETVID_ENV` | `production` | ✅ | Bật startup gate + tắt cổng dev tự động |
| `VIETVID_DATABASE_URL` | chuỗi non-superuser role | ⚙️ cần tạo role | `+psycopg2`; nếu sai/thiếu → lỗi auth |
| `DEV_JWT_SECRET` | chuỗi ngẫu nhiên ≥32 | 🔜 phải sinh | HOẶC cắm `SUPABASE_*` thay |
| `CORS_ORIGINS` | `https://web.vyra.vn` | 🔜 set khi có domain | KHÔNG để `*` (gate chặn) |
| `VIETVID_APP_URL` | `https://web.vyra.vn` | 🔜 | Dùng dựng link email reset/verify |

### Auth (chọn 1 trong 2)
| Env | Trạng thái | Ghi chú |
|---|---|---|
| `SUPABASE_JWKS_URL` + `SUPABASE_JWT_AUD` | 🔜 nếu dùng Supabase | Khuyến nghị prod (`config.py:56`) |
| `DEV_JWT_SECRET` mạnh | ⚙️ | Mode "dev" tự verify HS256 — chạy được prod nếu secret mạnh |

### Thanh toán (xem [10](10-payments.md))
| Env | Trạng thái | Ghi chú |
|---|---|---|
| `VIETVID_BANK_BIN`, `VIETVID_BANK_ACCOUNT`, `VIETVID_BANK_ACCOUNT_NAME`, `VIETVID_BANK_NAME` | ⚙️ chỉ test | Bật QR bank VietQR |
| `VIETVID_SEPAY_TOKEN` | ⚙️ chỉ test | Token webhook tự cộng tiền |
| `VIETVID_MOMO_*` | 🔜 chờ merchant | Trống = cổng momo báo "chưa cấu hình" |
| `VNPAY_TMN_CODE`, `VNPAY_HASH_SECRET` | 🔜 chờ merchant | — |

### Render thật (xem [06](06-providers.md)) — hiện MOCK
| Env | Trạng thái | Ghi chú |
|---|---|---|
| `GEMINI_API_KEY` | ❌ thiếu | Ảnh + video thật + kịch bản |
| `GROQ_API_KEY` | ❌ thiếu | Kịch bản AI |
| `PIAPI_API_KEY` | ❌ thiếu | Video Seedance |
| `_fal_key.txt` → cần đưa thành env prod | ✅ có ở dev | fal.ai: ảnh Flux + i2v. Ở prod đọc qua env, KHÔNG file |

### Storage R2 (xem [04](04-storage-media.md))
| Env | Trạng thái |
|---|---|
| `VIETVID_S3_BUCKET`, `VIETVID_S3_ENDPOINT`, `VIETVID_S3_ACCESS_KEY`, `VIETVID_S3_SECRET_KEY` | 🔜 set khi nối R2 |
| `VIETVID_S3_PUBLIC_BASE` | 🔜 CDN base (tuỳ chọn) |

### Queue + observability
| Env | Trạng thái | Ghi chú |
|---|---|---|
| `JOB_EXECUTION_MODE` | `inline` (hiện) → `queue` (prod) | ⚙️ queue CHƯA nối ([05](05)) |
| `REDIS_URL` (khi queue) | 🔜 | Railway/Upstash cấp |
| `VIETVID_LOG_JSON` | tự `true` ở prod | ✅ log máy-đọc (xem [12](12-logging-observability.md)) |
| `VIETVID_ADMIN_EMAILS` | 🔜 email bạn | Quyền admin panel ([11](11-admin-panel.md)) |
| `SENTRY_DSN` (nếu dùng) | 🔜 | Xem [12](12-logging-observability.md) |

### Frontend (Vercel)
| Env | Giá trị | Trạng thái |
|---|---|---|
| `NEXT_PUBLIC_API_BASE` | `https://api.vyra.vn` | 🔜 set khi có domain backend |

> ⚠️ Secret ở dev là file gitignored (`_vietvid_db_url.txt`, `_fal_key.txt`). Ở prod KHÔNG dùng file — dán giá trị vào Railway/Vercel Variables. KHÔNG in secret ra log/PR ([15](15-security.md)).

---

## 7. Deploy WEB lên Vercel + preview env

### Bước 7.1 — Import project
1. https://vercel.com (GitHub login).
2. **Add New → Project** → chọn repo Vyra.
3. **Root Directory: `apps/web`** (quan trọng — repo là monorepo, web nằm trong `apps/web`).
4. Framework: Next.js (tự nhận). Build command: `next build` (script `build` trong `apps/web/package.json:8`). Install: Vercel tự chạy `bun install`/`npm install`.
5. Environment Variables → `NEXT_PUBLIC_API_BASE=https://api.vyra.vn`.

### Bước 7.2 — Domain
- Vercel → Settings → Domains → thêm `web.vyra.vn` (hoặc `vyra.vn`). Thêm bản ghi DNS theo hướng dẫn Vercel.

### Bước 7.3 — Preview env (tự động)
- Mỗi PR vào `main` → Vercel tự dựng **preview URL** riêng (vd `vyra-web-git-feat-x.vercel.app`). Xem trước UI thật trước khi merge — đây là cách verify an toàn không đụng prod.
- Preview dùng env "Preview" riêng (Vercel → Settings → Environment Variables → scope Preview). Trỏ preview vào API staging nếu có, hoặc cùng API prod nếu chấp nhận.

> ⚠️ **i18n geo (xem [16](16-i18n.md)):** middleware nhận locale theo header geo của Vercel/Cloudflare. Trên Vercel header là `x-vercel-ip-country`. Local dev KHÔNG có header này → middleware fallback cookie/default. Verify locale-by-IP CHỈ test được trên Vercel preview/prod, không test được local.

### Bước 7.4 — Xác minh
```bash
curl -s -o /dev/null -w "%{http_code}" https://web.vyra.vn        # mong 200
# mở browser thật → login dev tắt ở prod → cần luồng auth thật
```
Live QA Playwright trên domain prod sau deploy (xem [HANDOFF.md §6](../HANDOFF.md) cho harness).

---

## 8. Rollback

**Backend (Railway):**
- Railway → service → tab **Deployments** → chọn deploy cũ đang xanh → **Redeploy** (rollback tức thì về image cũ).
- ⚠️ Nếu deploy mới đã chạy migration phá vỡ schema → rollback code KHÔNG tự rollback DB. Phải có downgrade migration HOẶC khôi phục từ backup ([14](14-backup-dr-maintenance.md)). → đây là lý do ưu tiên migration "expand/contract" không phá vỡ.

**Web (Vercel):**
- Vercel → Deployments → deploy cũ → **... → Promote to Production** (rollback tức thì, không build lại).

**Rollback bằng git (nếu cần):**
```bash
git revert <sha-xấu>        # tạo commit đảo ngược (KHÔNG force-push main)
git push origin main        # tự deploy lại bản đã revert
```
> CẤM `git push --force` lên `main` ở prod — phá lịch sử + có thể mất commit người khác. Dùng `git revert`.

---

## 9. Checklist "GO-LIVE" lần đầu (làm theo thứ tự)

Đây là lần deploy prod ĐẦU TIÊN. Mọi mục phải xác minh THẬT (không tin xanh giả).

**A. Chuẩn bị tài khoản & hạ tầng**
- [ ] Tạo project Railway + Postgres (mục 4).
- [ ] Tạo project Vercel, root = `apps/web` (mục 7).
- [ ] Tạo bucket Cloudflare R2 + API token ([04](04-storage-media.md)).
- [ ] Mua domain + trỏ DNS: `api.vyra.vn` → Railway, `web.vyra.vn` → Vercel.

**B. Bảo mật trước khi mở cổng**
- [ ] Sinh `DEV_JWT_SECRET` ngẫu nhiên ≥32 ký tự (HOẶC cắm `SUPABASE_*`).
- [ ] Set `CORS_ORIGINS=https://web.vyra.vn` (KHÔNG `*`).
- [ ] Xác nhận `VIETVID_DEV_AUTH` + `VIETVID_BILLING_DEV` KHÔNG set (tự tắt ở prod).
- [ ] Tạo **role non-superuser** cho app + trỏ `VIETVID_DATABASE_URL` vào nó (để FORCE RLS hiệu lực) ([03](03-database.md), [15](15-security.md)).
- [ ] Boot backend → log phải báo `startup: cấu hình prod hợp lệ.`

**C. Migration & dữ liệu**
- [ ] `alembic upgrade head` chạy sạch trên DB prod (tự động qua Dockerfile CMD, kiểm log).
- [ ] Bật backup tự động Postgres ([14](14-backup-dr-maintenance.md)).

**D. Thanh toán (để nhận tiền thật)**
- [ ] Set `VIETVID_BANK_*` + `VIETVID_SEPAY_TOKEN` THẬT.
- [ ] Cấu hình webhook SePay trỏ về `https://api.vyra.vn/v1/billing/ipn/sepay`.
- [ ] Test nạp +1 khoản nhỏ thật → xác minh credit cộng đúng, replay không cộng đôi ([10](10-payments.md)).

**E. Render (để tạo video thật, không mock)**
- [ ] Điền `GEMINI_API_KEY` / `PIAPI_API_KEY` / fal key → render thật ([06](06-providers.md)).
- [ ] Set `VIETVID_S3_*` → video upload R2 + signed URL hoạt động ([04](04-storage-media.md)).
- [ ] (Khi cần scale) bật `JOB_EXECUTION_MODE=queue` + Redis + worker service ([05](05-queue-worker-rendering.md)).

**F. Observability & xác minh cuối**
- [ ] Healthcheck `/health` xanh trên Railway.
- [ ] Set `VIETVID_ADMIN_EMAILS` = email bạn → vào được admin panel ([11](11-admin-panel.md)).
- [ ] Set `SENTRY_DSN` (nếu dùng) → lỗi prod bắn về ([12](12-logging-observability.md)).
- [ ] Uptime monitor ping `/health` mỗi 1-5 phút ([13](13-monitoring-uptime.md)).
- [ ] **Smoke test thật end-to-end:** đăng ký → nạp tiền → tạo 1 video → tải về. Mắt thấy video chạy.

---

## 10. Bẫy đã biết (đừng vấp)

| Bẫy | Hậu quả | Cách tránh |
|---|---|---|
| `next build` khi `next dev` chạy | `.next` hỏng, trang trắng | KHÔNG build tay; build trên Vercel |
| `DATABASE_URL` của Railway thiếu `+psycopg2` | SQLAlchemy không nối được | Set `VIETVID_DATABASE_URL` với prefix driver |
| App connect bằng role owner | RLS bị bypass → rò tenant | Dùng role non-superuser ([03](03)) |
| `CORS_ORIGINS=*` ở prod | Startup gate chặn boot | Set domain cụ thể |
| Quên `VIETVID_ENV=production` | Cổng dev (dev-token, dev-billing) mở ở prod | Set `production` |
| Force-push `main` | Mất commit, deploy hỏng | Dùng `git revert` |
| Migration phá vỡ + rollback code | Schema lệch code | Backup trước; expand/contract |
| Test locale-by-IP ở local | Không có header geo | Test trên Vercel preview ([16](16)) |

---

## Việc cần làm (checklist)

- [ ] **Thống nhất nhánh deploy:** đang làm trên `master`, base là `main`. Chốt merge `master`→`main` hay đổi nhánh deploy thành `master` trước go-live.
- [ ] **Làm rõ CI vs pytest:** `.github/workflows/ci.yml` chạy `pytest tests` nhưng nội quy worktree (`RULES.md`) cấm pytest, ưu tiên `/real-qa`. Quyết: giữ pytest trong CI (test ví/RLS/auth) hay thay bằng harness khác.
- [ ] Tạo `railway.json` (hoặc cấu hình UI) chốt: builder=Dockerfile, healthcheck=`/health`, pre-deploy=`alembic upgrade head`.
- [ ] Tạo cấu hình Vercel chốt root=`apps/web` + env `NEXT_PUBLIC_API_BASE` (hoặc dùng UI Vercel, không cần file).
- [ ] Bổ sung bước `tsc --noEmit` (web) vào CI để chặn lỗi type trước merge.
- [ ] Tạo script/đoạn hướng dẫn tạo **role non-superuser** prod (copy pattern từ `ci.yml` bước 4) — chốt ở [03-database.md](03-database.md).
- [ ] Tách migration thành Railway "Pre-deploy command" khi chạy ≥2 instance backend.
- [ ] Sinh + lưu an toàn `DEV_JWT_SECRET` prod (hoặc dựng Supabase project).
- [ ] **Đo thật chi phí PaaS thực tế** (Railway + Vercel + R2/tháng) sau 1 tháng chạy — hiện chỉ ước lượng, chưa đo. Đối chiếu [07-economics.md](07-economics.md) + [21-financial-model.md](21-financial-model.md).
- [ ] Chạy thử toàn bộ checklist Go-live mục 9 trên môi trường staging trước khi mở cho user thật.
