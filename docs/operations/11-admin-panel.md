# Web admin vận hành

Đặc tả trang quản trị (super-admin) để solo founder vận hành Vyra một mình: tra cứu user, cộng/trừ/hoàn credit, xem kinh tế (doanh thu vs chi phí AI vs biên), suspend tài khoản, kiểm duyệt KOL mặt thật, đổi cấu hình provider/quota lúc chạy (không deploy), broadcast thông báo.

**Trạng thái:** ⚙️ một phần — backend `routers/admin.py` + `platform.py` đã xong và frontend `app/app/admin/page.tsx` render hầu hết. Còn thiếu: maintenance mode THẬT, audit viewer trên UI, drill-down job/log theo từng user, tắt từng provider riêng.

**Liên quan:** [07-economics.md](07-economics.md) (cách tính biên) · [08-pricing-plans-credits.md](08-pricing-plans-credits.md) (credit/gói) · [06-providers.md](06-providers.md) (provider chain) · [09-free-tier-abuse.md](09-free-tier-abuse.md) (quota/abuse) · [12-logging-observability.md](12-logging-observability.md) (log theo user) · [15-security.md](15-security.md) (gating admin) · [03-database.md](03-database.md) (RLS, ledger) · [18-runbooks.md](18-runbooks.md) (xử lý sự cố)

---

## 1. Admin là ai — cách bật quyền

Admin KHÔNG cần bảng riêng. Gate bằng **email trong env** (`config.py:192`):

```python
ADMIN_EMAILS: str = _str("VIETVID_ADMIN_EMAILS")   # phẩy phân tách
def is_admin_email(email): ...                       # config.py:199
```

Mọi route `/v1/admin/*` đi qua `require_admin` (`deps.py:125`) — so email trong JWT với set này, 403 nếu không khớp.

**Bật quyền cho chính bạn (prod):** thêm env trên Railway/host:

```bash
VIETVID_ADMIN_EMAILS=progamingeasport@gmail.com
# nhiều admin: "a@x.com,b@y.com"
```

Frontend đọc cờ `is_admin` từ `/v1/me` (`page.tsx:19`); không phải admin thì hiện màn "không có quyền truy cập" (`page.tsx:36`).

> ⚠️ **Bảo mật:** đây là allowlist email, KHÔNG phải RBAC bảng. Đổi `VIETVID_ADMIN_EMAILS` = đổi admin tức thì, nhưng cần redeploy/restart để env mới có hiệu lực (trừ khi host hot-reload env). Chi tiết threat model ở [15-security.md](15-security.md).

**Cross-org KHÔNG dùng BYPASSRLS:** bảng global (`users`/`orgs`) query thẳng trong `session_scope`; dữ liệu RLS (ví/job/KOL) thao tác qua `tenant_session(org_id)` cho TỪNG org (admin chỉ định org → set GUC `vietvid.current_org` → policy cho qua). Duyệt toàn-hệ-thống = vòng lặp `_org_ids()` rồi mở tenant_session từng org (`admin.py:28`). An toàn khi số org còn nhỏ; xem mục §10 về scale.

---

## 2. Bản đồ chức năng — backend ↔ frontend ↔ trạng thái

Mọi endpoint dưới prefix `/v1/admin` (`admin.py:25`). Frontend gọi qua `lib/api/endpoints.ts:117-131`.

| Chức năng | Endpoint backend | Hàm FE (`api.*`) | UI render | Trạng thái |
|---|---|---|---|---|
| Thống kê tổng | `GET /stats` | `adminStats` | ✅ 5 thẻ (user/org/job/video/credit) | ✅ |
| Kinh tế (doanh thu/chi phí/biên) | `GET /economics` | `adminEconomics` | ✅ thẻ "Kinh tế vận hành" | ✅ |
| Tra cứu user (search email) | `GET /users?q=` | `adminUsers` | ✅ danh sách + tìm | ✅ |
| Suspend / mở lại user | `POST /users/{id}/status` | `adminSetUserStatus` | ✅ nút Khoá/Mở | ✅ |
| Cộng/trừ credit (ghi ADJUST) | `POST /orgs/{org}/credit-adjust` | `adminCreditAdjust` | ✅ nút "Credit" (prompt) | ✅ |
| Kiểm duyệt KOL mặt thật | `GET /moderation` + `POST /moderation/{id}/decision` | `adminModeration` / `adminModerate` | ✅ hàng chờ Duyệt/Chặn | ✅ |
| Cấu hình runtime (provider chain, quota API) | `GET /config` + `PUT /config` | `adminConfig` / `adminSetConfig` | ✅ 2 ô (chain + quota/ngày) | ✅ |
| Feature-flag theo gói | (trong `/config` → `feature_flags`) | (trong `adminConfig`) | 🔜 chưa có ô riêng trên UI | ⚙️ |
| Broadcast thông báo toàn hệ thống | `POST /broadcast` | `adminBroadcast` | ✅ ô tiêu đề + nội dung | ✅ |
| Audit log viewer | `GET /audit` | 🔜 chưa có hàm FE | 🔜 chưa render | ⚙️ |
| Xem job/render theo TỪNG user | 🔜 chưa có | — | — | 🔜 |
| Xem log structured theo user | 🔜 chưa có | — | — | 🔜 |
| Tắt/bật TỪNG provider riêng | 🔜 (chỉ override chuỗi chain) | — | ⚙️ chỉ sửa chuỗi | ⚙️ |
| Monitor chi phí/biên theo provider | 🔜 (chỉ tổng) | — | — | 🔜 |
| Maintenance mode THẬT | 🔜 (chỉ broadcast + feature_flags) | — | — | 🔜 |

---

## 3. Tra cứu & quản lý user

### 3.1 Tìm user (`GET /v1/admin/users?q=&limit=`)

`admin.py:149`. Không có `q` → trả 50 user mới nhất. Có `q` → tìm `email ILIKE %q%`. `limit` clamp 1..200.

Mỗi user trả: `id, email, full_name, status, org_id, plan_code, created_at`. `org_id`/`plan_code` lấy từ org mà user là `owner` (org đầu tiên — `admin.py:159`).

```bash
# Lấy admin token (dev): POST /v1/dev/token → access_token
TOKEN="<jwt admin>"
curl -s "http://127.0.0.1:8099/v1/admin/users?q=gmail.com&limit=20" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

UI: ô tìm "Tìm theo email..." (`page.tsx:241`), danh sách hiện email + badge trạng thái + badge gói.

### 3.2 Suspend / mở lại (`POST /v1/admin/users/{user_id}/status`)

`admin.py:176`. Body `{"status": "ACTIVE" | "SUSPENDED" | "DELETED"}` (regex chặn giá trị lạ — `admin.py:173`).

**Kill-switch THẬT:** khi `status` = `SUSPENDED`/`DELETED`, lần gọi API kế tiếp của user đó bị chặn ở `get_principal` (`deps.py:40-42`) → **403 "Tài khoản đã bị khoá"**, ngay cả khi JWT còn hạn. Không cần đợi token hết hạn.

```bash
curl -s -X POST "http://127.0.0.1:8099/v1/admin/users/<user_id>/status" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"status":"SUSPENDED"}'
```

Mọi thao tác ghi `audit_log` action `user.status` (`admin.py:183`). UI: nút "Khoá"/"Mở" mỗi hàng (`page.tsx:264`).

> Lưu ý: hiện chỉ chặn user. **Chưa có** "suspend cả workspace/org" — nếu cần khoá toàn org, suspend owner (nhưng member khác vẫn vào được). 🔜 cân nhắc thêm org-level suspend khi có team plan.

---

## 4. Credit: cộng / trừ / hoàn tay

`POST /v1/admin/orgs/{org_id}/credit-adjust` (`admin.py:195`). Body `{"amount": <int khác 0>, "note": "..."}`. `amount>0` cộng, `<0` trừ.

- Đi qua `wallet.topup(... kind=LedgerKind.ADJUST)` → ghi 1 dòng ledger **append-only** (trigger DB chặn sửa/xoá — xem [03-database.md](03-database.md)), snapshot rate.
- Vào đúng `tenant_session(org_id)` → RLS cho qua.
- Trừ quá số dư → `WalletError` → HTTP 400 (CHECK `balance>=0` ở DB là lưới chặn cuối).
- Ghi audit `credit.adjust`.

```bash
# Tặng 500 credit cho org (đền bù lỗi)
curl -s -X POST "http://127.0.0.1:8099/v1/admin/orgs/<org_id>/credit-adjust" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"amount":500,"note":"đền bù render lỗi #abc"}'
```

UI: nút "Credit" mỗi user → `prompt()` nhập số (`page.tsx:48`). Đủ cho solo founder; 🔜 nếu cần lý do chuẩn hoá thì thay prompt bằng form có dropdown lý do.

> **Đây là kênh "hoàn tiền tay" chính** cho khiếu nại. Hoàn tự động khi render lỗi-hệ-thống đã có sẵn ở engine (REFUND 100% hold — [05-queue-worker-rendering.md](05-queue-worker-rendering.md)); credit-adjust dành cho ca ngoại lệ (đền bù thiện chí, sửa nhầm lẫn).

---

## 5. Kinh tế vận hành (doanh thu vs chi phí AI → biên)

`GET /v1/admin/economics` (`admin.py:53`). Quét mọi org, cộng dồn:

| Trường trả về | Ý nghĩa | Nguồn |
|---|---|---|
| `revenue_vnd` | Tổng tiền vào (Payment SUCCEEDED) | `Payment.amount_vnd` |
| `provider_cost_usd` / `provider_cost_vnd` | Chi phí AI thật đã trả provider | `Job.actual_cost_usd` × `USD_TO_VND` |
| `margin_vnd` | `revenue_vnd − provider_cost_vnd` | tính |
| `credits_issued` | Credit đã phát (TOPUP+BONUS) | ledger |
| `credits_consumed` | Credit tiêu thật (≈ trừ phần đang HOLD) | ledger |
| `jobs_total` / `jobs_by_status` / `success_rate` | Số job + tỷ lệ READY | `Job.status` |

UI render ở thẻ "Kinh tế vận hành" (`page.tsx:118`): Doanh thu / Chi phí AI / Biên lợi nhuận + tỷ lệ render thành công.

> ⚠️ **Số liệu là THẬT từ DB**, KHÔNG bịa. Nhưng `provider_cost_usd` chỉ đúng khi engine ghi `Job.actual_cost_usd` thật — hiện render đang **mock** (thiếu key GEMINI/PIAPI), nên trên môi trường dev/mock cột chi phí có thể = 0 hoặc giá ước lượng. Khi cắm key thật + queue mode, cột này mới phản ánh chi tiêu thật. Cách hiểu/diễn giải biên: [07-economics.md](07-economics.md).
>
> ⚠️ **Hạn chế hiện tại:** chỉ là TỔNG toàn hệ thống. KHÔNG có:
> - biên theo từng provider (Kling vs Seedance vs fal) → 🔜 cần group theo `Job.provider`/cost field (xem [06-providers.md](06-providers.md)).
> - biên theo từng thể loại video / từng plan.
> - drill-down chi phí của 1 user/1 job cụ thể.

---

## 6. Cấu hình runtime — đổi không cần deploy

`GET/PUT /v1/admin/config` (`admin.py:94`, `admin.py:106`). Lưu vào bảng `vv_platform_config` (1 hàng id=1), merge lên `DEFAULTS` (`platform.py:13`) nên thiếu key luôn có giá trị an toàn.

Các key đổi được lúc chạy (`platform.py:13`):

| Key | Mặc định | Tác dụng |
|---|---|---|
| `video_provider_chain` | `""` (rỗng = dùng env) | Override thứ tự provider video, vd `"fal,kling,seedance"` |
| `max_api_jobs_per_day` | `200` | Quota tạo video qua API/ngày mỗi org (0 = không giới hạn) |
| `feature_flags` | `{free:{api_access,batch}, pro:{...}}` | Bật/tắt năng lực theo gói (`plan_flag()` đọc — `platform.py:57`) |

```bash
# Đổi chuỗi provider + siết quota free, áp dụng NGAY
curl -s -X PUT "http://127.0.0.1:8099/v1/admin/config" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"video_provider_chain":"fal,kling","max_api_jobs_per_day":50}'
```

UI: thẻ "Cấu hình vận hành" 2 ô (chain + quota — `page.tsx:170`). Ghi audit `config.update` (chỉ log danh sách key, không log giá trị — `admin.py:111`).

**Đây là cần gạt khẩn cấp:** provider tăng giá đột ngột → đổi chain sang provider rẻ ngay; bị abuse → hạ `max_api_jobs_per_day`; muốn tắt API cho free → sửa `feature_flags.free.api_access=false` (qua PUT, vì UI chưa có ô — 🔜).

> **Validation:** `video_provider_chain` max 200 ký tự; `max_api_jobs_per_day` 0..100000 (`admin.py:101`). PUT chỉ nhận key trong `_ALLOWED` (`platform.py:25`) — key lạ bị bỏ.

---

## 7. Kiểm duyệt KOL mặt thật

KOL nguồn AI (`source=ai`) tự `APPROVED` (xem `routers/content.py`). KOL **mặt thật** (user upload) vào hàng chờ `moderation_status=PENDING` → admin duyệt.

- `GET /v1/admin/moderation` (`admin.py:224`): quét mọi org, trả KOL `PENDING` (id, org_id, name, avatar_url, description).
- `POST /v1/admin/moderation/{kol_id}/decision` (`admin.py:246`): body `{"org_id": "...", "approve": true|false}` → set `APPROVED` / `BLOCKED`. Ghi audit `kol.moderate`.

UI: thẻ "Chờ kiểm duyệt KOL mặt thật" CHỈ hiện khi có hàng chờ (`page.tsx:204`), nút Duyệt/Chặn + preview avatar.

```bash
curl -s "http://127.0.0.1:8099/v1/admin/moderation" -H "Authorization: Bearer $TOKEN"
curl -s -X POST "http://127.0.0.1:8099/v1/admin/moderation/<kol_id>/decision" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"org_id":"<org>","approve":true}'
```

> ⚠️ Đây là kiểm duyệt **danh tính/consent** (chống dùng mặt người khác trái phép). Đây là điểm rủi ro pháp lý/uy tín → nên duyệt thủ công nghiêm. 🔜 chưa có: chặn nội dung video output (chỉ duyệt persona đầu vào), không có audit ảnh đã upload, không có lý do từ chối gửi cho user.

---

## 8. Broadcast & "maintenance mode"

### 8.1 Broadcast (`POST /v1/admin/broadcast`) ✅

`admin.py:122`. Body `{"title": "...", "body": "..."}` → tạo 1 notification type `system` cho MỌI org (`notify.create` trong tenant_session từng org). Trả `{ok, sent}`. Ghi audit `broadcast`.

UI: ô tiêu đề + nội dung + nút Gửi (`page.tsx:142`), báo "Đã gửi tới N workspace".

### 8.2 Maintenance mode — ⚙️ chưa có cờ chặn thật

**Hiện trạng:** KHÔNG có cờ `maintenance` chặn request. Cách duy nhất bây giờ:
1. Broadcast báo "Bảo trì lúc X" (chỉ thông báo, KHÔNG chặn).
2. Hoặc `feature_flags`/`max_api_jobs_per_day=0` để tắt tạo video qua API (chặn 1 phần).

**🔜 Để có maintenance mode thật**, cách đơn giản (cầm tay chỉ việc):
1. Thêm key `"maintenance": false` vào `DEFAULTS` (`platform.py:13`).
2. Trong `deps.py` (hoặc middleware), nếu `platform.get_config()["maintenance"]` = true thì các route tạo việc (POST /jobs, topup) trả 503 "Đang bảo trì" — chừa route admin + /me + đọc.
3. Thêm ô bật/tắt trên UI admin (giống ô config sẵn có).
Ưu điểm: bật/tắt qua DB, không deploy, audit lại được. Xem runbook bảo trì ở [18-runbooks.md](18-runbooks.md) và quy trình deploy ở [17-deployment-cicd.md](17-deployment-cicd.md).

---

## 9. Xem log / job / render theo user

| Nhu cầu | Hiện trạng | Làm gì |
|---|---|---|
| Xem audit log toàn hệ thống | ⚙️ backend `GET /v1/admin/audit` đã có (`admin.py:274`), trả 50 dòng mới nhất | 🔜 thêm hàm FE `adminAudit` + 1 thẻ bảng trên `admin/page.tsx` |
| Xem job/render của 1 user | 🔜 chưa có endpoint | 🔜 thêm `GET /v1/admin/orgs/{org}/jobs` quét trong tenant_session, trả Job + cost + status |
| Xem log structured (request-id) theo user | 🔜 chưa | Tạm thời: lọc theo `org_id`/`user_id` trên Sentry/log aggregator — xem [12-logging-observability.md](12-logging-observability.md) |

**Audit hiện ghi gì** (action đã wire): `config.update`, `broadcast`, `user.status`, `credit.adjust`, `kol.moderate`. Mỗi dòng: `action, actor_email, org_id, detail(dict), created_at`. Đây là sổ "ai làm gì" của chính admin — cần render lên UI để tự soi (chống chính admin lạm quyền + đối soát khiếu nại).

```bash
# Đọc audit log (đã có backend, chưa có UI)
curl -s "http://127.0.0.1:8099/v1/admin/audit?limit=50" -H "Authorization: Bearer $TOKEN"
```

---

## 10. Lưu ý vận hành & scale

- **Quét toàn-org là vòng lặp Python** (`_org_ids()` → tenant_session từng org) cho `stats`/`economics`/`moderation`/`broadcast`. Ổn khi < vài trăm org. Khi nhiều org hơn, các call này sẽ chậm → 🔜 cân nhắc role BYPASSRLS cho 1 query gộp, hoặc bảng tổng hợp (materialized) cập nhật định kỳ. Xem [13-monitoring-uptime.md](13-monitoring-uptime.md).
- **Audit best-effort:** `audit.record` nuốt lỗi (không làm hỏng hành động chính — `audit.py:25`). Nghĩa là audit có thể THIẾU dòng nếu DB lỗi lúc ghi; đừng coi audit là sổ tiền (sổ tiền là `ledger_entries` bất biến).
- **Không có 2FA cho admin:** chỉ JWT + email allowlist. Token admin rò = toàn quyền. Giữ token cẩn thận; cân nhắc IP allowlist ở tầng host. Xem [15-security.md](15-security.md).
- **Đứng tên ai khi adjust:** mọi action ghi `actor_email` từ JWT admin → truy được ai làm.

---

## Việc cần làm (checklist)

- [ ] Set `VIETVID_ADMIN_EMAILS` trên host prod (email chủ dự án) và verify `/v1/me.is_admin=true`.
- [ ] Render **audit log viewer** trên UI admin (backend `GET /v1/admin/audit` đã sẵn — chỉ cần `adminAudit` + 1 thẻ bảng).
- [ ] Thêm ô chỉnh **feature_flags theo gói** trên UI (hiện chỉ sửa được qua PUT thủ công).
- [ ] Làm **maintenance mode THẬT**: thêm key `maintenance` vào `platform.DEFAULTS` + chặn POST /jobs & topup khi bật + ô toggle UI (§8.2).
- [ ] Thêm **drill-down job/render theo 1 user/org** (endpoint `GET /v1/admin/orgs/{org}/jobs` + bảng cost/status).
- [ ] Thêm **biên theo từng provider/thể loại/plan** vào `/economics` (hiện chỉ tổng) — cần group theo `Job.provider`.
- [ ] Cho phép **tắt từng provider riêng** (không chỉ override chuỗi chain) — cân nhắc cờ `provider_disabled: [...]`.
- [ ] Thêm **org-level suspend** (khoá cả workspace, không chỉ owner) khi có team plan.
- [ ] Bổ sung **lý do từ chối** khi BLOCK KOL mặt thật, gửi notify cho user.
- [ ] Cân nhắc **2FA / IP allowlist** cho route admin trước khi mở public (đo: thử truy cập /v1/admin bằng token non-admin → phải 403).
- [ ] Khi số org tăng: đo thời gian `/stats` + `/economics` (ước lượng, cần đo thật) → nếu > ~2s, chuyển sang query gộp BYPASSRLS hoặc bảng tổng hợp.
