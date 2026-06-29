# Lưu trữ video & media

Nơi cất file video/ảnh/giọng sau khi render: vì sao chọn **Cloudflare R2**, cách cấu hình `VIETVID_S3_*`, object key, signed URL để xem/chia sẻ, và vòng đời (GC) xoá video quá hạn theo `videos.expires_at`.

**Trạng thái:** ⚙️ một phần — code upload R2 + signed URL ✅ đã có (`storage.py`, `media.py`); GC theo `videos.expires_at` 🔜 CHƯA nối (cột có sẵn nhưng không ai ghi, không ai quét).

**Liên quan:** [02-infrastructure.md](02-infrastructure.md) (R2 là 1 mảnh hạ tầng) · [05-queue-worker-rendering.md](05-queue-worker-rendering.md) (worker gọi `store_output`) · [03-database.md](03-database.md) (bảng `videos` giữ key) · [07-economics.md](07-economics.md) (chi phí lưu trữ trong unit economics) · [14-backup-dr-maintenance.md](14-backup-dr-maintenance.md) (sao lưu R2 + dọn rác).

---

## 1. Vì sao Cloudflare R2 (không phải ổ cứng / không phải S3 thường)

Vyra render xong **chỉ giữ `final.mp4`** → đẩy lên object storage → xoá thư mục tạm. Người dùng tải/xem lại nhiều lần. Ba phương án:

| Phương án | Egress (băng thông user tải về) | Ổ cứng cần | Phù hợp |
|---|---|---|---|
| Ổ cứng máy nhà / VPS | — | Phải mua đĩa to, tự backup | ❌ máy nhà chỉ là DEV (rủi ro uptime/mất dữ liệu) |
| AWS S3 | **~$0.09/GB** (đắt — user xem video tốn tiền mỗi lần) | 0 | ⚠️ egress giết biên lợi nhuận |
| **Cloudflare R2** | **$0/GB (miễn phí egress)** | 0 | ✅ **chọn cái này** |

**Lý do cốt lõi:** video là file nặng, user xem/tải lại liên tục → egress là chi phí ẩn lớn nhất. R2 tính tiền lưu trữ + thao tác (request) nhưng **KHÔNG tính egress** → tải về bao nhiêu cũng 0đ. Đây là lý do duy nhất nhưng quyết định.

→ Không cần mua ổ cứng to. Máy laptop i7 ở nhà chỉ là máy DEV; prod lưu trên R2. Xem [02-infrastructure.md](02-infrastructure.md).

**Code đã sẵn sàng R2:** `store_output()` trong [app_api/storage.py:29](../../app_api/storage.py) dùng `boto3` client với `endpoint_url` → R2 nói giao thức S3, nên cùng một code chạy được cả AWS S3, R2, hay MinIO. Chỉ đổi env.

---

## 2. Cấu hình `VIETVID_S3_*`

Tất cả env đọc trong [app_api/config.py:175-188](../../app_api/config.py). **Để trống = lưu file local** (chế độ MVP 1-box, `final.mp4` nằm trong thư mục tạm). Set đủ 3 biến bắt buộc + boto3 → bật cloud.

| Env | Bắt buộc? | Ý nghĩa | Ví dụ (R2) |
|---|---|---|---|
| `VIETVID_S3_BUCKET` | ✅ | Tên bucket | `vyra-videos` |
| `VIETVID_S3_ACCESS_KEY` | ✅ | R2 Access Key ID | (từ R2 dashboard → API Tokens) |
| `VIETVID_S3_SECRET_KEY` | ✅ | R2 Secret Access Key | (như trên — **bí mật, không in ra**) |
| `VIETVID_S3_ENDPOINT` | ⚙️ R2 cần | Endpoint S3-compat của R2 | `https://<account_id>.r2.cloudflarestorage.com` |
| `VIETVID_S3_REGION` | ⚙️ | Region; R2 dùng `auto` | `auto` (mặc định) |
| `VIETVID_S3_PUBLIC_BASE` | 🔜 tuỳ chọn | Base CDN public để trả URL trực tiếp | `https://cdn.vyra.vn` |

**Điều kiện bật cloud** (`config.storage_configured()`): chỉ `BUCKET` + `ACCESS_KEY` + `SECRET_KEY` cùng có. Nếu thiếu 1 trong 3 → `store_output` trả lại local path, hệ thống chạy local-mode (xem [app_api/config.py:187](../../app_api/config.py)).

> ⚠️ R2 **bắt buộc** `VIETVID_S3_ENDPOINT` (khác AWS S3 — AWS để trống là OK). Quên endpoint → boto3 gọi nhầm AWS, upload lỗi (nhưng job KHÔNG hỏng — `store_output` bắt mọi exception, log rồi giữ file local; xem [storage.py:49](../../app_api/storage.py)).

### Lấy key R2 (cầm tay chỉ việc)
1. Cloudflare dashboard → **R2** → Create bucket → đặt tên (vd `vyra-videos`).
2. R2 → **Manage R2 API Tokens** → Create API Token → quyền **Object Read & Write** cho bucket đó.
3. Copy **Access Key ID**, **Secret Access Key**, và **Account ID** (account ID nằm trong endpoint URL).
4. Endpoint = `https://<ACCOUNT_ID>.r2.cloudflarestorage.com`.
5. Set 4 env trên ở Railway (prod) — KHÔNG commit vào git, KHÔNG để trong file tracked.

### Cách kiểm chứng đã bật
```bash
# Trong tiến trình python (chạy ở thư mục repo, đã export VIETVID_S3_*):
/c/Python314/python -c "from app_api import config; print('cloud=', config.storage_configured())"
# True = đã bật cloud; False = đang local-mode
```
Sau đó render thử 1 job rồi xem bucket R2: phải xuất hiện object `videos/<job_id>.mp4`.

---

## 3. Object key & luồng upload

**Object key cố định:** `videos/<job_id>.mp4` — sinh trong [storage.py:43](../../app_api/storage.py):
```python
key = f"videos/{job_id}.mp4"
client.upload_file(local_path, config.STORAGE_BUCKET, key,
                   ExtraArgs={"ContentType": "video/mp4"})
```

**Luồng (đã code, ✅):**
1. Worker render xong → có `final.mp4` ở thư mục tạm (`workdir`).
2. [app_api/worker.py:41-44](../../app_api/worker.py) gọi `storage.store_output(result.path, job_id)` **TRƯỚC** khi `complete_job` ghi DB. Trả về:
   - Cloud bật + `STORAGE_PUBLIC_BASE` có → `https://cdn.../videos/<job_id>.mp4`
   - Cloud bật, không public base → `s3://<bucket>/videos/<job_id>.mp4`
   - Cloud tắt / upload lỗi → giữ nguyên local path.
3. `complete_job` ghi giá trị đó vào `videos.storage_url` ([jobs.py:144-148](../../app_api/jobs.py)).

> Vì key chỉ phụ thuộc `job_id` (đã unique), render lại cùng job sẽ **ghi đè** đúng object đó — không sinh rác trùng. `videos` có `UniqueConstraint(job_id)` nên 1 job = 1 row video = 1 object.

**`org_id` KHÔNG nằm trong key.** Cách ly tenant dựa vào DB (RLS): chỉ chủ org đọc được `videos.storage_url`, và signed URL gắn `org_id` (mục 4). Key phẳng `videos/<uuid>.mp4` không lộ thông tin tenant.

---

## 4. Signed URL — xem & chia sẻ không cần Bearer

Trình duyệt không gắn header `Authorization` vào `<video src>`. Nên Vyra cấp **URL có chữ ký HMAC** hết hạn. Code: [app_api/media.py](../../app_api/media.py) + [app_api/routers/media.py](../../app_api/routers/media.py).

**Token** = `base64(job_id:org_id:exp)` + `.` + `HMAC-SHA256(msg, DEV_JWT_SECRET)`. Verify check chữ ký + `job_id` khớp + chưa quá `exp` ([media.py:39-54](../../app_api/media.py)).

**Hai loại URL (đã có ✅):**

| Endpoint (authed, chủ job gọi) | TTL | Env | Dùng cho |
|---|---|---|---|
| `GET /v1/jobs/{id}/video-url` | `MEDIA_URL_TTL` (mặc định **3600s = 1h**) | `VIETVID_MEDIA_URL_TTL` | Phát video trong app |
| `GET /v1/jobs/{id}/share-url` | `MEDIA_SHARE_TTL` (mặc định **30 ngày**) | `VIETVID_MEDIA_SHARE_TTL` | Link chia sẻ công khai `/share/{id}/{token}` |

Cả hai trả URL dạng `/v1/media/video/{job_id}?token=...`. Endpoint công khai `GET /v1/media/video/{job_id}` ([routers/media.py:23](../../app_api/routers/media.py)):
- Verify token → lấy `org_id`.
- Mở `tenant_session(org_id)` đọc `videos.storage_url`.
- Nếu là URL `http(s)://` (R2 public/CDN) → **redirect 302** thẳng tới R2 (browser tải trực tiếp, không qua app → 0 băng thông app + 0đ egress R2).
- Nếu là path local → `FileResponse` serve file.

> ⚠️ **Hiện chưa ký URL R2 riêng tư (presigned S3 URL).** Code chỉ redirect tới `STORAGE_PUBLIC_BASE` (giả định object **public-read** qua CDN). Nếu bucket R2 để private, redirect sẽ 403. Hai lựa chọn khi lên prod thật:
> - **(A) Cho object public-read** qua R2 custom domain / `STORAGE_PUBLIC_BASE` = đơn giản, nhưng ai có URL đều xem được (URL = `videos/<uuid>.mp4`, đoán khó nhưng không có hạn). Bảo vệ bằng việc URL chỉ lộ qua signed token.
> - **(B) Sinh R2 presigned URL** (`client.generate_presigned_url`) có hạn → an toàn hơn. 🔜 chưa code; cần thêm hàm trong `media.py`/`storage.py` để redirect tới presigned thay vì public base.
> Khuyến nghị MVP: (A) + để token Vyra là cổng chính, vì video user tự tạo không quá nhạy cảm. Nâng (B) khi có khách doanh nghiệp yêu cầu private. Ghi nhận ở checklist.

---

## 5. Vòng đời / GC theo `videos.expires_at` — 🔜 CẦN NỐI

**Hiện trạng (sự thật từ code):**
- Cột `videos.expires_at` **CÓ tồn tại** ([models.py:617](../../app_api/models.py)), nullable.
- Nhưng **KHÔNG nơi nào GHI** giá trị: khi tạo video [jobs.py:144-148](../../app_api/jobs.py) không set `expires_at` → luôn `NULL`.
- Và **KHÔNG nơi nào QUÉT** để xoá: reaper ([app_api/reaper.py](../../app_api/reaper.py)) chỉ hoàn HOLD cho job treo + `sweep_old_workdirs()` xoá **thư mục tạm** mồ côi (≠ object trên R2). Xem [storage.py:79](../../app_api/storage.py).

→ Kết quả: video lưu trên R2 **không bao giờ tự xoá**. Với free tier siết (xem [09-free-tier-abuse.md](09-free-tier-abuse.md)), video free nên có hạn (vd 7 ngày) để không phình dung lượng vô tận.

**Việc cần làm (3 mảnh, độc lập):**

**(a) Ghi `expires_at` khi tạo video.** Trong [jobs.py:144](../../app_api/jobs.py), thêm hạn theo plan của org. Ví dụ free = 7 ngày, trả phí = NULL (giữ mãi). Cần env mới, vd:
```python
# config.py (đề xuất 🔜)
VIDEO_TTL_FREE_DAYS: int = _int("VIETVID_VIDEO_TTL_FREE_DAYS", 7)
# jobs.py khi tạo Video: nếu plan free → expires_at = now + TTL; trả phí → None
```
> Cần đọc plan của org để quyết. Plan/credit logic: xem [08-pricing-plans-credits.md](08-pricing-plans-credits.md).

**(b) Job GC quét + xoá.** Thêm hàm trong `storage.py` (vd `gc_expired_videos()`): quét `videos` có `expires_at < now()` ở mọi org (như reaper lặp org tôn trọng RLS), với mỗi video:
1. Xoá object R2: `client.delete_object(Bucket, Key=f"videos/{job_id}.mp4")`.
2. Đặt cờ đã xoá (vd `storage_url=''` hoặc thêm cột `purged_at`) — KHÔNG xoá row video để giữ lịch sử/đối soát.

**(c) Lên lịch GC.** Gọi `gc_expired_videos()` trong vòng lặp reaper định kỳ (`REAPER_INTERVAL_SECONDS`, mặc định 600s) hoặc cron riêng. Pattern lặp-org-tôn-trọng-RLS đã có sẵn ở [reaper.py:42-75](../../app_api/reaper.py) — copy cấu trúc đó.

> Lưu ý RLS: quét toàn-org cần role **BYPASSRLS** hoặc lặp từng org qua `tenant_session` (reaper đang làm cách 2). Xem [03-database.md](03-database.md) về BYPASSRLS.

---

## 6. Ước tính dung lượng & chi phí (ước lượng — cần đo thật)

> ⚠️ **TRUNG THỰC:** Vyra mới ra mắt, chưa có video thật trên prod. Mọi số dưới là **ước lượng dựa trên giả định kích thước file**, phải **đo thật** sau khi render bằng provider thật (Kling/Seedance/Veo). Cách đo: render 10 video mỗi độ phân giải/độ dài thật → lấy trung bình `file_size_bytes` (cột này đã có trong `videos`, [models.py:611](../../app_api/models.py)) → nhân lên.

**Giả định để ước lượng** (KHÔNG phải số đo):
- 1 video ~15-20s, 720p, mp4 nén → **~2 MB/video** (cần xác nhận với provider thật; có thể 1-5 MB).
- Free tier 480p/≤20s/watermark → có thể nhẹ hơn (~0.5-1.5 MB).

**Bảng ước lượng (giả định 2 MB/video, giá R2 niêm yết tại thời điểm viết — tự xác nhận trên trang giá Cloudflare):**

| Số video tích luỹ | Dung lượng (~2MB/cái) | Lưu trữ R2/tháng (~$0.015/GB) | Egress |
|---|---|---|---|
| 10.000 | ~20 GB | ~$0.30 | $0 |
| 100.000 | ~200 GB | ~$3 | $0 |
| 1.000.000 | ~2 TB | ~$30 | $0 |

→ **Lưu trữ rất rẻ; egress 0đ là điểm ăn tiền.** Chi phí thật của Vyra là VIDEO RENDER (provider), không phải storage — xem [06-providers.md](06-providers.md) và [07-economics.md](07-economics.md).

**Chi phí thao tác (Class A/B operations):** R2 tính tiền theo số request ghi/đọc. Mỗi render = 1 PUT (Class A). Đọc qua redirect tới R2 public/CDN = Class B (rẻ hơn) hoặc qua Cloudflare CDN cache = miễn phí. Với MVP số request nhỏ → gần như 0đ. Xác nhận giá Class A/B trên trang giá R2.

> Cách giảm chi phí + tăng tốc: gắn **Cloudflare CDN** trước R2 (qua custom domain `STORAGE_PUBLIC_BASE`) → video xem lại được cache ở edge, không tính Class B mỗi lần.

---

## 7. Tóm tắt file/đường dẫn liên quan

| File | Vai trò |
|---|---|
| [app_api/storage.py](../../app_api/storage.py) | `store_output` (upload R2), `cleanup_workdir`, `sweep_old_workdirs` (dọn tmp, KHÔNG dọn R2) |
| [app_api/media.py](../../app_api/media.py) | Ký + verify token HMAC cho signed URL |
| [app_api/routers/media.py](../../app_api/routers/media.py) | Endpoint public `GET /v1/media/video/{job_id}` (redirect R2 hoặc serve local) |
| [app_api/routers/jobs.py:259-304](../../app_api/routers/jobs.py) | `video-url`, `share-url`, `video` (cấp URL, xoá file khi xoá job) |
| [app_api/config.py:175-188](../../app_api/config.py) | Env `VIETVID_S3_*`, `MEDIA_*_TTL`, `storage_configured()` |
| [app_api/models.py:595-626](../../app_api/models.py) | Bảng `videos` (`storage_url`, `expires_at`, `file_size_bytes`, `has_watermark`) |

---

## Việc cần làm (checklist)

- [ ] Tạo bucket R2 `vyra-videos` + API token (Object Read & Write) trên Cloudflare.
- [ ] Set `VIETVID_S3_BUCKET`, `VIETVID_S3_ACCESS_KEY`, `VIETVID_S3_SECRET_KEY`, `VIETVID_S3_ENDPOINT` ở Railway (prod). KHÔNG commit.
- [ ] Render thử 1 job prod → xác nhận object `videos/<job_id>.mp4` xuất hiện trong bucket + `videos.storage_url` ghi đúng URL.
- [ ] Quyết public-read (A) hay presigned URL (B) cho R2; nếu (A) → gắn `VIETVID_S3_PUBLIC_BASE` (custom domain + CDN); nếu (B) → code thêm `generate_presigned_url`.
- [ ] **Nối GC `expires_at`** (3 mảnh): (a) ghi `expires_at` khi tạo video theo plan ([jobs.py:144](../../app_api/jobs.py)); (b) viết `gc_expired_videos()` xoá object R2 + đánh dấu purged; (c) lên lịch trong vòng lặp reaper.
- [ ] Thêm env `VIETVID_VIDEO_TTL_FREE_DAYS` (đề xuất 7) + đọc plan org để quyết hạn.
- [ ] **Đo thật** kích thước file/video bằng provider thật (Kling/Seedance/Veo) → cập nhật bảng ước tính dung lượng ở mục 6 (dùng cột `file_size_bytes`).
- [ ] Gắn Cloudflare CDN cache trước R2 để giảm Class B operations + tăng tốc xem lại.
- [ ] Xác nhận chiến lược backup R2 (versioning / sao lưu chéo) — xem [14-backup-dr-maintenance.md](14-backup-dr-maintenance.md).
