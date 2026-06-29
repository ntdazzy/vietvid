# 01 — Kiến trúc hệ thống

Sơ đồ + luồng dữ liệu thật của Vyra: web → api → queue → worker → providers → storage → DB. Mục tiêu: bạn (chủ dự án) và các phiên Claude sau **nhìn 1 file là hiểu toàn bộ đường đi của 1 request tạo video**, biết file nào chịu trách nhiệm gì, và ranh giới giữa các thành phần.

Trạng thái: ⚙️ một phần — lõi (api/wallet/engine/RLS) ✅ đã code+verify thật; queue mode + cloud storage 🔜 đã code khung, **chưa bật ở prod**.

Liên quan: [00-overview.md](00-overview.md) · [02-infrastructure.md](02-infrastructure.md) · [03-database.md](03-database.md) · [04-storage-media.md](04-storage-media.md) · [05-queue-worker-rendering.md](05-queue-worker-rendering.md) · [06-providers.md](06-providers.md) · [15-security.md](15-security.md). Nguồn sự thật ngữ cảnh: [../HANDOFF.md](../HANDOFF.md) + [../VISION.md](../VISION.md) (file VISION thắng khi mâu thuẫn định vị).

---

## 1. Sơ đồ tổng thể (ASCII)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  NGƯỜI DÙNG                                                               │
│  Web (Next.js 14) · Mobile (Flutter — 🔜) · Public API (Product C — 🔜)  │
└───────────────────────────────┬─────────────────────────────────────────┘
                                 │  HTTPS + Bearer JWT
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  app_api  (FastAPI + SQLAlchemy 2.0)        ✅ đã build+verify             │
│  ───────────────────────────────────────────────────────────────────────│
│  middleware: CORS · security headers · rate-limit · request-id           │
│  auth (JWT dual-mode) → tenancy (org_id) → routers/*                      │
│                                                                           │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐  │
│   │ auth     │  │ billing  │  │ jobs     │  │ wallet   │  │ admin     │  │
│   │ orgs     │  │ /ipn     │  │ /estimate│  │ content  │  │ media...  │  │
│   └──────────┘  └────┬─────┘  └────┬─────┘  └──────────┘  └───────────┘  │
│                      │             │ POST /v1/jobs                        │
│                      │             │  validate→clamp→HOLD credit→enqueue  │
│                      │             ▼                                      │
│                      │      executor.submit_job(mode)                     │
└──────────────────────┼─────────────┼─────────────────────────────────────┘
        tiền vào (IPN) │             │  enqueue
                       │             ▼
                       │   ┌───────────────────────────────────────┐
                       │   │  HÀNG ĐỢI  (Redis + Arq)   🔜 chưa bật │
                       │   │  inline (M1): BackgroundTasks cùng    │
                       │   │  tiến trình app — KHÔNG scale          │
                       │   └───────────────┬───────────────────────┘
                       │                   ▼
                       │   ┌───────────────────────────────────────┐
                       │   │  worker.run_job(org_id, job_id)       │
                       │   │  load→RUNNING→render(spec,sink)       │
                       │   └───────┬───────────────────┬───────────┘
                       │           │ render(spec,sink) │ complete_job
                       │           ▼                   │ (SETTLE/REFUND)
                       │   ┌───────────────────────┐   │
                       │   │ video_engine          │   │
                       │   │ render(spec, sink)    │   │
                       │   │ STATELESS — KHÔNG DB  │   │
                       │   │ image→voice→video→QA  │   │
                       │   │ →compose final.mp4    │   │
                       │   └───────┬───────────────┘   │
                       │           │ HTTP API          │
                       │           ▼                   │
                       │   ┌───────────────────────┐   │
                       │   │ PROVIDERS bên thứ 3   │   │
                       │   │ PiAPI/fal (video) ·   │   │
                       │   │ fal Flux (ảnh) ·      │   │
                       │   │ Vbee/VieNeu (giọng)   │   │
                       │   └───────────────────────┘   │
                       │           │ final.mp4         │
                       │           ▼                   │
                       │   ┌───────────────────────┐   │
                       │   │ STORAGE  (R2/S3)      │   │ upload final.mp4
                       │   │ storage.store_output  │◀──┘ → xoá workdir tạm
                       │   └───────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Postgres  (ACID + RLS FORCE đa-tenant)     ✅                            │
│  orgs · wallets · ledger_entries (append-only) · jobs · job_events ·     │
│  videos · payments · notifications · audit_log ...                        │
└─────────────────────────────────────────────────────────────────────────┘
```

Hai mũi tên vào DB có ý nghĩa khác nhau:
- **Tiền vào** (trái): cổng thanh toán gọi **IPN webhook** → `billing.apply_topup` cộng credit (idempotent). KHÔNG tin redirect trình duyệt. Chi tiết [10-payments.md](10-payments.md).
- **Credit → video** (phải): `POST /v1/jobs` HOLD credit → worker render → SETTLE/REFUND.

---

## 2. Luồng 1 request tạo video — end-to-end (đường đi thật)

Đây là đường đi của **đúng 1 lần bấm "Tạo video"**, bám theo code thật. File:dòng ghi kèm để bạn lần ngược được.

### Bước 0 — User đã có credit
Trước đó user nạp tiền (IPN webhook → `apply_topup`), hoặc dùng free grant `FREE_GRANT_CREDITS=300` cấp khi `bootstrap` org lần đầu (`app_api/config.py:74`). Xem [08-pricing-plans-credits.md](08-pricing-plans-credits.md) + [09-free-tier-abuse.md](09-free-tier-abuse.md).

### Bước 1 — Web gọi `POST /v1/jobs`
Web gửi spec (mode/thể loại, seconds, resolution, input...) + `Bearer JWT` + `idempotency_key`. Router: `app_api/routers/jobs.py:61` (`create_job`).

### Bước 2 — Validate + clamp theo plan
`validate_and_clamp(spec_input, plan_code)` (`routers/jobs.py:69` → `app_api/validate.py`). Free plan bị siết cứng (480p / ≤ thời lượng / provider rẻ / watermark). Sai → `422`. **Đây là cửa chặn lạm dụng/chi phí đầu tiên** — xem [09-free-tier-abuse.md](09-free-tier-abuse.md).

### Bước 3 — HOLD credit (1 transaction NGẮN có RLS)
Trong `tenant_session(org_id)` (`routers/jobs.py:76`):
- `jobs_svc.create_job` (`app_api/jobs.py:56`): chèn `Job(status=QUEUED)` + gọi `wallet.hold(...)`.
- Báo giá: `estimate_hold` (`jobs.py:37`) → `estimate_job_cost` (`video_engine/providers/routing.py:72`) ra `est_usd` → `usd_to_credits` (`pricing.py`).
- **HOLD = `ceil(est_credits × 1.5)`** (`jobs.py:45`) — giữ dư 50% để render thật không vượt báo giá.
- Idempotent theo `(org_id, idempotency_key)` (`jobs.py:59`): bấm 2 lần = 1 job, không HOLD đôi.
- Hết credit → `InsufficientCredits` → HTTP `402` (cửa chặn cuối, có `CHECK(balance≥0)` ở DB).
- **COMMIT** kết thúc transaction ngắn → khoá ví được nhả NGAY (không giữ lock qua lúc gọi API render chậm). Ranh giới này nằm ở `app_api/db.py:67` (`tenant_session`).

### Bước 4 — Enqueue SAU commit
`submit_job(org_id, job_id, background_tasks)` (`app_api/executor.py:15`), chạy **sau** khi commit để worker chắc chắn thấy job:
- `JOB_EXECUTION_MODE=inline` (mặc định hiện tại, `config.py:78`): đẩy `worker.run_job` vào FastAPI `BackgroundTasks` (Starlette chạy trong threadpool). **POST trả về NGAY** với `job_id` + số dư sau HOLD.
- `JOB_EXECUTION_MODE=queue` (🔜): enqueue Arq vào Redis. **Hiện `executor.py:19` còn `raise RuntimeError` — chưa nối Arq.** Đây là việc "bật queue mode" ở [05-queue-worker-rendering.md](05-queue-worker-rendering.md).

> Hợp đồng `POST /v1/jobs` KHÔNG đổi khi chuyển inline→queue. Chỉ đổi 1 env var + nối hàm enqueue.

### Bước 5 — Worker render (KHÔNG giữ DB)
`worker.run_job(org_id, job_id)` (`app_api/worker.py:26`):
1. transaction NGẮN: load job → `mark_running` (RUNNING) → tạo `workdir` tạm → `build_job_spec` (`jobs.py:89`, đọc `Job.params` JSONB = dict `JobSpec`).
2. `render(spec, QueueSink(org_id, job_id))` (`worker.py:39`) — **không giữ DB transaction trong lúc render**. `QueueSink` (`app_api/sink_queue.py`) tự mở session NGẮN để ghi `job_events` (live progress) + persist `piapi_task_id` ngay khi tạo i2v task (chống trả tiền 2 lần khi worker crash).

### Bước 6 — Engine stateless gọi providers
`video_engine/render_service.py:54` (`render(spec, sink)`):
- Chỉ làm `product_ad` / `premium` (+ nhánh `kol_full`). `long_narrative` / `film_recap` còn `NotImplementedError` (xem [00-overview.md](00-overview.md) + VISION §3).
- Pipeline: ảnh (fal Flux) → giọng Việt (Vbee/VieNeu) → video (PiAPI/fal Seedance/Kling) → QA → compose `final.mp4`.
- Trả `RenderResult(status, path, cost_usd, fault_class, stage_timings, ...)` (`video_engine/spec.py`).
- **Đây là ranh giới sạch:** engine không biết gì về org/ví/DB. Chi tiết providers + routing: [06-providers.md](06-providers.md).

### Bước 7 — Upload storage TRƯỚC khi ghi DB
`worker.py:43`: nếu READY → `storage.store_output(final.mp4, job_id)` (`app_api/storage.py:29`) upload lên R2/S3 (nếu `VIETVID_S3_*` cấu hình), trả về object key/URL. Lỗi upload **degrade graceful** — giữ file local, không làm hỏng job. Chi tiết [04-storage-media.md](04-storage-media.md).

### Bước 8 — complete_job: SETTLE / REFUND ví + ghi video
transaction NGẮN cuối (`worker.py:47` → `complete_job` ở `jobs.py:120`):
- READY → chèn `Video(storage_url, ...)` + `notify` "Video đã sẵn sàng".
- Map RenderResult → ví (`jobs.py:162`):

| RenderResult | Hành động ví | File:dòng |
|---|---|---|
| `READY` / `QA_FAIL` | **SETTLE** theo chi phí thật (≤ hold), hoàn phần thừa | `jobs.py:163` |
| `FAILED` + `fault_class="system"` | **REFUND 100%** hold (lỗi hệ thống = hoàn hết) | `jobs.py:166` |
| `FAILED` + lỗi input | **SETTLE** theo chi phí thật | `jobs.py:168` |
| `WAITING_CONFIG` | **GIỮ hold** (retry sau, không settle/refund) | `jobs.py:171` |

- Mỗi job: HOLD rồi **đúng một** trong {SETTLE, REFUND}, **idempotent**.

### Bước 9 — Dọn workdir + webhook B2B
`worker.py:51`: job ở trạng thái CUỐI → `cleanup_workdir` (cloud: xoá sạch; local: giữ `final.mp4`, xoá ảnh/clip/voice trung gian). Best-effort báo `webhooks.notify_terminal` cho Product C (B2B).

### Bước 10 — Web poll trạng thái + lấy video
Web gọi `GET /v1/jobs/{id}` tới khi READY → lấy video qua **signed URL** (media router). Reaper quét job kẹt RUNNING quá `REAPER_STUCK_MINUTES=15` → hoàn HOLD + CANCELLED (`reaper.py`, `config.py:171`). Xem [05-queue-worker-rendering.md](05-queue-worker-rendering.md).

---

## 3. Ranh giới stateless engine (bất biến nền — đừng phá)

| Nguyên tắc | Vì sao | Bằng chứng |
|---|---|---|
| `render(spec, sink)` **KHÔNG đọc/ghi DB** | Engine tái dùng được cho B (web) lẫn C (API/white-label); test được không cần DB | `render_service.py:1-16` (docstring), `worker.py:37` (comment "KHÔNG giữ DB") |
| Mọi trạng thái/asset đi qua `sink.*` | DB-coupling chỉ ở `QueueSink` (app_api), engine chỉ phát event | `sink_queue.py` kế thừa `NullSink` |
| Tiền (HOLD/SETTLE/REFUND) **chỉ ở app_api** | Engine không biết org/ví; chi phí trả về trong `RenderResult` | `render_service.py:8-9` (comment), `jobs.py:complete_job` |
| Worker mở transaction NGẮN ở **đầu/cuối**, KHÔNG giữ qua lúc render | Render gọi API ngoài chậm (chục giây–phút); giữ lock = treo ví/PgBouncer | `worker.py:26-49` |

⚠️ `video_engine/pipeline.py` là bản GỐC stateful (di sản affiliatebot) — **KHÔNG dùng trong Vyra**, chỉ tái dùng helper thuần (`_ensure_product_image`, `_build_product_facts`...). Đừng gọi `pipeline.run_job`.

---

## 4. Đa-tenant qua RLS (bất biến nền)

Cô lập dữ liệu giữa các org bằng Postgres **Row Level Security FORCE** (fail-closed):

- Bảng tenant bật `ENABLE + FORCE ROW LEVEL SECURITY`, policy `org_isolation` = `org_id = nullif(current_setting('vietvid.current_org', true),'')::uuid`. **Chưa set GUC = thấy 0 dòng** (an toàn mặc định).
- Mọi truy cập bảng tenant đi qua `app_api.db.tenant_session(org_id)` (`db.py:67`): `SET LOCAL vietvid.current_org = :org` ngay đầu transaction (an toàn PgBouncer transaction-mode).
- GUC key cấu hình ở `config.py:50` (`RLS_GUC = "vietvid.current_org"`).
- `FORCE RLS` áp **cả owner** → cron toàn-org (vd `audit_all`) cần role **BYPASSRLS**.
- Bảng GLOBAL (đọc pre-auth, không RLS): allowlist trong `models.py` (`memberships`, `org_invitations`, `vv_affiliate_links`, `vv_link_clicks`, `audit_log`, `vv_api_keys`).
- Mọi query vẫn lọc `org_id` tường minh (RLS = lưới an toàn; `WHERE org_id` = index path).

Chi tiết schema + migration: [03-database.md](03-database.md). Chi tiết đe doạ/bảo mật: [15-security.md](15-security.md).

---

## 5. Các thành phần & trách nhiệm (ai làm gì)

| Thành phần | Thư mục/file | Trách nhiệm | Trạng thái |
|---|---|---|---|
| **Web** | `apps/web/` (Next.js 14) | UI/UX, gọi api qua Bearer JWT, poll job, hiển thị video | ✅ |
| **HTTP API** | `app_api/main.py` + `routers/*` | auth, tenancy, validate/clamp, billing, jobs, admin | ✅ |
| **Auth** | `routers/auth.py` + `config.py:52-67` | JWT dual-mode (Supabase JWKS/HS256 **hoặc** dev HS256) | ✅ |
| **Tenancy/RLS** | `db.py` (`tenant_session`) + `models.py` | cô lập org bằng RLS GUC | ✅ |
| **Ví (wallet)** | `wallet.py` + `routers/wallet.py` | HOLD/SETTLE/REFUND ACID, ledger append-only | ✅ verify thật |
| **Pricing** | `pricing.py` + `config.py:46-47` | điểm quy đổi USD→credit DUY NHẤT | ✅ |
| **Jobs orchestration** | `jobs.py` (create/build/complete) | nối ví ↔ engine | ✅ |
| **Executor (seam)** | `executor.py` | chọn inline / queue runner | ⚙️ inline ✅, queue 🔜 |
| **Worker** | `worker.py` | pull job → render → complete + cleanup | ✅ (inline) |
| **Sink** | `sink_queue.py` (`QueueSink`) | forward stage events → `job_events`, persist `piapi_task_id` | ✅ |
| **Engine** | `video_engine/render_service.py` (`render`) | render STATELESS, gọi providers | ⚙️ product_ad/premium ✅; long_narrative/film_recap 🔜 |
| **Provider routing** | `video_engine/providers/routing.py` | chọn model + ước tính chi phí | ✅ (⚠️ phụ thuộc `config.settings` di sản — xem [06-providers.md](06-providers.md)) |
| **Storage** | `storage.py` | upload final.mp4 R2/S3 + cleanup workdir | ⚙️ code ✅, R2 chưa cấu hình prod |
| **Reaper** | `reaper.py` + `config.py:168-173` | quét job treo + workdir → hoàn HOLD | ✅ |
| **Billing/IPN** | `billing.py` + `routers/billing.py` | VietQR + SePay IPN idempotent | ✅ verify thật |
| **Admin** | `routers/admin.py` | vận hành cho solo founder | ⚙️ một phần |
| **DB** | Postgres + `alembic/` (→ 0011) | ACID + RLS + migrations | ✅ |
| **Queue/Redis** | (Arq — chưa nối) | hàng đợi render prod | 🔜 |
| **Mobile** | Flutter | self-serve B2C | 🔜 (M4) |
| **Public API** | `routers/api_public.py` + `vv_api_keys` | engine làm API/white-label | 🔜 (M5, Product C) |

---

## 6. Hai chế độ thực thi (so sánh nhanh)

| | inline (M1, ĐANG dùng) | queue (prod đích) |
|---|---|---|
| Env | `JOB_EXECUTION_MODE=inline` (mặc định) | `JOB_EXECUTION_MODE=queue` |
| Runner | FastAPI `BackgroundTasks` (cùng tiến trình app) | Arq worker fleet + Redis |
| Scale | ❌ render chiếm threadpool app; redeploy = mất job đang chạy | ✅ tách worker, scale ngang, retry |
| Trạng thái code | ✅ chạy thật | 🔜 `executor.py:19` còn `raise RuntimeError` — **chưa nối Arq** |
| Hợp đồng `POST /v1/jobs` | giống hệt | giống hệt (chỉ đổi runner) |

→ Việc bật queue (cài Arq, viết `app_api/queue.py`, chạy worker process) ở [05-queue-worker-rendering.md](05-queue-worker-rendering.md). Hạ tầng Redis (Upstash/Railway) ở [02-infrastructure.md](02-infrastructure.md).

---

## 7. Bản đồ "lỗi ở đâu thì xem file nào" (cho điều tra)

| Triệu chứng | Nghi can | File |
|---|---|---|
| User bị trừ credit oan / không hoàn khi lỗi | map RenderResult→ví | `jobs.py:complete_job` (162-171) |
| Org A thấy data org B | RLS/GUC chưa set | `db.py:tenant_session`, `models.py` (allowlist) |
| POST /jobs trả 402 dù vừa nạp | IPN chưa cộng / free grant thấp | `billing.py:apply_topup`, `config.py:74` |
| Job kẹt RUNNING mãi | worker chết, reaper tắt | `reaper.py`, `config.py:171` |
| Render xong nhưng không tải được video | upload storage lỗi / signed URL | `storage.py:store_output`, `routers/media.py` |
| Tạo job 2 lần cộng tiền đôi | idempotency_key | `jobs.py:59` |

Chi tiết log/request-id để Claude lần vết: [12-logging-observability.md](12-logging-observability.md). Sổ tay sự cố: [18-runbooks.md](18-runbooks.md).

---

## Việc cần làm (checklist)

- [ ] Nối Arq vào `executor.py` (xoá `raise RuntimeError`, viết `app_api/queue.py:enqueue_render`) — chi tiết [05-queue-worker-rendering.md](05-queue-worker-rendering.md).
- [ ] Bật `JOB_EXECUTION_MODE=queue` ở prod + chạy worker process riêng.
- [ ] Cấu hình Redis prod (Upstash/Railway) — xem [02-infrastructure.md](02-infrastructure.md).
- [ ] Cấu hình `VIETVID_S3_*` (Cloudflare R2) để `store_output` upload thật — [04-storage-media.md](04-storage-media.md).
- [ ] Gỡ phụ thuộc `config.settings` di sản trong `routing.py` (hoặc xác nhận `config/settings.py` deploy kèm) — [06-providers.md](06-providers.md).
- [ ] Tạo role DB BYPASSRLS cho cron toàn-org trước khi bật cron prod — [03-database.md](03-database.md).
- [ ] Đo chi phí render THẬT/video sau khi cắm key provider → cập nhật báo giá `estimate_job_cost` nếu lệch — [07-economics.md](07-economics.md).
