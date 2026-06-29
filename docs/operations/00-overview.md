# Tổng quan dự án như một công ty

Mục đích: cho chủ dự án (solo, không chuyên hạ tầng) và các phiên Claude sau một bức tranh "Vyra là gì, gồm những mảnh nào, vận hành ra sao" — đủ để biết khi cần thì mở file nào trong bộ tài liệu này.

**Trạng thái:** ⚙️ một phần — lõi sản phẩm (engine + ví + RLS + HTTP + thanh toán bank) đã build và verify thật; phần VẬN HÀNH PROD (queue mode, R2 storage, render thật bằng API bên thứ 3, hosting managed) phần lớn 🔜 chưa bật. Bộ tài liệu này mô tả cách đưa nó lên prod đúng cách.

**Liên quan:** đây là file gốc của bộ `docs/operations/`. Ngữ cảnh sản phẩm đầy đủ ở [../VISION.md](../VISION.md) (định vị + roadmap) và [../HANDOFF.md](../HANDOFF.md) (ngữ cảnh kỹ thuật). Build-spec chi tiết: [../designs/SYSTEM_DESIGN.md](../designs/SYSTEM_DESIGN.md).

---

## 1. Vyra là gì (1 câu)

**Vyra là SaaS đa-tenant tạo MỌI loại video bằng AI cho người Việt — giọng Việt thật, giá minh bạch (hiện credit trước khi tiêu, hoàn 100% khi lỗi hệ thống).**

Người dùng vào web → chọn thể loại (quảng cáo/affiliate, video trend, phim ngắn AI, KOL, kể chuyện) → đưa input (ý tưởng/ảnh/link/kịch bản) → Vyra dựng video hoàn chỉnh (hình + giọng Việt + nhạc + phụ đề) → tải/chia sẻ.

> Tên cũ trong code vẫn là "vietvid" (env `VIETVID_*`, file `_vietvid_db_url.txt`, GUC `vietvid.current_org`). Tên thương hiệu là **Vyra**. Đừng đổi prefix env — sẽ vỡ config.

## 2. Mô hình kinh doanh (1 dòng)

**Mua sỉ API render (video/ảnh/giọng) → bán lại cho người dùng qua credit có markup → biên gộp ~40-60% nếu định giá đúng.**

- Người dùng nhận **VIDEO** (sản phẩm cuối), KHÔNG nhận quyền truy cập API → đây là markup SaaS hợp lệ, **với điều kiện** mua đúng gói API thương mại (đọc ToS Vbee/PiAPI/fal trước khi bán).
- Quy đổi tiền DUY NHẤT (xem [08-pricing-plans-credits.md](08-pricing-plans-credits.md)): `credits(usd) = ceil(usd × USD_TO_VND / CREDIT_PRICE_VND)` — định nghĩa ở `app_api/config.py:46-47`, mặc định `CREDIT_PRICE_VND=150`, `USD_TO_VND=25400`.
- Doanh thu = nạp credit (gói subscription + nạp lẻ). Chi phí lớn nhất = **render video** (~3.000-12.000đ/video — **ước lượng, cần đo thật**, xem [07-economics.md](07-economics.md)). Giọng Vbee rẻ (~vài trăm đồng/video — cũng cần đo).

> ⚠️ TRUNG THỰC: Vyra mới ra mắt, CHƯA có số liệu thật về chi phí/doanh thu. Mọi con số tiền trong bộ tài liệu phải ghi rõ "ước lượng, cần đo thật" + cách đo. CẤM bịa.

## 3. Sơ đồ các mảnh

Hình dung Vyra như một công ty nhỏ với các "phòng ban" là các thành phần phần mềm:

```
                    NGƯỜI DÙNG (trình duyệt / mobile sau)
                              │  Bearer JWT
        ┌─────────────────────┼──────────────────────┐
        ▼                     ▼                       ▼
   WEB USER              WEB ADMIN               PUBLIC API (Product C, 🔜)
  (apps/web)         (apps/web /admin)          (app_api/routers/api_public.py)
   Next.js 14            solo founder
        │                support+vận hành
        └──────────────┬──────────────────────────────┘
                       ▼
              app_api (FastAPI đa-tenant)  ✅
   auth · tenancy(RLS) · wallet(ACID) · billing · jobs · admin
                       │
        POST /jobs → validate → HOLD credit → enqueue
                       ▼
         QUEUE (Arq + Redis)  ⚙️ có code, 🔜 chưa bật prod
                       │
                       ▼
         WORKER → engine render(spec, sink)  ✅ stateless, KHÔNG chạm DB
                       │   gọi API render bên thứ 3 (🔜 chưa cắm key prod):
                       │   video: PiAPI/fal (Kling/Seedance) · ảnh: Flux(fal) · giọng: Vbee
                       ▼
        upload final.mp4 → STORAGE (Cloudflare R2)  🔜
                       │
                       ▼
        complete_job → SETTLE/REFUND ví + ghi videos/job_events
                       │
        ┌──────────────┴───────────────┐
        ▼                              ▼
   POSTGRES (ACID + RLS) ✅      THANH TOÁN (VN trước)
   sổ cái tiền + tenant          VietQR + SePay IPN ✅ · MoMo 🔜 · Stripe 🔜
```

### Bảng các mảnh + trạng thái + file tài liệu

| Mảnh | Vai trò ("phòng ban") | Code chính | Trạng thái | Tài liệu |
|---|---|---|---|---|
| Web user | Mặt tiền tạo video self-serve | `apps/web/` (Next.js 14) | ✅ UI premium nhiều màn | [16-i18n.md](16-i18n.md) |
| Web admin | Bàn điều khiển solo founder (support, hoàn tiền, xem job) | `app_api/routers/admin.py` + `apps/web` admin | ⚙️ backend có, UI tuỳ | [11-admin-panel.md](11-admin-panel.md) |
| HTTP API | "Lễ tân + kế toán" — auth, ví, billing, jobs | `app_api/` (FastAPI) | ✅ M1 verified | [01-architecture.md](01-architecture.md) |
| Engine render | "Xưởng sản xuất" video, stateless | `video_engine/render_service.py` | ⚙️ product_ad/premium chạy; long_narrative/film_recap còn `NotImplementedError` | [05-queue-worker-rendering.md](05-queue-worker-rendering.md) |
| Queue + worker | "Dây chuyền" chạy render nền | `executor.py` `worker.py` `sink_queue.py` | ⚙️ có code, 🔜 bật prod | [05-queue-worker-rendering.md](05-queue-worker-rendering.md) |
| Providers AI | "Nhà cung cấp nguyên liệu" (video/ảnh/giọng) | `video_engine/providers/`, `video_stage/`, `voice/` | ⚙️ mock (thiếu key prod) | [06-providers.md](06-providers.md) |
| Ví / credit | "Sổ cái tiền" ACID | `app_api/wallet.py` `pricing.py` | ✅ verify thật | [07-economics.md](07-economics.md), [08-pricing-plans-credits.md](08-pricing-plans-credits.md) |
| Thanh toán | "Quầy thu ngân" | `app_api/billing.py` `routers/billing.py` | ✅ VietQR+SePay; 🔜 MoMo/Stripe | [10-payments.md](10-payments.md) |
| Database | "Kho hồ sơ" — tenant + sổ cái | Postgres + RLS + `alembic/` (→0011) | ✅ | [03-database.md](03-database.md) |
| Storage media | "Kho video" | `app_api/storage.py` (R2/S3) | ⚙️ code có, 🔜 cắm R2 | [04-storage-media.md](04-storage-media.md) |
| Hạ tầng/hosting | "Văn phòng" — nơi chạy prod | (chưa deploy) | 🔜 Railway/Vercel + R2 | [02-infrastructure.md](02-infrastructure.md) |
| Quan sát/log | "Camera an ninh" để debug | `app_api/observability.py` | ✅ structured log + request-id | [12-logging-observability.md](12-logging-observability.md) |
| Reaper | "Dọn dẹp" job treo + workdir | `app_api/reaper.py` | ✅ | [14-backup-dr-maintenance.md](14-backup-dr-maintenance.md) |

> Trạng thái lấy từ [../HANDOFF.md](../HANDOFF.md) §3, §7 và đọc code thật (`config.py`, `main.py`). Khi mâu thuẫn, đọc lại code rồi cập nhật ở đây.

## 4. Nguyên tắc vận hành (đã chốt — bám sát)

Các quyết định này chốt ở consultation 2026-06-29. Đừng re-litigate; nếu muốn đổi, ghi rõ lý do.

1. **Laptop = máy DEV thôi.** i7-13700H/16GB/512GB chỉ để code + QA local. KHÔNG chạy prod ở nhà (rủi ro uptime, mất sổ cái tiền, bảo mật). → [02-infrastructure.md](02-infrastructure.md).
2. **PROD = managed PaaS rẻ.** Railway (backend FastAPI + worker + Postgres + Redis, có thể chứa cả Next.js) HOẶC Vercel Pro (Next.js) + Railway (backend). Có thể khởi đầu Neon (Postgres) + Upstash (Redis) free-tier. → [02-infrastructure.md](02-infrastructure.md), [17-deployment-cicd.md](17-deployment-cicd.md).
3. **Render = API bên thứ 3.** Video PiAPI/fal (Kling/Seedance), ảnh Flux (fal), giọng Vbee. KHÔNG self-host GPU lúc này. → [06-providers.md](06-providers.md).
4. **Bật QUEUE mode cho prod.** Codebase đã có `JOB_EXECUTION_MODE=queue` (`config.py:78`, `executor.py`, `worker.py`, `sink_queue.py`) — chỉ cần bật + thêm Redis. → [05-queue-worker-rendering.md](05-queue-worker-rendering.md).
5. **Video lên Cloudflare R2** (egress 0đ → không cần ổ cứng to). → [04-storage-media.md](04-storage-media.md).
6. **Free tier siết cứng** vì render tốn tiền thật: 480p / ≤20s / có watermark / provider rẻ / giới hạn số video. → [09-free-tier-abuse.md](09-free-tier-abuse.md).
7. **Thanh toán VN trước** (MoMo/VietQR/SePay), quốc tế (Stripe/Visa) pha sau. Hoá đơn VAT khi khách công ty yêu cầu. → [10-payments.md](10-payments.md).
8. **Trung thực tuyệt đối.** Không bịa số liệu, không nút giả. "Đang bảo trì" trung thực hơn nút không hoạt động. Mọi tính năng "xong" phải verify bằng vận hành thật.
9. **Quan sát để Claude debug được.** Structured log + Sentry + request-id xuyên suốt → khi lỗi, đưa log cho Claude tự điều tra + fix. → [12-logging-observability.md](12-logging-observability.md).
10. **Admin mạnh** để solo founder tự support + bảo trì. → [11-admin-panel.md](11-admin-panel.md).
11. **Đa-tenant bất biến nền (RLS fail-closed).** Mọi truy cập bảng tenant qua `tenant_session(org_id)`; chưa set GUC = 0 dòng. → [03-database.md](03-database.md), [15-security.md](15-security.md).
12. **Ví ACID, một job HOLD rồi ĐÚNG MỘT trong {SETTLE, REFUND}, idempotent.** Lỗi hệ thống → hoàn 100%. → [07-economics.md](07-economics.md).

## 5. Cách đọc bộ tài liệu này

Bộ `docs/operations/` đi từ "công ty là gì" → từng hệ thống → kinh tế → vận hành → triển khai → tài chính. Đọc theo nhu cầu:

| Bạn muốn | Đọc file |
|---|---|
| Hiểu tổng thể (bạn đang ở đây) | 00-overview.md |
| Code chạy thế nào | [01-architecture.md](01-architecture.md) |
| Đưa lên prod chạy ở đâu | [02-infrastructure.md](02-infrastructure.md), [17-deployment-cicd.md](17-deployment-cicd.md) |
| DB / migration / sổ cái | [03-database.md](03-database.md) |
| Lưu + phát lại video | [04-storage-media.md](04-storage-media.md) |
| Render nền không treo app | [05-queue-worker-rendering.md](05-queue-worker-rendering.md) |
| Cắm nhà cung cấp AI | [06-providers.md](06-providers.md) |
| Tiền vào/ra mỗi video, có lời không | [07-economics.md](07-economics.md), [21-financial-model.md](21-financial-model.md) |
| Định giá gói + credit | [08-pricing-plans-credits.md](08-pricing-plans-credits.md) |
| Chống xài chùa | [09-free-tier-abuse.md](09-free-tier-abuse.md) |
| Nhận tiền + đối soát | [10-payments.md](10-payments.md) |
| Tự support + bảo trì | [11-admin-panel.md](11-admin-panel.md), [19-support.md](19-support.md) |
| Khi có sự cố | [12-logging-observability.md](12-logging-observability.md), [13-monitoring-uptime.md](13-monitoring-uptime.md), [18-runbooks.md](18-runbooks.md) |
| Sao lưu + phục hồi | [14-backup-dr-maintenance.md](14-backup-dr-maintenance.md) |
| An toàn + bí mật | [15-security.md](15-security.md) |
| Đa ngôn ngữ | [16-i18n.md](16-i18n.md) |
| Kế hoạch A-Z | [20-roadmap.md](20-roadmap.md) |

Mỗi file đầu có "Trạng thái:" + "Liên quan:", cuối có checklist `- [ ]`. Mọi file đọc độc lập được nhưng cross-link sang nhau bằng đường dẫn tương đối.

## 6. Glossary (thuật ngữ dùng xuyên suốt)

| Thuật ngữ | Nghĩa trong Vyra |
|---|---|
| **Tenant / org** | Một "tổ chức" = một không gian dữ liệu riêng. Mỗi user thuộc 1+ org; dữ liệu org này KHÔNG thấy org kia (RLS). Bảng `orgs`, GUC `vietvid.current_org`. |
| **Đa-tenant (multi-tenant)** | Nhiều org dùng chung 1 hệ thống nhưng cách ly dữ liệu. |
| **RLS (Row Level Security)** | Lưới an toàn DB: Postgres tự lọc dòng theo org đang set. "FORCE" = áp cả owner. "Fail-closed" = chưa set org = thấy 0 dòng. |
| **`tenant_session(org_id)`** | Hàm Python mở transaction ngắn, set `vietvid.current_org` đầu tiên → mọi query trong đó chỉ thấy org đó. Bắt buộc dùng để chạm bảng tenant. |
| **Credit** | Đơn vị tiền nội bộ user mua. Mặc định 1 credit ≈ 150đ (`CREDIT_PRICE_VND`). Render trừ credit. |
| **Ví / wallet** | Sổ tiền của org: `balance` (dùng được), `held` (đang giữ cho job đang chạy). `app_api/wallet.py`. |
| **Ledger** | Sổ cái append-only (chỉ thêm, không sửa/xoá — trigger chặn). Mỗi dòng = 1 giao dịch HOLD/SETTLE/REFUND/TOPUP/BONUS. |
| **HOLD** | Tạm giữ credit khi tạo job: `balance -= hold; held += hold`. `hold = ceil(est_credits × 1.5)` (đệm phòng vượt giá). |
| **SETTLE** | Chốt khi render xong: trừ thật `min(actual, hold)`, hoàn phần thừa, `held -= hold`. |
| **REFUND** | Lỗi HỆ THỐNG → hoàn 100% hold (user không mất tiền vì lỗi của ta). |
| **Job** | Một yêu cầu render. Vòng đời: tạo → HOLD → enqueue → worker render → complete (SETTLE/REFUND). `app_api/jobs.py`. |
| **Engine / `render(spec, sink)`** | "Xưởng" dựng video, **stateless** (không chạm DB). Nhận `spec` (mô tả video) + `sink` (nơi ghi kết quả). `video_engine/`. |
| **`spec`** | Bản mô tả video cần dựng (mode, kịch bản, ảnh, giọng...). `video_engine/spec.py`. |
| **`sink`** | Nơi engine ghi tiến độ + kết quả. Prod dùng `QueueSink` (`sink_queue.py`). |
| **mode** | Loại video engine: `product_ad` / `premium` / `kol_full` (chạy) · `long_narrative` / `film_recap` (chưa port). |
| **Provider** | Nhà cung cấp AI bên thứ 3: PiAPI/fal (video), Flux/fal (ảnh), Vbee (giọng). |
| **Queue mode (Arq + Redis)** | Chạy render nền bằng hàng đợi để không treo app + scale nhiều worker. `JOB_EXECUTION_MODE=queue`. |
| **Inline mode** | Chế độ hiện tại: render ngay trong tiến trình app qua BackgroundTasks. Không scale → chỉ dev/MVP. |
| **Reaper** | Tiến trình dọn job treo (RUNNING quá hạn → hoàn HOLD + CANCELLED) + dọn workdir. `app_api/reaper.py`. |
| **IPN (Instant Payment Notification)** | Webhook ngân hàng/cổng báo "tiền đã vào". Idempotent (replay không cộng đôi). Nguồn sự thật cho nạp tiền, KHÔNG tin redirect trình duyệt. |
| **SePay** | Dịch vụ đọc biến động số dư bank → gọi webhook Vyra tự cộng credit. ✅ đã build. |
| **VietQR** | Chuẩn QR chuyển khoản ngân hàng VN (sinh keyless qua img.vietqr.io). ✅ đã build. |
| **R2** | Cloudflare R2 = object storage tương thích S3, egress (tải về) miễn phí → rẻ cho video. |
| **Signed URL** | Link xem/tải video có chữ ký + hạn, không cần Bearer token. `app_api/media.py`. |
| **PaaS** | Platform-as-a-Service (Railway/Vercel): nơi chạy app mà không phải tự quản máy chủ. |

---

## Việc cần làm (checklist)

Đây là file gốc; các việc chi tiết nằm ở từng file con. Ở đây chỉ theo dõi mức "đã có khung tài liệu chưa":

- [ ] Viết xong toàn bộ 22 file `docs/operations/` (00 → 21) — file này là 00, các file khác 🔜.
- [ ] Khi mỗi hệ thống lên prod thật, cập nhật cột "Trạng thái" ở bảng §3 cho khớp code thật.
- [ ] Đo chi phí render thật (video/giọng) rồi điền vào [07-economics.md](07-economics.md) — bỏ chữ "ước lượng".
- [ ] Quyết hosting cuối: Railway-all-in-one hay Vercel + Railway (xem [02-infrastructure.md](02-infrastructure.md)).
- [ ] Bật queue mode + Redis trước khi mở cho nhiều người dùng (xem [05-queue-worker-rendering.md](05-queue-worker-rendering.md)).
