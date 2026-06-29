# Hàng đợi & worker render

Cách Vyra biến một lần bấm "Tạo video" thành một file mp4 mà không treo HTTP, không trừ oan tiền, và không kẹt credit khi server chết. File này giải thích **vì sao cần queue**, vòng đời 1 job, và đúng các lệnh để **bật queue mode** cho prod.

**Trạng thái:** ⚙️ một phần — inline mode ✅ chạy + verify thật (M1, 10/10 PASS); reaper job treo ✅ đã có + chạy định kỳ; queue mode (Arq+Redis) 🔜 chưa nối (`submit_job` raise khi `JOB_EXECUTION_MODE=queue`).

**Liên quan:** [01-architecture.md](01-architecture.md) (bức tranh tổng) · [02-infrastructure.md](02-infrastructure.md) (Railway + Redis) · [04-storage-media.md](04-storage-media.md) (upload final.mp4) · [06-providers.md](06-providers.md) (provider render thật) · [07-economics.md](07-economics.md) (chi phí render) · [12-logging-observability.md](12-logging-observability.md) (job_events + log) · [18-runbooks.md](18-runbooks.md) (xử lý job treo).

---

## 1. Vì sao bắt buộc phải có queue (không phải làm cho sang)

Render 1 video AI **không phải vài giây** — nó gọi provider bên thứ 3 (Seedance/Kling qua PiAPI/fal), poll trạng thái, tải video về, ghép giọng + nhạc + phụ đề bằng ffmpeg. **Ước lượng, cần đo thật:** 1 video 480p/15s mất khoảng **30 giây đến vài phút** tuỳ provider và độ dài (cách đo: bật render thật với 1 key, xem `stage_timings` trong bảng `job_events` / `jobs.stage_timings`).

Vấn đề: nếu để HTTP request `POST /jobs` **đợi render xong rồi mới trả lời**, thì:

| Tầng | Giới hạn | Hậu quả nếu render đồng bộ |
|---|---|---|
| Vercel (Next.js serverless) | timeout ~10-60s tuỳ plan | request render đứt giữa chừng → user thấy lỗi dù video vẫn đang dựng |
| Railway / proxy | thường ngắt idle ~60-100s | tương tự, 504 Gateway Timeout |
| Trình duyệt user | user không chờ nổi 2 phút màn hình treo | bỏ đi, F5 → tạo job trùng |

→ **Nguyên tắc nền (đã chốt, đã code):** tách HTTP ra khỏi render. `POST /jobs` chỉ **nhận đơn + giữ tiền + trả `job_id` NGAY**; render chạy ở chỗ khác; frontend poll trạng thái job. Hợp đồng này KHÔNG đổi khi chuyển inline → queue.

> Lưu ý kiến trúc: front-end Vyra dự kiến đặt ở Vercel/Railway, nhưng **backend FastAPI + worker đặt ở Railway** (xem [02-infrastructure.md](02-infrastructure.md)). Timeout Vercel chỉ áp cho request đi qua nó; nhưng kể cả backend tự host thì render dài vẫn cần queue để không chiếm process API.

---

## 2. Hai chế độ thực thi: `inline` và `queue`

Toàn bộ "chạy job ở đâu" gói trong MỘT seam: `app_api/executor.py:submit_job()`. Router không biết job chạy thế nào — nó chỉ gọi `submit_job` sau khi đã commit HOLD.

Công tắc: env `JOB_EXECUTION_MODE` (`app_api/config.py:78`).

| Mode | Render chạy ở đâu | Khi nào dùng | Trạng thái |
|---|---|---|---|
| `inline` (mặc định) | Ngay trong process API qua FastAPI `BackgroundTasks` (Starlette chạy hàm sync trong threadpool) | Dev, demo 1 box, ít user | ✅ chạy + verify |
| `queue` | Đẩy vào Arq (Redis), 1 fleet worker riêng pull ra render | Prod nhiều user | 🔜 chưa nối — `submit_job` đang `raise RuntimeError` |

`app_api/executor.py:15-29` — đọc thẳng:

```python
def submit_job(org_id, job_id, *, background_tasks=None) -> None:
    mode = config.JOB_EXECUTION_MODE
    if mode == "queue":
        raise RuntimeError("JOB_EXECUTION_MODE=queue cần Arq worker (item 2) — chưa nối...")
    from app_api.worker import run_job
    if background_tasks is not None:
        background_tasks.add_task(run_job, str(org_id), str(job_id))
    else:
        run_job(org_id, job_id)
```

**Vì sao inline KHÔNG scale (phải bỏ ở prod):**
- Render chiếm thread của process API → API ít CPU/RAM, nhiều job song song làm nghẽn cả endpoint khác.
- API restart/redeploy (Railway deploy mới) **giết luôn job đang render** → job kẹt `RUNNING`, tiền kẹt HOLD (reaper sẽ cứu, mục 6, nhưng đó là vá chứ không phải đúng).
- Không retry, không tách worker rẻ/đắt, không giới hạn concurrency theo provider.

---

## 3. Vòng đời 1 job (đọc kỹ — đây là tim hệ thống)

Đường đi từ lúc user bấm tới lúc có video, **đã code + verify thật** (M1 tim: 10/10 PASS — xem [docs/HANDOFF.md](../HANDOFF.md) §4).

```
1. POST /jobs (routers/jobs.py)
   ├─ validate_and_clamp(spec, plan)        # siết theo gói: 480p/≤20s cho free (validate.py)
   ├─ tenant_session NGẮN:
   │    create_job(): estimate_hold → HOLD credit → insert Job(status=QUEUED)
   │    (idempotent theo (org_id, idempotency_key) — gửi lại KHÔNG tạo job đôi)
   └─ COMMIT  ← tiền đã giữ, job đã nằm trong DB

2. submit_job(org, job_id)  ← SAU commit (worker phải THẤY job trong DB)
   ├─ inline: BackgroundTasks.add_task(run_job, ...)
   └─ queue:  enqueue Arq (chưa nối)
   * Nếu submit_job NÉM lỗi → release_hold() hoàn 100% HOLD + job=CANCELLED ngay
     (credit KHÔNG kẹt HELD) — routers/jobs.py:113-122

3. run_job(org, job_id)  (worker.py) — chạy NỀN, KHÔNG giữ HTTP
   ├─ tenant_session ngắn: mark_running (QUEUED→RUNNING) + build_job_spec
   ├─ render(spec, QueueSink)   ← KHÔNG giữ DB transaction suốt lúc render
   │    QueueSink forward stage events → bảng job_events (live progress)
   ├─ store_output(final.mp4) → R2/S3 (nếu cấu hình)   ← xem 04-storage-media.md
   └─ tenant_session ngắn: complete_job() → SETTLE / REFUND ví + ghi Video row

4. Frontend poll GET /jobs/{id} cho tới khi status terminal (READY/FAILED/...)
```

**Bản đồ RenderResult → ví** (`app_api/jobs.py:complete_job`, dòng 162-171) — quy tắc tiền:

| Kết quả render | Trạng thái job | Hành động ví |
|---|---|---|
| Render xong | `READY` | **SETTLE** theo chi phí thật (clamp ≤ hold) → hoàn phần thừa |
| QA fail (video ra nhưng không đạt) | `QA_FAIL` | **SETTLE** theo chi phí thật |
| Lỗi **hệ thống** (provider sập, mạng) | `FAILED` + `fault_class="system"` | **REFUND 100%** — user không mất tiền vì lỗi của ta |
| Lỗi **đầu vào** (ảnh hỏng, brief sai) | `FAILED` (input fault) | **SETTLE** theo chi phí thật (đã tiêu provider rồi) |
| Cần config thêm | `WAITING_CONFIG` | **GIỮ HOLD**, resume sau |

Bất biến: mỗi job HOLD đúng MỘT lần, rồi ĐÚNG MỘT trong {SETTLE, REFUND}, **idempotent** (khoá `SELECT ... FOR UPDATE`). Chi tiết cơ chế ví ở [07-economics.md](07-economics.md) + [03-database.md](03-database.md) (ledger append-only).

---

## 4. Idempotency & retry (vì sao không trừ tiền 2 lần)

Có 3 lớp idempotency, tất cả ✅ đã code:

1. **Tạo job đôi** — `create_job` (`jobs.py:59-63`) tra `(org_id, idempotency_key)`; trùng → trả job cũ, KHÔNG HOLD lần nữa. Frontend phải gửi `idempotency_key` ổn định cho 1 lần bấm (vd UUID sinh client).
2. **Trả tiền i2v 2 lần khi worker crash giữa render** — `QueueSink.merge_params` (`sink_queue.py:36-53`) persist `piapi_task_id` **NGAY** khi engine tạo task image-to-video. Worker chết → chạy lại đọc lại task id cũ, **resume** thay vì tạo task provider mới (đỡ trả tiền đôi cho provider).
3. **SETTLE/REFUND idempotent** — ledger có khoá + trigger append-only; gọi lại complete_job không cộng/trừ đôi.

**Retry hiện tại (inline):** 🔜 **chưa có retry tự động**. Job lỗi hệ thống → REFUND, user tự bấm lại. Khi bật queue (mục 5), Arq cho cấu hình `max_tries` + backoff — nhưng phải cẩn thận: chỉ retry lỗi **hệ thống/tạm thời** (timeout, 5xx provider), KHÔNG retry lỗi đầu vào, và nhờ lớp (2) resume task cũ để không đốt tiền provider mỗi lần thử.

---

## 5. Bật queue mode cho prod (cầm tay chỉ việc) 🔜

Đây là việc **chưa làm** (xem [docs/HANDOFF.md](../HANDOFF.md) §10.B mục 5 + [20-roadmap.md](20-roadmap.md)). Các bước dưới là kế hoạch cụ thể, bám đúng seam đã thiết kế sẵn.

### Bước 1 — cài thư viện
`requirements.txt:52-53` đã để sẵn dòng comment, chỉ cần bỏ comment + cài:

```bash
# trong requirements.txt, bỏ # ở 2 dòng:
arq>=0.26
redis>=5.0
```
```bash
/c/Python314/python -m pip install arq redis
```

### Bước 2 — có Redis
- Dev: chạy Redis local (Docker `redis:7`) hoặc dùng **Upstash** free-tier.
- Prod: **Upstash** (free khởi đầu) hoặc Redis add-on của Railway. Set env `VIETVID_REDIS_URL` (env var này **chưa tồn tại** trong `config.py` — phải thêm khi làm). Xem [02-infrastructure.md](02-infrastructure.md).

### Bước 3 — viết module queue (chưa có file)
Tạo `app_api/queue.py`: định nghĩa Arq `WorkerSettings` + hàm task bọc `worker.run_job`. Theo gợi ý trong code (`executor.py:18`, `config.py:5` nhắc `q_fast/q_slow`): tách 2 hàng đợi — **q_fast** cho draft ngắn/preview, **q_slow** cho video dài/nặng — để job nhanh không kẹt sau job nặng.

Khung mẫu (cần hoàn thiện + đo):
```python
# app_api/queue.py (PHÁC THẢO — chưa có trong repo)
from arq import create_pool
from arq.connections import RedisSettings
from app_api.worker import run_job

async def render_task(ctx, org_id: str, job_id: str):
    return run_job(org_id, job_id)   # run_job là sync → cân nhắc to_thread nếu chặn loop

class WorkerSettings:
    functions = [render_task]
    redis_settings = RedisSettings.from_dsn(os.environ["VIETVID_REDIS_URL"])
    max_tries = 2            # chỉ hữu ích cho lỗi tạm thời; cẩn thận tiền provider
    job_timeout = 600        # ước lượng, cần đo theo render dài nhất
```

### Bước 4 — nối `submit_job`
Sửa `app_api/executor.py:17-21` (chỗ đang `raise`) thành enqueue thật:
```python
if mode == "queue":
    from app_api.queue import enqueue_render
    enqueue_render(org_id, job_id)   # đẩy vào q_fast/q_slow tuỳ seconds/purpose
    return
```
Hợp đồng `POST /jobs` **không đổi** — router vẫn gọi `submit_job` y như cũ; nếu enqueue ném lỗi, `release_hold` đã hoàn tiền sẵn (`routers/jobs.py:113-122`).

### Bước 5 — chạy worker fleet (process riêng)
Trên Railway tạo **service worker thứ 2** (cùng repo, khác lệnh start):
```bash
arq app_api.queue.WorkerSettings
```
API service và worker service **chia sẻ cùng Postgres + Redis**. Muốn nhiều worker → tăng số instance của service worker.

### Bước 6 — bật công tắc
```bash
# env trên Railway (cả API và worker)
JOB_EXECUTION_MODE=queue
VIETVID_REDIS_URL=<redis dsn>
```
> Lưu ý: ở queue mode, router vẫn truyền `background_tasks` vào `submit_job` nhưng nhánh queue bỏ qua nó — render chạy ở worker process, KHÔNG trong API.

### Cách verify đã chạy thật (đừng tin xanh giả)
1. `POST /v1/jobs` → nhận `job_id` ngay (< 1s).
2. Xem **log worker** (process riêng) báo nhận task — KHÔNG phải log API.
3. `GET /v1/jobs/{id}` chuyển QUEUED → RUNNING → READY.
4. Bảng `job_events` có dòng stage STARTED/PROGRESS/SUCCEEDED.
5. Ví: ledger có HOLD rồi SETTLE; balance khớp `SUM(ledger)`.

---

## 6. Reaper — cứu job treo + tiền kẹt ✅

File: `app_api/reaper.py`. Đã có, chạy tự động.

**Vấn đề nó vá:** job đang `RUNNING` (inline qua BackgroundTasks) mà process API chết/redeploy → job kẹt RUNNING vĩnh viễn, HOLD không bao giờ SETTLE/REFUND → **credit đóng băng của user**.

**Cách hoạt động** (`reaper.py:35-88`):
- Quét MỌI org (tôn trọng RLS — lặp từng org rồi mở `tenant_session`, KHÔNG bypass).
- Tìm job ở trạng thái treo (`RUNNING/QUEUED/HELD/WAITING_CONFIG`) mà `updated_at` cũ hơn ngưỡng → **hoàn 100% HOLD** + đặt `CANCELLED` (`release_hold`).
- Tiện thể: Payment `PENDING` quá 24h → `FAILED`; dọn workdir mồ côi (cloud-mode).

**Chạy** (`app_api/main.py:57-82`): 1 lần lúc boot (dọn job mồ côi từ process trước) + vòng lặp định kỳ.

| Env | Mặc định | Ý nghĩa |
|---|---|---|
| `VIETVID_REAPER` | `True` | bật/tắt reaper |
| `VIETVID_REAPER_STUCK_MIN` | `15` | job treo > N phút mới hoàn (đừng để < thời gian render dài nhất, nếu không reaper cướp job đang chạy bình thường) |
| `VIETVID_REAPER_INTERVAL` | `600` | chu kỳ quét (giây) |

> ⚠️ **Quan trọng khi bật queue + render thật:** nếu video dài render > 15 phút (ước lượng, cần đo), tăng `VIETVID_REAPER_STUCK_MIN` lên trên thời gian render dài nhất — nếu không reaper sẽ hoàn tiền + huỷ job **đang render bình thường**. Đo `stage_timings` trước, đặt ngưỡng = max thời gian render × hệ số an toàn (vd ×2).

Xem thêm runbook xử lý job treo ở [18-runbooks.md](18-runbooks.md).

---

## 7. Bản đồ file (để session sau tìm đúng chỗ)

| File | Vai trò |
|---|---|
| `app_api/routers/jobs.py` | `POST /jobs`: validate → HOLD → submit_job; release_hold khi lỗi |
| `app_api/jobs.py` | orchestration: `create_job` (HOLD), `build_job_spec`, `complete_job` (SETTLE/REFUND), `release_hold`, `estimate_hold` |
| `app_api/executor.py` | seam `submit_job` — công tắc inline/queue |
| `app_api/worker.py` | `run_job`: mark_running → render → store → complete_job → cleanup → webhook |
| `app_api/sink_queue.py` | `QueueSink`: stage events → `job_events`; persist `piapi_task_id` (idempotency i2v) |
| `app_api/reaper.py` | quét + hoàn job treo, payment treo, workdir mồ côi |
| `app_api/config.py` | `JOB_EXECUTION_MODE`, `REAPER_*` |
| `app_api/queue.py` | 🔜 **chưa tồn tại** — module Arq cần viết khi bật queue |

---

## Việc cần làm (checklist)

- [ ] Đo thời gian render thật (`stage_timings`) cho 480p/720p, ngắn/dài → ghi số thật vào [07-economics.md](07-economics.md) (thay các "ước lượng" trong file này).
- [ ] Bỏ comment `arq` + `redis` trong `requirements.txt`, cài (`pip install arq redis`).
- [ ] Dựng Redis (Upstash free hoặc Railway add-on); thêm env `VIETVID_REDIS_URL` vào `config.py`.
- [ ] Viết `app_api/queue.py` (WorkerSettings + `enqueue_render` + tách q_fast/q_slow).
- [ ] Nối nhánh `queue` trong `executor.py:submit_job` (thay `raise` bằng enqueue).
- [ ] Tạo service worker thứ 2 trên Railway: `arq app_api.queue.WorkerSettings`.
- [ ] Bật `JOB_EXECUTION_MODE=queue` trên cả API và worker.
- [ ] Verify thật: POST /jobs trả ngay → log worker nhận → READY → ledger HOLD/SETTLE đúng.
- [ ] Cấu hình retry Arq (`max_tries`/backoff) CHỈ cho lỗi hệ thống; tận dụng resume `piapi_task_id` để không đốt tiền provider khi retry.
- [ ] Sau khi đo render dài nhất: chỉnh `VIETVID_REAPER_STUCK_MIN` > thời gian render max (tránh reaper cướp job đang chạy).
- [ ] (Tuỳ) thêm giới hạn concurrency theo provider để không vượt rate-limit PiAPI/fal (xem [06-providers.md](06-providers.md)).
