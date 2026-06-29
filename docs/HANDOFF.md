# VYRA — TÀI LIỆU BÀN GIAO (Handoff) · cập nhật 2026-06-28

> Tài liệu ngữ cảnh ĐẦY ĐỦ cho người/agent tiếp nhận. Đọc hết trước khi làm tiếp.
> Mọi câu trả lời với chủ dự án: **TIẾNG VIỆT**. Mọi tính năng "xong" phải **verify bằng vận hành thật** (không tin pytest/mock xanh).

> 🔀 **PIVOT (chốt 2026-06-28):** Vyra mở rộng từ "clone autovis chốt đơn" → **nền tảng tạo MỌI loại video bằng AI** (studio sáng tạo: quảng cáo/affiliate, video trend, **phim ngắn AI nguyên gốc**, KOL, kể chuyện). Affiliate giờ là 1 thể loại flagship. **Định vị + thư mục thể loại + roadmap đầy đủ ở [VISION.md](VISION.md) (file đó thắng khi mâu thuẫn).** Việc đang làm: nâng cấp toàn bộ UI/UX mọi màn vượt đối thủ + chuyển IA sang đa-thể-loại.

---

## 1. DỰ ÁN NÀY LÀ GÌ

**Vyra** (tên cũ: VietVid) — SaaS **đa-tenant** (multi-tenant) **tạo MỌI loại video bằng AI, giọng Việt thật** (creative AI video studio). Người dùng vào web → **chọn thể loại** → đưa input (ý tưởng/ảnh/link/kịch bản) → Vyra dựng video hoàn chỉnh (hình + giọng Việt + nhạc + phụ đề) → tải/chia sẻ.
Thể loại: quảng cáo/affiliate (1 ảnh SP → video chốt đơn), video trend, **phim ngắn AI nguyên gốc**, KOL bán hàng, kể chuyện/giải thích. → chi tiết & trạng thái từng thể loại: [VISION.md §3](VISION.md).

- **Định vị (sau pivot):** **studio video AI Việt-first** vượt autovis.ai, Arcads, KlingAI, CapCut, Pika/Runway. Phải cao cấp, KHÔNG nhìn "AI generic". (Trước pivot chỉ là clone autovis cho mảng quảng cáo.)
- **Lợi thế cạnh tranh (wedge):** (A) **giọng Việt thật** (clone VieNeu, hơn TTS generic của autovis) + (D) **giá minh bạch** — hiện số credit TRƯỚC khi tiêu, **hoàn 100% khi lỗi hệ thống**, gói trả phí không watermark. KHÔNG đua giá đáy.
- **2 sản phẩm trên MỘT engine stateless:** **B** = nền tảng web/mobile self-serve (B2C); **C** = bán engine làm **API/white-label** (B2B).
- **Thư mục gốc:** `c:\Users\NTD\Desktop\vietvid` · branch hiện tại `master` (base là `main`).

### Stack kỹ thuật
| Lớp | Công nghệ | Thư mục |
|---|---|---|
| Backend HTTP | FastAPI + SQLAlchemy 2.0 + Pydantic | `app_api/` |
| DB | Postgres + **RLS FORCE** (fail-closed GUC `vietvid.current_org`) + Alembic (migrations → 0011) | `app_api/models.py`, `alembic/` |
| Video engine | **stateless** `render(spec, sink)` — TTS, ffmpeg, image/video providers | `video_engine/` |
| Frontend | **Next.js 14 App Router** + Tailwind + framer-motion + TanStack Query + Zustand | `apps/web/` |

### Đa-tenant (RLS) — bất biến nền
- Bảng tenant bật `ENABLE + FORCE ROW LEVEL SECURITY` + policy `org_isolation` = `org_id = nullif(current_setting('vietvid.current_org', true),'')::uuid` → **fail-closed**: chưa set GUC = 0 dòng.
- Truy cập bảng tenant qua `app_api.db.tenant_session(org_id)` = transaction NGẮN, set `SET LOCAL vietvid.current_org` ngay đầu (an toàn PgBouncer transaction-mode).
- ⚠️ **FORCE RLS áp cả owner** → MỌI truy cập bảng tenant phải qua `tenant_session`. Cron toàn-org (`audit_all`) cần role **BYPASSRLS** ở prod.
- Bảng GLOBAL (đọc pre-auth, không RLS): allowlist trong `models.py` (`memberships, org_invitations, vv_affiliate_links, vv_link_clicks, audit_log, vv_api_keys`). `orgs` là bảng gốc, đọc được trong `session_scope`.
- Mọi query vẫn lọc `org_id` tường minh (RLS là lưới an toàn, WHERE là index path).

---

## 2. NGƯỜI DÙNG MUỐN GÌ (chủ dự án)

- **Cao cấp, "xịn xò đỉnh đỉnh", vượt đối thủ** — bấm vào màn nào cũng phải "chất", không đơn sơ, không "y chang nhau".
- **Thật, không lộ AI:** KOL như người thật; **CẤM bịa số liệu** ("5.000+ creator", "triệu view" — Vyra mới ra mắt). Chỉ nêu năng lực thật.
- **Tiếng Việt toàn bộ** UI + 7 giọng Việt thật.
- **Quyết định sản phẩm ĐÃ CHỐT** (đừng re-litigate — memory `vietvid-product-decisions`):
  - Subscription + credits. Giá **~150đ/credit** + thưởng nạp gói lớn; free credit reset hàng tháng.
  - Thanh toán: **MoMo-first** + **bank VietQR + SePay** (đã build) + VNPay; **USDT đang bảo trì** (chốt với user).
  - KOL **cả AI lẫn mặt thật**. **Không auto-post** (M1).
  - Engine video user CHỌN được (Seedance/Veo/Kling/Hailuo) qua PiAPI + fal.ai. KHÔNG Sora 2.
- **Phản hồi gần nhất (CHƯA làm — ưu tiên cao, xem §9.A):**
  1. KOL ở **login + thư viện casting** vẫn "hơi giống AI quá" → cần **chân thực nhất**.
  2. **Hover phải ZOOM/phóng to** thẻ (hiện mới chỉ play video).
  3. Video hover bị **móp + mờ, không nét** → **nâng model lên Kling hoặc Gemini Veo**.
  4. "UI/UX vẫn như cũ, chỉ nâng mỗi hover" → muốn **nâng UI/UX sâu hơn nữa**.

---

## 3. TIẾN ĐỘ HIỆN TẠI (tổng quan)

- ✅ **Lõi đã xong + verify thật:** engine stateless tách-DB · ví ACID (không-trừ-oan) · vòng tiền hold→render→settle/refund · RLS đa-tenant · HTTP layer M1 · auth JWT.
- ✅ **UI/UX premium (session này):** billing/QR · 7 màn quản lý có bản sắc riêng · màn tạo video studio · 7 feature page khác biệt · casting studio KOL · hover-video live-portrait.
- ✅ **Thanh toán bank:** VietQR + SePay auto-reconcile **e2e thật**.
- ⚙️ **Đang mock (thiếu key):** render video/ảnh trong app (thiếu GEMINI/PIAPI). Ảnh marketing trên web do mình generate sẵn bằng fal.ai.
- 🔜 **Chưa làm:** queue mode prod (Arq+Redis), R2 storage + GC video, mặt KOL chân thực hơn, hover zoom, i2v nét hơn, nâng nốt tool screens.

---

## 4. NHỮNG GÌ ĐÃ LÀM (theo commit, mới → cũ)

**Session gần nhất — UI/UX premium + ảnh AI:**
| Commit | Nội dung |
|---|---|
| `4066356` | hover mặt KOL → chạy video live-portrait (component `HoverVideo`) |
| `da6b334` | 16 clip i2v (LTX-Video + ffmpeg nén, 870KB tổng) |
| `12b250b` | dựng lại `/app/kol` = **"phòng casting"** (hero điện ảnh + 2 thẻ chế độ + thư viện 12 mặt theo ngành + "Dùng mẫu" tạo persona) |
| `d21539e` | 12 mặt AI casting library (Flux ultra+raw); sửa 2 ảnh hở (genz, gym-nam) |
| `9aa1e96` | **feature pages khác biệt từng cái** (heroVariant kol/transform/tool + bộ section riêng + accent riêng) |
| `fcde904` | tách `lib/accents.ts` (palette accent dùng chung, dùng được ở server component) |
| `5b9e909` | màn tạo video: **chọn KOL bằng gương mặt** + mặt KOL trên khung preview |
| `c42e445` | **7 màn quản lý có bản sắc riêng** (ScreenHero + accent: reports/affiliate/team/templates/brand-kits/api/settings) |
| `032610f` | regenerate mặt KOL tự nhiên (Flux ultra+raw — hết "AI bóng nhựa") |
| `ab9edef` | cắm mặt AI + ảnh điện ảnh vào home/KOL/login |
| `b75df6a` | assets: mặt KOL + khung theme + nền cinematic |
| `d54a4cd` | log giao dịch SePay không khớp |
| `e8dcaba` | **QR scan-to-pay + lưới phương thức nạp (autovis-style)** |
| `8c3b054` | **VietQR bank + tự đối soát SePay + nạp số tiền tuỳ ý** (backend) |
| `793564e` | redesign **Ví & Sổ cái** premium (trust proof HOLD→SETTLE→REFUND, value gói trung thực) |

**Trước đó:** dashboard/library/tools premium, 7 màn iconned header, fix nav 2 dòng, QA 18 màn, login polish, FAQ/pricing, intro/logo Vyra, homepage "Winner Loop Reel".

**Lõi engine/ví (giai đoạn M0/M1, đã verify thật):**
- **M0** engine stateless `render(spec, sink)` — chạy trọn stage DIRECTING zero-DB; audit đối kháng 4-agent 0 critical.
- **M1 nền** DB + ví ACID + RLS + Alembic — 15/15 PASS (concurrent over-draw bị chặn, RLS isolation fail-closed, immutable ledger trigger, settle clamp, refund idempotent).
- **M1 tim** jobs orchestration + QueueSink + worker — 10/10 PASS (render lỗi-hệ-thống → REFUND tự động, balance khôi phục).
- **M1 HTTP** FastAPI + auth (45/45 real-op verified — memory `m1-http-layer-done`).

### Trạng thái verify
- Mọi commit UI: `tsc --noEmit` sạch + **live QA Playwright 0 lỗi console**.
- Backend QR + SePay: **e2e thật** (nạp +2000, replay không cộng đôi, sai số tiền không cộng, token sai 401, custom amount đúng). Security review sạch các tính chất tiền-bạc.
- Ví/credit ledger: HOLD/SETTLE/REFUND ACID, idempotent (FOR UPDATE), reaper hoàn job treo.

---

## 5. KIẾN TRÚC NGHIỆP VỤ (phải hiểu trước khi code tiếp)

```
web (Next.js) / mobile (Flutter sau) / public API (Product C)
        │  Bearer JWT
        ▼
app_api (FastAPI đa-tenant): auth · tenancy · wallet(ACID) · billing · jobs
        │  POST /jobs → validate → HOLD credit → enqueue
        ▼
engine worker: render(spec, sink) — STATELESS, KHÔNG chạm DB
        │  RenderResult(path, cost_usd, fault_class)
        ▼  upload S3/R2 → complete_job: SETTLE/REFUND ví + ghi video/job_events
Postgres (ACID + RLS) · S3/R2 (media) · VieNeu GPU (giọng, qua tunnel)
```

### Nghiệp vụ ví (đã code+verify ở `app_api/wallet.py`)
- Quy đổi DUY NHẤT: `credits(usd) = ceil(usd × USD_TO_VND / CREDIT_PRICE_VND)` (`pricing.py`), snapshot rate vào mỗi ledger row.
- **HOLD** (tạo job): `SELECT … FOR UPDATE` khoá wallet → pre-check → `balance -= hold; held += hold` + ledger `HOLD(-hold)`. `hold = ceil(est_credits × 1.5)`.
- **SETTLE** (render xong): `final = min(usd_to_credits(actual), hold)` (không quá báo giá) → hoàn phần thừa (delta dương); `held -= hold`.
- **REFUND** (lỗi hệ thống): hoàn 100% hold. Mỗi job: HOLD rồi ĐÚNG MỘT trong {SETTLE, REFUND}, **idempotent**.
- `CHECK(balance≥0)` = lưới chặn cuối ở DB; `ledger_entries` **append-only** (trigger chặn UPDATE/DELETE); audit cron `cache == SUM(ledger)`.
- Map RenderResult→ví (`jobs.py:complete_job`): READY/QA_FAIL→settle actual; FAILED+system→refund 100%; FAILED+input→settle actual; WAITING_CONFIG→giữ hold.

### Flow thanh toán → tạo video (prod nhiều người) — đã tư vấn chủ
- **Tách đôi:** (A) tiền vào — **IPN webhook idempotent** (KHÔNG tin redirect trình duyệt); (B) credit→video — `POST /jobs` HOLD credit → enqueue → trả `job_id` ngay; worker render → SETTLE/REFUND.
- **Hiện tại:** render **inline** (`JOB_EXECUTION_MODE="inline"`, BackgroundTasks) — KHÔNG scale. **Cần bật `queue` (Arq + Redis + worker fleet)** cho prod — hợp đồng `POST /jobs` không đổi. File: `executor.py`, `worker.py`, `config.py`.

### Lưu trữ video (KHÔNG cần ổ cứng to)
- Render → upload **chỉ final.mp4** lên **object storage** → xoá workdir. File: `storage.py`.
- **Khuyến nghị Cloudflare R2** (egress 0đ — user tải lại nhiều). Set `VIETVID_S3_*`. 100k video ≈ ~200GB ≈ ~$3/tháng.
- "Tải lại được": DB (`videos`) giữ object key; endpoint cấp **signed URL**.
- **Cần nối:** GC tự xoá video quá hạn theo `videos.expires_at` (reaper hiện chỉ quét workdir + job treo).

---

## 6. CÁCH CHẠY / SETUP (lệnh thật — đã verify)

**KHÔNG có file `.env`.** Config đọc thẳng `os.environ` với default. Secrets ở file **gitignored** (KHÔNG in nội dung ra log):
- `_vietvid_db_url.txt` — connection string Postgres (user `affiliate`, localhost:5432).
- `_fal_key.txt` — khoá fal.ai (tạo ảnh + image-to-video). Đang có.

### Backend (port 8099)
```bash
cd /c/Users/NTD/Desktop/vietvid
export VIETVID_DATABASE_URL="$(cat _vietvid_db_url.txt)"
# (test luồng QR bank, set thêm:)
export VIETVID_BANK_BIN=970436 VIETVID_BANK_ACCOUNT=9988776655 \
       VIETVID_BANK_ACCOUNT_NAME="CONG TY VYRA" VIETVID_BANK_NAME="Vietcombank" \
       VIETVID_SEPAY_TOKEN="sepay_test_token_123"
/c/Python314/python -m uvicorn app_api.main:app --host 127.0.0.1 --port 8099 --log-level warning
```
> ⚠️ Restart backend PHẢI kèm `VIETVID_DATABASE_URL`, nếu không lỗi `password authentication failed for user "vietvid"` (default URL sai pass).

### Migration
```bash
PYTHONUTF8=1 /c/Python314/python -m alembic upgrade head   # alembic KHÔNG trên PATH → python -m alembic
```

### Frontend (port 3000)
```bash
cd /c/Users/NTD/Desktop/vietvid/apps/web && bun run dev
```
> ⚠️ **TUYỆT ĐỐI không `next build` khi `next dev` đang chạy** → hỏng `.next`, CSS 404, trang trắng. Verify bằng `tsc --noEmit`. Nếu trắng: kill dev → `rm -rf .next` → chạy lại.

### QA thật (Playwright — bắt buộc trước khi tin "chạy được")
- Harness ở `apps/web/node_modules/playwright`. Import tuyệt đối:
  `import { chromium } from "file:///c:/Users/NTD/Desktop/vietvid/apps/web/node_modules/playwright/index.mjs";`
- **Đăng nhập dev:** `POST http://127.0.0.1:8099/v1/dev/token` body `{}` (KHÔNG truyền email → backend tự sinh unique, tránh 409) → lấy `access_token` → `POST /v1/tenants/bootstrap` (tạo org + 300 credit) → `localStorage.vietvid_dev_token = token` → rồi mới goto.
- Reveal-on-scroll KHÔNG trigger trong screenshot tĩnh → phải scroll trước khi chụp.
- Viết QA vào file `.mjs` (unicode tiếng Việt an toàn) thay vì `node -e` inline. Mẫu: scratchpad `qa-hover.mjs`.

### Tạo ảnh / video qua fal
- `scripts/gen_*.py` đọc `_fal_key.txt`. Chạy: `PYTHONUTF8=1 /c/Python314/python -m scripts.<tên>`.
- Models đã dùng: **Flux 1.1 Pro ultra + raw** (mặt người thật, `aspect_ratio:"3:4"`, `raw:true`), **LTX-Video** (i2v hover, rẻ ~$0.04, queue API).
- i2v queue API: POST `https://queue.fal.run/<model>/image-to-video` (image_url nhận **data URI base64**, không cần upload) → poll `…/requests/<id>/status` → tải `video.url` → **ffmpeg nén** `scale=400:-2 -crf 30 -an` (7MB → ~50KB). ffmpeg CÓ trên máy.

---

## 7. ENV / KEYS — TRẠNG THÁI

| Key | Trạng thái | Dùng cho |
|---|---|---|
| `_fal_key.txt` (fal.ai) | ✅ có | Tạo ảnh (Flux) + video hover (LTX). **Tốt nhất cho ảnh.** |
| `_vietvid_db_url.txt` | ✅ có | Kết nối Postgres |
| `GEMINI_API_KEY` | ❌ thiếu | Render ảnh + video THẬT + kịch bản (đang mock) |
| `GROQ_API_KEY` | ❌ thiếu | Kịch bản AI sắc hơn (đang template) |
| `PIAPI_API_KEY` | ❌ thiếu | Video Seedance (đang mock) |
| `VIETVID_BANK_*` + `VIETVID_SEPAY_TOKEN` | ⚙️ chỉ test | Bật QR bank + tự cộng tiền thật khi deploy |

→ **Render video/ảnh trong app đang MOCK.** Lấy key từ `affiliatebot/.env` nếu cần render thật. Deploy MVP "Cách 2": engine worker cloud + VieNeu chạy desktop 3060 ở nhà qua Cloudflare Tunnel + token.

---

## 8. QUY TẮC LÀM VIỆC (bắt buộc tuân thủ)

Nguồn: `CLAUDE.md` + `.claude/CLAUDE.md` + skill `real-qa` + nếp session.

1. **Trung thực tuyệt đối — KHÔNG fake.** Không bịa số liệu/option/seal. Option chỉ hiện khi backend xử lý thật (vd KHÔNG thêm "format/nhạc" vì `app_api` không honor; `bank_qr`/`usdt` thì honor). "Đang bảo trì" (USDT) là cách trung thực thay vì giả nút.
2. **real-qa — chỉ tin hành vi thật.** CẤM lấy pytest/tsc xanh làm bằng chứng "chạy được" (có `USE_FAKE_CLIENTS`/`useMock` → xanh vẫn có thể là data giả). Phải: live Playwright (mắt thấy ảnh) + DB/log/HTTP thật. Mỗi kết luận kèm bằng chứng (`file:dòng`/ảnh/DB row). Kiểm chéo báo cáo agent với env+DB thật.
3. **Quy trình task lớn:** scout (đọc code thật, ưu tiên codegraph) → design (Workflow panel: nhiều concept → judge/synthesis) → build → **adversarial review** (verify từng phát hiện, default refuted nếu không chắc) → `tsc` + live QA → commit. Ultracode BẬT → ưu tiên Workflow cho task lớn (output văn bản tự do nếu schema lỗi retry).
4. **Commit bisect:** mỗi commit 1 thay đổi logic; tách asset/refactor/feature. `git add` từng path tường minh — **CẤM `git add .` / `-A`** (binaries + secret + `_m0_out/`). Kết commit:
   `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`. **Chỉ commit khi user bảo** (hoặc đã được phép rõ).
5. **Surgical:** chỉ sửa cái cần; không "cải thiện" code lân cận; match style hiện có. Dọn orphan do MÌNH tạo.
6. **Trả lời TIẾNG VIỆT** (memory `user-prefers-vietnamese`).
7. **Background task:** poll tới khi xong, đừng bỏ cuộc.
8. **CHANGELOG/VERSION:** branch-scoped; viết cho user (release notes), không kể nội bộ. (Chưa bump session này.)

---

## 9. QUY TẮC LÀM UI/UX (design system)

> Nguồn: skill `design-taste-frontend` + `redesign-existing-projects` + design system của repo. **Anti-slop** là cốt lõi.

### 9.0 Design dials (mặc định dự án)
- `DESIGN_VARIANCE 7-8` · `MOTION_INTENSITY 6-7` · `VISUAL_DENSITY 4` — premium consumer/landing. Đọc brief trước, khai báo "Design Read" 1 dòng trước khi build.

### 9.1 Token & font (KHÔNG tự chế token mới)
- **Nền tối** `#06070d` (bg-base) · surface `#0B0D16` · surface2 `#12141F` · elevated `#1A1C2A`.
- **Brand gradient** violet→indigo→blue (`#7C4DFF → #6366F1 → #3B82F6`). `bg-grad-brand`, `bg-grad-brand-soft`.
- **Font:** `font-display` = **Be Vietnam Pro** (DUY NHẤT cho tiêu đề — có dấu tiếng Việt) · body = Inter · `font-numeric` = **Space Grotesk** (**CHỈ cho SỐ** — không dấu, **KHÔNG BAO GIỜ bọc chữ tiếng Việt** = lỗi cốt tử).
- **Màu chữ:** ink-high/medium/low/disabled. Semantic: success(xanh)/danger(đỏ)/hold(amber)/refund(cyan).
- **Utilities:** `.glass`, `.glass-bordered`, `.text-gradient`, `.glow-radial`, `.mesh-bg` (1 halo tím, KHÔNG cầu vồng), `shadow-glow-sm/md`.

### 9.2 Hệ thống nhận-diện-màn-hình (đã build)
- `apps/web/src/lib/accents.ts` — 7 accent (violet/emerald/amber/sky/rose/cyan/slate), mỗi accent có `{tile,icon,glow,ring,line,chip,text,grad,bar}` (string tĩnh để Tailwind purge giữ).
- `apps/web/src/components/app/screen-hero.tsx` — `ScreenHero` (hero icon-tile accent + tiêu đề + stat slot) + `StatTile`. **Mỗi màn 1 accent riêng** để nhìn lướt phân biệt, vẫn chung brand.
- Feature page: `feature-showcase.tsx` (dispatcher) + `marketing/feature/` (hero 3 biến thể **kol/transform/tool** + 7 section: highlights/beforeAfter/results/useCases/voiceBar/comparison/proof). Config ở `lib/feature-pages.ts`.

### 9.3 Anti-slop (CẤM — đây là "nét AI" cần tránh)
- ❌ Hàng **4 thẻ y hệt** làm feature row trang trí. ❌ Nút play tròn rải khắp. ❌ Glass-on-everything (1 màn ~1 surface bordered). ❌ Nhiều glow (1 glow/màn). ❌ **Số liệu bịa.** ❌ Gradient tím AI vô tội vạ (violet phải có chủ đích: selection/value).
- ❌ Mọi thứ căn giữa đối xứng (VARIANCE>4 → split/asymmetric). ❌ `h-screen` cho hero (dùng `min-h-[100dvh]`). ❌ Flex %-math (dùng CSS Grid). ❌ Lucide tràn lan không chủ đích.
- ✅ Mobile responsive (test 375/390px, không tràn ngang). ✅ Reveal-on-scroll (`marketing/reveal.tsx`, whileInView once). ✅ a11y (aria-label nút icon, aria-pressed chip, aria-expanded disclosure, role progressbar, focus-visible ring). ✅ Đủ trạng thái: loading skeleton + empty + error inline (không `alert()`). ✅ Tactile `:active` scale-[0.98].

### 9.4 Component mẫu tái dùng
- `HoverVideo` (`ui/hover-video.tsx`) — ảnh tĩnh → hover play clip (preload=none, cross-fade). Dùng ở casting studio, kol-picker, FeaturedKol. **(Cần thêm: zoom on hover.)**
- `MiniReel` (`marketing/mini-reel.tsx`) — Ken-Burns + caption gõ chữ, có `video?` prop.
- Billing: `PackCard, WalletHero, TrustProof, LedgerStatement, MethodGrid, QrPayPanel, CustomAmount`.
- Create: `KolPicker, TemplateGallery, AdvancedDisclosure, MobileCostBar`.

---

## 10. VIỆC CẦN LÀM TIẾP (ưu tiên cao → thấp)

> Roadmap đầy đủ theo Sóng (UI → Multi-genre engine → Activation → Growth) ở [VISION.md §8](VISION.md). Mục dưới là việc cụ thể của **Sóng UI (đang làm)**.

### A. SÓNG UI — nâng cấp TOÀN BỘ màn vượt đối thủ + chuyển IA đa-thể-loại (ĐANG LÀM)
0. **Nâng cấp toàn bộ UI/UX mọi màn** theo `docs/UI-UPGRADE-BLUEPRINT.md` (sinh từ audit toàn bộ màn): design primitives dùng chung (motion/depth/micro-interaction/states) → Home (bán "tạo mọi video AI") → Create (**chọn thể loại trước**) → Dashboard → còn lại. Verify từng màn: `tsc --noEmit` + live QA screenshot.
1. **Mặt KOL chân thực hơn** — mặt ở login showcase + casting library vẫn "hơi AI". Hướng: prompt mạnh tay hơn (đời thường, khuyết điểm da, không model, ánh sáng tự nhiên), hoặc đổi model. Ưu tiên mặt LỘ nhiều: login (lookbook/kol_review/food_review) + library (Phong, v.v.).
2. **Hover ZOOM** — thẻ phải phóng to khi hover (thêm `group-hover:scale-[1.03]` + `transition-transform duration-300` vào `HoverVideo`/thẻ chứa), không chỉ play video.
3. **Nâng model i2v cho nét hơn** — LTX bị móp/mờ. Đổi sang **Kling** (`fal-ai/kling-video/v1.6/standard/image-to-video`, ~$0.25/clip, nét hơn nhiều) hoặc **Gemini Veo** (cần GEMINI key). Giữ pattern queue + nén ffmpeg (`scripts/gen_kol_videos.py`); cân nhắc giữ res cao hơn (scale 512-600px) cho nét.
4. **UI/UX sâu hơn** — không chỉ hover. Còn: 3 màn công cụ (`/app/image-gen`, `/app/audio`, `/app/compose`) + dashboard chưa lên chuẩn accent/ScreenHero. Thêm motion cao cấp: spotlight theo con trỏ, parallax, chuyển cảnh mượt (spring physics).

### B. Kỹ thuật / prod (đã tư vấn chủ)
5. Bật **queue mode** (Arq + Redis + worker fleet) — `JOB_EXECUTION_MODE=queue`; `pip install arq`.
6. Cấu hình **R2** (`VIETVID_S3_*`) + nối **GC xoá video quá hạn** theo `videos.expires_at`.
7. Điền **GEMINI/GROQ/PIAPI key** → render video/ảnh + kịch bản THẬT (đang mock).
8. Deploy: set `VIETVID_BANK_*` + `VIETVID_SEPAY_TOKEN` thật → QR bank tự cộng tiền.

### C. Lộ trình xa (M2-M5)
- **M2 B-core:** KOL Studio (persona từ 1 ảnh + consent) + engine-chọn-được UI + Momo + productionize VieNeu (health-check + fallback Vbee CÓ ĐỒNG Ý, không tụt edge-tts âm thầm).
- **M3 B-full:** template/trend VN + lịch/auto-post TikTok + moderation + admin.
- **M4 Mobile:** Flutter. **M5 Product C:** public API + api_keys + quota + white-label.

---

## 11. FILE / THƯ MỤC QUAN TRỌNG

```
app_api/
  main.py routers/          # FastAPI HTTP + auth JWT
  routers/billing.py        # topup (dev/vnpay/momo/bank_qr) + /ipn/sepay + /payment/{id} + dev-confirm
  billing.py                # VietQR, create_payment, apply_topup (idempotent), resolve_bank_payment_org
  routers/content.py        # create_kol (source ai → APPROVED), list_kol
  wallet.py jobs.py worker.py executor.py sink_queue.py storage.py reaper.py
  pricing.py models.py config.py db.py deps.py
  alembic/versions/         # migrations → 0011
video_engine/
  spec.py sink.py render_service.py runner_cli.py   # stateless render(spec, sink)
  pipeline.py               # bản GỐC stateful — KHÔNG dùng trong vyra, chỉ tái dùng helper thuần
apps/web/src/
  lib/accents.ts feature-pages.ts kol-faces.ts      # config dùng chung
  components/app/screen-hero.tsx                     # ScreenHero + StatTile
  components/ui/hover-video.tsx                       # hover → video
  components/marketing/feature/*.tsx feature-showcase.tsx
  components/billing/*.tsx components/create/*.tsx
  app/app/{kol,reports,affiliate,team,templates,brand-kits,api,settings,billing,create}/page.tsx
  public/kol/*.jpg + *.mp4          # mặt KOL persona + hover clip
  public/kol/lib/*.jpg + *.mp4      # 12 mặt casting library + hover clip
  public/samples/*.{png,mp4}        # khung nội dung mẫu
  public/bg/*.jpg                   # nền cinematic (studio/desk/ring/city)
scripts/gen_landing_images.py gen_kol_v2.py gen_kol_library.py gen_web_backgrounds.py gen_kol_videos.py
docs/designs/SYSTEM_DESIGN.md       # build-spec M2+ (kiến trúc chi tiết)
```

`.gitignore` quan trọng: `*.mp4` bị ignore TOÀN CỤC, đã EXCEPT `apps/web/public/samples/*.mp4` + `apps/web/public/kol/*.mp4` + `apps/web/public/kol/lib/*.mp4`. Secret: `_vietvid_db_url.txt`, `_fal_key.txt`, `_*_key.txt`, `_m0_out/`.

---

## 12. GOTCHAS (đã gặp — đừng vấp lại)
- Windows console **cp1258** vỡ tiếng Việt khi `print` → luôn `PYTHONUTF8=1`.
- `alembic`/`uvicorn` không trên PATH → `/c/Python314/python -m alembic` / `-m uvicorn`.
- Restart backend thiếu `VIETVID_DATABASE_URL` → lỗi auth `vietvid` (default URL sai).
- **FORCE RLS áp cả owner** → mọi truy cập bảng tenant cần `tenant_session`; cron toàn-org cần BYPASSRLS.
- `next build` khi `next dev` đang chạy → hỏng `.next`, trang trắng.
- Vietnamese trong `node -e` inline → SyntaxError → viết QA ra file `.mjs`.
- `font-numeric` (Space Grotesk) bọc chữ Việt → mất dấu. CHỈ dùng cho số.
- Ảnh người AI phải **tasteful, mặc đủ đồ, hợp môi trường công sở** (đã từng sinh ảnh hở phải làm lại).
- `git add` từng path — CẤM `git add .` (binaries tracked + secret).

---

## 13. MEMORY / DECISIONS (ngữ cảnh bền)
- Memory dir: `C:\Users\NTD\.claude\projects\c--Users-NTD-Desktop-vietvid\memory\` (index `MEMORY.md`).
  - `user-prefers-vietnamese` · `vietvid-product-decisions` · `vietvid-build-roadmap` · `m1-http-layer-done` · `free-grant-min-hold` · `activation-boundary`.
- Decisions store: `~/.gstack/projects/<slug>/decisions.jsonl` (event-sourced; `bin/gstack-decision-search`/`-log`).
- Plan A-Z gốc (đã duyệt): `C:\Users\NTD\.claude\plans\glimmering-leaping-sutton.md`.

---
**TÓM TẮT 1 DÒNG:** Vyra = SaaS video AI giọng Việt đa-tenant (lõi engine+ví+RLS+HTTP đã verify thật), đang **nâng UI/UX vượt autovis** (đã xong: billing/QR, 7 màn quản lý, create studio, 7 feature page, casting studio, hover-video). **Việc kế tiếp: mặt KOL chân thực hơn + hover zoom + i2v nét hơn (Kling/Veo) + nâng nốt tool screens; kỹ thuật: queue mode + R2 + GC + điền API keys render thật.**
