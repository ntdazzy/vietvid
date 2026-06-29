# Log & quan sát (cho AI debug)

Mục đích: làm rõ Vyra log cái gì, ở đâu, định dạng nào, và **làm sao để Claude (hoặc bạn) lần ra 1 lỗi job từ đầu đến cuối** — vì observability ở đây thiết kế để AI điều tra + fix nhanh, không phải để "đẹp dashboard".

Trạng thái: ⚙️ một phần — structured log + request-id + access log + exception handler + audit_log + job_events **đã có và chạy**; Sentry, log aggregation tập trung (Logtail/Better Stack), và request-id chảy xuống worker **chưa nối** (🔜).

Liên quan: [05-queue-worker-rendering.md](05-queue-worker-rendering.md) (worker + job_events), [11-admin-panel.md](11-admin-panel.md) (xem audit_log/job_events qua admin), [13-monitoring-uptime.md](13-monitoring-uptime.md) (alert khi log báo lỗi), [15-security.md](15-security.md) (KHÔNG log secret/PII), [18-runbooks.md](18-runbooks.md) (quy trình xử lý khi log báo sự cố).

---

## 1. Bức tranh tổng (đọc 30 giây)

Vyra có **4 tầng quan sát**, tất cả viết bằng stdlib `logging` (logger tên `"vietvid"`) — KHÔNG kéo loguru của project cũ vào lớp HTTP:

| Tầng | Cái gì | File:dòng | Trạng thái |
|---|---|---|---|
| **Structured log (JSON)** | mỗi dòng log có `ts/level/logger/request_id/msg`, prod xuất JSON 1 dòng | `app_api/observability.py:38` `_JsonFormatter` | ✅ |
| **Request-id xuyên suốt** | mỗi request 1 id, gắn vào MỌI dòng log cùng request + trả về header `X-Request-Id` | `app_api/observability.py:73` `RequestContextMiddleware` | ✅ (web→api ✅, →worker 🔜) |
| **Access log** | 1 dòng/request: method, path, status, ms | `app_api/observability.py:85` | ✅ |
| **Exception handler** | bắt MỌI lỗi chưa xử lý → log traceback + trả 500 envelope an toàn (không lộ stack) | `app_api/observability.py:116` | ✅ |
| **audit_log (DB)** | nhật ký hành động NHẠY CẢM (admin suspend, cộng/trừ credit, moderation, tạo API key) — append-only, sống sót cả khi org bị xoá | `app_api/audit.py` + bảng `AuditLog` (`models.py:162`) | ✅ |
| **job_events (DB)** | tiến trình render từng stage (STARTED/PROGRESS/SUCCEEDED/FAILED) + provider + cost + asset_url | `app_api/sink_queue.py` + bảng `JobEvent` (`models.py:576`) | ✅ |
| **Sentry (lỗi tập trung)** | gom exception về 1 nơi, alert | — | 🔜 chưa nối |

Tất cả được bật trong `app_api/main.py`:
- `configure_logging()` — `main.py:45`
- `install_exception_handlers(app)` — `main.py:92`
- `app.add_middleware(RequestContextMiddleware)` — `main.py:98`

---

## 2. Structured logging (JSON) — ✅ đã có

### Định dạng prod (JSON, máy đọc)
Mỗi dòng log ở prod là 1 dòng JSON (`observability.py:38-49`):

```json
{"ts":"2026-06-29T10:22:01","level":"INFO","logger":"vietvid","request_id":"a1b2c3d4e5f6a7b8","msg":"POST /v1/jobs -> 202 (38.4ms)"}
```

Nếu có exception, thêm field `"exc"` = traceback đầy đủ.

### Định dạng dev (text, người đọc)
Khi `VIETVID_LOG_JSON=false` (mặc định dev), format dễ đọc (`observability.py:64-68`):

```
10:22:01 INFO  [a1b2c3d4e5f6a7b8] vietvid: POST /v1/jobs -> 202 (38.4ms)
```

### Env điều khiển (`config.py:131-132`)
| Env var | Mặc định | Ý nghĩa |
|---|---|---|
| `VIETVID_LOG_LEVEL` | `INFO` | `DEBUG`/`INFO`/`WARNING`/`ERROR` |
| `VIETVID_LOG_JSON` | `true` ở prod (`IS_PROD`), `false` ở dev | bật JSON 1-dòng cho prod |

> Trên Railway: đặt `VIETVID_LOG_JSON=true` để log ra JSON → Railway "Logs" tab vẫn xem được, và sau này forward sang Better Stack/Logtail parse được. Đặt `VIETVID_LOG_LEVEL=INFO` (KHÔNG để DEBUG ở prod — ồn + có thể lộ chi tiết).

### Log từ code của bạn
Bất kỳ đâu trong `app_api`:
```python
import logging
log = logging.getLogger("vietvid")
log.info("topup applied org=%s amount=%s", org_id, amount)   # request_id tự gắn
log.exception("render thất bại job=%s", job_id)              # tự kèm traceback
```
`request_id` được filter tự bơm vào (`observability.py:32-35`) — bạn KHÔNG cần truyền tay.

---

## 3. Request-id xuyên suốt web → api → worker

### Đã có ✅: web → api
- Middleware lấy `X-Request-Id` từ header, hoặc sinh `uuid4().hex[:16]` nếu thiếu (`observability.py:77`).
- Lưu vào `ContextVar` → MỌI dòng log trong cùng request mang đúng id (`observability.py:78`).
- Trả lại client qua header `X-Request-Id` (`observability.py:83`) + nhét vào mọi envelope lỗi (500/HTTPException/422 — `observability.py:129,138,146`).

→ Khi user báo lỗi, **xin họ cái `request_id`** trong thông báo lỗi (hoặc đọc từ tab Network → response header) → grep thẳng ra toàn bộ dòng log của request đó.

**Cách dùng phía frontend (🔜 nên làm):** cho client gửi `X-Request-Id` riêng mỗi action để dễ truy. Hiện tại chưa gửi → backend tự sinh, vẫn truy được nhưng id nằm ở response.

### Chưa có 🔜: api → worker
Đây là **lỗ hổng quan sát cần vá**. Khi `POST /jobs` enqueue job, render chạy ở **worker tách process** (`worker.py:run_job`). Worker mở `tenant_session` mới, **KHÔNG** kế thừa `request_id_ctx` của request gốc → log của worker mang `request_id="-"`.

**Cách vá (việc cần làm):**
1. Khi enqueue, lưu `request_id` hiện tại vào job (cột `params` hoặc cột mới `request_id`).
2. Đầu `run_job`, đọc lại và `request_id_ctx.set(...)` để mọi log của worker mang đúng id.

Trước khi vá, để truy job ở worker hãy **dùng `job_id` làm khoá nối** (xem §6) — `job_id` đã có trong cả log api lẫn `job_events`.

---

## 4. Access log + exception handler — ✅ đã có

- **Access log:** mỗi request 1 dòng `INFO` (`observability.py:85-91`). Đo thời gian bằng `time.monotonic()` → phát hiện endpoint chậm.
- **Exception handler** (`observability.py:116-147`):
  - Lỗi chưa xử lý → `log.exception(...)` (traceback đầy đủ vào log) + trả `500 {"detail":"Lỗi hệ thống...","request_id":...}`. **Stack KHÔNG lộ ra client** — chỉ vào log.
  - `HTTPException` (4xx có chủ đích) → giữ status gốc + kèm `request_id`.
  - `RequestValidationError` (422) → trả lỗi field + `request_id`.

> Đây là điểm "thiết kế cho AI debug": client chỉ thấy `request_id`, còn traceback + ngữ cảnh nằm trong log server. Đưa Claude cái `request_id` + đoạn log JSON là đủ để lần ra file:dòng.

---

## 5. audit_log — ✅ đã có (hành động nhạy cảm)

Bảng `audit_log` (`models.py:162-174`) ghi nhật ký **hành động nhạy cảm**, **append-only** (trigger DB chặn UPDATE/DELETE), **GLOBAL** (sống sót cả khi org/user bị xoá — phục vụ điều tra/pháp lý).

Ghi qua helper `audit.record(...)` (`audit.py:15`) — **best-effort**: nếu ghi audit lỗi, KHÔNG làm hỏng hành động chính (chỉ `log.exception` rồi bỏ qua).

Các action đang ghi (grep `audit.record`):
| action | Ở đâu | Khi nào |
|---|---|---|
| `config.update` | `routers/admin.py:111` | admin đổi config runtime |
| `broadcast` | `routers/admin.py:133` | admin gửi thông báo |
| `user.status` | `routers/admin.py:183` | suspend/mở khoá user |
| `credit.adjust` | `routers/admin.py:207` | admin cộng/trừ credit |
| `kol.moderate` | `routers/admin.py:258` | duyệt/từ chối KOL |
| `apikey.create` | `routers/integrations.py:41` | tạo API key B2B |

Mỗi bản ghi: `action`, `actor_email`, `actor_user_id`, `org_id`, `detail` (JSONB), `created_at`. Index theo `created_at` (`models.py:174`).

> **Quy tắc:** mọi hành động admin chạm tiền hoặc trạng thái user/KOL PHẢI gọi `audit.record`. Khi thêm action admin mới, thêm 1 dòng audit. Xem audit qua admin panel — [11-admin-panel.md](11-admin-panel.md).

---

## 6. job_events — ✅ đã có (tiến trình render, khoá truy job)

Bảng `job_events` (`models.py:576-592`) là **dòng thời gian render của 1 job**, ghi bởi `QueueSink` (`sink_queue.py`). Mỗi stage của engine sinh event:

| event_type | Khi nào (sink_queue.py) |
|---|---|
| `STARTED` | `stage_start` — bắt đầu 1 stage (vd DIRECTING, VOICE, VIDEO) |
| `PROGRESS` | `add_asset` — sinh ra 1 asset (kèm `provider`, `cost_usd`, `asset_url`) |
| `SUCCEEDED` / `FAILED` | `stage_end` — kết thúc stage (FAILED kèm `note` lý do) |

Mỗi event có: `job_id`, `org_id`, `stage`, `event_type`, `provider`, `cost_usd`, `asset_url`, `detail` (JSONB, có thể chứa `qa` report hoặc `note`).

Ghi là **best-effort** (`sink_queue.py:63` — `except: pass`): ghi progress KHÔNG được làm hỏng render thật. Nghĩa là **đừng coi job_events là nguồn sự thật tuyệt đối** về tiền — sổ cái ví (`ledger_entries`) mới là sự thật ACID. job_events là để **xem job chạy tới đâu / hỏng ở stage nào**.

> `job_events` là **khoá nối api↔worker khi chưa có request-id ở worker** (§3): có `job_id` là truy được toàn bộ tiến trình + provider + cost.

---

## 7. Sentry (lỗi tập trung) — 🔜 chưa nối (việc cần làm)

Hiện CHƯA có Sentry. Lỗi chỉ vào stdout/JSON log. Với solo founder + prod managed PaaS, Sentry (gói free) đáng nối vì: gom exception, dedup, alert email/Telegram khi có lỗi mới, kèm request_id + breadcrumb.

**Cách nối tối thiểu (ước lượng ~30 phút):**
1. `pip install sentry-sdk` (thêm vào requirements).
2. Trong `main.py`, trước `configure_logging()`:
   ```python
   import os, sentry_sdk
   dsn = os.environ.get("SENTRY_DSN", "")
   if dsn:
       sentry_sdk.init(dsn=dsn, traces_sample_rate=0.0, send_default_pii=False)
   ```
   `send_default_pii=False` để KHÔNG gửi PII (xem §8).
3. Trong exception handler (`observability.py:124`), trước khi trả 500: gắn `request_id` làm tag rồi `sentry_sdk.capture_exception(exc)`.
4. Worker (`worker.py`): bọc `render(...)` để capture exception render về Sentry kèm `job_id`.
5. Đặt `SENTRY_DSN` trên Railway (backend + worker). KHÔNG hardcode DSN vào code.

> Sentry là **bổ sung**, không thay JSON log. JSON log vẫn là nguồn chính cho Claude grep. Sentry là để **bạn được báo** khi có lỗi mới mà không phải ngồi đọc log.

---

## 8. Cái gì LOG / cái gì KHÔNG (secret + PII)

**TUYỆT ĐỐI KHÔNG log:**
- Secret: nội dung `_vietvid_db_url.txt`, `_fal_key.txt`, `GEMINI/PIAPI/GROQ key`, `VIETVID_SEPAY_TOKEN`, JWT token, password hash. (CLAUDE.md: "KHÔNG in secret ra".)
- Body thanh toán đầy đủ / số tài khoản người dùng / chữ ký IPN.
- PII không cần thiết: KHÔNG log email/họ tên ở mức INFO nếu chỉ cần debug kỹ thuật. Ưu tiên log **id** (`org_id`, `user_id`, `job_id`) — id đủ để truy mà không phơi PII ra log.

**ĐƯỢC log:**
- `request_id`, `org_id`, `user_id`, `job_id`, action name, status code, thời gian ms.
- Stage render + provider + cost_usd (vào job_events) — đây là dữ liệu vận hành, không nhạy cảm.
- `actor_email` trong **audit_log** — đây là chủ đích (audit pháp lý cần biết AI làm), nhưng audit_log là bảng DB có kiểm soát truy cập, KHÔNG phải log stdout.

**Quy tắc thực hành khi viết log mới:** dùng `%s` placeholder với **id**, không nội suy object/dict thô (có thể chứa token/PII). Trước khi `log.info(detail)`, hỏi: "dòng này lộ ra Railway Logs cho ai đọc được thì có sao không?".

> Nếu nối Sentry: bật `send_default_pii=False` và **scrub** trường nhạy cảm trước khi gửi.

---

## 9. Ví dụ truy vết 1 lỗi job (cầm tay chỉ việc)

**Tình huống:** user báo "tạo video bị lỗi, không ra video, mất credit?".

**Bước 1 — lấy mã.** Xin user `request_id` (trong thông báo lỗi / response header `X-Request-Id`) HOẶC `job_id` (URL trang job / API trả về).

**Bước 2 — grep log api theo request_id.** Trên Railway Logs (hoặc local stdout):
```bash
# nếu JSON log:
grep '"request_id":"a1b2c3d4e5f6a7b8"' logs.txt
```
→ thấy dòng access `POST /v1/jobs -> 202` (job tạo OK, đã HOLD credit) hay `-> 402/422/500` (lỗi ngay ở api).

**Bước 3 — nếu api OK (202), lỗi nằm ở worker.** Dùng `job_id` truy `job_events` (qua admin panel — [11-admin-panel.md](11-admin-panel.md) — hoặc SQL):
```sql
SELECT stage, event_type, provider, cost_usd, detail, created_at
FROM job_events WHERE job_id = '<job_id>' ORDER BY id;
```
→ thấy stage cuối là `FAILED` ở stage nào, `detail->>'note'` lý do (vd provider PiAPI timeout).

**Bước 4 — đối chiếu trạng thái job + ví.**
```sql
SELECT id, status, fault_class FROM jobs WHERE id = '<job_id>';
SELECT entry_type, amount FROM ledger_entries WHERE job_id = '<job_id>' ORDER BY id;
```
→ Nếu `status=FAILED` + `fault_class=system` → phải có `REFUND` hoàn 100% (không mất credit). Nếu có HOLD mà thiếu SETTLE/REFUND → job treo → reaper sẽ dọn ([05-queue-worker-rendering.md](05-queue-worker-rendering.md), `reaper.py`).

**Bước 5 — tìm traceback nếu là lỗi code.** Grep log worker theo `job_id`:
```bash
grep '<job_id>' logs.txt | grep -i 'error\|exc\|Traceback'
```
→ trong JSON, field `"exc"` chứa traceback đầy đủ → ra file:dòng → đưa Claude fix.

**Kết luận mẫu cho user (trung thực):** "Job lỗi ở stage VIDEO do provider timeout (lỗi hệ thống) → credit đã hoàn 100% (ledger có REFUND), không mất tiền. Mã: job_id=...".

---

## 10. Hạn chế hiện tại (đừng tự huyễn)

- 🔜 **request_id chưa chảy xuống worker** → log worker hiện mang `request_id="-"`. Tạm dùng `job_id` để nối (§3, §6).
- 🔜 **Chưa có log aggregation tập trung.** Prod Railway giữ log có hạn (retention ngắn). Cần forward sang Better Stack/Logtail (free tier) để giữ lâu + grep nhanh + alert. Xem [13-monitoring-uptime.md](13-monitoring-uptime.md).
- 🔜 **Chưa có Sentry** → không có alert chủ động khi lỗi mới xuất hiện; bạn phải ngồi đọc log.
- ⚙️ **job_events best-effort** → có thể thiếu event nếu DB chập (render vẫn đúng). Sổ cái ví mới là sự thật tiền bạc.
- 🔜 **Chưa có metric** (số job/giờ, tỉ lệ FAILED, latency p95). Hiện chỉ có log thô. Đo bằng cách đếm trong log/job_events; muốn dashboard thì cần thêm (Prometheus/Grafana hoặc đơn giản query SQL định kỳ).

---

## Việc cần làm (checklist)

- [ ] **Nối Sentry** (§7): `pip install sentry-sdk`, init trong `main.py` (gated bởi `SENTRY_DSN`), capture ở exception handler + worker, đặt `SENTRY_DSN` trên Railway (backend + worker), `send_default_pii=False`.
- [ ] **request_id chảy xuống worker** (§3): lưu `request_id` vào job khi enqueue → `request_id_ctx.set(...)` đầu `run_job` để log worker mang đúng id.
- [ ] **Frontend gửi `X-Request-Id`** riêng mỗi action (để user copy mã báo lỗi dễ hơn).
- [ ] **Đặt env log đúng ở prod**: `VIETVID_LOG_JSON=true`, `VIETVID_LOG_LEVEL=INFO` trên Railway.
- [ ] **Log aggregation**: forward Railway log → Better Stack/Logtail (free) để giữ lâu + grep + alert. Liên kết [13-monitoring-uptime.md](13-monitoring-uptime.md).
- [ ] **Rà soát log không lộ secret/PII** (§8): grep code chỗ `log.` nội suy object/dict thô; đổi sang id-only.
- [ ] **Audit cho action admin mới**: khi thêm endpoint admin chạm tiền/trạng thái, nhớ gọi `audit.record(...)`.
- [ ] **(Sau) Metric cơ bản**: tỉ lệ job FAILED, latency p95 endpoint render — bắt đầu bằng query SQL định kỳ trên `jobs`/`job_events`, lên dashboard sau.
- [ ] **Đo thật** (ước lượng, cần đo thật): retention log Railway thực tế bao lâu, để quyết khi nào bắt buộc forward ra ngoài.
