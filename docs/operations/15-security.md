# 15 — Bảo mật & bí mật

Cách giữ an toàn cho hệ thống Vyra: quản lý secret (không bao giờ commit), xác thực JWT, cách ly đa-tenant fail-closed (RLS), chống brute-force/lạm dụng, xử lý dữ liệu cá nhân (PII), và một checklist phải tích đủ TRƯỚC KHI mở web cho người lạ.

**Trạng thái tổng quát:** ⚙️ một phần — nền bảo mật code đã có và verify (JWT dual-mode, RLS fail-closed, rate limit, startup gate prod, security headers); CHƯA bật đầy đủ ở môi trường prod thật (Supabase chưa cắm, secret prod chưa đặt trên Railway, redaction log chưa có lớp lọc tự động).

**Liên quan:**
- [02-infrastructure.md](02-infrastructure.md) — nơi đặt env/secret trên Railway, HTTPS
- [03-database.md](03-database.md) — RLS đa-tenant chi tiết
- [09-free-tier-abuse.md](09-free-tier-abuse.md) — chống farm credit, lạm dụng free tier
- [10-payments.md](10-payments.md) — bảo vệ webhook IPN (idempotent, token SePay)
- [11-admin-panel.md](11-admin-panel.md) — quyền admin
- [12-logging-observability.md](12-logging-observability.md) — log có request-id, không lộ stack
- [16-i18n.md](16-i18n.md) — CORS theo domain vùng
- [17-deployment-cicd.md](17-deployment-cicd.md) — đặt secret lúc deploy

---

## 1. Mô hình mối đe doạ (ai tấn công cái gì)

Vyra là SaaS đa-tenant giữ **sổ cái tiền thật** (credit) và gọi **API trả tiền theo lượt** (render video ~3.000–12.000đ/video, *ước lượng, cần đo thật* — xem [07-economics.md](07-economics.md)). Bề mặt tấn công ưu tiên:

| Đe doạ | Hậu quả | Lớp phòng thủ trong code |
|---|---|---|
| Giả mạo token → truy cập tài khoản người khác | Lộ video/dữ liệu, tiêu credit hộ | JWT verify (`auth.py`), kill-switch tài khoản (`deps.py`) |
| Xem dữ liệu tenant khác (org A đọc org B) | Rò video, doanh thu, danh sách KH | **RLS FORCE fail-closed** (`db.py`, `models.py`) |
| Brute-force login / farm 300 credit free | Mất tiền render, spam | Rate limit (`ratelimit.py`) + free-tier siết ([09](09-free-tier-abuse.md)) |
| Đốt tiền provider (spam POST /jobs) | Hoá đơn fal/PiAPI tăng vọt | Rate limit `expensive` + HOLD credit trước (`wallet.py`) |
| Cộng tiền giả qua webhook | Lỗ trực tiếp | IPN idempotent + token SePay ([10](10-payments.md)) |
| Lộ secret (API key, JWT secret, DB pass) | Toàn quyền hệ thống | Secret để env/file gitignored, KHÔNG in ra log |
| Lộ stack trace / chi tiết lỗi | Lộ cấu trúc nội bộ | Exception handler trả envelope an toàn (`observability.py`) |

Đây là **solo founder, web công khai** → ưu tiên cao nhất là: (1) không lộ secret, (2) RLS không bao giờ rò chéo tenant, (3) prod không boot với cấu hình dev.

---

## 2. Quản lý secret — KHÔNG BAO GIỜ commit ✅ (cơ chế) / 🔜 (đặt trên prod)

### 2.1 Nguyên tắc
- **Mọi secret đọc từ `os.environ`** qua helper `_str()/_int()/_bool()` trong `app_api/config.py`. KHÔNG hardcode secret trong code.
- **KHÔNG có file `.env`** trong repo. Dev đọc 2 file **gitignored**:
  - `_vietvid_db_url.txt` — connection string Postgres (`config.py:36` fallback `VIETVID_DATABASE_URL`).
  - `_fal_key.txt` — khoá fal.ai.
- `.gitignore` đã chặn: `.env`, `.env.local`, `_vietvid_db_url.txt`, `_fal_key.txt`, `_*_key.txt`, `secrets/`, `*.local`, `.gstack/` (xem `.gitignore:7-48`).
- **CẤM in nội dung secret ra stdout/log/console.** Khi cần xác nhận đã set, in `bool(value)` chứ không in value.

### 2.2 Danh sách secret prod cần đặt (trên Railway → tab Variables)

> Đặt qua dashboard Railway hoặc `railway variables set KEY=VALUE`. KHÔNG dán secret vào terminal có lưu lịch sử dùng chung. Chi tiết nơi đặt: [02-infrastructure.md](02-infrastructure.md), [17-deployment-cicd.md](17-deployment-cicd.md).

| Env var | Bắt buộc prod? | Dùng cho | Trạng thái |
|---|---|---|---|
| `VIETVID_DATABASE_URL` | ✅ | Kết nối Postgres (role non-superuser) | 🔜 đặt khi deploy |
| `VIETVID_ENV=production` | ✅ | Bật startup gate + tắt cổng dev | 🔜 |
| `SUPABASE_JWKS_URL` hoặc `SUPABASE_JWT_SECRET` | ✅ (nếu dùng Supabase) | Verify JWT prod | 🔜 chưa cắm |
| `DEV_JWT_SECRET` | ✅ (nếu KHÔNG dùng Supabase) | Ký token HS256 — phải ≥24 ký tự, ngẫu nhiên mạnh | 🔜 |
| `CORS_ORIGINS` | ✅ | Domain frontend cụ thể (CẤM `*`) | 🔜 |
| `VIETVID_BANK_*` + `VIETVID_SEPAY_TOKEN` | ✅ (bật nạp tiền) | QR bank + webhook đối soát | ⚙️ chỉ test |
| `VIETVID_S3_*` (R2) | ✅ (lưu video) | Object storage | 🔜 |
| `VIETVID_SMTP_*` | ⚙️ | Gửi email reset/verify thật | 🔜 |
| `VIETVID_ADMIN_EMAILS` | ✅ | Cấp quyền super-admin | 🔜 |
| `GEMINI_API_KEY` / `PIAPI_API_KEY` / `GROQ_API_KEY` | ⚙️ | Render thật (đang mock) | ❌ thiếu |

### 2.3 Cách sinh secret mạnh
```bash
# DEV_JWT_SECRET (≥32 ký tự ngẫu nhiên) — chạy local, dán kết quả vào Railway
/c/Python314/python -c "import secrets; print(secrets.token_urlsafe(48))"
```

### 2.4 Nếu lỡ commit secret
1. **Coi như đã lộ** — đổi (rotate) ngay key đó ở nhà cung cấp (fal/Supabase/SePay/DB pass).
2. Xoá khỏi lịch sử git (`git filter-repo` hoặc tạo lại repo nếu chưa push xa).
3. Kiểm tra `git log -p -- <file>` xem còn dấu vết không.
> Quy tắc vận hành sống còn: `git add` **từng path tường minh**, CẤM `git add .` / `-A` (vô tình kéo secret + binary). Xem [HANDOFF.md §8.4].

---

## 3. Xác thực JWT (auth.py + tokens.py) ✅

### 3.1 Dual-mode (`app_api/auth.py`)
`verify_token(token)` → `Principal(user_id, email, claims)` hoặc raise `AuthError` (router map sang 401). Hai chế độ tự chọn theo env (`config.auth_mode()`, `config.py:65`):

- **supabase** (prod khuyến nghị): có `SUPABASE_JWKS_URL` → verify RS256/ES256 qua JWKS (khoá bất đối xứng, tự refresh, cache 1h, `auth.py:40-47`); hoặc `SUPABASE_JWT_SECRET` → HS256 legacy.
- **dev** (chưa cắm Supabase): tự ký/verify HS256 bằng `DEV_JWT_SECRET`. Cho phép verify lớp HTTP ngay trên Postgres thật mà không cần Supabase.

Bất biến an toàn đã có trong `_decode()` (`auth.py:50-70`):
- `options={"require": ["exp", "sub"]}` — token thiếu hạn/chủ thể bị từ chối.
- `leeway=30` — chịu lệch đồng hồ nhẹ.
- Chỉ chấp nhận thuật toán khai báo tường minh (`algorithms=[...]`) → chặn tấn công `alg=none` / nhầm RS↔HS.
- Verify `aud`/`iss` khi có cấu hình.

### 3.2 Token vòng đời (`app_api/tokens.py`) ✅
Reset mật khẩu / verify email / refresh — **chỉ lưu `sha256(token)` trong DB**, raw token chỉ xuất hiện 1 lần (email/response):
- `issue()` sinh `secrets.token_urlsafe(32)`, lưu hash + `expires_at` (`tokens.py:28`).
- One-time token (reset/verify): `consume()` đánh dấu `used_at`, không tái dùng (`tokens.py:59`).
- Refresh: rotate = revoke cũ + issue mới; `revoke_all()` để logout-all / trước khi đổi mật khẩu (`tokens.py:79`).

### 3.3 Khoá API B2B (`app_api/apikeys.py`) ✅
- Prefix `vv_live_` + `secrets.token_urlsafe(32)`; **chỉ lưu `sha256(key)`**, raw trả 1 lần (`apikeys.py:24`).
- `verify()` tra theo hash, bỏ key đã `revoked_at`, cập nhật `last_used_at` (`apikeys.py:36`).
- Auth qua header `X-API-Key` hoặc `Authorization: Bearer vv_live_…` (`deps.py:81`).

### 3.4 Kill-switch tài khoản ✅
`get_principal` (`deps.py:38-43`) gọi `tenancy.user_account_status` — tài khoản `SUSPENDED`/`DELETED` bị chặn 403 **dù token còn hạn**. Tức là khoá user có hiệu lực ngay, không phải đợi token hết hạn.

### 3.5 TTL token (chỉnh qua env, `config.py:151-154`)
| Token | Mặc định | Env |
|---|---|---|
| Access | 1h | `VIETVID_ACCESS_TTL` |
| Refresh | 30 ngày | `VIETVID_REFRESH_TTL` |
| Reset mật khẩu | 1h | `VIETVID_RESET_TTL` |
| Verify email | 24h | `VIETVID_VERIFY_TTL` |

---

## 4. Cách ly đa-tenant — RLS fail-closed ✅

Đây là lưới an toàn QUAN TRỌNG NHẤT: org này không bao giờ đọc được dữ liệu org khác, kể cả khi code quên lọc `org_id`.

- **FORCE ROW LEVEL SECURITY** trên bảng tenant + policy `org_isolation`:
  `org_id = nullif(current_setting('vietvid.current_org', true), '')::uuid` (`models.py:73`).
- **Fail-closed:** GUC chưa set → predicate so với NULL → **0 dòng** (không phải "thấy hết"). Quên set scope = không thấy gì, an toàn hơn là rò.
- Mọi truy cập bảng tenant phải qua `tenant_session(org_id)` (`db.py:67-83`): transaction NGẮN, `SET LOCAL vietvid.current_org` ngay đầu (an toàn PgBouncer transaction-mode).
- ⚠️ **FORCE áp cả owner DB** → cron toàn-org (vd `audit_all`) cần role **BYPASSRLS** riêng ở prod.
- Bảng GLOBAL đọc pre-auth (không RLS) nằm trong allowlist ở `models.py` (memberships, org_invitations, vv_affiliate_links, vv_link_clicks, audit_log, vv_api_keys).
- **Lớp kép:** RLS là lưới an toàn; mọi query vẫn lọc `org_id` tường minh (vừa là index path, vừa là phòng thủ chiều sâu).

> Bất biến: role app connect là **non-superuser** (`VIETVID_DB_APP_ROLE`, `config.py:43`) — superuser bỏ qua RLS, sẽ phá fail-closed. Kiểm tra trước khi mở prod (xem checklist §9).

---

## 5. Chống brute-force & lạm dụng (ratelimit.py) ✅ (MVP) / ⚙️ (prod đa-instance)

`RateLimitMiddleware` (`app_api/ratelimit.py`) — cửa sổ cố định trong-tiến-trình (dict + lock), khoá theo `(IP, bucket)`:

| Bucket | Mặc định | Route | Env |
|---|---|---|---|
| `auth` | 10 / 60s | login/register/forgot/reset/verify/change-password/dev-token | `VIETVID_RL_AUTH` |
| `expensive` | 30 / 60s | POST /v1/jobs, /images/generate, /voice/preview, /compose | `VIETVID_RL_EXPENSIVE` |
| `default` | 120 / 60s | mọi route còn lại | `VIETVID_RL_DEFAULT` |

- Vượt giới hạn → `429` + header `Retry-After` (`ratelimit.py:81-86`).
- IP lấy từ `X-Forwarded-For` (sau proxy Railway) rồi tới client trực tiếp (`ratelimit.py:52-56`).
- Bật/tắt: `VIETVID_RATE_LIMIT` (mặc định bật, `config.py:139`).

⚠️ **Giới hạn quan trọng — prod đa-instance:** bộ đếm nằm **trong RAM mỗi tiến trình**. Khi Railway chạy ≥2 instance (app + scale-out), mỗi instance đếm riêng → giới hạn thực = N × limit. Bucket `auth` chống brute-force sẽ lỏng hơn dự kiến.
- **Cách sửa (🔜):** thay `_hits` dict bằng Redis `INCR`+`EXPIRE` (knob config giữ nguyên — chỉ đổi backend). Redis đã có sẵn cho queue mode (Arq) nên không tốn thêm hạ tầng. Xem [05-queue-worker-rendering.md](05-queue-worker-rendering.md).
- Lạm dụng free tier (farm 300 credit) còn được chặn ở tầng kinh tế: clamp theo plan (`validate.py`) + HOLD credit trước khi render. Chi tiết [09-free-tier-abuse.md](09-free-tier-abuse.md).

---

## 6. Security headers + CORS + xử lý lỗi (observability.py + main.py) ✅

### 6.1 Security headers (`observability.py:97-113`)
`SecurityHeadersMiddleware` đặt (bật mặc định prod, `config.py:135`):
- `X-Content-Type-Options: nosniff` — chặn MIME-sniffing.
- `X-Frame-Options: DENY` — chống clickjacking.
- `Referrer-Policy: strict-origin-when-cross-origin`.
- `Strict-Transport-Security` (HSTS 1 năm) — **chỉ phát khi đã HTTPS** (`scheme==https` hoặc `x-forwarded-proto==https`), tránh tự khoá khi chạy http local.

### 6.2 CORS (`main.py:95-102`)
Thứ tự middleware: CORS → RequestContext → RateLimit → SecurityHeaders → app.
- `CORS_ORIGINS` (`config.py:81`) — prod đặt domain cụ thể, phẩy phân tách. **CẤM `*`** (startup gate chặn boot — §7).

### 6.3 Không lộ stack trace (`observability.py:116-147`)
- Lỗi chưa xử lý → `500` envelope `{"detail": "Lỗi hệ thống...", "request_id": ...}` — **không trả stack ra client**, traceback chỉ vào log server.
- Mọi response gắn `X-Request-Id` để truy vết (xem [12-logging-observability.md](12-logging-observability.md)).

---

## 7. Startup gate — prod không boot với cấu hình dev ✅

`validate_prod_config()` (`startup_checks.py:26-57`) chạy lúc boot (`main.py:54`). Khi `VIETVID_ENV=production`, **ném `UnsafeProdConfig` và chặn khởi động** nếu:

1. Dùng dev-auth (HS256 tự phát) mà `DEV_JWT_SECRET` còn placeholder/yếu (<24 ký tự, kiểm qua `looks_real_secret`) → token giả mạo được.
2. `CORS_ORIGINS=*` ở prod.
3. `VIETVID_DEV_AUTH` còn bật (cổng `/v1/dev/token` tạo token vô hạn).
4. `VIETVID_BILLING_DEV` còn bật (nạp credit miễn phí không qua cổng thật).

> Đây là phanh tay cuối: dù bạn quên tắt cổng dev, prod sẽ **không lên** thay vì chạy với lỗ hổng. Khi deploy mà app crash với message "Cấu hình prod không an toàn", đọc log để biết thiếu env nào.

Cổng dev tự tắt theo `IS_PROD` (`config.py:62, 90`): `DEV_AUTH_ENABLED`/`BILLING_DEV_ENABLED` mặc định = `not IS_PROD`.

---

## 8. Dữ liệu cá nhân (PII) & redaction

### 8.1 PII Vyra lưu (⚙️ rà soát trước khi mở)
- **Email** người dùng (lowercased, `auth.py:94`) — đăng nhập/định danh.
- **Token hash** (không phải raw) — reset/verify/refresh/API key đều chỉ sha256.
- **Lịch sử giao dịch** (ledger, payment) — gắn org, không lưu số thẻ (thanh toán qua cổng VietQR/SePay, Vyra không chạm PAN).
- **Nội dung user tạo** — kịch bản, ảnh upload, video output (lưu R2, cấp signed URL — [04-storage-media.md](04-storage-media.md)).

### 8.2 Không lộ PII/secret trong log 🔜 (cần lớp lọc)
- Access log hiện chỉ ghi method/path/status/ms/request_id (`observability.py:85-91`) — **không log body**, tốt.
- ⚠️ **Rủi ro cần kiểm:** nếu code nào đó `log.info(payload)` chứa email/token, nó vào log prod. CHƯA có lớp lọc redaction tự động.
- **Việc cần làm:** rà toàn bộ `log.*` đảm bảo không in token/secret/PII thô; cân nhắc filter logging mask các khoá nhạy (`token`, `secret`, `password`, `authorization`). Đo bằng grep:
  ```bash
  grep -rn "log\.\(info\|debug\|warning\)" app_api/ | grep -iE "token|secret|password|email"
  ```

### 8.3 Quyền dữ liệu (GDPR-lite, 🔜 khi có user thật)
- Cần endpoint/admin action: xoá tài khoản (đã có trạng thái `DELETED` → kill-switch), export dữ liệu user khi yêu cầu. Hiện admin có thể SUSPEND/DELETE ([11-admin-panel.md](11-admin-panel.md)).

---

## 9. Checklist bảo mật TRƯỚC KHI mở công khai

> Tích đủ những mục ✅-bắt-buộc trước khi cho người lạ vào. Mục 🔜 là phải làm; ⚙️ là kiểm tra lại.

### Trước khi deploy prod đầu tiên
- [ ] `VIETVID_ENV=production` đã đặt (kích hoạt startup gate + tắt cổng dev).
- [ ] App **boot thành công** với env prod (nếu crash "Cấu hình prod không an toàn" → đọc log sửa từng mục).
- [ ] Auth: đã đặt `SUPABASE_JWKS_URL`/`SUPABASE_JWT_SECRET` **HOẶC** `DEV_JWT_SECRET` ≥32 ký tự ngẫu nhiên mạnh (không placeholder).
- [ ] `CORS_ORIGINS` = domain frontend thật, KHÔNG `*`.
- [ ] `VIETVID_DEV_AUTH` và `VIETVID_BILLING_DEV` **tắt** (rỗng) — đã được gate ép, vẫn xác nhận.
- [ ] DB role app là **non-superuser** (RLS FORCE mới có hiệu lực). Kiểm: `SELECT rolsuper FROM pg_roles WHERE rolname=current_user;` phải `f`.
- [ ] Cron toàn-org (nếu chạy) dùng role **BYPASSRLS** riêng, KHÔNG dùng role app.
- [ ] HTTPS bật (Railway cấp domain TLS) → HSTS sẽ tự phát.

### Secret
- [ ] Không secret nào nằm trong git (`git log -p` không lộ; `.gitignore` đã chặn `_*_key.txt`, `.env`).
- [ ] Tất cả secret prod đặt trên Railway Variables, không in ra log/console.
- [ ] Token webhook SePay (`VIETVID_SEPAY_TOKEN`) là chuỗi mạnh, đã đặt; IPN verify token + idempotent ([10-payments.md](10-payments.md)).

### Cách ly & lạm dụng
- [ ] Thử thật: đăng nhập org A, gọi API đọc dữ liệu → KHÔNG thấy dữ liệu org B (test RLS fail-closed bằng vận hành thật, không tin pytest mock).
- [ ] Rate limit bật (`VIETVID_RATE_LIMIT=1`); nếu chạy ≥2 instance → đã chuyển sang Redis backend (nếu chưa, ghi nhận giới hạn lỏng × N).
- [ ] Free tier siết cứng (480p/≤20s/watermark/giới hạn số video) — [09-free-tier-abuse.md](09-free-tier-abuse.md).

### PII / log
- [ ] Grep log không in token/secret/password/email thô (lệnh §8.2).
- [ ] Lỗi 500 trả envelope an toàn, không lộ stack (kiểm bằng gọi route gây lỗi).

---

## Việc cần làm (checklist)

- [ ] **Đặt toàn bộ secret prod trên Railway** (bảng §2.2) — bắt buộc trước deploy.
- [ ] **Cắm Supabase** (`SUPABASE_JWKS_URL`) hoặc sinh `DEV_JWT_SECRET` mạnh ≥32 ký tự.
- [ ] **Đặt `CORS_ORIGINS`** = domain thật, bỏ `*`.
- [ ] **Xác minh DB role non-superuser** + tạo role BYPASSRLS riêng cho cron toàn-org.
- [ ] **Chuyển rate limit sang Redis** (`INCR`+`EXPIRE`) khi prod chạy đa-instance — tái dùng Redis của queue mode.
- [ ] **Thêm lớp lọc redaction cho log** (mask `token`/`secret`/`password`/`authorization`/email) + rà toàn bộ `log.*` hiện có.
- [ ] **Test RLS chéo tenant bằng vận hành thật** (org A không đọc được org B) — không tin mock.
- [ ] **Đo & ghi chi phí render thật** để hiệu chỉnh HOLD và chống đốt tiền provider (liên kết [07-economics.md](07-economics.md)).
- [ ] **Bổ sung GDPR-lite**: endpoint xoá/export dữ liệu user khi có người dùng thật.
- [ ] **Quy trình rotate secret** + ghi sổ ngày tạo từng key (DB pass, SePay token, fal/Gemini key).
