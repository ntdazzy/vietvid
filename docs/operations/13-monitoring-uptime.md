# Giám sát & uptime

Cách biết Vyra còn sống hay đã sập — và biết SỚM, trước khi user phàn nàn. File này dạy bạn (solo founder) dựng giám sát rẻ/đủ-dùng bằng những endpoint đã có sẵn trong code, không phải hệ thống giám sát "doanh nghiệp" cồng kềnh.

**Trạng thái:** ⚙️ một phần — `/health` + `/health/ready` + reaper đã có trong code ✅; UptimeRobot/alert/dashboard ngoài 🔜 chưa cắm (cần làm khi deploy prod).

**Liên quan:** [02-infrastructure.md](02-infrastructure.md) (Railway/host), [05-queue-worker-rendering.md](05-queue-worker-rendering.md) (queue/worker), [06-providers.md](06-providers.md) (provider lỗi), [12-logging-observability.md](12-logging-observability.md) (log + Sentry), [18-runbooks.md](18-runbooks.md) (khi alert kêu thì làm gì), [11-admin-panel.md](11-admin-panel.md) (dashboard nội bộ).

---

## 1. Hai loại "sống" cần phân biệt

| Loại | Câu hỏi | Endpoint | Ý nghĩa |
|---|---|---|---|
| **Liveness** | Tiến trình còn chạy không? | `GET /health` | Trả 200 = process FastAPI còn thở. KHÔNG kiểm DB. |
| **Readiness** | Có sẵn sàng nhận traffic không? | `GET /health/ready` | Trả 200 nếu Postgres `SELECT 1` OK; **503** nếu DB chết → load balancer ngừng route. |

Hai cái này đã có thật trong code:

- `/health` — `app_api/main.py:132-138`. Trả `{status:"ok", auth_mode, exec_mode}`. ✅
- `/health/ready` — `app_api/main.py:141-148`, gọi `db_healthy()` (`startup_checks.py:60-68` = `SELECT 1`). 200 hoặc **503**. ✅

> Vì sao tách 2 cái: nếu monitor chỉ ping `/health`, app vẫn "xanh" dù Postgres đã chết (user không tạo được video nhưng bạn không biết). `/health/ready` mới bắt được DB chết. **Monitor uptime nên ping `/health/ready`.**

Thử ngay trên máy dev (backend chạy port 8099):

```bash
curl -s http://127.0.0.1:8099/health
# {"status":"ok","auth_mode":"dev","exec_mode":"inline"}
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8099/health/ready
# 200  (hoặc 503 nếu DB chết)
```

---

## 2. Startup gate — app TỪ CHỐI boot nếu prod cấu hình sai

Trước cả khi nói tới uptime, có một lớp bảo vệ "fail-fast lúc khởi động": `validate_prod_config()` (`startup_checks.py:26-57`). Khi `ENV=production`, nếu phát hiện cấu hình nguy hiểm thì **ném `UnsafeProdConfig` → app KHÔNG boot**. Đây là tính năng giám sát tốt nhất: lỗi bị chặn ngay, không âm thầm chạy sai.

Các điều kiện chặn boot (chỉ áp khi `IS_PROD`):

| Vấn đề | Điều kiện |
|---|---|
| Token giả mạo được | `auth_mode="dev"` mà `DEV_JWT_SECRET` còn placeholder/yếu (không có Supabase) |
| API mở toang | `CORS_ORIGINS=*` |
| Cổng dev còn mở | `VIETVID_DEV_AUTH` bật |
| Cổng nạp-tiền-giả còn mở | `VIETVID_BILLING_DEV` bật |

**Hệ quả vận hành:** nếu sau khi deploy mà app crash-loop lúc khởi động (Railway báo "Deploy failed" / log có dòng `Cấu hình prod không an toàn`), nguyên nhân số 1 là một trong 4 mục trên. Xem [15-security.md](15-security.md) cho danh sách env phải đặt.

> ⚠️ `ENV` phải = `production` để gate này bật. Mặc định `ENV` không set → `IS_PROD=False` (`config.py:32`) → gate TẮT. Trên Railway nhớ set `ENV=production`.

---

## 3. Giám sát uptime ngoài bằng UptimeRobot (free) — 🔜 cần cắm

Solo founder không nên tự dựng monitor (lấy ai canh cái máy canh?). Dùng dịch vụ ngoài, free tier đủ:

**UptimeRobot** (free tier: 50 monitor, ping mỗi 5 phút). Các lựa chọn tương đương: Better Stack (free), Cronitor, hoặc healthcheck tích hợp sẵn của Railway.

> Số "5 phút" là giới hạn free của UptimeRobot tại thời điểm viết — **cần xác nhận lại** khi đăng ký (gói free đôi khi đổi). Muốn ping dày hơn (1 phút) thường phải trả phí.

### Cấu hình tối thiểu (3 monitor)

| Monitor | URL | Kỳ vọng | Cảnh báo khi |
|---|---|---|---|
| API readiness | `https://<api-domain>/health/ready` | HTTP 200 | ≠ 200 trong 2 lần liên tiếp |
| Web (Next.js) | `https://<web-domain>/` | HTTP 200 | ≠ 200 |
| (tuỳ chọn) API liveness | `https://<api-domain>/health` | HTTP 200 | ≠ 200 |

Các bước (cầm tay):

1. Đăng ký tài khoản UptimeRobot, xác minh email.
2. **Add New Monitor** → Monitor Type = `HTTP(s)`.
3. Friendly Name = `Vyra API ready`; URL = `https://<api-domain>/health/ready`.
4. Monitoring Interval = 5 minutes (free).
5. Mục **Alert Contacts**: thêm email của bạn (`progamingeasport@gmail.com`) + (khuyến nghị) một kênh đẩy nhanh — Telegram bot hoặc Slack webhook để nhận thông báo ngay trên điện thoại.
6. Lặp lại cho monitor Web.
7. Bật **SSL expiry** alert (UptimeRobot tự cảnh báo cert HTTPS sắp hết hạn — Railway/Vercel tự gia hạn nhưng cứ bật cho chắc).

> Đặt monitor đọc `/health/ready` chứ KHÔNG đọc trang chủ API, vì 503 (DB chết) sẽ được bắt đúng — trong khi `/` có thể vẫn 200 dù DB đã chết.

---

## 4. Những thứ KHÔNG có endpoint sẵn — cách biết vẫn còn

Có 3 sự cố quan trọng mà uptime-ping đơn thuần KHÔNG thấy. Bảng dưới ghi rõ trạng thái và cách phát hiện hiện tại.

| Sự cố | Endpoint kiểm? | Cách biết hiện tại | Trạng thái |
|---|---|---|---|
| **Queue đầy / worker chết** | ❌ chưa có | Job kẹt `RUNNING/QUEUED` → reaper hoàn HOLD sau 15 phút + log dòng `reaper: hoàn N job treo` | ⚙️ phát hiện gián tiếp |
| **Provider video lỗi** (PiAPI/fal) | ❌ chưa có | Job FAILED+system → ví REFUND 100% + log; Sentry bắt exception | ⚙️ |
| **Credit rò / sổ cái lệch** | ⚙️ có audit cron | Audit `cache == SUM(ledger)` (xem [03-database.md](03-database.md)); admin `/economics` | ⚙️ |

### 4.1 Queue/worker — dấu hiệu sớm là REAPER kêu

Hiện `JOB_EXECUTION_MODE=inline` (`config.py:78`); khi bật `queue` (Arq+Redis, xem [05-queue-worker-rendering.md](05-queue-worker-rendering.md)) thì worker là một tiến trình RIÊNG — nó chết mà `/health` của API vẫn 200. Cách biết worker chết:

- **Reaper là kim chỉ nam.** `reap_stuck_jobs()` (`reaper.py:35`) quét job kẹt ở `RUNNING/QUEUED/HELD/WAITING_CONFIG` (`reaper.py:30-32`) quá `REAPER_STUCK_MINUTES` (mặc định **15 phút**, `config.py:172`) → hoàn HOLD + đánh CANCELLED, rồi log: `reaper: hoàn N job treo + M payment treo→FAILED` (`reaper.py:78`). Reaper chạy 1 lần lúc boot + lặp mỗi `REAPER_INTERVAL_SECONDS` (mặc định **600s**, `config.py:173`) — xem `main.py:57-76`.
- **Quy tắc cảnh báo (cần cắm vào Sentry/log-alert):** nếu thấy `reaper: hoàn N job treo` với **N tăng đều mỗi vòng**, gần như chắc chắn worker đã chết hoặc provider treo. Reaper đang dọn rác, KHÔNG phải "mọi thứ ổn". Coi đây là alert P1.
- **Việc nên làm 🔜:** thêm một endpoint admin trả "số job đang RUNNING/QUEUED quá X phút" để UptimeRobot/cron đọc và cảnh báo TRƯỚC khi reaper phải hoàn tiền. Hiện chưa có; admin `/stats` (`routers/admin.py:34`) chỉ đếm tổng job/video/user, không lọc theo trạng thái-treo.

### 4.2 Provider lỗi (PiAPI/fal/Vbee)

Khi provider trả lỗi hệ thống, job → FAILED+system → ví REFUND 100% (logic ở `jobs.py:complete_job`, xem [07-economics.md](07-economics.md)). Nghĩa là **user không mất tiền**, nhưng bạn vẫn cần biết để báo provider/đổi tuyến.

- Phát hiện: exception lên Sentry ([12-logging-observability.md](12-logging-observability.md)); log có request-id để truy. Khi nhiều REFUND+system dồn dập = provider đang sập.
- Cảnh báo nên đặt: Sentry alert rule "spike số lỗi từ module `video_stage`/`providers`" trong 5 phút.
- Khắc phục: đổi tuyến provider (Kling↔Seedance) — xem [06-providers.md](06-providers.md) + runbook [18-runbooks.md](18-runbooks.md).

---

## 5. Dashboard tối thiểu cho solo founder

Đừng dựng Grafana. Ba "màn hình" sau là đủ:

1. **UptimeRobot status page** (free) — bật public/private status page; xem 1 liếc biết API + Web còn xanh. Lịch sử downtime + uptime % tự tính.
2. **Sentry Issues** — lỗi mới + tần suất; xem [12-logging-observability.md](12-logging-observability.md).
3. **Admin nội bộ** — `/v1/admin/stats` (`routers/admin.py:34`, trả `{users, orgs, jobs, videos, credits_issued}`) + `/v1/admin/economics` (`routers/admin.py:53`, biên doanh thu/chi phí). Xem màn admin web ở [11-admin-panel.md](11-admin-panel.md). Đây là "sức khoẻ kinh doanh", không phải uptime, nhưng cùng một thói quen liếc mỗi ngày.

> Railway có sẵn metrics CPU/RAM/log-stream cho service — dùng làm dashboard hạ tầng, khỏi cắm thêm. Vercel có Analytics cho web. Bắt đầu bằng cái-có-sẵn, chỉ thêm khi thấy thiếu.

---

## 6. SLO khiêm tốn (thành thật với chính mình)

Vyra **mới ra mắt, solo founder, một mình trực**. Đừng hứa "99.9%" (= chỉ được sập ~43 phút/tháng — bạn còn phải ngủ). Mục tiêu thực tế ban đầu:

| Chỉ số | Mục tiêu khởi đầu | Ghi chú |
|---|---|---|
| Uptime API (`/health/ready` 200) | **~99%** | ~7 giờ downtime/tháng cho phép. PaaS managed (Railway/Vercel) thường vượt mức này. |
| Thời gian phát hiện sự cố | **< 10 phút** | = chu kỳ ping UptimeRobot (5') + 1 lần xác nhận. |
| Thời gian phản hồi alert | **< vài giờ ban ngày** | Solo → ban đêm có thể chậm; đây là sự thật, không phải cam kết với khách. |
| Mất tiền/sổ cái sai | **0 (cứng)** | Đây là SLO KHÔNG nhân nhượng — ví ACID + audit cron + reaper bảo vệ. Tiền sai = sự cố P0 luôn. |

> Đừng đăng con số SLO này lên trang bán hàng như cam kết với khách. Đây là mục tiêu nội bộ để bạn biết khi nào "đủ tốt" và khi nào phải bỏ việc khác mà chữa.

**Tất cả các con số trên là MỤC TIÊU đặt ra, chưa phải số đo thật.** Vyra chưa chạy prod đủ lâu để có uptime thực. Sau 1 tháng prod, đọc uptime % từ UptimeRobot và cập nhật lại bảng này.

---

## 7. Nhận biết sự cố SỚM — checklist phản xạ

Khi alert kêu (hoặc bạn nghi ngờ), chạy theo thứ tự — chi tiết xử lý ở [18-runbooks.md](18-runbooks.md):

1. `curl https://<api>/health/ready` → 503? ⇒ DB chết → xem Railway/Neon Postgres.
2. `curl https://<api>/health` → không 200? ⇒ process API chết → xem log boot (có thể vướng startup gate §2).
3. Mở web `/` → trắng/500? ⇒ Next.js. **Nhớ:** không bao giờ `next build` khi `next dev` chạy (hỏng `.next`) — nhưng đó là dev; prod build do CI/PaaS làm.
4. Sentry có spike lỗi mới? ⇒ provider hoặc bug mới deploy.
5. Log có `reaper: hoàn N job treo` tăng? ⇒ worker/provider treo (§4.1).
6. Admin `/economics` biên âm bất thường? ⇒ provider tăng giá hoặc bug định giá → [07-economics.md](07-economics.md).

---

## Việc cần làm (checklist)

- [ ] Set `ENV=production` trên host prod để bật startup gate (§2) — nếu thiếu, gate cấu hình-an-toàn TẮT âm thầm.
- [ ] Tạo monitor UptimeRobot đọc `https://<api>/health/ready` (5 phút) + monitor web `/` (§3).
- [ ] Thêm Alert Contact: email + 1 kênh đẩy nhanh (Telegram/Slack) để nhận trên điện thoại.
- [ ] Bật SSL-expiry alert trên UptimeRobot.
- [ ] Bật public/private status page UptimeRobot làm dashboard liếc-1-cái.
- [ ] (Khi bật queue mode) Thêm endpoint admin trả "số job treo > X phút" để cảnh báo TRƯỚC khi reaper phải hoàn tiền (§4.1) — hiện chưa có.
- [ ] Cấu hình Sentry alert rule: spike lỗi `video_stage`/`providers` 5 phút (provider sập) + alert khi `reaper` hoàn job tăng đều.
- [ ] Sau 1 tháng prod: đọc uptime % thật từ UptimeRobot, cập nhật bảng SLO §6 (thay "mục tiêu" bằng "đo thật").
- [ ] Đưa quy trình §7 vào [18-runbooks.md](18-runbooks.md) thành runbook đầy đủ (kèm lệnh khôi phục từng bước).
