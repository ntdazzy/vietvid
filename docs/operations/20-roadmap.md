# Lộ trình triển khai A-Z

Mục đích: cho chủ dự án (solo, không chuyên hạ tầng) một con đường **cầm tay chỉ việc** đưa Vyra từ "chạy local có mock" → "prod thật, có người dùng, có thu tiền". Mỗi pha có mục tiêu rõ, việc cụ thể (lệnh + file:dòng + env), định nghĩa "xong", và cách **verify bằng vận hành thật** (không tin pytest/mock xanh).

**Trạng thái:** ⚙️ một phần — lõi sản phẩm (engine + ví + RLS + HTTP + thanh toán bank) đã build & verify thật; phần vận hành prod (queue, R2 GC, render thật, payments go-live, observability, i18n, mở thể loại) phần lớn 🔜 chưa bật. File này là thứ tự bật chúng.

**Liên quan:** [00-overview.md](00-overview.md) (bức tranh tổng) · [02-infrastructure.md](02-infrastructure.md) (hosting) · [05-queue-worker-rendering.md](05-queue-worker-rendering.md) (queue chi tiết) · [04-storage-media.md](04-storage-media.md) (R2 + GC) · [06-providers.md](06-providers.md) (API render) · [10-payments.md](10-payments.md) (thanh toán) · [16-i18n.md](16-i18n.md) (đa ngôn ngữ) · [21-financial-model.md](21-financial-model.md) (hoà vốn). Ngữ cảnh nền: [../HANDOFF.md](../HANDOFF.md) + [../VISION.md](../VISION.md).

> ⚠️ Đọc trước khi bắt đầu: laptop i7-13700H/16GB = **MÁY DEV**, KHÔNG chạy prod ở nhà (rủi ro uptime + mất sổ cái tiền + bảo mật). Prod = PaaS managed rẻ (Railway/Vercel + Neon/Upstash + Cloudflare R2). Render = API bên thứ 3, KHÔNG self-host GPU lúc này.

---

## Bản đồ pha (đọc dọc từ trên xuống)

| Pha | Tên | Mục tiêu một câu | Tiền điều kiện | Trạng thái |
|---|---|---|---|---|
| 0 | Dọn nền + queue + R2 | App chạy đúng kiến trúc prod (queue mode, video lưu R2), CHƯA cần khách | Code hiện tại | ⚙️ một phần (seam có, chưa nối) |
| 1 | Bật render thật | Có API key → tạo ra video THẬT (hết mock) | Pha 0 | 🔜 thiếu key |
| 2 | Payments go-live | Khách nạp tiền thật → cộng credit tự động, đối soát đúng | Pha 1 | ⚙️ bank đã build, cần go-live |
| 3 | Admin + observability | Solo founder thấy được hệ thống + debug được khi lỗi | Pha 2 | ⚙️ admin có, log cần chuẩn |
| 4 | i18n + quốc tế | Web đa ngôn ngữ + Stripe cho khách nước ngoài | Pha 3 | 🔜 chưa làm |
| 5 | Mở thể loại | Phim ngắn AI / kể chuyện / trend render thật được | Pha 1 | 🔜 còn NotImplementedError |

> Pha 0→3 là đường tới "MVP có thu tiền tại VN". Pha 4-5 là mở rộng — làm sau khi có khách trả tiền thật. **Đừng nhảy cóc**: Pha 1 vô nghĩa nếu Pha 0 chưa xong (render xong không có chỗ lưu); Pha 2 vô nghĩa nếu Pha 1 chưa xong (bán credit mà không render được = lừa khách).

---

## PHA 0 — Dọn nền: queue mode + R2 storage + GC

**Mục tiêu:** App chạy đúng hình dạng prod *trước khi* có khách: render qua **hàng đợi** (không chặn API), video lưu **R2** (không phình ổ cứng), video quá hạn **tự dọn**. Làm pha này lúc còn 0 khách = sai sót không tốn tiền ai.

### 0.1 Bật queue mode (Arq + Redis) — 🔜 SEAM CÓ, CHƯA NỐI

> ⚠️ **Đính chính sự thật:** HANDOFF từng ghi "codebase đã có queue mode, chỉ bật". Thực tế: `app_api/executor.py:17-21` mới chỉ là **seam** — set `JOB_EXECUTION_MODE=queue` thì nó **raise RuntimeError** ("cần Arq worker — chưa nối"). Việc thật còn phải làm, KHÔNG phải bật cờ là xong.

Hiện trạng đúng (đọc `app_api/executor.py`, `app_api/worker.py`):
- `submit_job(org_id, job_id, background_tasks)` — `inline` chạy `worker.run_job` qua FastAPI `BackgroundTasks` (✅ chạy, KHÔNG scale: render chết theo tiến trình API khi redeploy).
- `worker.run_job(org_id, job_id)` — hàm **đồng bộ** đã hoàn chỉnh: load job → `mark_running` → `build_job_spec` → `render(spec, QueueSink)` → `store_output` → `complete_job` (SETTLE/REFUND) → dọn workdir → webhook. Đây là phần khó, **đã có và verify**.

Việc cần làm (chi tiết từng bước ở [05-queue-worker-rendering.md](05-queue-worker-rendering.md)):

1. `pip install arq` (thêm vào requirements).
2. Tạo `app_api/queue.py`: định nghĩa Arq `WorkerSettings` + hàm `enqueue_render(org_id, job_id)` (push vào Redis) + task wrapper gọi `worker.run_job(org_id, job_id)`.
3. Sửa `app_api/executor.py:17-19` — thay `raise RuntimeError` bằng `from app_api.queue import enqueue_render; enqueue_render(org_id, job_id)`.
4. Chạy worker process riêng: `arq app_api.queue.WorkerSettings`.
5. Set env: `JOB_EXECUTION_MODE=queue` (`config.py:78`) + `REDIS_URL` (Upstash free-tier để khởi đầu).

**Định nghĩa "xong":** với `JOB_EXECUTION_MODE=queue`, POST `/v1/jobs` trả `job_id` ngay (< 300ms), một worker process **tách rời** nhặt job và render; kill API process giữa chừng KHÔNG làm mất job (reaper hoặc Arq retry xử lý).

**Verify thật:**
```bash
# Terminal 1: API
JOB_EXECUTION_MODE=queue REDIS_URL=... VIETVID_DATABASE_URL="$(cat _vietvid_db_url.txt)" \
  /c/Python314/python -m uvicorn app_api.main:app --port 8099
# Terminal 2: worker
JOB_EXECUTION_MODE=queue REDIS_URL=... arq app_api.queue.WorkerSettings
# Terminal 3: tạo job qua HTTP thật, xác minh trả job_id NGAY rồi job chạy ở worker
```
Soi `job_events` trong DB để thấy stage chạy ở worker (không phải API). Kill Terminal 1 lúc job RUNNING → job vẫn hoàn tất ở worker.

### 0.2 Cấu hình R2 storage — ✅ CODE SẴN, ⚙️ CẦN SET ENV

Code đã hoàn chỉnh: `app_api/storage.py:29` `store_output()` — nếu `storage_configured()` (`config.py:187`) thì upload `final.mp4` lên S3/R2 qua boto3, trả URL; ngược lại giữ local. Worker đã gọi nó (`worker.py:44`). Cần:

1. Tạo bucket Cloudflare R2 (egress 0đ → KHÔNG cần ổ cứng to; xem [04-storage-media.md](04-storage-media.md)).
2. `pip install boto3` (storage.py import lazy).
3. Set env:
   | Env (`config.py:176-181`) | Giá trị |
   |---|---|
   | `VIETVID_S3_BUCKET` | tên bucket R2 |
   | `VIETVID_S3_ENDPOINT` | endpoint R2 (dạng `https://<acc>.r2.cloudflarestorage.com`) |
   | `VIETVID_S3_ACCESS_KEY` / `VIETVID_S3_SECRET_KEY` | R2 token (đọc qua os.environ, KHÔNG commit) |
   | `VIETVID_S3_REGION` | `auto` |
   | `VIETVID_S3_PUBLIC_BASE` | (tuỳ chọn) CDN/public base nếu bật |

**Định nghĩa "xong":** render xong → `videos` row có object key trỏ R2 (không phải đường dẫn local), workdir bị xoá (`worker.py:53` cloud-mode `keep=None`), tải lại video qua signed URL được.

**Verify thật:** chạy 1 job thật với R2 bật → mở R2 dashboard thấy file `videos/<job_id>.mp4` → gọi endpoint signed URL → tải file về xem được. Kiểm tmp local **trống** sau job (không phình).

### 0.3 GC xoá video quá hạn — 🔜 CHƯA NỐI

Sự thật (đọc `app_api/reaper.py`): reaper hiện chỉ (a) hoàn HOLD job treo, (b) đánh FAILED payment treo, (c) `sweep_old_workdirs` (xoá thư mục tmp mồ côi). **KHÔNG có** GC xoá object R2 theo `videos.expires_at`. Video sẽ tích vĩnh viễn trên R2 → tốn tiền dần.

Việc cần làm:
1. Trong `reaper.reap_stuck_jobs` (hoặc hàm GC mới), thêm bước quét `videos` có `expires_at < now()` → xoá object R2 (`boto3 delete_object`) → đánh dấu row đã GC.
2. Đảm bảo cron toàn-org dùng role **BYPASSRLS** (FORCE RLS áp cả owner — xem HANDOFF §1).

**Định nghĩa "xong":** video quá hạn (theo `expires_at` của gói) tự biến mất khỏi R2 + DB, không cần tay.

**Verify thật:** set `expires_at` 1 video về quá khứ → chạy reaper → object biến mất khỏi R2, row đánh dấu GC. Đo dung lượng bucket trước/sau.

---

## PHA 1 — Bật render THẬT (điền API key)

**Mục tiêu:** Hết mock. User tạo video → ra video THẬT (hình AI + giọng Việt + nhạc + phụ đề). Đây là pha biến Vyra từ "demo đẹp" → "sản phẩm dùng được".

> ⚠️ Sự thật về kiến trúc: engine `video_engine/render_service.py` vẫn import `config.settings` + `core.*` (config legacy của project gốc), KHÔNG đọc thuần `app_api/config.py`. Provider/giá đọc từ `settings.video_seedance_prices_json`, `settings.video_provider`... → bật render thật là chuyện cấu hình **lớp settings của engine**, không chỉ env app_api. Đọc kỹ [06-providers.md](06-providers.md) để biết chính xác từng knob.

### 1.1 Điền key render

Trạng thái key (HANDOFF §7):
| Key | Trạng thái | Dùng cho |
|---|---|---|
| `_fal_key.txt` (fal.ai) | ✅ có | ảnh Flux + i2v (đã dùng gen ảnh marketing) |
| `_vietvid_db_url.txt` | ✅ có | Postgres |
| `GEMINI_API_KEY` | ❌ thiếu | ảnh + video thật + kịch bản (đang mock) |
| `GROQ_API_KEY` | ❌ thiếu | kịch bản sắc hơn (đang template) |
| `PIAPI_API_KEY` | ❌ thiếu | video Seedance (đang mock) |

Việc: lấy key từ nhà cung cấp (PiAPI/fal cho video, Vbee cho giọng — xem [06-providers.md](06-providers.md)), set qua env/secret file, set `settings.video_provider` khác `"mock"` (`render_service.py:66` `is_mock`). Cần điền `VIDEO_SEEDANCE_PRICES_JSON` thật (routing.py:34 đọc giá từ đây — KHÔNG có giá thì `route_video` raise).

**Định nghĩa "xong":** một job product_ad thật chạy hết stage DIRECTING→IMAGING→RENDERING_VIDEO→VOICING→COMPOSING→QA, ra `final.mp4` có hình động + giọng Việt thật.

**Verify thật (real-qa, BẮT BUỘC):** tạo job qua web thật → **xem video output**: trích vài khung hình (đúng sản phẩm/cảnh chưa?) + nghe lại giọng (giọng Việt thật, khớp lời, không tụt edge-tts âm thầm). Kiểm `job_events` có cost_usd thật mỗi stage. Kiểm ví: HOLD → SETTLE đúng `min(actual, hold)`.

### 1.2 Đo chi phí thật mỗi loại video

**TRUNG THỰC:** chi phí ~3.000-12.000đ/video là **ước lượng, CHƯA đo**. Pha này phải đo thật.

Cách đo: chạy ~5-10 job mỗi loại (draft 480p / product_ad / premium 720p / kol_full) → đọc `actual_cost_usd` (worker ghi qua `complete_job`) hoặc tổng `cost_usd` trong `job_events` → quy ra VND (× `USD_TO_VND`). Ghi bảng thật vào [07-economics.md](07-economics.md).

**Định nghĩa "xong":** có bảng chi phí THẬT/loại video (min/median/max), thay thế con số ước lượng. Đây là input bắt buộc cho [08-pricing-plans-credits.md](08-pricing-plans-credits.md) và [21-financial-model.md](21-financial-model.md).

### 1.3 Siết free tier (render tốn tiền thật)

Vì giờ render = tiền thật, free tier PHẢI siết: 480p / ≤20s / watermark / provider rẻ (draft seedance-2-fast) / giới hạn số video. Validate theo plan đã có ở `app_api/validate.py` (clamp). Chi tiết: [09-free-tier-abuse.md](09-free-tier-abuse.md).

**Verify thật:** user free thử vượt giới hạn → bị clamp/từ chối; user trả phí render được res cao + không watermark.

---

## PHA 2 — Payments go-live (thu tiền thật)

**Mục tiêu:** Khách nạp tiền thật → credit tự cộng đúng, đối soát khớp, không cộng đôi, không cộng nhầm. Tiền là chỗ KHÔNG được sai.

### 2.1 Bật VietQR + SePay thật — ✅ ĐÃ BUILD + verify e2e, ⚙️ CẦN SET ENV THẬT

Code đã verify e2e thật (HANDOFF §4: nạp +2000, replay không cộng đôi, sai số tiền không cộng, token sai 401). Chỉ cần set env thật:
| Env (`config.py:113-118`) | Ý nghĩa |
|---|---|
| `VIETVID_BANK_BIN` | mã BIN ngân hàng (vd 970436 = VCB) |
| `VIETVID_BANK_ACCOUNT` / `_NAME` | số + tên tài khoản nhận |
| `VIETVID_BANK_NAME` | tên hiển thị |
| `VIETVID_SEPAY_TOKEN` | token xác thực webhook SePay (đọc env, KHÔNG in ra) |

**Định nghĩa "xong":** khách quét QR → chuyển khoản thật → SePay webhook `/v1/billing/ipn/sepay` cộng credit idempotent. Chi tiết đối soát: [10-payments.md](10-payments.md).

**Verify thật:** chuyển 1 khoản nhỏ thật vào tài khoản → credit cộng đúng số (theo `CREDIT_PRICE_VND`), ledger có row, **gửi lại webhook cùng id → KHÔNG cộng đôi**, sai số tiền → không cộng.

### 2.2 MoMo (khi có merchant) — ⚙️ seam config có

`config.py:98-107` có `MOMO_*` + `momo_configured()`. Bật khi có merchant MoMo. VNPay tương tự (`config.py:85-94`). USDT: "đang bảo trì" (trung thực, chốt với user) — KHÔNG làm nút giả.

### 2.3 Tắt cổng dev ở prod

Set `VIETVID_ENV=production` (`config.py:31`) → tự tắt `/v1/dev/token` (`DEV_AUTH_ENABLED`) + cổng billing dev (`BILLING_DEV_ENABLED`). Startup gate từ chối boot nếu `DEV_JWT_SECRET` còn placeholder (`config.py:145`). Hoá đơn VAT: làm khi khách công ty yêu cầu.

**Verify thật:** ở prod, gọi `/v1/dev/token` → 404/403; nạp dev → từ chối.

---

## PHA 3 — Admin + observability (solo founder vận hành được)

**Mục tiêu:** Một người (chủ dự án) support + bảo trì được; khi lỗi, **Claude debug được** từ log.

### 3.1 Admin panel — ⚙️ ĐÃ CÓ, mở rộng dần

`app_api/routers/admin.py` có. Set `VIETVID_ADMIN_EMAILS` (`config.py:192`) = email super-admin. Mở rộng theo nhu cầu support: xem user/ví/job, hoàn tiền tay, khoá user. Chi tiết: [11-admin-panel.md](11-admin-panel.md).

### 3.2 Log có cấu trúc + request-id + Sentry — ⚙️ knob có

`config.py:131-132` `LOG_JSON` (JSON cho prod) + `LOG_LEVEL`. Thiết kế để Claude điều tra: structured log + request-id xuyên suốt + Sentry. Chi tiết: [12-logging-observability.md](12-logging-observability.md).

**Định nghĩa "xong":** khi 1 job lỗi, mở log thấy được request-id → trace toàn bộ stage → biết lỗi ở provider nào, fault system hay input (`render_service` phân loại `fault_class`).

### 3.3 Monitoring + uptime + backup

Health-check + alert khi down ([13-monitoring-uptime.md](13-monitoring-uptime.md)); backup Postgres định kỳ + thử restore ([14-backup-dr-maintenance.md](14-backup-dr-maintenance.md)); runbook sự cố ([18-runbooks.md](18-runbooks.md)).

**Verify thật:** giả lập down (tắt API) → nhận alert. Backup → restore vào DB rỗng → dữ liệu khớp.

---

## PHA 4 — i18n + quốc tế

**Mục tiêu:** Web đa ngôn ngữ + thu tiền khách nước ngoài. **Làm sau khi VN có khách trả tiền thật** — đừng phân tán sớm.

### 4.1 i18n — 🔜 CHƯA LÀM (xác nhận: `next-intl` chưa có trong `apps/web/package.json`, không có `middleware.ts`)

Việc (chi tiết [16-i18n.md](16-i18n.md)):
1. `bun add next-intl` trong `apps/web/`.
2. Routing `/[locale]/...` + `middleware.ts` tự nhận locale theo IP (header geo Vercel/Cloudflare) + cookie override.
3. Locale: `vi/en/ja/zh/ko/es`. Nội dung theo vùng (vd "giọng Việt đỉnh cao" CHỈ khi vi/VN).

**Định nghĩa "xong":** vào từ IP nước ngoài → web tự ra ngôn ngữ phù hợp; đổi cookie override được; không vỡ tiếng Việt.

### 4.2 Stripe/Visa cho khách quốc tế

Pha sau VN (MoMo/VietQR đã trước). Thêm cổng Stripe vào billing.

**Verify thật:** test mode Stripe → nạp credit từ thẻ quốc tế → cộng đúng, IPN idempotent.

---

## PHA 5 — Mở thể loại (multi-genre engine)

**Mục tiêu:** Render thật được các thể loại ngoài quảng cáo: phim ngắn AI nguyên gốc, kể chuyện, trend.

Sự thật (đọc `render_service.py:61-64` + VISION §3): mode `long_narrative` / `film_recap` còn **raise NotImplementedError** — chúng kéo helper DB của `pipeline.*` + phụ thuộc `module4_dispatch`/`module5_revenue` (2 module **không có trong repo**). `trend_distiller` mới là 1 bước directing, chưa thành mode riêng.

Việc thật:
1. Port `long_narrative` (phim ngắn cinematic) sang stateless `render(spec, sink)`, cắt phụ thuộc `core.*`/`pipeline.*`/`module4-5`.
2. Mỗi thể loại: spec + template + UX create (chọn thể loại trước) + giá/credit riêng.
3. Nâng `trend_distiller` thành mode/thể loại.

**Định nghĩa "xong" (1 thể loại):** chọn được ở web → render ra video ĐÚNG thể loại (thật, không mock) → ví HOLD/SETTLE/REFUND đúng → tải/chia sẻ được → **QA thật bằng xem video output** (trích khung hình + nghe lại giọng).

---

## Nguyên tắc xuyên suốt mọi pha

- **real-qa:** mỗi "xong" phải verify bằng hành vi thật (mắt thấy video/ảnh, DB row, log, HTTP thật). CẤM lấy pytest/tsc xanh làm bằng chứng (có mock → xanh vẫn có thể là data giả).
- **Trung thực số liệu:** Vyra mới ra mắt — số tiền/chi phí chưa đo phải ghi "ước lượng, cần đo thật" + cách đo. CẤM bịa.
- **Tiền không được sai:** mọi đường cộng tiền phải idempotent (đã verify cho bank; áp tương tự MoMo/Stripe).
- **Đừng nhảy cóc pha:** thứ tự 0→1→2→3 là đường tới MVP-có-thu-tiền-VN; 4-5 chỉ làm sau khi có khách trả tiền thật.

---

## Việc cần làm (checklist)

**Pha 0 — nền:**
- [ ] `pip install arq`; tạo `app_api/queue.py` (`enqueue_render` + Arq `WorkerSettings`)
- [ ] Nối `executor.py:17-19` gọi `enqueue_render` (thay `raise RuntimeError`)
- [ ] Set `JOB_EXECUTION_MODE=queue` + `REDIS_URL` (Upstash) — verify job chạy ở worker tách rời
- [ ] `pip install boto3`; tạo bucket R2; set `VIETVID_S3_*` — verify video lên R2 + workdir trống
- [ ] Thêm GC `videos.expires_at` vào reaper (xoá object R2 + đánh dấu) — verify video quá hạn biến mất

**Pha 1 — render thật:**
- [ ] Điền `PIAPI_API_KEY` / `GEMINI_API_KEY` / `GROQ_API_KEY` + key Vbee; set `settings.video_provider` ≠ mock
- [ ] Set `VIDEO_SEEDANCE_PRICES_JSON` giá thật (routing.py raise nếu thiếu)
- [ ] Chạy job thật mỗi loại → **xem video output** (khung hình + nghe giọng) — verify real-qa
- [ ] Đo chi phí THẬT/loại video → ghi bảng vào [07-economics.md](07-economics.md) (thay số ước lượng)
- [ ] Siết free tier (480p/≤20s/watermark/giới hạn) qua `validate.py` — verify clamp

**Pha 2 — payments:**
- [ ] Set `VIETVID_BANK_*` + `VIETVID_SEPAY_TOKEN` thật — verify nạp thật, không cộng đôi
- [ ] (khi có merchant) bật `VIETVID_MOMO_*`
- [ ] Set `VIETVID_ENV=production` — verify cổng dev tắt + startup gate chặn DEV_JWT placeholder

**Pha 3 — admin/observability:**
- [ ] Set `VIETVID_ADMIN_EMAILS`; kiểm admin panel xem/hoàn tay được
- [ ] Bật `VIETVID_LOG_JSON=1` + request-id + Sentry — verify trace 1 job lỗi từ log
- [ ] Cấu hình monitoring/alert + backup Postgres + thử restore

**Pha 4 — i18n/quốc tế:**
- [ ] `bun add next-intl`; routing `/[locale]` + `middleware.ts` (geo IP + cookie) — verify auto-locale
- [ ] Thêm Stripe (test mode) — verify nạp thẻ quốc tế idempotent

**Pha 5 — mở thể loại:**
- [ ] Port `long_narrative` sang stateless `render(spec, sink)` (cắt `core.*`/`pipeline.*`/`module4-5`)
- [ ] Mỗi thể loại: spec + template + UX chọn-thể-loại-trước + giá/credit
- [ ] QA thật từng thể loại (xem video output)
