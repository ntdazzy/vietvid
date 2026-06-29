# Hạ tầng & hosting

Chọn nơi chạy Vyra ở production: ai chạy backend, ai chạy web, DB/Redis/lưu video ở đâu, vùng nào gần VN, chi phí ước tính theo bậc, và vì sao KHÔNG chạy prod trên laptop ở nhà. Đây là file "dựng từ số 0" cho chủ dự án (solo, không chuyên hạ tầng).

Trạng thái: ⚙️ một phần — code đã sẵn (env var + Dockerfile + storage abstraction), nhưng CHƯA deploy thật lên cloud lần nào (đang chạy local 1-box).

Liên quan: [01-architecture.md](01-architecture.md) · [03-database.md](03-database.md) · [04-storage-media.md](04-storage-media.md) · [05-queue-worker-rendering.md](05-queue-worker-rendering.md) · [10-payments.md](10-payments.md) · [15-security.md](15-security.md) · [17-deployment-cicd.md](17-deployment-cicd.md) · [07-economics.md](07-economics.md)

---

## 1. Tóm tắt 1 phút: chạy ở đâu

| Thành phần | Chạy ở đâu (chốt) | Vùng gần VN | Trạng thái |
|---|---|---|---|
| Web (Next.js 14) | **Vercel** (root dir `apps/web`) | edge `sin1` (Singapore) / `hkg` | 🔜 chưa deploy |
| Backend API + worker (FastAPI) | **Railway** (Docker, 1 image → 2 service) | `asia-southeast1` (Singapore) | 🔜 chưa deploy |
| Postgres | **Neon** (khởi đầu free) → có thể tự host trên Railway sau | Singapore | 🔜 |
| Redis (queue + rate limit) | **Upstash** (khởi đầu free) | Singapore | 🔜 |
| Lưu video/media | **Cloudflare R2** (egress 0đ) | global, gần VN qua CF | 🔜 (`VIETVID_S3_*` đã có trong code) |
| Auth JWT | **Supabase** (hoặc dev HS256) | — | ⚙️ code dual-mode sẵn |
| Render video/ảnh/giọng | **API bên thứ 3** (fal/PiAPI/Vbee) — KHÔNG self-host GPU | — | xem [06-providers.md](06-providers.md) |

> **Laptop i7-13700H = MÁY DEV.** KHÔNG chạy prod ở nhà. Lý do ở [§7](#7-vì-sao-không-chạy-prod-trên-laptop).

> ⚠️ Lưu ý docs cũ: `docs/DEPLOY.md` và `docs/designs/SYSTEM_DESIGN.md` viết "Render/Fly/Railway" và lấy **Render** làm ví dụ chính. Quyết định vận hành chốt (consultation 2026-06-29) là **Railway**. Code KHÔNG phụ thuộc nhà cung cấp nào (chỉ đọc `os.environ` + Dockerfile), nên đổi Render↔Railway chỉ là đổi nơi dán env. File này là nguồn đúng cho lựa chọn hosting.

---

## 2. Chọn cái nào, vì sao

### 2.1 Web → Vercel
- `apps/web` là Next.js 14 App Router — Vercel là đường đi mặc định, không phải sửa code. Đặt **Root Directory = `apps/web`**.
- Edge SSR ở Singapore (`sin1`) phục vụ user VN/SEA độ trễ thấp.
- i18n `next-intl` + middleware nhận vùng theo header geo Vercel (`x-vercel-ip-country`) — xem [16-i18n.md](16-i18n.md).
- Free tier Vercel đủ chạy thử; lên **Pro (~$20/tháng)** khi cần băng thông/analytics. Ước lượng, cần đo thật theo traffic.

### 2.2 Backend (API + worker) → Railway
- FastAPI + worker render đóng gói **1 Dockerfile** (đã có ở repo root). Railway build từ Dockerfile, chạy được nhiều service từ cùng repo.
- **Tách 2 service từ CÙNG 1 image** (rẻ + đúng):
  - `vyra-api`: chạy `uvicorn app_api.main:app` (cần port, ~512MB RAM).
  - `vyra-worker`: chạy Arq worker (không cần port, cần RAM/CPU burst cho ffmpeg). Bật khi `JOB_EXECUTION_MODE=queue`.
- Vì sao tách: render nặng (ffmpeg) sẽ "ăn" CPU làm nghẽn API nếu chung tiến trình — đúng lỗi của chế độ `inline` hiện tại. Xem [05-queue-worker-rendering.md](05-queue-worker-rendering.md).
- Railway có Postgres + Redis add-on nếu muốn gom 1 chỗ; nhưng khởi đầu dùng **Neon + Upstash free** rẻ hơn (xem dưới).
- Vùng: chọn **Singapore** (`asia-southeast1`) gần VN nhất.

### 2.3 Postgres → Neon (khởi đầu)
- Postgres + RLS FORCE đa-tenant (xem [03-database.md](03-database.md)). Neon role mặc định là **non-superuser** → FORCE RLS có hiệu lực (đúng yêu cầu bất biến của Vyra).
- Free tier Neon đủ MVP; có **branch-per-PR** tiện cho CI migration-smoke.
- Connection string phải đổi sang dạng SQLAlchemy + bật SSL:
  `postgresql+psycopg2://USER:PASS@HOST/DB?sslmode=require` → dán vào `VIETVID_DATABASE_URL`.
- App **tự `alembic upgrade head`** lúc khởi động (migrations → 0011).

### 2.4 Redis → Upstash (khởi đầu)
- Dùng cho: (a) hàng đợi Arq khi bật queue mode; (b) rate limit đa-instance (thay dict in-proc trong `app_api/`).
- Upstash serverless, pay-per-command, TLS mặc định (`rediss://`). Free tier đủ khởi đầu.
- Code đọc env `VIETVID_REDIS_URL` (knob đã thiết kế; xem [05-queue-worker-rendering.md](05-queue-worker-rendering.md)).

### 2.5 Lưu video → Cloudflare R2
- **Egress 0đ** — quyết định với sản phẩm video (user tải lại nhiều). Nếu dùng S3/AWS, phí egress sẽ lớn hơn cả phí lưu.
- Code đã có abstraction `storage.py` (`boto3`, import lazy) — chỉ cần set `VIETVID_S3_*`.
- KHÔNG cần ổ cứng to: render xong → upload final.mp4 → xoá workdir. Chi tiết + GC theo `videos.expires_at` ở [04-storage-media.md](04-storage-media.md).
- R2 endpoint dạng `https://<accountid>.r2.cloudflarestorage.com`, region để `auto`.

---

## 3. Biến môi trường (env var) — đặt ở đâu, cái nào

Nguồn đúng: `app_api/config.py` (đọc `os.environ`) + `.env.production.example`. KHÔNG có file `.env` ở prod — dán thẳng vào dashboard Railway/Vercel.

### 3.1 Đặt trên Railway (service API + worker dùng chung)
| Env | Bắt buộc | Ghi chú |
|---|---|---|
| `VIETVID_ENV=production` | ✅ | Tự tắt dev-token + dev-billing; **fail-fast** nếu còn DEV secret placeholder hoặc `CORS=*` |
| `VIETVID_DATABASE_URL` | ✅ | Neon, dạng `postgresql+psycopg2://...?sslmode=require` |
| `CORS_ORIGINS` | ✅ | Domain web thật, KHÔNG để `*` (vd `https://app.vyra.vn`) |
| `SUPABASE_JWKS_URL` | nên | Có cái này → `/v1/dev/token` tự tắt. Không có → set `DEV_JWT_SECRET` ≥32 ký tự |
| `JOB_EXECUTION_MODE=queue` | prod | Bật queue; mặc định `inline` |
| `VIETVID_REDIS_URL` | khi queue | Upstash `rediss://...` |
| `VIETVID_S3_BUCKET/_ENDPOINT/_ACCESS_KEY/_SECRET_KEY` | prod | R2; thiếu → video mất khi redeploy |
| `VIETVID_S3_PUBLIC_BASE` | tuỳ | CDN base (vd `https://media.vyra.vn`) |
| `CREDIT_PRICE_VND=150` `USD_TO_VND=25400` `FREE_GRANT_CREDITS=300` | nên | Kinh tế credit — xem [08-pricing-plans-credits.md](08-pricing-plans-credits.md) |
| `FAL_API_KEY` / `PIAPI_API_KEY` / `GEMINI_API_KEY` / `GROQ_API_KEY` | render thật | Thiếu → mock. Xem [06-providers.md](06-providers.md) |
| `VIETVID_MOMO_*` / `VIETVID_BANK_*` + `VIETVID_SEPAY_TOKEN` | thu tiền | Xem [10-payments.md](10-payments.md) |
| `VIETVID_ADMIN_EMAILS` | nên | Email vào `/app/admin` — xem [11-admin-panel.md](11-admin-panel.md) |
| `VIETVID_SMTP_*` | nên | Email reset/verify thật; thiếu → ghi log |
| `VIETVID_LOG_JSON` | tự bật prod | Log JSON cho máy đọc — xem [12-logging-observability.md](12-logging-observability.md) |

> Worker service dùng **cùng nhóm env** với API (Railway: shared variables / reference). Tránh lệch DB/Redis/R2 giữa 2 service.

### 3.2 Đặt trên Vercel (web)
| Env | Ghi chú |
|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | URL backend Railway (vd `https://api.vyra.vn`) |
| `NEXT_PUBLIC_SUPABASE_URL` | `https://<ref>.supabase.co` (nếu dùng Supabase) |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | anon key Supabase |

⚠️ Mọi biến lộ ra client phải có tiền tố `NEXT_PUBLIC_`. KHÔNG đặt secret (DB, R2 secret, provider key) ở Vercel — chúng thuộc backend.

---

## 4. Vùng (region) — chọn gần VN

| Dịch vụ | Vùng nên chọn | Lý do |
|---|---|---|
| Vercel | `sin1` (Singapore), fallback `hkg` | edge gần VN, độ trễ thấp |
| Railway | `asia-southeast1` (Singapore) | gần VN, cùng vùng với DB/Redis |
| Neon | Singapore (`ap-southeast-1`) | giảm round-trip API↔DB |
| Upstash | Singapore | cùng vùng API |
| R2 | toàn cầu (Cloudflare anycast) | tự gần user qua CDN; region để `auto` |

**Nguyên tắc:** API, DB, Redis nên CÙNG vùng (Singapore) để mỗi query không vòng qua nửa địa cầu. R2 không cần ghim vùng (CDN lo).

---

## 5. Chi phí ước tính theo bậc

> ⚠️ **TRUNG THỰC:** Vyra chưa deploy thật, chưa có hoá đơn cloud nào. Bảng dưới là **giá niêm yết tham khảo của nhà cung cấp + ước lượng, CẦN ĐO THẬT.** Chi phí lớn nhất KHÔNG phải hạ tầng — mà là **API render video** (xem [07-economics.md](07-economics.md)).

| Bậc | Vercel | Railway (API+worker) | Neon | Upstash | R2 | Tổng hạ tầng/tháng (ước lượng) |
|---|---|---|---|---|---|---|
| **Bậc 0 — thử/MVP** | Free | ~$5 (dùng-bao-nhiêu-trả) | Free | Free | ~vài nghìn đồng | **~$5–10** |
| **Bậc 1 — có user trả phí** | Pro ~$20 | ~$20–40 | ~$19 | ~$10 | theo dung lượng video | **~$70–90** |
| **Bậc 2 — tăng trưởng** | $20+ | $50–150 (scale worker) | $69+ | $30+ | theo dung lượng | **~$170–300+** |

Cách đo R2 (theo HANDOFF): ~100k video ≈ ~200GB ≈ ~$3/tháng lưu trữ, egress 0đ. Đo thật bằng dashboard R2 (Storage + Class A/B operations).

**Cách đo chi phí thật khi đã chạy:**
1. Bật billing dashboard từng nhà cung cấp (Vercel/Railway/Neon/Upstash/Cloudflare).
2. Tách rõ **chi phí hạ tầng** (bảng trên) vs **chi phí render** (fal/PiAPI/Vbee) — render là biến phí theo số video, ghi vào [07-economics.md](07-economics.md).
3. Mỗi video phải lưu `cost_usd` thật (engine trả `RenderResult.cost_usd`) để tính biên gộp.

---

## 6. Sơ đồ deploy

```
                 Người dùng (VN / quốc tế)
                          │ HTTPS
        ┌─────────────────┴──────────────────┐
        ▼                                     ▼
  Vercel (sin1)                         (gọi API)
  Next.js web  ──── Bearer JWT ────►  Railway (Singapore)
  apps/web                            ┌───────────────────────┐
                                      │ vyra-api (uvicorn)     │
                                      │  POST /jobs → HOLD →   │
                                      │  enqueue Arq           │
                                      ├───────────────────────┤
                                      │ vyra-worker (arq)      │
                                      │  render(spec, sink)    │
                                      │  → upload R2 → SETTLE  │
                                      └─────────┬─────────────┘
                  ┌─────────────────────────────┼───────────────────┐
                  ▼                              ▼                   ▼
            Neon Postgres                 Upstash Redis         Cloudflare R2
            (Singapore, RLS,              (Arq queue +          (video final.mp4,
             PITR/backup)                  rate limit)           signed URL, GC)
                  ▲
                  │ API bên thứ 3 (render/giọng): fal, PiAPI, Vbee, Supabase(auth)
```

- **2 đường tiền/video tách đôi:** (A) tiền vào qua IPN webhook idempotent; (B) credit→video qua `POST /jobs`. Xem [10-payments.md](10-payments.md) + [05-queue-worker-rendering.md](05-queue-worker-rendering.md).
- **Secrets** chỉ nằm trong dashboard từng nền tảng (Railway/Vercel), KHÔNG commit. Xem [15-security.md](15-security.md).

---

## 7. Vì sao KHÔNG chạy prod trên laptop

Laptop i7-13700H/16GB/512GB chỉ là **máy DEV**. Chạy prod ở nhà bị các rủi ro:

| Rủi ro | Hậu quả |
|---|---|
| **Uptime** | Mất điện, mất mạng, ngủ máy, reboot Windows update → user truy cập 502, video đang render mất. |
| **Mất sổ cái tiền** | DB ví/credit (HOLD→SETTLE/REFUND) nằm trên 1 ổ 512GB không backup tự động → hỏng ổ = mất tiền của khách. Không thể chấp nhận với sản phẩm thu tiền. |
| **Bảo mật** | Mở port ra Internet từ máy cá nhân = lộ bề mặt tấn công (RLS/JWT vẫn cần, nhưng OS nhà không cứng như PaaS). IPN webhook payment phải có HTTPS + domain ổn định. |
| **Không scale** | 1 máy không tách được API/worker, không auto-restart, không nhiều instance. |
| **Vận hành solo** | Bạn đi vắng/ngủ → không ai vực dậy. PaaS tự restart + healthcheck. |

**Kết luận:** prod = managed PaaS rẻ (Railway + Vercel + Neon/Upstash + R2). Laptop để code, QA thật (Playwright), generate asset bằng fal. Render/giọng = API bên thứ 3 (KHÔNG self-host GPU lúc này). VieNeu (nếu muốn giọng clone) là bước sau, qua tunnel — không phải prod cốt lõi.

---

## 8. Checklist dựng từ số 0

Làm theo thứ tự. Mỗi bước có cách verify.

- [ ] **DB:** Tạo project Neon (vùng Singapore) → lấy connection string → đổi sang `postgresql+psycopg2://...?sslmode=require`. Verify: kết nối được từ máy dev.
- [ ] **Auth:** Tạo project Supabase → lấy JWKS URL + anon key. (Hoặc dùng dev HS256 với `DEV_JWT_SECRET` ≥32 ký tự.)
- [ ] **Storage:** Tạo bucket R2 `vyra-prod` trên Cloudflare → lấy `endpoint/access_key/secret_key`. Verify: upload thử 1 file qua `aws s3 --endpoint-url`.
- [ ] **Redis:** Tạo DB Upstash (Singapore) → lấy `rediss://` URL.
- [ ] **Backend (Railway):** New Project → Deploy from repo (Dockerfile) → tạo service `vyra-api`. Dán env mục [§3.1](#31-đặt-trên-railway-service-api--worker-dùng-chung). Verify: `GET https://<api>/health` trả `{"status":"ok"}`.
- [ ] **Worker (Railway):** Thêm service thứ 2 cùng repo → override start command sang Arq worker → set `JOB_EXECUTION_MODE=queue` + `VIETVID_REDIS_URL`. Verify: tạo 1 job → worker nhận → video lên R2.
- [ ] **Web (Vercel):** Import repo → Root Dir `apps/web` → dán env [§3.2](#32-đặt-trên-vercel-web). Verify: mở domain, đăng nhập được.
- [ ] **Domain + CORS:** Gắn domain web → cập nhật `CORS_ORIGINS` ở backend = domain đó. Verify: web gọi API không bị CORS block.
- [ ] **Migration:** Xác nhận `alembic upgrade head` chạy lúc boot (xem log). Verify: `GET /health/ready` trả `{"db":true}`.
- [ ] **Thanh toán:** Set `VIETVID_MOMO_*` (+ `VIETVID_BANK_*`/`VIETVID_SEPAY_TOKEN`). Khai báo IPN URL trên cổng. Verify: nạp thử 1 gói → credit cộng đúng. Xem [10-payments.md](10-payments.md).
- [ ] **Render thật:** Set `FAL_API_KEY`/`PIAPI_API_KEY`/`GEMINI_API_KEY`. Verify: tạo 1 video ra file thật (không mock). Xem [06-providers.md](06-providers.md).
- [ ] **Admin:** Set `VIETVID_ADMIN_EMAILS` = email của bạn. Verify: vào `/app/admin` được.
- [ ] **Go-live gate:** `VIETVID_ENV=production`, `CORS` không phải `*`, Supabase JWKS set (`/v1/dev/token` → 404), HTTPS toàn bộ. Xem [17-deployment-cicd.md](17-deployment-cicd.md) + [15-security.md](15-security.md).
- [ ] **Backup/DR:** Bật PITR Neon + backup. Xem [14-backup-dr-maintenance.md](14-backup-dr-maintenance.md).
- [ ] **Quan sát:** Bật Sentry + structured log + request-id. Xem [12-logging-observability.md](12-logging-observability.md) + [13-monitoring-uptime.md](13-monitoring-uptime.md).
- [ ] **Đo chi phí thật:** Sau 1 tuần chạy, ghi chi phí từng nhà cung cấp vào [07-economics.md](07-economics.md), tách hạ tầng vs render.
