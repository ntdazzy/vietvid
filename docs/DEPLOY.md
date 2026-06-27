# VietVid — Hướng dẫn deploy production

Kiến trúc (theo plan §9c): **Web (Next.js) → Vercel** · **API+worker (FastAPI) → Render/Fly/Railway** (Docker) · **Postgres → Neon/Render** · **Auth → Supabase** · (tuỳ chọn) **R2** media · **PiAPI** cho video thật · **VieNeu** giọng qua tunnel.

> MVP 1-instance: API + worker chạy CHUNG 1 container (job inline qua BackgroundTasks), media lưu local trên container đó. Đủ cho lưu lượng nhỏ. Scale → tách Arq worker + Redis + R2 (xem "Nâng cấp scale" cuối).

---

## 0. Chuẩn bị (cần bạn cấp)
- Tài khoản: **Vercel**, **Render** (hoặc Fly/Railway), **Neon** (Postgres), **Supabase**, **Cloudflare** (domain + R2).
- Key bắt buộc để render: **GEMINI_API_KEY**, **GROQ_API_KEY** (kịch bản + ảnh AI), **PIAPI_API_KEY** (video i2v thật — TỐN PHÍ).
- Thu tiền: **MoMo Business** (Partner/Access/Secret Key) — cổng chính; VNPay tuỳ chọn.
- Tuỳ chọn nhưng nên có: **R2** (lưu video bền), **SMTP/Resend** (email reset/verify thật), **Sentry** (theo dõi lỗi).
- `VIETVID_ADMIN_EMAILS` = email quản trị của bạn.

> Toàn bộ đã được dựng sẵn trong code (adapter MoMo/VNPay, abstraction lưu trữ, gửi email) —
> chỉ cần dán key vào env là kích hoạt, KHÔNG sửa code. Xem đủ biến ở `.env.production.example`.

## 1. Postgres (Neon)
1. Tạo project Neon → copy connection string.
2. Đổi sang dạng SQLAlchemy: `postgresql+psycopg2://USER:PASS@HOST/DB?sslmode=require`.
3. App tự chạy `alembic upgrade head` lúc khởi động (xem Dockerfile CMD) → tạo **~21 bảng** (migrations 0001→0008: auth/ví/job/video + auth_tokens, org_invitations, plans, credit_packs, templates/KOL/brand_kit, affiliate, notifications, audit_log) + RLS + trigger.
   - **Lưu ý RLS:** role app phải là **non-superuser** để FORCE RLS có hiệu lực (Neon role mặc định OK). CI có test quét `pg_policy` chặn bảng tenant thiếu RLS.

## 2. Auth (Supabase)
1. Tạo project Supabase → Authentication bật Email + Google.
2. Lấy `Project URL` + `anon key` (cho web) và **JWKS URL** `https://<ref>.supabase.co/auth/v1/.well-known/jwks.json` (cho API).
3. Có Supabase → backend tự verify JWT qua JWKS, và `/v1/dev/token` **tự tắt**.

## 3. API (Render bằng Docker)
1. New → Web Service → connect repo, chọn **Dockerfile** (ở repo root).
2. Set env (xem `.env.production.example`): tối thiểu `VIETVID_ENV=production`, `VIETVID_DATABASE_URL`, `CORS_ORIGINS=https://<domain-web>`, `SUPABASE_JWKS_URL`, `GEMINI_API_KEY`, `GROQ_API_KEY`, `IMAGE_PROVIDER=gemini`.
3. Video thật: `VIDEO_PROVIDER=seedance` + `PIAPI_API_KEY` (bỏ trống/`mock` thì ra clip mock).
4. Deploy → kiểm `GET https://<api>/health` trả `{"status":"ok","auth_mode":"supabase"}`.

## 4. Web (Vercel)
1. Import repo → **Root Directory = `apps/web`** → Framework: Next.js (tự nhận).
2. Env:
   - `NEXT_PUBLIC_API_BASE_URL=https://<api-domain>`
   - `NEXT_PUBLIC_SUPABASE_URL=https://<ref>.supabase.co`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY=<anon key>`
3. Deploy → mở domain → đăng nhập Google/Email (Supabase).

## 5. Domain + CORS
- Gắn domain web (Vercel) → cập nhật `CORS_ORIGINS` ở API = domain đó.
- `VNPAY_RETURN_URL` (nếu dùng) = `https://<domain-web>/billing/return`.

## 6. Thanh toán

### MoMo (cổng chính)
- Đăng ký **MoMo Business** → lấy `Partner Code` / `Access Key` / `Secret Key`.
- Set env: `VIETVID_MOMO_PARTNER_CODE`, `VIETVID_MOMO_ACCESS_KEY`, `VIETVID_MOMO_SECRET_KEY`,
  `VIETVID_MOMO_ENDPOINT=https://payment.momo.vn/v2/gateway/api/create` (prod),
  `VIETVID_MOMO_RETURN_URL=https://<web>/billing/return`,
  `VIETVID_MOMO_IPN_URL=https://<api>/v1/billing/ipn/momo`.
- Khai báo IPN URL trên cổng MoMo = `https://<api>/v1/billing/ipn/momo`.
- IPN tự **verify chữ ký HMAC + đối soát số tiền + idempotent** (chống replay & lệch tiền).

### VNPay (cổng phụ, tuỳ chọn)
- Set `VNPAY_TMN_CODE`/`VNPAY_HASH_SECRET`/`VNPAY_URL`. IPN = `https://<api>/v1/billing/ipn/vnpay`.
- Prod tự tắt cổng `dev` (nạp tức thì).

## 7. Admin
- Set `VIETVID_ADMIN_EMAILS=email1@..,email2@..` → các email này vào được `/app/admin`
  (thống kê, khoá user, cộng/trừ credit, duyệt KOL mặt thật). Hành động ghi `audit_log` bất biến.

---

## Checklist trước khi go-live
- [ ] `VIETVID_ENV=production` (dev-token + dev-billing TẮT). App **fail-fast** nếu còn `DEV_JWT_SECRET` placeholder / `CORS=*` → sửa env mới boot được.
- [ ] `CORS_ORIGINS` = domain thật (không `*`).
- [ ] Supabase JWKS set → `/v1/dev/token` trả 404.
- [ ] `alembic upgrade head` chạy OK (migrations 0001→0008; xem log khởi động).
- [ ] `GET /health` ok; `GET /health/ready` trả `{"db":true}`; tạo thử 1 video (cần GEMINI+PIAPI).
- [ ] MoMo: `VIETVID_MOMO_*` set + khai báo IPN URL; nạp thử 1 gói credit.
- [ ] `VIETVID_ADMIN_EMAILS` set; vào `/app/admin` được.
- [ ] Email: `VIETVID_SMTP_*` set (nếu không, link reset/verify chỉ ghi log).
- [ ] Lưu video: `VIETVID_S3_*` (R2) set — nếu không, video mất khi redeploy.
- [ ] HTTPS toàn bộ; secrets chỉ trong env (không commit). CI (`.github/workflows/ci.yml`) xanh.

## Giới hạn MVP & nâng cấp scale
- **Media tạm:** video/ảnh lưu `/tmp` của container → mất khi restart, không chia sẻ đa-instance. Nâng cấp: **Cloudflare R2** (upload sau render, serve URL ký). 1-instance thì OK.
- **Job inline:** render chạy trong tiến trình API (BackgroundTasks). Tải cao → tách **Arq worker + Redis** (2 queue q_fast/q_slow) như plan §7.4.
- **Giọng VieNeu:** chưa cắm → tự fallback edge-tts. Bật clone: dựng VieNeu trên GPU + `TTS_VIENEU_URL`/token (plan §9c "Cách 2").
