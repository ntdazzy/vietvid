# Sao lưu, phục hồi & bảo trì

Cách giữ Vyra **không mất tiền của khách và không mất sổ cái** khi máy/DB/provider hỏng: backup tự động Postgres + PITR, diễn tập restore (restore drill), backup media trên R2, bật trang "đang bảo trì", rollback deploy, và kế hoạch thảm hoạ (mất DB / mất laptop).

**Trạng thái:** ⚙️ một phần — code có reaper + dọn workdir + GC-ready (`videos.expires_at`); backup tự động + diễn tập restore + maintenance page = 🔜 chưa làm (phụ thuộc chọn PaaS).
**Liên quan:** [02-infrastructure.md](02-infrastructure.md) · [03-database.md](03-database.md) · [04-storage-media.md](04-storage-media.md) · [10-payments.md](10-payments.md) · [13-monitoring-uptime.md](13-monitoring-uptime.md) · [15-security.md](15-security.md) · [17-deployment-cicd.md](17-deployment-cicd.md) · [18-runbooks.md](18-runbooks.md)

---

## 0. Vì sao file này tồn tại (đọc 30 giây)

Vyra giữ **tiền thật**: sổ cái credit (`ledger_entries` append-only) là nguồn sự thật về số dư của mọi khách. Nếu mất DB mà không có backup → **mất sổ cái = mất tiền khách = chết SaaS**. Đây không phải "nên có", đây là điều kiện sống.

Hai tài sản phải bảo vệ, mức độ khác nhau:

| Tài sản | Ở đâu | Mất thì sao | Ưu tiên |
|---|---|---|---|
| **Postgres** (ví, sổ cái, org, job, payment) | Neon / Railway PG | Mất tiền khách, mất danh tính org | 🔴 SỐNG-CÒN |
| **Media** (video final.mp4 trên R2) | Cloudflare R2 | Khách không tải lại được; re-render tốn tiền | 🟡 quan trọng, tái tạo được (1 phần) |
| **Secrets** (DB url, fal key, bank/sepay token) | file gitignored + env PaaS | Lộ = nguy hiểm; mất = phải xoay vòng key | 🟠 xem [15-security.md](15-security.md) |
| **Laptop i7** | nhà | Chỉ là MÁY DEV — không chứa prod | 🟢 thay được |

> Quyết định vận hành đã chốt: **prod KHÔNG chạy ở laptop**. Laptop = dev. Vì thế "mất laptop" KHÔNG phải mất prod — chỉ mất môi trường dev. Đây là lý do đặt sổ cái lên managed Postgres ngay từ đầu.

---

## 1. Backup Postgres tự động (🔴 việc số 1)

### 1.1 Hiểu PITR vs snapshot

- **Snapshot/base backup** = ảnh chụp DB tại 1 thời điểm. Khôi phục về đúng thời điểm đó.
- **PITR (Point-In-Time Recovery)** = snapshot + WAL log liên tục → khôi phục về **bất kỳ giây nào** trong cửa sổ giữ. Đây là thứ cứu bạn khi "10:42 ai đó chạy nhầm `DELETE`" — restore về 10:41:59.

Với SaaS có tiền, **PITR là chuẩn tối thiểu**. May là cả Neon lẫn Railway đều cho PITR managed — không phải tự dựng `pg_basebackup` + archive WAL.

### 1.2 Nếu dùng Neon (Postgres) — khuyến nghị khởi đầu

Neon có **history retention** (giữ lịch sử WAL) bật sẵn → restore = tạo branch tại 1 timestamp.

✅ Đã sẵn trong Neon (không phải code):
- WAL/history liên tục. Free tier giữ ~1 ngày, gói trả phí giữ 7-30 ngày (đọc bảng giá Neon hiện tại — **cần xác nhận con số đúng tại thời điểm mua**, đừng tin con số trong doc này).

🔜 Việc cần làm (1 lần, qua Neon Console):
1. Mở project → **Settings → History retention** → đặt **≥ 7 ngày** (gói trả phí). Lý do: nếu phát hiện sự cố cuối tuần, vẫn còn cửa sổ restore.
2. Bật **Branch protection** cho branch `main` (production) để không xoá nhầm.
3. (Tuỳ chọn) Lên lịch export logic định kỳ ra R2 (xem §1.4) làm "đai an toàn ngoài Neon".

Restore với Neon = tạo branch từ timestamp:
```bash
# Cài Neon CLI 1 lần: npm i -g neonctl ; neonctl auth
# Tạo branch khôi phục tại đúng thời điểm trước sự cố:
neonctl branches create --project-id <project-id> \
  --name restore-2026-06-29 \
  --parent main \
  --timestamp 2026-06-29T10:41:59Z
# → Neon cấp connection string mới của branch restore. Kiểm tra dữ liệu trên branch
#   này TRƯỚC, rồi mới trỏ app sang (đổi VIETVID_DATABASE_URL) hoặc copy dữ liệu về.
```

### 1.3 Nếu dùng Railway Postgres

Railway PG plugin có **backup** trong tab Database. Mức độ PITR tuỳ plan — **cần kiểm tra tại thời điểm mua** (Railway thay đổi tính năng thường xuyên; đừng tin doc này cho con số). Nếu Railway PITR yếu hơn Neon, dùng thêm backup logic định kỳ ở §1.4 làm chính.

### 1.4 Backup logic độc lập (đai an toàn — KHÔNG phụ thuộc nhà cung cấp)

Dù dùng Neon hay Railway, nên có **1 bản `pg_dump` định kỳ đẩy lên R2**. Lý do: nếu tài khoản Neon/Railway bị khoá/xoá/lỗi billing → backup managed cũng mất theo. Bản dump trên R2 là sao lưu **ngoài hệ sinh thái** đó.

Script (chạy từ một cron — xem §1.5):
```bash
#!/usr/bin/env bash
set -euo pipefail
# Đọc URL từ env (KHÔNG hardcode secret). Trên PaaS set VIETVID_DATABASE_URL.
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
OUT="/tmp/vyra-${STAMP}.dump"

# -Fc = custom format (nén, restore chọn lọc được). --no-owner cho restore sang DB khác dễ.
pg_dump "$VIETVID_DATABASE_URL" -Fc --no-owner -f "$OUT"

# Đẩy lên R2 bằng aws-cli (R2 nói S3 API). Endpoint = R2 của bạn.
aws s3 cp "$OUT" "s3://${VIETVID_S3_BUCKET}/backups/db/vyra-${STAMP}.dump" \
  --endpoint-url "$VIETVID_S3_ENDPOINT"

rm -f "$OUT"
echo "backup ok: vyra-${STAMP}.dump"
```
> `pg_dump` phải cùng major version với server (PG 16 → dùng `pg_dump` 16). Trên Railway có thể chạy script này như 1 **cron service** riêng; với Neon chạy từ GitHub Actions cron (xem [17-deployment-cicd.md](17-deployment-cicd.md)).

**Giữ bao nhiêu bản:** giữ daily 7 ngày + weekly 4 tuần. Tự xoá bản cũ bằng lifecycle rule trên R2 (xem [04-storage-media.md](04-storage-media.md)) hoặc 1 lệnh `aws s3 ls + rm` trong script.

### 1.5 Lịch backup (đề xuất)

| Loại | Tần suất | Giữ | Công cụ |
|---|---|---|---|
| WAL/PITR managed | liên tục | ≥ 7 ngày | Neon/Railway (bật trong console) |
| `pg_dump` → R2 | hằng ngày 03:00 ICT | 7 ngày | GitHub Actions cron / Railway cron |
| `pg_dump` → R2 | Chủ nhật | 4 tuần | cùng cron, prefix `weekly/` |

> Cron đặt **giờ ít user** (03:00 ICT). `pg_dump` đọc-only, không khoá ghi với format custom, nhưng vẫn nên tránh giờ cao điểm.

---

## 2. Diễn tập restore (restore drill) — backup chưa test = chưa có backup

**Quy tắc sắt:** một backup chưa từng restore thành công là backup giả định. Lên lịch **diễn tập 1 tháng/lần**.

Quy trình diễn tập (làm trên môi trường tách biệt, KHÔNG động prod):
```bash
# 1. Lấy bản dump mới nhất từ R2
aws s3 cp "s3://${VIETVID_S3_BUCKET}/backups/db/<file mới nhất>.dump" /tmp/test.dump \
  --endpoint-url "$VIETVID_S3_ENDPOINT"

# 2. Tạo DB rỗng để restore vào (local dev hoặc 1 Neon branch nháp)
createdb vyra_restore_test   # hoặc tạo Neon branch nháp

# 3. Restore
pg_restore --no-owner -d "postgresql://.../vyra_restore_test" /tmp/test.dump

# 4. KIỂM CHỨNG bằng truy vấn — đây là phần quan trọng nhất:
psql "postgresql://.../vyra_restore_test" -c "SELECT count(*) FROM orgs;"
psql "...vyra_restore_test" -c "SELECT count(*) FROM ledger_entries;"
# Bất biến sổ cái: cache số dư phải khớp tổng ledger (xem audit cron trong wallet)
psql "...vyra_restore_test" -c "
  SELECT w.org_id, w.balance, COALESCE(SUM(l.delta),0) AS ledger_sum
  FROM wallets w LEFT JOIN ledger_entries l ON l.org_id = w.org_id
  GROUP BY w.org_id, w.balance
  HAVING w.balance <> COALESCE(SUM(l.delta),0)
  LIMIT 5;"
# → 0 dòng = sổ cái nhất quán sau restore. Có dòng = restore hỏng, ĐIỀU TRA NGAY.
```
> ⚠️ Tên cột `delta` ở trên là **ví dụ** — kiểm cột thật trong `app_api/models.py` (bảng `ledger_entries`) trước khi chạy. Mục tiêu của truy vấn: chứng minh "số dư = tổng sổ cái" vẫn đúng sau restore.

**Sau diễn tập:** ghi vào [18-runbooks.md](18-runbooks.md) thời gian restore mất bao lâu (RTO thực đo) + bản dump dùng được hay không. Đây là số liệu THẬT, không ước lượng.

**Mục tiêu khôi phục (đặt mục tiêu, đo dần — chưa có số thật):**
- **RPO** (mất tối đa bao nhiêu dữ liệu): ≤ 5 phút nếu PITR; ≤ 24h nếu chỉ dump daily. *Ước lượng theo cấu hình, cần đo thật qua diễn tập.*
- **RTO** (khôi phục mất bao lâu): mục tiêu < 1 giờ. *Cần đo thật ở lần diễn tập đầu.*

---

## 3. Backup media trên R2 (🟡)

Media = video `final.mp4` user tạo (xem [04-storage-media.md](04-storage-media.md)). Code đã có:
- `app_api/storage.py:store_output` — upload `videos/<job_id>.mp4` lên bucket khi `VIETVID_S3_*` set. ⚙️ (chưa cấu hình prod)
- Bản ghi DB `videos.storage_url` trỏ tới object key → tái tạo URL/signed-URL.

**R2 có bền không?** Cloudflare R2 có độ bền cao như S3 (11 số 9 theo Cloudflare — **theo tài liệu nhà cung cấp, không tự đo được**). Với 1 bucket region R2, rủi ro lớn nhất KHÔNG phải hỏng đĩa mà là **xoá nhầm / khoá tài khoản / app ghi đè sai key**.

🔜 Việc cần làm:
1. **Bật versioning** trên bucket R2 → object bị xoá/ghi đè vẫn lấy lại được phiên bản cũ.
2. (Tuỳ chọn, sau) Cấu hình **R2 → R2 replication** hoặc dump định kỳ sang 1 bucket/region khác cho video "quan trọng". MVP solo founder **không cần** ngay — video tái render được; DB thì KHÔNG.
3. Bản `pg_dump` (§1.4) đã sống trên R2 → nếu R2 chết, dump cũng chết. Vì vậy với DB, **PITR managed của Neon/Railway** mới là lớp 1; R2-dump là lớp 2.

> Ưu tiên đúng: **DB > media**. Media mất từng phần thì re-render. DB mất = mất tiền không tái tạo được.

---

## 4. Maintenance mode (trang "đang bảo trì")

Cần khi: nâng cấp DB lớn, migration nguy hiểm, restore khẩn cấp, hoặc provider render chết hàng loạt. Mục tiêu: **KHÔNG nhận `POST /jobs` mới** (tránh HOLD credit rồi không render được) và báo user lịch sự.

Trạng thái: 🔜 chưa có flag maintenance trong code.

**Cách làm gọn nhất (đề xuất — chưa code):** thêm 1 env flag đọc trong `app_api/config.py`, ví dụ `VIETVID_MAINTENANCE=1`, rồi 1 middleware/dependency trong `app_api/` trả **503** cho các route ghi (`POST /jobs`, `/billing/topup`) nhưng vẫn cho **đọc** (xem ví, lịch sử) để user không hoảng. Mẫu logic:

1. Bật cờ: trên PaaS set biến `VIETVID_MAINTENANCE=1` → redeploy (vài giây).
2. Backend: route ghi → trả `503 {"error":"maintenance","retry_after":900}`. Route đọc → bình thường.
3. Frontend `apps/web/` đọc trạng thái (gọi 1 endpoint `/v1/health` trả `maintenance:true`) → hiện banner "Vyra đang nâng cấp, quay lại sau ít phút" thay vì nút tạo video bị lỗi khó hiểu.
4. Xong việc → `VIETVID_MAINTENANCE=0` → redeploy.

> Quan trọng cho TIỀN: trong maintenance, **đặc biệt chặn `POST /jobs`**. Nếu cho tạo job mà render không chạy được, credit bị HOLD → reaper sẽ hoàn sau (xem §6), nhưng tốt nhất là không tạo nợ đó ngay từ đầu.

Nếu chưa muốn động code: PaaS (Railway/Vercel) cho phép tạm **pause service** hoặc trỏ domain sang 1 trang tĩnh "maintenance.html" — thô hơn nhưng nhanh.

---

## 5. Rollback deploy (khi bản mới hỏng)

Chi tiết CI/CD ở [17-deployment-cicd.md](17-deployment-cicd.md); ở đây là phần "lùi lại an toàn".

**Rollback code (dễ):**
- Railway/Vercel giữ lịch sử deploy → bấm **Redeploy** bản trước đó (rollback tức thì, không build lại).
- Hoặc `git revert <commit hỏng>` → push → CI deploy lại. (Đừng `git reset --hard` trên nhánh đã push.)

**Rollback migration (NGUY HIỂM — đọc kỹ):**
- Migration đổi schema thường KHÔNG rollback sạch được nếu đã có dữ liệu mới theo schema mới. `alembic downgrade -1` chạy được khi `down_revision`/`downgrade()` viết đúng, nhưng dữ liệu đã ghi theo cột mới có thể mất.
- **Quy tắc:** migration phải **tương thích ngược** (expand → migrate → contract):
  1. **Expand:** thêm cột/bảng mới (nullable), deploy. Code cũ vẫn chạy.
  2. **Migrate:** backfill dữ liệu, deploy code dùng cột mới.
  3. **Contract:** chỉ xoá cột cũ ở deploy SAU, khi chắc không còn ai dùng.
- Nhờ vậy rollback code 1 bậc luôn an toàn vì schema vẫn tương thích cả 2 bản.
- Trước migration nguy hiểm trên prod: **chụp snapshot/branch DB** (Neon branch / Railway backup) NGAY TRƯỚC. Nếu hỏng → restore branch đó.

Lệnh migration thật của dự án (xem [HANDOFF.md](../HANDOFF.md) §6):
```bash
PYTHONUTF8=1 /c/Python314/python -m alembic upgrade head
PYTHONUTF8=1 /c/Python314/python -m alembic downgrade -1   # lùi 1 bậc (chỉ khi downgrade() đúng)
```

---

## 6. Kế hoạch thảm hoạ (DR) — kịch bản & cách xử

### Kịch bản A — Mất/hỏng Postgres prod
1. Bật maintenance (§4) để dừng nhận job/nạp mới.
2. Restore: Neon → tạo branch tại timestamp trước sự cố (§1.2); hoặc `pg_restore` từ dump R2 (§1.4) vào DB mới.
3. **Kiểm chứng sổ cái** bằng truy vấn ở §2 (số dư = tổng ledger). Đây là cổng chặn — không pass thì không mở lại.
4. Trỏ app sang DB đã restore (đổi `VIETVID_DATABASE_URL` trên PaaS) → redeploy.
5. Tắt maintenance. Đối chiếu payment gần thời điểm sự cố với cổng thanh toán (SePay) — xem [10-payments.md](10-payments.md), IPN idempotent nên replay an toàn.

### Kịch bản B — Mất laptop dev
- Prod KHÔNG ảnh hưởng (chạy trên PaaS). Việc cần làm:
  1. Secrets KHÔNG ở git (file `_*.txt` gitignored) → laptop mới phải lấy lại key từ nguồn (Neon/fal/bank console, password manager). **Phải có 1 nơi lưu secret an toàn ngoài laptop** — xem [15-security.md](15-security.md). Nếu chưa có → đây là rủi ro lớn, làm ngay.
  2. Clone lại repo, tạo lại file secret local, `pip install` + `bun install`.
  3. Khôi phục `_vietvid_db_url.txt` (prod đọc từ env PaaS, dev cần URL DB dev riêng).

### Kịch bản C — Provider render (PiAPI/fal/Vbee) chết
- Không phải DR dữ liệu, là DR dịch vụ. Render fail-hệ-thống → ví **REFUND 100%** tự động (đã code, xem [05-queue-worker-rendering.md](05-queue-worker-rendering.md) + wallet trong [HANDOFF.md](../HANDOFF.md) §5). Tiền khách KHÔNG mất.
- Nếu chết kéo dài: bật maintenance hoặc tạm ẩn thể loại phụ thuộc provider đó. Routing đa-provider (`video_engine/providers/routing.py`) cho phép đổi provider — xem [06-providers.md](06-providers.md).

### Kịch bản D — Lộ secret (DB url / bank token / fal key)
- Xoay vòng (rotate) ngay: đổi mật khẩu DB (Neon/Railway), tạo key fal mới, đổi SePay token. Cập nhật env PaaS → redeploy. Quy trình đầy đủ ở [15-security.md](15-security.md).

---

## 7. Job/credit "treo" — reaper đã lo (✅ có, cần bật + theo dõi)

Đây là DR cấp-job: nếu tiến trình render chết giữa chừng (API restart/redeploy lúc job RUNNING), HOLD credit không được SETTLE/REFUND → **credit đóng băng của khách**. Code đã giải quyết:

- `app_api/reaper.py:reap_stuck_jobs` — quét mọi org, job non-terminal **quá hạn** (`RUNNING/QUEUED/HELD/WAITING_CONFIG`, `updated_at < cutoff`) → `release_hold` (hoàn 100% HOLD) + CANCELLED. ✅
- Cũng đánh `Payment` PENDING > 24h → FAILED (cổng bỏ dở). ✅
- Cũng `sweep_old_workdirs` xoá thư mục tạm mồ côi > 48h ở **cloud-mode** (local-mode giữ `final.mp4` đang serve). ✅
- Chạy: 1 lần lúc boot + vòng lặp định kỳ (`app_api/main.py`). ✅

Env điều khiển (`app_api/config.py:171-181`):

| Env | Mặc định | Ý nghĩa |
|---|---|---|
| `VIETVID_REAPER` | `True` | Bật/tắt reaper |
| `VIETVID_REAPER_STUCK_MIN` | `15` | Job quá số phút này mà không tiến triển → coi là treo |
| `VIETVID_REAPER_INTERVAL` | `600` | Chu kỳ quét (giây) = 10 phút |

> ⚠️ Reaper quét **mọi org** (bảng global lấy danh sách org rồi mở `tenant_session` từng org) → ở prod cron toàn-org cần role **BYPASSRLS** hoặc đúng cơ chế đang dùng (xem [HANDOFF.md](../HANDOFF.md) §1 + [03-database.md](03-database.md)). Theo dõi log `reaper: hoàn N job treo` để biết có rò rỉ bất thường không (xem [12-logging-observability.md](12-logging-observability.md)).

---

## 8. GC video quá hạn (🔜 chưa nối)

`videos.expires_at` đã có trong schema (`app_api/models.py:617`) nhưng **reaper hiện chỉ quét workdir + job treo, CHƯA xoá object R2 theo `expires_at`**. Đây là việc cần làm khi bật R2 (xem [04-storage-media.md](04-storage-media.md) + [HANDOFF.md](../HANDOFF.md) §5):
- Quét `videos` có `expires_at < now()` → xoá object trên R2 (`videos/<job_id>.mp4`) → đánh dấu DB.
- Để tránh "xoá rồi user còn muốn tải": áp `expires_at` theo plan (free ngắn, trả phí dài). Liên quan free tier: [09-free-tier-abuse.md](09-free-tier-abuse.md).

---

## 9. Lịch bảo trì định kỳ (để chủ dự án không quên)

| Việc | Tần suất | Tham chiếu |
|---|---|---|
| Kiểm `pg_dump → R2` còn chạy + bản mới nhất tồn tại | hằng tuần | §1.4 |
| **Diễn tập restore** + đo RTO + verify sổ cái | hằng tháng | §2 |
| Soát log reaper (job treo bất thường?) | hằng tuần | §7, [12-logging-observability.md](12-logging-observability.md) |
| Kiểm dung lượng R2 + chi phí + lifecycle xoá backup cũ | hằng tháng | §1.4, [04-storage-media.md](04-storage-media.md) |
| Chạy `alembic upgrade head` đã sạch chưa (drift schema) | mỗi deploy | §5, [17-deployment-cicd.md](17-deployment-cicd.md) |
| Soát secret sắp hết hạn / cần xoay vòng | hằng quý | [15-security.md](15-security.md) |
| Kiểm cửa sổ giữ PITR (Neon/Railway) còn ≥ 7 ngày | hằng quý | §1.2 |

---

## Việc cần làm (checklist)

- [ ] Chọn PaaS DB (Neon hay Railway PG) và **bật PITR/history retention ≥ 7 ngày** trong console.
- [ ] Viết + lên lịch script `pg_dump → R2` (daily 03:00 ICT, weekly Chủ nhật) — §1.4, §1.5.
- [ ] Cấu hình lifecycle xoá backup cũ trên R2 (giữ 7 daily + 4 weekly).
- [ ] Làm **diễn tập restore lần đầu** → đo RTO thật, verify sổ cái (số dư = tổng ledger) → ghi vào [18-runbooks.md](18-runbooks.md).
- [ ] Đặt lịch diễn tập restore hằng tháng (nhắc trong lịch cá nhân hoặc cron báo).
- [ ] Bật **versioning** trên bucket R2 (media).
- [ ] Thêm **maintenance flag** (`VIETVID_MAINTENANCE`) + middleware chặn route ghi (đặc biệt `POST /jobs`) + banner frontend — §4.
- [ ] Xác minh quy trình **rollback** trên PaaS đang dùng (thử redeploy bản trước 1 lần để biết cách).
- [ ] Áp **expand→migrate→contract** cho mọi migration đổi schema từ giờ — §5.
- [ ] Lưu secret ở nơi an toàn **ngoài laptop** (password manager/secret store) để DR "mất laptop" — §6.B, [15-security.md](15-security.md).
- [ ] **Bật reaper ở prod** + đảm bảo role BYPASSRLS đúng + theo dõi log job-treo — §7.
- [ ] **Nối GC `videos.expires_at`** vào reaper khi bật R2 (xoá object quá hạn) — §8.
- [ ] Đo & điền **RPO/RTO thật** (đang là mục tiêu ước lượng) sau diễn tập đầu — §2.
