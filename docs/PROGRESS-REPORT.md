# VYRA — BÁO CÁO TIẾN ĐỘ (cập nhật 2026-06-29)

> Trạng thái thật, có verify. Đọc nhanh để biết: ĐÃ XONG gì · CÒN gì · CẦN BẠN cấp gì.

## 🔧 PHIÊN 2026-06-29 (chiều) — CỨU LỖI 500 + HOÀN TẤT i18n + QA NÚT SÂU

**Bối cảnh:** workflow i18n pha-2 (`wbd0hg9is`) **FAIL** (output rỗng, chết giữa lô) → để lại app **vỡ (trang chủ 500)** + 16 màn rò key thô. Đã chẩn đoán + sửa tận gốc:

| Lỗi | Gốc rễ | Fix | Verify |
|---|---|---|---|
| Trang chủ **500** | `getTranslations` (server) thiếu `createNextIntlPlugin` + `request.ts` | thêm `src/lib/i18n/request.ts` + bọc plugin vào `next.config.mjs` | `/`=200 vi+en |
| 16 màn **rò key thô** | workflow convert `t()` nhưng chưa merge maps | **khôi phục 18 namespace (~450 key vi+en) từ transcript agent** (StructuredOutput) + nest lại | 0 MISSING_MESSAGE |
| key `a.b` không resolve | agent lưu key **phẳng có chấm** | unflatten → object lồng | validator 0 key literal thiếu |
| audio/compose thiếu | 2 agent chết theo lô | tự author vi+en + wire chrome | compose EN 0 Việt sót |
| **tràn ngang mobile** (admin/settings/api) | grid/flex con thiếu `min-w-0` | min-w-0 + `overflow-x-clip` shell | scrollWidth=390 mọi màn |
| **admin avatar vỡ** (seed `http://x/a.jpg`) | render thẳng url giả | avatar fallback chữ-cái + img onError | hiện initials |

**i18n giờ ĐỦ 23 namespace, render EN thật** (dashboard/settings/admin/billing/compose). Việt còn sót = DATA backend (tên giọng/KOL, template seed, tiền, ledger) — đúng, không phải lỗi.

**QA nút (real-qa, bằng chứng backend):** 22 GET đọc → 200 đúng shape; 7 write hoàn-lại-được (createKol/brandKit/apiKey/webhook/affiliateLink/template + markRead + estimate) → tạo→verify→**undo sạch**; tốn-tiền/render (createJob/topup/voicePreview/generateImage/compose) skip (đã PASS phiên trước). **Pivot copy** đúng đa-thể-loại; "chốt đơn" chỉ còn trong genre bán hàng (hợp lệ).

## ✅ ĐÃ XONG + VERIFY (tsc EXIT=0 + screenshot/HTTP thật)

**Giao diện — 24 màn redesign "Vyra-native"** (brand tím + glass + ảnh candid thật + chữ không-AI), **mỗi màn một bố cục riêng**, đã **bỏ hết dấu hiệu autovis** (viewfinder/REC/SCENE/DIRECTOR'S CUT/gold):
- App: Dashboard · Create (chọn thể loại trước) · KOL casting · Library (cuộn phim) · Video-detail · Series · Image-gen · Audio · Compose · Billing · Reports · Affiliate · Team · Templates · Brand-kits · API · Settings · Admin.
- Marketing: Home (cuộn-reel bento) · mega-menu header (spotlight) · Feature pages (3 hero khác nhau) · Pricing · Login · Share.
- Nền dùng chung: kit `cinematic.tsx` (CineHero/ContentCard/FilmLabel eyebrow) · chuyển cảnh `template.tsx` + skeleton `loading.tsx` · 10 ảnh showcase candid (fal) · 7 accent/màn.

**Quốc tế hoá (i18n)** — next-intl theo cookie (KHÔNG đổi URL, an toàn): vi mặc định + en, **nút đổi ngôn ngữ** ở header, messages phần UI chung. Tự nhận theo IP qua middleware.

**Middleware** (`apps/web/src/middleware.ts`) — chọn locale theo header geo (VN→vi, khác→en) + **security headers** (X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy). *(Chưa chặn route /app — xem "Còn lại".)*

**Render thật ĐÃ armed** — `.env` (gitignored) lấy 43 key từ affiliatebot: video=PiAPI/Seedance, ảnh=Gemini, giọng=Gemini TTS, `use_fake_clients=false`, **trần ngân sách** video $3/LLM $2/TTS $1 mỗi ngày.

**Admin** — tài khoản `admin@vyra.local` / `Admin@12345` → `is_admin=true` → vào `/app/admin` (đã chụp ảnh kiểm).

**Tài liệu** — `docs/operations/` (22 file vận hành) + `VISION.md` + `UI-REDESIGN-ROADMAP.md` + `UI-UPGRADE-BLUEPRINT.md`.

## 🔜 CÒN LẠI (theo thứ tự, có cái cần làm cẩn thận)

| Việc | Ghi chú | Rủi ro |
|---|---|---|
| Pivot copy Home + component marketing | LandingHero/UseCases còn "chốt đơn" → "tạo mọi loại video AI" | thấp (chỉ chữ) |
| QA mobile toàn bộ 24 màn | chụp 390px từng màn, sửa tràn cột | thấp |
| **Auth** cookie-session + middleware auth-guard | để middleware chặn /app; phải additive, **không khoá nhầm** | **cao** (động vào login) |
| Features: test render THẬT end-to-end | ≤1 job nhỏ/loại để verify, tiết kiệm | trung (tốn tiền API) |
| Database | verify migration M2 + seed plans/credit_packs (DEV) | trung |
| Payments | scaffold MoMo/Stripe chế độ TEST + UI đa cổng | trung |
| Bảo mật | chạy `/cso` (OWASP+STRIDE) + vá P0 | thấp (audit) |

> Các việc **rủi ro cao (auth, payments-live)** tôi sẽ làm **có verify từng bước** (test login không khoá nhầm; không đụng ledger tiền), hoặc khi bạn online để xác nhận.

## ⚠️ CẦN BẠN CẤP (tôi KHÔNG tự làm thay được)

1. **Xác nhận key render còn hạn/quota** — key lấy từ affiliatebot, cần bạn chắc còn dùng được + có ngân sách (PiAPI/Gemini/Vbee tính tiền thật khi render).
2. **Nạp tiền THẬT:** mã merchant **MoMo** + tài khoản **Stripe/Visa** (cho quốc tế). Có rồi tôi cắm vào là chạy; chưa có thì chạy chế độ test.
3. **Deploy production:** tài khoản **Railway/Vercel** + **Neon (Postgres)** + **Upstash (Redis)** + **Cloudflare R2**. Xem `docs/operations/02-infrastructure.md` + `17-deployment-cicd.md`.
4. **ToS gói Vbee/PiAPI/fal** — xác nhận gói thương mại cho phép phục vụ end-user (mô hình bán lại credit).

## Cách theo dõi
- `/workflows` — xem các workflow đã/đang chạy.
- Todo list trong phiên chat.
- `git status` — file đã đổi.
- App đang chạy: backend `:8099` + frontend `:3000`.
