# 18 — Sổ tay xử lý sự cố (runbook)

Cầm-tay từng kịch bản sự cố hay gặp ở Vyra: job kẹt, provider sập, tiền vào không cộng credit, cộng tiền đôi, DB chậm/đầy, R2 lỗi, queue tắc, user kêu mất credit. **Mỗi kịch bản: triệu chứng → kiểm tra (lệnh/SQL/log) → khắc phục → phòng ngừa.** Mục tiêu: chủ dự án (solo, không chuyên hạ tầng) hoặc một phiên Claude sau mở đúng mục, làm theo, không phải đoán.

**Trạng thái:** ⚙️ một phần — phần lớn kịch bản dựa trên code đã có + verify thật (ví ACID, reaper, SePay idempotent); một số kịch bản (queue tắc, R2 lỗi) là 🔜 chưa chạy prod nên ghi rõ "khi đã bật".

**Liên quan:** [05-queue-worker-rendering.md](05-queue-worker-rendering.md) (vòng đời job + reaper) · [10-payments.md](10-payments.md) (đối soát SePay/IPN) · [11-admin-panel.md](11-admin-panel.md) (credit-adjust thủ công) · [12-logging-observability.md](12-logging-observability.md) (đọc log/request-id) · [13-monitoring-uptime.md](13-monitoring-uptime.md) (cảnh báo trước khi user kêu) · [04-storage-media.md](04-storage-media.md) (R2/upload) · [14-backup-dr-maintenance.md](14-backup-dr-maintenance.md) (khôi phục DB) · [03-database.md](03-database.md) (bảng `payments`, ledger).

---

## 0. Trước khi xử lý BẤT KỲ sự cố nào — 4 bước nền

1. **Đừng đoán — nhìn dữ liệu thật.** Mọi kết luận phải có bằng chứng (1 row DB / 1 dòng log / 1 HTTP response). Đây là quy tắc `real-qa` (xem [docs/HANDOFF.md](../HANDOFF.md) §8).
2. **Tìm `request_id`.** User báo lỗi → hỏi (hoặc lấy từ Sentry) `request_id` của lần bấm đó, rồi grep xuyên log (xem [12-logging-observability.md](12-logging-observability.md)). Một `request_id` nối được HTTP → job → ledger.
3. **Kết nối DB an toàn (prod).** Mọi truy vấn bảng tenant (`jobs`, `payments`, `wallets`, `ledger_entries`, `videos`) phải set GUC org trước, nếu không **RLS trả 0 dòng** (fail-closed). Mẫu trong psql:
   ```sql
   SET app.org := '<ORG_UUID>';                       -- tên biến chỉ để nhớ
   SET LOCAL "vietvid.current_org" = '<ORG_UUID>';    -- ĐÚNG tên GUC RLS đọc
   SELECT * FROM jobs WHERE org_id = '<ORG_UUID>';
   ```
   > Bảng GLOBAL (không RLS) đọc trực tiếp được: `orgs`, `memberships`, `payments`? — **KHÔNG**, `payments` có RLS. Allowlist global xem `app_api/models.py`. Khi nghi RLS chặn, dùng admin endpoint thay vì psql tay.
4. **Ưu tiên admin panel hơn psql tay.** Admin (`/v1/admin/*`, xem [11-admin-panel.md](11-admin-panel.md)) đã bọc `tenant_session` + ghi `audit_log`. Sửa tiền bằng tay trong psql = không có vết audit + dễ phá bất biến ledger.

---

## 1. Job kẹt / treo (status RUNNING/QUEUED mãi không xong)

**Triệu chứng:** User báo "tạo video mãi không xong", spinner quay hoài. `GET /v1/jobs/{id}` trả `status=RUNNING` (hoặc `QUEUED`) đã lâu. Credit của user đang bị **HELD** (giữ), balance hiển thị thấp hơn user nghĩ.

**Nguyên nhân gốc thường gặp:**
- API restart/redeploy lúc job inline đang render (BackgroundTasks chết theo process) → job kẹt `RUNNING` (xem [05-queue-worker-rendering.md](05-queue-worker-rendering.md) §6).
- (Khi đã bật queue) worker chết / Redis mất kết nối → job kẹt `QUEUED`.
- Provider render treo lâu (xem mục 2).

**Kiểm tra:**
```sql
SET LOCAL "vietvid.current_org" = '<ORG_UUID>';
SELECT id, status, purpose, created_at, updated_at, now() - updated_at AS stale
FROM jobs
WHERE status IN ('RUNNING','QUEUED','HELD','WAITING_CONFIG')
ORDER BY updated_at ASC;
```
- `stale` lớn (> thời gian render dài nhất) = thật sự treo, không phải đang chạy.
- Xem tiến trình stage:
  ```sql
  SELECT stage, event, created_at FROM job_events WHERE job_id = '<JOB_ID>' ORDER BY created_at;
  ```
  Stage dừng lại lâu ở một bước = treo ở bước đó.

**Khắc phục:**
1. **Để reaper tự cứu (mặc định).** `app_api/reaper.py` quét job treo (`RUNNING/QUEUED/HELD/WAITING_CONFIG`) cũ hơn `VIETVID_REAPER_STUCK_MIN` (mặc định 15 phút) ở MỌI org → **hoàn 100% HOLD** + đặt `CANCELLED`. Credit về lại ví user tự động. Chu kỳ quét = `VIETVID_REAPER_INTERVAL` (mặc định 600s).
2. **Cần cứu NGAY (không chờ reaper):** hạ tạm ngưỡng rồi gọi reaper thủ công. Reaper chạy trong tiến trình API; cách đơn giản nhất là chỉnh env `VIETVID_REAPER_STUCK_MIN` xuống thấp (vd 1) + restart API → vòng quét đầu sẽ hoàn job. **Nhớ trả env về cũ sau đó** (xem cảnh báo phòng ngừa).
3. **Nếu reaper không cứu được 1 job cụ thể** (lỗi org đó): kiểm tra log `reaper: lỗi khi quét org <id>` (reaper bắt exception per-org để 1 org lỗi không chặn org khác — `reaper.py:74`). Xử lý org đó riêng, hoặc dùng admin `credit-adjust` để bù credit cho user (mục 8).

**Phòng ngừa:**
- ⚠️ **Đặt `VIETVID_REAPER_STUCK_MIN` > thời gian render dài nhất** (đo `stage_timings` trước — ước lượng, cần đo thật). Nếu để thấp hơn, reaper sẽ **cướp job đang render bình thường**, hoàn tiền + huỷ oan. Khuyến nghị = max render time × 2.
- Bật queue mode để API redeploy không giết job (job sống ở worker process riêng — xem [05-queue-worker-rendering.md](05-queue-worker-rendering.md) §5).
- Cảnh báo khi số job treo > ngưỡng (xem [13-monitoring-uptime.md](13-monitoring-uptime.md)).

---

## 2. Provider render sập (PiAPI / fal / Vbee lỗi hoặc chậm)

**Triệu chứng:** Nhiều job `FAILED` cùng lúc, hoặc render rất chậm. Log có lỗi HTTP từ provider (timeout, 5xx, 429 rate-limit).

> Trạng thái: render thật qua provider **đang mock** ở repo (thiếu key — xem [docs/HANDOFF.md](../HANDOFF.md) §7). Kịch bản này áp dụng **sau khi cắm key thật**. Chi tiết provider + routing: [06-providers.md](06-providers.md).

**Kiểm tra:**
1. Lỗi provider rơi vào loại nào — `system` hay `input`?
   ```sql
   SET LOCAL "vietvid.current_org" = '<ORG_UUID>';
   SELECT id, status, fault_class, updated_at FROM jobs
   WHERE status = 'FAILED' ORDER BY updated_at DESC LIMIT 20;
   ```
   - `fault_class = 'system'` (provider sập, mạng) → job đã **REFUND 100%** tự động (`jobs.py:complete_job`), user KHÔNG mất tiền.
   - `fault_class = 'input'` (ảnh hỏng, brief sai) → **SETTLE** theo chi phí thật (đã tiêu provider rồi).
2. Kiểm tra trực tiếp provider còn sống không (status page của PiAPI/fal/Vbee; hoặc gọi thử 1 request đo độ trễ).
3. Lỗi `429` = vượt rate-limit → không phải provider sập, là ta gửi quá nhanh.

**Khắc phục:**
1. **Provider sập diện rộng:** vì lỗi `system` đã auto-REFUND, ưu tiên là **dừng nhận thêm job vào provider đó**. Nếu routing có nhiều provider (xem `video_engine/providers/routing.py:route_video`), chuyển traffic sang provider còn sống. Nếu chỉ 1 provider → tạm thông báo cho user (banner) + (tuỳ) tắt nút tạo video.
2. **Rate-limit (429):** giảm concurrency. Khi đã bật queue, đặt giới hạn concurrency theo provider trong WorkerSettings (xem checklist [05-queue-worker-rendering.md](05-queue-worker-rendering.md)).
3. **Job FAILED-system lẻ tẻ:** không cần làm gì — user đã được hoàn tiền, chỉ cần báo họ thử lại.

**Phòng ngừa:**
- ⚠️ **Retry CHỈ cho lỗi `system`/tạm thời**, KHÔNG retry lỗi `input`. Và tận dụng resume `piapi_task_id` (`sink_queue.py:merge_params`) để retry **không đốt tiền provider lần nữa** (xem [05-queue-worker-rendering.md](05-queue-worker-rendering.md) §4).
- Health-check provider định kỳ → cảnh báo sớm ([13-monitoring-uptime.md](13-monitoring-uptime.md)).
- Free tier ép provider rẻ (xem [09-free-tier-abuse.md](09-free-tier-abuse.md)) để 1 provider sập không kéo sập trải nghiệm trả phí.

---

## 3. Tiền vào nhưng KHÔNG cộng credit (đối soát SePay)

**Triệu chứng:** User chuyển khoản thành công (có biên lai bank) nhưng credit không tăng. Payment vẫn `PENDING`.

**Nguyên nhân gốc (xem `routers/billing.py:sepay_webhook`):**
- (a) SePay chưa gọi `/ipn/sepay` (cấu hình webhook SePay sai, hoặc URL không reachable).
- (b) User **gõ sai/thiếu memo** `VYRAxxxxxxxx` → `parse_sepay_memo` không bóc được mã → SePay ack nhưng không khớp payment.
- (c) **Số tiền lệch** so với payment PENDING → code **cố tình KHÔNG tự cộng** (chờ admin), log `sepay: memo ... số tiền lệch`.
- (d) Memo đúng nhưng không còn payment `PENDING` nào khớp (đã xử lý / memo lạ) → log `sepay: memo ... không khớp payment PENDING nào`.

**Kiểm tra:**
1. Tìm payment của user:
   ```sql
   SET LOCAL "vietvid.current_org" = '<ORG_UUID>';
   SELECT id, provider, ext_ref AS memo, amount_vnd, credits_granted, status, created_at
   FROM payments WHERE provider='bank_qr' ORDER BY created_at DESC LIMIT 10;
   ```
   `ext_ref` chính là memo `VYRAxxxxxxxx` mà user phải ghi khi chuyển khoản.
2. Grep log webhook quanh thời điểm đó:
   ```bash
   # tìm dấu vết IPN SePay (xem 12-logging-observability.md để biết nơi log)
   grep -i "sepay" <logfile>
   ```
   - Có dòng `sepay: memo ... không khớp` → (b) hoặc (d).
   - Có dòng `sepay: memo ... số tiền lệch — nhận X, cần Y` → (c).
   - **Không có dòng SePay nào** → (a): SePay chưa gọi tới. Kiểm tra cấu hình webhook + token bên SePay.
3. Xác nhận token khớp: `/ipn/sepay` yêu cầu header `Authorization: Apikey <VIETVID_SEPAY_TOKEN>`. Token sai → 401, SePay sẽ báo lỗi gửi.

**Khắc phục:**
1. **(a) SePay chưa gọi:** sửa cấu hình webhook SePay (URL `https://<api>/v1/billing/ipn/sepay` + token). Sau khi sửa, có thể **replay** webhook từ dashboard SePay — `apply_topup` idempotent nên an toàn (không cộng đôi).
2. **(b)/(d) memo sai hoặc số tiền đúng nhưng cần cộng tay:** dùng admin `credit-adjust` để cộng đúng số credit cho user (mục 8 + [11-admin-panel.md](11-admin-panel.md)). Ghi `note` rõ: "bù SePay memo sai, ref biên lai bank #...". Việc này ghi `audit_log`.
3. **(c) số tiền lệch:** quyết định theo chính sách (cộng theo số tiền thật nhận, hay yêu cầu user nạp bù). Cộng bằng `credit-adjust` theo số tiền THẬT, không phải số trên payment.

> ⚠️ **KHÔNG** sửa `payments.status` thành `SUCCEEDED` bằng psql tay rồi mong credit tự cộng — credit chỉ cộng qua `apply_topup`/`wallet.topup` (ghi ledger). Sửa status tay = payment "đã xong" nhưng ví không tăng = càng rối.

**Phòng ngừa:**
- UI nạp QR phải hiện memo **to, rõ, copy 1 chạm** + cảnh báo "ghi đúng nội dung này". (Memo do backend sinh, hiện trên cả ảnh VietQR — `billing.vietqr_image_url`.)
- Cảnh báo khi có payment `bank_qr` PENDING > 30 phút mà có log "không khớp"/"lệch" ([13-monitoring-uptime.md](13-monitoring-uptime.md)).
- Reaper tự đặt payment PENDING > 24h thành `FAILED` (`reaper.py:_PAYMENT_STALE_HOURS`) — dọn rác, nhưng KHÔNG hoàn tiền (tiền chưa vào). Đừng nhầm: PENDING→FAILED ≠ mất tiền user.

---

## 4. Cộng tiền ĐÔI (credit cộng 2 lần cho 1 lần nạp)

**Triệu chứng:** User báo credit nhiều hơn số đã nạp, hoặc nghi ngờ 1 giao dịch cộng 2 lần.

**Thiết kế đã chống điều này (3 lớp — xem `billing.py` + `routers/billing.py`):**
- `apply_topup` dùng `SELECT ... FOR UPDATE` + check `status == SUCCEEDED` → IPN gọi lại lần 2 trả về luôn, KHÔNG cộng nữa (R3 idempotent).
- `ext_ref` UNIQUE per-provider = lưới cuối ở DB.
- SePay webhook lại check `FOR UPDATE` + `status` lần nữa trước khi `apply_topup` (`routers/billing.py:168-182`).

→ **Cộng đôi gần như không xảy ra qua đường IPN bình thường.** Nếu thấy nghi vấn, gần như chắc là **(a) cộng tay 2 lần qua admin** hoặc **(b) hiểu nhầm** (free grant + nạp).

**Kiểm tra (truy ngược ledger — nguồn sự thật):**
```sql
SET LOCAL "vietvid.current_org" = '<ORG_UUID>';
SELECT id, kind, delta, payment_id, note, created_at
FROM ledger_entries ORDER BY created_at DESC LIMIT 50;
```
- Tìm 2 dòng `TOPUP` cùng `payment_id` = thật sự cộng đôi (đáng lẽ không thể qua `apply_topup`).
- 2 dòng `TOPUP` khác `payment_id` = 2 lần nạp khác nhau, KHÔNG phải đôi.
- Dòng `ADJUST` lặp lại = admin bấm 2 lần (lỗi người).
- Đối chiếu cache vs ledger (bất biến hệ thống):
  ```sql
  SELECT w.balance_credits AS cached,
         (SELECT COALESCE(SUM(delta),0) FROM ledger_entries le WHERE le.org_id = w.org_id) AS ledger_sum
  FROM wallets w WHERE w.org_id = '<ORG_UUID>';
  ```
  `cached` phải == `ledger_sum`. Lệch = bug nghiêm trọng, báo động ngay (cron `wallet.audit_all` làm việc này tự động — xem [12-logging-observability.md](12-logging-observability.md)).

**Khắc phục:**
- Nếu là cộng tay thừa: dùng `credit-adjust` với số **âm** để trừ lại đúng phần thừa, ghi `note` rõ lý do. KHÔNG xoá ledger row (ledger **append-only**, trigger chặn DELETE/UPDATE — sửa bằng cách thêm dòng đối ứng).
- Nếu (giả định) phát hiện cộng đôi qua IPN: đây là bug — điều tra `apply_topup`/webhook, viết test tái hiện trước khi vá ([investigate] skill).

**Phòng ngừa:**
- Cron `wallet.audit_all` chạy định kỳ báo mọi org lệch cache vs ledger.
- Admin credit-adjust nên có xác nhận 2 bước ở UI để tránh double-click ([11-admin-panel.md](11-admin-panel.md)).

---

## 5. DB chậm / đầy

**Triệu chứng:** API chậm toàn cục, timeout, hoặc lỗi ghi DB ("disk full", "too many connections").

**Kiểm tra:**
1. **Kết nối:** Postgres managed (Neon/Railway) có giới hạn connection. RLS dùng `tenant_session` ngắn (transaction-mode an toàn PgBouncer) nên ít rò connection, nhưng kiểm:
   ```sql
   SELECT count(*), state FROM pg_stat_activity GROUP BY state;
   ```
   Nhiều `idle in transaction` = có transaction không đóng (bug). `too many connections` = cần pooler hoặc tăng giới hạn.
2. **Query chậm:**
   ```sql
   SELECT pid, now()-query_start AS dur, left(query,100)
   FROM pg_stat_activity WHERE state='active' ORDER BY dur DESC;
   ```
   ⚠️ Nghi can lớn: `resolve_bank_payment_org` quét **O(số org)** mỗi webhook SePay (`billing.py:114`, có `TODO(scale)`). Nhiều org + webhook tần suất cao = chậm.
3. **Đầy đĩa:** kiểm dashboard provider DB. Bảng phình: `job_events` (mỗi job nhiều dòng stage), `ledger_entries` (append-only, chỉ tăng), `audit_log`.

**Khắc phục:**
- Connection cạn: bật/đúng cấu hình PgBouncer (transaction mode), giảm `pool_size`, tìm transaction rò.
- Query chậm `resolve_bank_payment_org`: triển khai bảng GLOBAL `memo→org` như `TODO(scale)` gợi ý (mẫu `webhook_events` trong `docs/designs/SYSTEM_DESIGN.md`) trước khi nhiều org.
- Đầy đĩa: archive/dọn `job_events` cũ của job đã terminal (giữ `jobs` + `ledger_entries`). **KHÔNG xoá `ledger_entries`** (kế toán + bất biến). Nâng dung lượng DB plan.

**Phòng ngừa:**
- Monitor connection count + disk + p95 query latency ([13-monitoring-uptime.md](13-monitoring-uptime.md)).
- Mọi query lọc `org_id` tường minh để dùng index (RLS chỉ là lưới an toàn — [docs/HANDOFF.md](../HANDOFF.md) §1).
- Backup định kỳ trước khi đầy ([14-backup-dr-maintenance.md](14-backup-dr-maintenance.md)).

---

## 6. R2 / object storage lỗi (upload/tải video fail)

> Trạng thái: 🔜 R2 chưa cấu hình prod (`VIETVID_S3_*` chưa set — [docs/HANDOFF.md](../HANDOFF.md) §5). Kịch bản áp dụng **sau khi bật R2**. Chi tiết: [04-storage-media.md](04-storage-media.md).

**Triệu chứng:** Job render xong nhưng video không tải được (404/403 signed URL), hoặc job FAILED ở bước upload.

**Kiểm tra:**
1. Bước upload lỗi → xem `job_events` stage upload, và log worker (`worker.py:store_output`).
2. Video row có object key không?
   ```sql
   SET LOCAL "vietvid.current_org" = '<ORG_UUID>';
   SELECT id, job_id, object_key, expires_at, created_at FROM videos ORDER BY created_at DESC LIMIT 10;
   ```
3. Signed URL 403 = key R2 sai/hết hạn quyền, hoặc clock skew. 404 = object đã bị GC xoá (quá `expires_at`) hoặc chưa upload.

**Khắc phục:**
- Credentials R2 sai → sửa env `VIETVID_S3_*` (KHÔNG in giá trị ra log — [15-security.md](15-security.md)). Restart.
- Upload fail diện rộng (R2 down) → job render xong nhưng không lưu được: cân nhắc giữ workdir tạm + retry upload thay vì REFUND (tránh đốt tiền provider lần nữa). Hiện luồng xoá workdir sau upload — khi R2 chập chờn cần thận trọng.
- Object 404 do GC: video quá hạn đã xoá đúng thiết kế. Báo user video hết hạn lưu; render lại nếu cần (mất credit lần nữa — chính sách hiển thị `expires_at` rõ từ đầu).

**Phòng ngừa:**
- Hiển thị `expires_at` cho user ngay khi tạo video.
- Monitor tỉ lệ upload-fail ([13-monitoring-uptime.md](13-monitoring-uptime.md)).
- GC xoá video quá hạn (`videos.expires_at`) là việc 🔜 cần nối (reaper hiện chỉ quét workdir + job treo — [04-storage-media.md](04-storage-media.md)).

---

## 7. Queue tắc (job dồn, worker không tiêu)

> Trạng thái: 🔜 queue mode (Arq+Redis) chưa nối (`submit_job` raise khi `JOB_EXECUTION_MODE=queue`). Kịch bản áp dụng **sau khi bật queue** ([05-queue-worker-rendering.md](05-queue-worker-rendering.md) §5).

**Triệu chứng:** Nhiều job `QUEUED` đứng yên, không chuyển `RUNNING`. User chờ lâu.

**Kiểm tra:**
1. Worker service còn sống không? (Railway: service worker thứ 2, lệnh `arq app_api.queue.WorkerSettings`). Xem **log worker** (KHÔNG phải log API).
2. Redis còn kết nối? Thử ping Redis (`VIETVID_REDIS_URL`).
3. Đếm hàng đợi:
   ```sql
   SELECT status, count(*) FROM jobs GROUP BY status;  -- nhiều QUEUED, ít/không RUNNING = tắc
   ```
4. Worker đang kẹt ở 1 job dài chặn cả hàng (q_fast bị job nặng chiếm)?

**Khắc phục:**
- Worker chết → restart service worker. Job `QUEUED` sẽ được pull lại (nếu enqueue ghi vào Redis bền). Job `QUEUED` quá hạn vẫn được reaper hoàn HOLD nếu kẹt lâu (mục 1).
- Redis mất → khôi phục Redis (Upstash/Railway add-on). Cân nhắc job đã mất khỏi Redis: dựa vào `jobs` trong Postgres làm nguồn sự thật, re-enqueue job `QUEUED` thủ công nếu cần.
- Tắc do 1 job dài chặn hàng nhanh → tách `q_fast`/`q_slow` (đã thiết kế seam — [05-queue-worker-rendering.md](05-queue-worker-rendering.md) §5 bước 3).

**Phòng ngừa:**
- Tách 2 hàng đợi (draft ngắn vs video nặng) ngay khi bật queue.
- Tăng số instance worker khi job dồn.
- ⚠️ Đảm bảo `VIETVID_REAPER_STUCK_MIN` > render dài nhất (mục 1) để reaper không cướp job đang chạy bình thường trong queue.
- Cảnh báo khi depth hàng đợi > ngưỡng hoặc worker im lặng ([13-monitoring-uptime.md](13-monitoring-uptime.md)).

---

## 8. User kêu "mất credit" (balance ít hơn nghĩ)

**Triệu chứng:** User nói bị trừ credit oan, hoặc balance thấp bất thường.

**Nguyên tắc:** **Ledger là nguồn sự thật.** Mọi thay đổi credit đều có 1 dòng `ledger_entries`. Đọc ledger là biết chính xác tiền đi đâu — không cần đoán.

**Kiểm tra (đọc đủ câu chuyện credit của user):**
```sql
SET LOCAL "vietvid.current_org" = '<ORG_UUID>';
-- 1. Trạng thái ví hiện tại
SELECT balance_credits, held_credits FROM wallets WHERE org_id = '<ORG_UUID>';
-- 2. Toàn bộ lịch sử (HOLD/SETTLE/REFUND/TOPUP/ADJUST)
SELECT kind, delta, job_id, payment_id, note, created_at
FROM ledger_entries ORDER BY created_at DESC LIMIT 50;
```
Diễn giải các `kind`:
| kind | nghĩa | dấu delta |
|---|---|---|
| `TOPUP` | nạp tiền | + |
| `HOLD` | giữ tạm khi tạo job | − (sẽ hoàn phần thừa khi settle) |
| `SETTLE` | chốt chi phí thật (hoàn phần giữ thừa) | + (phần thừa) |
| `REFUND` | hoàn 100% khi lỗi hệ thống | + |
| `ADJUST` | admin điều chỉnh tay | ± |

**Các tình huống & khắc phục:**
1. **Credit đang HELD (không phải mất):** `held_credits > 0` + có job đang RUNNING/treo → tiền chưa mất, đang giữ. Xử lý job treo (mục 1) → HOLD sẽ hoàn.
2. **Job lỗi hệ thống nhưng chưa thấy REFUND:** job kẹt RUNNING (mục 1) — reaper sẽ hoàn. Nếu đã FAILED-system mà không có dòng REFUND → bug, điều tra.
3. **User render thật, bị trừ đúng:** giải thích bằng ledger (SETTLE theo chi phí thật). Đây là trừ đúng, không oan.
4. **Thật sự lệch (cache ≠ ledger):** chạy đối chiếu (mục 4 query cuối). Lệch = báo động hệ thống.
5. **Bù credit cho user (do lỗi của ta):** admin `POST /v1/admin/orgs/{org_id}/credit-adjust` body `{"amount": <credit dương>, "note": "bù ... ref ..."}` → cộng qua `wallet.topup(kind=ADJUST)` + ghi `audit_log` ([11-admin-panel.md](11-admin-panel.md)).

**Phòng ngừa:**
- UI ví hiển thị rõ HOLD vs balance (đã có TrustProof HOLD→SETTLE→REFUND — [docs/HANDOFF.md](../HANDOFF.md) §4).
- Hiện số credit TRƯỚC khi tiêu + hoàn 100% khi lỗi hệ thống (wedge minh bạch — [docs/VISION.md](../VISION.md)).
- Cron `wallet.audit_all` bắt lệch cache/ledger sớm.

---

## 9. Bảng tra nhanh (triệu chứng → mục)

| User/triệu chứng nói gì | Mục |
|---|---|
| "Tạo video mãi không xong" / spinner quay hoài | [1](#1-job-kẹt--treo-status-runningqueued-mãi-không-xong) |
| Nhiều job FAILED cùng lúc / render chậm | [2](#2-provider-render-sập-piapi--fal--vbee-lỗi-hoặc-chậm) |
| "Đã chuyển khoản mà không thấy credit" | [3](#3-tiền-vào-nhưng-không-cộng-credit-đối-soát-sepay) |
| Credit cộng 2 lần / nhiều hơn đã nạp | [4](#4-cộng-tiền-đôi-credit-cộng-2-lần-cho-1-lần-nạp) |
| Web chậm toàn cục / lỗi ghi DB | [5](#5-db-chậm--đầy) |
| Video không tải được / 403-404 | [6](#6-r2--object-storage-lỗi-uploadtải-video-fail) |
| Job QUEUED đứng yên không chạy | [7](#7-queue-tắc-job-dồn-worker-không-tiêu) |
| "Tự nhiên mất credit" | [8](#8-user-kêu-mất-credit-balance-ít-hơn-nghĩ) |

---

## Việc cần làm (checklist)

- [ ] Đo thời gian render thật (`stage_timings`) cho từng loại/độ phân giải → đặt `VIETVID_REAPER_STUCK_MIN` đúng (> render dài nhất × 2). Hiện là "ước lượng, cần đo thật".
- [ ] Viết script/snippet "reaper thủ công ngay" gọn (thay vì hạ env + restart) để cứu job treo nhanh khi cần.
- [ ] Triển khai bảng GLOBAL `memo→org` thay `resolve_bank_payment_org` quét O(orgs) trước khi nhiều org (TODO scale ở `billing.py:114`).
- [ ] Nối GC xoá video quá hạn theo `videos.expires_at` (reaper hiện chưa làm) — gắn vào mục 6.
- [ ] Khi bật queue: viết runbook bổ sung "re-enqueue job QUEUED khi Redis mất" + giới hạn concurrency theo provider.
- [ ] Dựng dashboard cảnh báo cho từng kịch bản (job treo, payment lệch, queue depth, upload-fail, cache≠ledger) — xem [13-monitoring-uptime.md](13-monitoring-uptime.md).
- [ ] Kiểm tra `wallet.audit_all` thật sự chạy định kỳ ở prod (cần role BYPASSRLS) và báo động khi lệch.
- [ ] Thêm xác nhận 2 bước cho admin `credit-adjust` để tránh cộng/trừ đôi do double-click ([11-admin-panel.md](11-admin-panel.md)).
- [ ] Bổ sung cách lấy `request_id` từ Sentry vào quy trình mục 0 sau khi cắm Sentry ([12-logging-observability.md](12-logging-observability.md)).
