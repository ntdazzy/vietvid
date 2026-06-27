# VietVid — Kế hoạch thiết kế Web UI/UX (chi tiết)

> Dark Cinematic × Electric Violet→Blue · Landing maximalist (WebGL) + App nhanh/gọn · bám API M1 thật.
> Sinh từ workflow ideation 6-agent + tổng hợp. Phần 0 (tầm nhìn/nguyên tắc/lộ trình) ở đầu, chi tiết A–F bên dưới.

## Mục lục
- [Phần 0 — Tầm nhìn, nguyên tắc & lộ trình (TỔNG HỢP)](#phần-0--tầm-nhìn-nguyên-tắc--lộ-trình)
- [A. ĐỊNH HƯỚNG SÁNG TẠO & CHỐNG "AI-SLOP"](#a-nh-h-ng-s-ng-t-o-ch-ng-ai-slop)
- [B. DESIGN SYSTEM (token cụ thể)](#b-design-system-token-c-th)
- [C. KIẾN TRÚC MOTION & TECH](#c-ki-n-tr-c-motion-tech)
- [D. BẢN ĐỒ MÀN HÌNH](#d-b-n-m-n-h-nh)
- [E. CREATE WIZARD (lõi) + minh bạch giá + timeline render](#e-create-wizard-l-i-minh-b-ch-gi-timeline-render)
- [F. SIGNATURE MOMENTS (tương tác đáng nhớ)](#f-signature-moments-t-ng-t-c-ng-nh)


---

# PHẦN 0 — TẦM NHÌN, NGUYÊN TẮC & LỘ TRÌNH

> Phần này là **tổng hợp & quyết định chuẩn** do mình biên tập từ 6 chuyên gia (A–F bên dưới). Đọc Phần 0 để nắm toàn cảnh + chốt; đọc A–F để có chi tiết thi công.

## 0.1 Tầm nhìn & định vị (1 câu)

> **"Runway/Kling cho điện ảnh — nhưng VietVid cho bạn *nghe được giọng Việt thật*, *thấy trước từng credit*, và *trả bằng VietQR*."**

Web phải bán **2 wedge** ở mọi điểm chạm: **(1) giọng Việt thật** (proof-by-ear, không nói suông) và **(2) minh bạch giá** (ước tính → giữ → hoàn, "hoàn 100% nếu lỗi hệ thống"). Phong cách **Dark Cinematic** như Kling/Runway, nhưng **ấm & rõ ràng kiểu Việt**.

## 0.2 Bảy nguyên tắc thiết kế (north-star)

1. **Output LÀ anh hùng** — hero/landing dùng *video thật do engine VietVid tạo* làm nền, không ảnh stock/3D vô hồn. Sản phẩm tự chứng minh.
2. **Đen NHIỀU LỚP, không `#000` phẳng** — nền near-black ám tím-lạnh + radial glow lệch tâm + film-grain. Gradient accent chỉ cho *glow/active/viền*, **không phủ nền** (đó là AI-slop).
3. **Glow phát ra TỪ nội dung** — không dùng `shadow-lg` đen mặc định; phần tử quan trọng tự phát quang cùng màu accent.
4. **Mỗi màn chỉ 1 "anh hùng thị giác"** — 1 video / 1 glow / 1 motion lớn. Phần còn lại tĩnh–rõ–nhanh. (Slop sinh ra khi mọi thứ cùng gây chú ý.)
5. **Density có nhịp** — xen section thở rộng với block dày đặc & full-bleed showcase; không `py-20` đều tăm tắp.
6. **Motion phục vụ wedge, không trang trí** — mọi animation lớn phản chiếu *giọng* hoặc *minh bạch giá*. Landing maximalist (WebGL), **App nhanh/gọn**.
7. **Minh bạch là THẬT** — mọi con số credit kéo từ API thật (`estimate`, `wallet/ledger`, `bootstrap`), không phải animation giả. Số liệu kỹ thuật dùng **mono `tabular-nums`**.

## 0.3 Quyết định CHUẨN (canonical — chốt để dựng design system)

6 agent đề xuất hơi lệch nhau vài hex/font; dưới đây là bản **đã hợp nhất, dùng làm chuẩn duy nhất**:

- **Nền (dark-only, KHÔNG light mode):** `--bg-base #06070D` → `--surface-1 #0B0D16` → `--surface-2 #12141F` → `--elevated #1A1C2A`. Glow đỉnh violet + vignette + grain 3–5%.
- **Accent gradient (brand):** **`#7C4DFF` (violet-500) → `#6366F1` (indigo) → `#3B82F6` (blue-500)**. Primary đơn sắc = `#7C4DFF`; nút default `#6A3CF0`. (Các mục dùng `#7C3AED/#2563EB` coi như cùng họ — quy về bộ này.)
- **Text trên nền tối:** `text-high #F4F5FA` · `text-medium #B4B7C7` · `text-low #7E8298` (đều ≥ WCAG AA). Viền `rgba(255,255,255,.06→.16)`.
- **Semantic & ledger:** success/READY `#34D399` · hold/amber `#FBBF24` · settle `#B4B7C7` (trung tính) · **refund `#22D3EE` cyan** (tách khỏi success để "hoàn" có bản sắc riêng) · danger `#F87171` · bonus `#7C4DFF`.
- **Font (đều phủ tiếng Việt chuẩn dấu, qua `next/font`):** Display = **Be Vietnam Pro** (700/800) · Body/UI = **Inter** (400/500/600) · Số credit/giá lớn = **Space Grotesk** (tabular) · Mã/ID/ledger = **Geist Mono**. *(Alt cho display marketing tiếng Anh: General Sans/Clash Display — tùy chọn.)*
- **Type scale:** display-2xl 72/-0.03em, display-xl 56, h1 34, h2 28, body 16, caption 13. Heading tracking **âm**, tương phản cỡ mạnh (display:body ~5×).
- **Glass chuẩn:** `bg-white/[0.04] backdrop-blur-xl border border-white/[0.08]` + viền-top gradient sáng + `inset 0 1px 0 rgba(255,255,255,.06)`. Bo `16px`.

## 0.4 Tech stack & thư viện

`Next.js 14 App Router + TypeScript` · `Tailwind + shadcn/ui` · `TanStack Query` (poll job 2.5s, backoff, dừng ở READY/QA_FAIL) · `Zustand` (wizard state, persist sessionStorage) · `Supabase Auth` (email+Google → Bearer JWT, API verify JWKS — **dual-mode đã sẵn ở backend**) · `Framer Motion` (layout/shared-element/`layoutId`) · `Lenis` (smooth-scroll) · `@react-three/fiber + drei` (hero shader, **chỉ landing**, dynamic import + fallback poster) · `Web Audio API` + canvas/`wavesurfer` (waveform giọng) · `lucide` icons · `next/font` · i18n `vi`. **Perf:** R3F lazy + `IntersectionObserver` pause; `prefers-reduced-motion` fallback khắp nơi; mobile tắt shader nặng → dùng video loop.

## 0.5 Tuyên ngôn chống "AI-slop" (6 quy tắc rút gọn — chi tiết ở mục A)

❌ KHÔNG: gradient tím→xanh phẳng phủ nền · blob tròn blur trôi nổi · icon generic "Fast/Secure/Easy" · hero 3D stock vô hồn · spacing đều `py-20` · copy sáo ("Powered by AI", "Unleash creativity") · `shadow-lg` đen · card trắng border xám · 1 font cho mọi cỡ · testimonial/logo giả.
✅ THAY BẰNG: video output thật · glow-từ-nội-dung + grain · mini-clip/số liệu thay icon · density có nhịp · copy cụ-thể-số-Việt ("1 ảnh → video chốt đơn 60s") · glow accent + viền sáng · 3-font pairing · social-proof thật (video khách + cơ chế hoàn tiền).

## 0.6 Bản đồ màn hình + ưu tiên (chi tiết ở mục D)

| Màn | Route | Mốc | Signature moment chính | Backend cần |
|---|---|---|---|---|
| Landing | `/` | **M1** | Voice A/B Duel · Product→Video morph (WebGL) | audio A/B *tĩnh pre-render* (đủ); demo video |
| Pricing/Top-up | `/pricing` | M1 UI / **M3 nạp** | bảng credit nói bằng "video" | **nạp tiền = item (3) billing chưa build** |
| Login/Signup | `/login` | **M1** | 300-credit reveal | Supabase + `/bootstrap` ✅ |
| Dashboard | `/app` | **M1** | Credit badge "đang giữ" · rail job live | `/me`,`/wallet`,`/jobs` ✅ |
| **Create Wizard** B1–B5 | `/app/create` | **M1** | Hold Meter · Render Timeline · Voice Try-on | `/estimate`,`/jobs`,`/jobs/{id}` ✅ · *VoicePreview cần endpoint TTS draft (chưa có)* · *engine-picker = M2* |
| Library | `/app/library` | **M1** | Hover scrub reel · shared-element transition | `/jobs`,`/jobs/{id}/video` ✅ |
| Video detail | `/app/v/{id}` | **M1** | player + "Tải MP4 không watermark" | ✅ |
| Wallet/Billing | `/app/billing` | **M1** | Living Ledger Receipt | `/wallet/ledger` ✅ |
| Settings | `/app/settings` | M1/M2 | API keys reveal-once (Product C) | brand-kit/keys = M2 |
| KOL Studio | `/app/kol` | **M2** | consent gate | backend M2 |
| Admin | `/admin` | M3 | duyệt/hoàn/job lỗi | backend M3 |

## 0.7 Chín "Signature Moment" (chi tiết ở mục F)

| Ưu tiên | Moment | Màn | Effort |
|---|---|---|---|
| **P0** | #1 Voice A/B Duel | Landing hero | med |
| **P0** | #2 Hold Meter (đồng hồ nhiên liệu credit) | Wizard B4 + global | med |
| **P0** | #3 Cinematic Render Timeline ("phòng dựng phim") | Wizard B5 | high |
| P1 | #6 Living Ledger Receipt | Billing | low-med |
| P1 | #4 Engine "lens rack" | Wizard B2 (M2) | med-high |
| P1 | #7 Voice "đọc thử câu của tôi" | Wizard B3 | med |
| P2 | #5 Product→Video morph (WebGL hero) | Landing | high |
| P2 | #8 300-credit reveal | post-signup | low |
| P2 | #9 Library hover-reel + shared transition | Library | med |

**Sợi chỉ xuyên suốt:** mọi màn dùng chung 1 ngôn ngữ "phim" (lens / frame / film-strip / grain / receipt) + shared-element `layoutId` giữa các trang → một thế giới liền mạch, không phải các trang rời rạc.

## 0.8 Lộ trình thi công web + phụ thuộc backend (QUAN TRỌNG — thành thật)

**Đã có backend (M1, verify thật) → dựng ngay được:** Landing, Auth+bootstrap, Dashboard, Wizard B1/B4/B5 (engine mặc định Seedance), Library, Video, Wallet/Billing(ledger), Settings(khung). 11 endpoint `/v1/*` đã chạy.

**CHƯA có backend → cần làm thêm trước khi nối thật (đừng hứa suông trên UI):**
- 🔴 **Top-up thanh toán** (VNPay/Momo/VietQR/USDT) = **item (3) billing** chưa build → Pricing dựng UI trước, nút "Nạp" để *coming-soon/sandbox* tới khi item 3 xong.
- 🟠 **Engine picker** (Veo/Kling/Hailuo) = **M2** (route đa-engine + bảng giá) → B2 dựng UI, tạm khóa về Seedance, mở khi M2.
- 🟠 **VoicePreview "đọc thử câu của tôi" + Voice A/B audio động** = cần **endpoint TTS draft/preview** (chưa có) → hero A/B dùng *audio pre-render tĩnh* (vẫn đủ wow); B3 try-on nối khi có endpoint.
- 🟡 **KOL Studio / templates / brand-kit / API keys** = M2.

**Phân đợt đề xuất (web):**
- **W0 — Scaffold:** Next14+TS, Tailwind+shadcn, design tokens (mục B), fonts, `lib/api` client typed theo 11 endpoint, Supabase auth, i18n vi, **app shell glass** (nav/sidebar, CreditBadge, ⌘K command palette).
- **W1 — Landing maximalist:** hero (video thật + R3F shader morph) + **Voice A/B Duel (P0)** + how-it-works + engine showcase + dải minh bạch giá + FAQ "lỗi có hoàn?" + footer; Pricing (UI).
- **W2 — App lõi:** Auth/bootstrap + **300-credit reveal** + Dashboard + **Wizard B1→B5** + **Hold Meter (P0)** + **Render Timeline (P0)**.
- **W3 — Quay lại nhiều:** Library (hover-reel + shared transition) + Video detail + **Billing Ledger Receipt** + Settings.
- **W4 — Polish/motion/perf:** page-transition toàn app, các moment P1/P2, reduced-motion, mobile, a11y (AA), perf budget (LCP/bundle).
- **M2 web:** Engine lens-rack, Voice try-on full, KOL Studio, templates.

> Khi bạn duyệt Phần 0, mình đề xuất bắt đầu **W0 (scaffold + design system + app shell)** rồi **W1 landing** để bạn "thấy chất" sớm nhất.

---

# A. ĐỊNH HƯỚNG SÁNG TẠO & CHỐNG "AI-SLOP"

Đủ dữ liệu. Dưới đây là tổng hợp đậm đặc, áp dụng được ngay cho VietVid.

---

# VietVid — "CHỮ KÝ" thị giác & chống AI-slop

## PHẦN 1 — 12 PATTERN khiến Kling/Runway/Luma/Sora/HeyGen trông CAO CẤP & ĐIỆN ẢNH → áp cho VietVid

| # | Pattern họ dùng | Cụ thể (cách làm) | Áp cho VietVid |
|---|---|---|---|
| **1. Output LÀ background, không phải minh hoạ** | Runway/Luma/Sora cho video output thật chạy full-bleed làm nền hero (muted, autoplay, loop), chữ đặt đè lên. Họ tin sản phẩm đủ đẹp để là nền. | Hero = `<video>` loop 6-10s ghép 3-4 clip thật do engine VietVid tạo, `object-fit:cover`, overlay gradient `linear-gradient(180deg, rgba(8,8,12,.2) 0%, rgba(8,8,12,.85) 100%)` để chữ đọc được. Poster frame load tức thì, video fade-in sau. R3F shader hero chỉ ở 1 lớp phía trên (particle/grain), KHÔNG thay thế video thật. | Có sẵn pipeline → render 5-6 demo "product ad" thật, lazy-load qua `IntersectionObserver`. |
| **2. Nền gần-đen NHIỀU LỚP, không phải `#000` phẳng** | Sora/Kling dùng đen ám màu + vignette + radial glow lệch tâm. Không bao giờ `#000000` thuần. | Base `#08080C` → `#0B0B12`; thêm 2 lớp radial: `radial-gradient(120% 80% at 50% 0%, rgba(124,58,237,.18), transparent 60%)` (violet glow đỉnh) + vignette `radial-gradient(at 50% 50%, transparent 40%, rgba(0,0,0,.6))`. Film-grain `<svg feTurbulence baseFrequency=0.9>` opacity 3-5%, `mix-blend-mode:overlay`. | Token: `--bg-0:#08080C --bg-1:#0B0B12 --bg-2:#12121C`. Glow accent violet→blue. |
| **3. Glow phát ra TỪ nội dung, không phải box-shadow generic** | Card/nút "tự phát sáng" bằng glow cùng màu accent, blur lớn, opacity thấp → cảm giác nội phát quang điện ảnh. | CTA chính: `box-shadow: 0 0 0 1px rgba(124,58,237,.5), 0 8px 40px -8px rgba(99,102,241,.55)`. Card video khi hover: lớp `::after` blur-40 màu accent. Tránh `box-shadow:0 4px 6px rgba(0,0,0,.1)` mặc định Tailwind. | Util `.glow-violet`, `.glow-blue`; chỉ glow phần tử quan trọng (1-2/màn). |
| **4. Hover-to-scrub / hover-to-play trên gallery** | Luma/Pika gallery: thumbnail tĩnh, **hover → video phát hoặc scrub theo vị trí chuột**. Cảm giác "sống", chứng minh là video thật. | Library grid + landing showcase: `onMouseEnter` → play muted; di chuột ngang → set `currentTime` theo `offsetX/width`. Mobile: autoplay clip ngắn 2s khi vào viewport. Badge engine góc dưới-trái (Veo/Kling/Seedance). | Mỗi card 2 lớp: poster `<img>` + `<video preload="none">`. |
| **5. Micro-typography điện ảnh: tracking ÂM trên heading lớn, cỡ tương phản mạnh** | Sora/Runway heading rất to (clamp 48-96px), `letter-spacing:-0.03em`, `line-height:0.95-1.05`, font geometric. Body nhỏ, xám, tracking dương nhẹ. Tỉ lệ tương phản display:body ~ 5-7×. | Display: **Clash Display** hoặc **General Sans** (Fontshare, free) HOẶC **Geist** — `clamp(2.75rem,6vw,6rem)`, `tracking-[-0.03em]`, `leading-[0.98]`. Body: **Inter** / **Geist Sans** 15-16px, `text-white/60`, `tracking-[0.01em]`. Tiếng Việt: bắt buộc test dấu (Inter/Geist/Be Vietnam Pro phủ tốt). | Eyebrow nhãn nhỏ uppercase `text-[11px] tracking-[0.18em] text-violet-300/70`. |
| **6. Hệ thống "kính mờ" có VIỀN sáng + noise, không phải blur trơn** | Glassmorphism cao cấp = `backdrop-blur` + **viền 1px gradient sáng phía trên** (mô phỏng cạnh kính bắt sáng) + grain bên trong. Nút phẳng = AI-slop. | Panel/modal/wizard step: `bg-white/[0.04] backdrop-blur-xl border border-white/[0.08]`, thêm `::before` viền top `linear-gradient(90deg,transparent,rgba(255,255,255,.25),transparent)`. Inner shadow `inset 0 1px 0 rgba(255,255,255,.06)`. | Component `<GlassCard>` chuẩn hoá cho toàn app. |
| **7. Demo TƯƠNG TÁC ngay trên landing (không chỉ video xem)** | Runway/HeyGen nhúng mini-tool chơi được trước khi đăng ký (gõ prompt thấy preview, chọn avatar nghe thử). Giảm ma sát, "show don't tell". | Tận dụng **wedge giọng Việt**: "Voice A/B blind demo" ngay hero — 2 nút phát cùng kịch bản (giọng robot TTS vs giọng VietVid clone), người dùng đoán, reveal. Thanh waveform (wavesurfer.js / canvas) chạy realtime khi phát. | Đây vừa là pattern cao cấp vừa là wedge → ưu tiên #1. |
| **8. Density có NHỊP: section thở rộng xen kẽ block dày đặc** | Trang xịn không spacing đều tăm tắp. Hero thoáng (whitespace lớn) → section feature dày (grid 3-4 cột, số liệu) → showcase full-bleed → pricing nén. Nhịp tạo cảm giác biên tập. | Section padding biến thiên: hero `py-32`, feature `py-24`, showcase `py-0` (full-bleed), social-proof `py-16`. Dùng thang spacing 4/8/12/16/24/32/48/64/96/128px, KHÔNG mỗi section đều `py-20`. | Lenis smooth-scroll + scroll-driven reveal (Framer `whileInView`, stagger 0.06s). |
| **9. Camera/parallax có CHIỀU SÂU theo trục Z** | Luma/Sora: scroll làm các lớp di chuyển khác tốc độ (foreground nhanh, glow nền chậm), giống dolly máy quay. | Parallax 3 lớp: grain/particle `translateY(scroll*0.1)`, content `*0`, glow nền `*-0.15`. R3F hero: camera nhích nhẹ theo cursor (`lerp`, damping 0.05). | `useScroll`+`useTransform` (Framer). Tắt khi `prefers-reduced-motion`. |
| **10. Timeline/stage render PHƠI BÀY như tính năng, không giấu** | Runway/HeyGen biến tiến trình render thành UI đẹp (giai đoạn có tên, animation chuyển). Chờ trở thành trải nghiệm, không phải spinner. | Step 5 wizard: timeline 8 stage (QUEUED→DIRECTING→IMAGING→RENDERING_VIDEO→VOICING→COMPOSING→QA→READY) dạng node phát sáng dần, dùng `stage_timings` vẽ progress thật, mỗi stage có icon lucide + nhãn tiếng Việt + thời gian. Stage đang chạy: pulse glow + shimmer. | Poll 2.5s (TanStack Query), `asset_url` preview frame xuất hiện ở stage IMAGING. |
| **11. Số liệu/chữ MONO cho dữ liệu kỹ thuật** | Trang dev-credible (Runway, Linear-style) dùng mono cho số, credit, ID, timing → cảm giác chính xác, "đã đo". | Mọi credit/giá/job_id/timing: **Geist Mono** / **JetBrains Mono** `tabular-nums`. Badge "đang giữ X credit" mono. Ledger table mono cột số. | Tạo `<CreditValue>` mono + `tabular-nums` để số không nhảy khi update. |
| **12. Color grade NHẤT QUÁN một "LUT"** | Sản phẩm xịn trông như cùng 1 bộ lọc màu: tất cả thumbnail/ảnh ám về cùng tông (teal-violet shadow). Tạo cohesion thị giác. | Áp `--accent-gradient: linear-gradient(135deg,#7C3AED,#4F46E5,#2563EB)` (violet→indigo→blue) NHẤT QUÁN cho: progress, active state, glow, link hover, focus ring. Thumbnail overlay nhẹ cùng tông để gallery đồng bộ dù sản phẩm khác nhau. | Giới hạn palette: 1 accent gradient + đen nhiều lớp + trắng/xám text. Cấm thêm màu thứ 4 trừ semantic (green settle / amber hold / red fail). |

---

## PHẦN 2 — 10 dấu hiệu AI-SLOP / template rẻ / landing tự-làm-chán → TRÁNH + thay bằng human-crafted

| # | Dấu hiệu SLOP (tránh tuyệt đối) | Vì sao rẻ tiền | Thay bằng (human-crafted) |
|---|---|---|---|
| **1** | Gradient **tím→xanh phẳng full-page** kiểu `from-purple-500 to-blue-500` mặc định Tailwind, không texture | Đây CHÍNH XÁC là "AI slop" ai cũng nhận ra; phẳng, bão hoà, không chiều sâu | Đen nhiều lớp (Pattern 2) + accent gradient chỉ dùng cho **glow/active/viền**, không phủ nền. Gradient có grain + radial lệch tâm, hex riêng `#7C3AED/#4F46E5/#2563EB` chứ không màu Tailwind chuẩn |
| **2** | **Blob tròn bo mềm trôi nổi** (purple/pink blobs blur) làm trang trí nền | Dấu hiệu template Figma free / kit "SaaS gradient" 2021 | Glow tuyến tính từ nội dung + film grain + (tuỳ chọn) shader noise R3F. Hình khối nếu có phải có nghĩa (frame video, mask sản phẩm) |
| **3** | **Icon set generic** (Heroicons outline 24px tím trong vòng tròn nhạt, 3 cột "Fast/Secure/Easy") | Ai cũng dùng, vô hồn | Lucide stroke 1.5px mảnh, đặt trong glass-chip vuông bo nhẹ; HOẶC thay icon bằng **mini-clip/thumbnail thật** minh hoạ tính năng. Feature card dẫn bằng số/demo, không bằng icon |
| **4** | **Hero 3D stock vô hồn** (robot/khối abstract Spline mặc định, astronaut) | "AI startup" cliché, không liên quan sản phẩm | Hero = **video output thật của chính VietVid** (Pattern 1). Nếu cần 3D → particle field/shader tối giản phản ứng cursor, đứng SAU video |
| **5** | **Spacing đều đều** mọi section `py-20`, grid đối xứng cứng, mọi card cùng cỡ | Thiếu nhịp biên tập → cảm giác "ai đó tự kéo thả" | Density có nhịp (Pattern 8): xen full-bleed showcase với section nén; bento-grid card lệch cỡ (1 card lớn + 2 nhỏ) |
| **6** | **Copy sáo rỗng**: "Powered by AI", "Unleash your creativity", "The future of video", "Seamless & Powerful" | Vô nghĩa, không ai nhớ | Copy cụ thể-số-Việt: "1 ảnh → video chốt đơn 60 giây", "Nghe thử giọng thật, không phải robot", "Thấy trước tốn ~X credit rồi mới tạo". Verb hành động + lợi ích đo được |
| **7** | **Shadow xám mặc định** `shadow-lg` (đen 10% opacity) trên card sáng | Phẳng, "Bootstrap admin", phá vibe điện ảnh | Glow cùng màu accent (Pattern 3) + viền 1px sáng. Trên nền tối KHÔNG dùng drop-shadow đen — dùng `inset` highlight + outer glow |
| **8** | **Border xám phẳng** `border-gray-200` + nền trắng card | Light-mode SaaS template; lạc tông dark cinematic | `border-white/[0.06-0.10]` + viền-top gradient sáng (Pattern 6). Toàn app dark-first, không trộn card trắng |
| **9** | **Font hệ thống / 1 font / Poppins-Montserrat tròn** dùng cho mọi cỡ, `font-weight 400` cho heading | Trông như Google Docs / template Wix; thiếu cấp bậc | Pairing 3 vai: Display geometric (Clash/General Sans) đậm cho heading + Inter/Geist body + Geist Mono cho số. Tracking âm heading, tương phản cỡ mạnh (Pattern 5) |
| **10** | **Testimonial avatar tròn stock + logo xám "as seen on" + counter giả** | Tín hiệu tin cậy rỗng, ai cũng làm | Social proof THẬT: video kết quả khách hàng (hover-play), số liệu thật ("X video tạo hôm nay" từ API), badge minh bạch giá. Nếu chưa có khách → khoe **output + cơ chế hoàn tiền**, không bịa logo |

**Quy tắc vàng chống slop:** mỗi màn chỉ **1 "anh hùng thị giác"** (1 video/1 glow/1 motion lớn), phần còn lại tĩnh-rõ-nhanh. Slop sinh ra khi MỌI thứ cùng cố gây chú ý.

---

## PHẦN 3 — 6 "DIFFERENTIATOR MOVE" để VietVid KHÁC & nhớ được (không chỉ clone)

> Đối thủ (Runway/Kling/Sora) mạnh về *model*, nhưng đều **mờ về giá** và **không có giọng Việt thật**. Đó là khe hở.

| # | Differentiator | Cách thể hiện trên UI (cụ thể) | Vì sao đối thủ không có |
|---|---|---|---|
| **1** | **"Voice A/B blind test" ngay hero** (wedge giọng Việt) | Hai nút phát cùng kịch bản tiếng Việt: 🤖 *giọng robot generic* vs ✨ *giọng VietVid clone*. Waveform realtime, người dùng đoán → reveal. Trong wizard B3: nghe-thử-từng-giọng + ô **"đọc thử CÂU CỦA TÔI"** (gõ → nghe ngay trước khi tốn credit tạo full). | Runway/Kling không làm voice; HeyGen có voice nhưng tiếng Việt yếu/robot. Đây là demo "chơi được" + bằng chứng tai-nghe-được. |
| **2** | **"3 khoảnh khắc minh bạch giá" thành signature visual** (wedge giá) | Một component xuyên suốt: (a) trước tạo → chip "Ước tính **~X credit**" (mono, có breakdown tooltip); (b) khi tạo → badge **"Đang GIỮ ⏳ ceil(est×1.5)"** cạnh số dư, số dư hiện 2 dòng *khả dụng / đang giữ*; (c) xong → animation **"HOÀN +Y credit phần thừa"** số chạy ngược + dòng ledger SETTLE/REFUND highlight. "Hoàn 100% nếu lỗi hệ thống" in đậm. | autovis bị chê "tự trừ tiền". Biến nỗi đau thành **chữ ký**: không đối thủ nào biến billing thành moment đẹp. Đây là thứ user kể lại. |
| **3** | **Engine picker dạng "card so kè điện ảnh"** | 4 card glass: Seedance (rẻ/nháp) · Veo 3.1 (hero) · Kling 3.0 (điện ảnh) · Hailuo (nhanh). Mỗi card: mini-clip loop thật của engine đó + 3 thanh đo **Chất lượng / Tốc độ / Credit** + nhãn "Nên dùng khi…". Hover → clip play. Chọn → glow viền accent. | Đối thủ KHOÁ bạn vào 1 model của họ. VietVid cho **chọn & so sánh minh bạch** → định vị "trung lập, vì người dùng". |
| **4** | **Tặng 300 credit + "ước tính được bao nhiêu video"** ngay lúc bootstrap | Sau signup: confetti nhẹ + "Bạn có **300 credit** ≈ ~X video 8s 1080p" (tính từ `/jobs/estimate`). Onboarding chỉ vào thẳng wizard với sản phẩm mẫu điền sẵn → tạo video đầu trong <60s. | Đối thủ bắt trả tiền/đăng ký mới thấy giá trị. Free-credit + quy đổi rõ = giảm ma sát, nhớ ngay. |
| **5** | **Live render timeline là "buồng đạo diễn"** | Step 5 không phải spinner mà là sân khấu: 8 stage node phát sáng tuần tự (Pattern 10), preview frame thật hiện ở IMAGING, waveform giọng hiện ở VOICING, mỗi stage có timing mono. Cảm giác "xem phim mình đang được dựng". | Render là lúc chờ → đối thủ lãng phí. VietVid biến nó thành moment giữ chân + tin tưởng (thấy từng bước, không hộp đen). |
| **6** | **"Made-in-Vietnam" thanh toán & ngôn ngữ là tính năng, không phải afterthought** | Top-up đa cổng nội địa hiển thị tự hào: VietQR/VNPay/Momo + USDT, QR bank **tự cộng credit khi tiền về** (toast realtime "đã nhận, +X credit"). Toàn UI tiếng Việt chuẩn (thuật ngữ EN giữ), giọng/kịch bản tối ưu văn phong bán hàng Việt. | Runway/Kling/Sora là sản phẩm Mỹ/TQ: thanh toán quốc tế phiền, không hiểu thị trường Việt. Đây là moat địa phương. |

**Tóm gọn định vị nhớ-được:** *"Runway cho điện ảnh — nhưng VietVid cho bạn **nghe được giọng Việt thật**, **thấy trước từng credit**, và **trả bằng VietQR**."* Ba thứ đối thủ toàn cầu không thể sao chép nhanh.

---

**Sources:**
- [Luma vs Sora vs Runway vs Kling 2026 — Marketing Scoop](https://www.marketingscoop.com/ai-2/what-is-luma-dream-machine-and-how-does-it-compare-with-sora-runway-and-kling-in-2026/)
- [Kling vs Pika vs Luma — Melies](https://melies.co/kling-vs-pika-vs-luma)
- [AI Video Showdown 2026: Kling v3 vs Hailuo vs Runway Gen-4.5 vs Luma — AI Magicx](https://www.aimagicx.com/blog/ai-video-generation-showdown-2026)
- [Sora vs Kling vs Luma vs Runway full comparison — CrePal](https://crepal.ai/blog/aivideo/sora-vs-kling-vs-luma-vs-runway/)
- [Autovis.ai (trang chính)](https://autovis.ai/)
- [Autovis — giới thiệu tính năng (VniTeach)](https://www.vniteach.com/2025/08/24/autovis-cong-cu-tao-video-tu-van-ban-va-hinh-anh-bang-ai/)
- [Glassmorphism best practices 2026 — Webflow](https://webflow.com/blog/glassmorphism)
- [Sora is here — OpenAI](https://openai.com/index/sora-is-here/)

---

# B. DESIGN SYSTEM (token cụ thể)

Đây là nhiệm vụ đặc tả design system, không cần đọc/sửa code. Tôi sẽ trả về spec đầy đủ dạng token sẵn-sàng-đổ-vào Tailwind + CSS variables.

# VietVid Design System — Dark Cinematic × Electric Violet→Blue

## 1) COLOR TOKENS (HEX cụ thể)

### 1.1 Thang nền tối nhiều lớp (5 bậc near-black, hơi ám tím-lạnh)
Dùng hue ~250 (violet-blue) với saturation rất thấp để nền "ấm điện ảnh" chứ không xám chết.

| Token | HEX | RGB | Dùng cho |
|---|---|---|---|
| `bg-base` | `#06070D` | 6 7 13 | nền ngoài cùng (body, viewport) |
| `bg-surface-1` | `#0B0D16` | 11 13 22 | section / panel chính |
| `bg-surface-2` | `#12141F` | 18 20 31 | card nền, input fill |
| `bg-elevated` | `#1A1C2A` | 26 28 42 | popover, dropdown, modal body |
| `bg-overlay` | `#22243440` (rgba 34 36 52 / .25) | — | scrim trên cùng, hover layer |
| `bg-scrim` | `rgba(6,7,13,0.72)` | — | backdrop modal/drawer |

### 1.2 Primary VIOLET→BLUE (50→900)
Violet là điểm neo (500 = brand). 600→700 ngả về blue cho gradient.

| Step | HEX | Note |
|---|---|---|
| `violet-50` | `#F2EEFF` | text-on-dark accent rất nhạt, focus tint |
| `violet-100` | `#E4DBFF` | |
| `violet-200` | `#C9B6FF` | |
| `violet-300` | `#A98CFF` | hover text link |
| `violet-400` | `#8B5CFF` | accent sáng / icon active |
| `violet-500` | `#7C4DFF` | **BRAND PRIMARY** (electric violet) |
| `violet-600` | `#6A3CF0` | button default |
| `violet-700` | `#5A2FD6` | button hover/pressed |
| `violet-800` | `#4322A8` | |
| `violet-900` | `#2E1772` | |

Nhánh BLUE (cho gradient stop & info):
| Step | HEX |
|---|---|
| `blue-400` | `#4C8DFF` |
| `blue-500` | `#3B82F6` |
| `blue-600` | `#2D6BE0` |

**Gradient stops chuẩn** (brand accent):
- `--grad-from: #7C4DFF` (violet-500)
- `--grad-mid: #6366F1` (indigo bridge)
- `--grad-to: #3B82F6` (blue-500)

### 1.3 Neutrals / Text (WCAG AA trên `bg-surface-1 #0B0D16`)
| Token | HEX | Contrast vs #0B0D16 | Mức |
|---|---|---|---|
| `text-high` | `#F4F5FA` | ~16.8:1 | tiêu đề, số dư, giá trị |
| `text-medium` | `#B4B7C7` | ~8.1:1 | body text |
| `text-low` | `#7E8298` | ~4.6:1 (AA normal) | caption, label phụ, placeholder |
| `text-disabled` | `#4B4E61` | — | disabled (không cần AA) |
| `text-on-accent` | `#FFFFFF` | trên violet-600 ~5.1:1 AA | chữ trên nút primary |

Border / divider:
| Token | HEX / rgba |
|---|---|
| `border-subtle` | `rgba(255,255,255,0.06)` |
| `border-default` | `rgba(255,255,255,0.10)` |
| `border-strong` | `rgba(255,255,255,0.16)` |
| `border-accent` | `rgba(124,77,255,0.45)` (focus ring base) |

### 1.4 Semantic
| Token | HEX | Tint-bg (rgba) | Dùng |
|---|---|---|---|
| `success` | `#34D399` | `rgba(52,211,153,0.12)` | hoàn tiền OK, READY |
| `success-fg` | `#6EE7B7` | — | text trên nền tối |
| `warn` | `#FBBF24` | `rgba(251,191,36,0.12)` | clamp_notes, WAITING_CONFIG |
| `warn-fg` | `#FCD34D` | — | |
| `danger` | `#F87171` | `rgba(248,113,113,0.12)` | FAILED, lỗi |
| `danger-fg` | `#FCA5A5` | — | |
| `info` | `#60A5FA` | `rgba(96,165,250,0.12)` | thông tin trung tính |
| `info-fg` | `#93C5FD` | — | |

### 1.5 Màu ledger entry_type
Mapping vào ý nghĩa "tiền vào/ra/giữ".
| entry_type | HEX dot/text | Tint-bg | Icon (lucide) | Hướng |
|---|---|---|---|---|
| `TOPUP` | `#34D399` (success) | `rgba(52,211,153,.12)` | `arrow-down-to-line` / `plus` | +xanh |
| `BONUS` | `#7C4DFF` (violet-500) | `rgba(124,77,255,.14)` | `gift` | +tím |
| `HOLD` | `#FBBF24` (warn/amber) | `rgba(251,191,36,.12)` | `lock` | giữ (vàng) |
| `SETTLE` | `#B4B7C7` (neutral) | `rgba(180,183,199,.10)` | `check` | trừ thực (xám trung tính) |
| `REFUND` | `#22D3EE` (cyan) | `rgba(34,211,238,.12)` | `rotate-ccw` | hoàn (cyan, tách khỏi success) |

Badge "đang giữ" cạnh số dư: dùng `HOLD` amber `#FBBF24`, fill `rgba(251,191,36,.12)`, border `rgba(251,191,36,.30)`.

### 1.6 Màu từng STAGE render (timeline)
Gradient tiến trình theo pipeline; stage active glow theo màu của nó.
| Stage | HEX | Ý nghĩa màu |
|---|---|---|
| `QUEUED` | `#7E8298` (neutral-low) | chờ |
| `DIRECTING` | `#A98CFF` (violet-300) | sáng tạo kịch bản |
| `IMAGING` | `#8B5CFF` (violet-400) | |
| `RENDERING_VIDEO` | `#6366F1` (indigo) | nặng nhất, lõi |
| `VOICING` | `#22D3EE` (cyan) | gắn wedge giọng Việt |
| `COMPOSING` | `#3B82F6` (blue-500) | ghép |
| `QA` | `#FBBF24` (amber) | kiểm |
| `READY` | `#34D399` (success) | xong |
| `QA_FAIL` | `#FB923C` (orange) | cảnh báo mềm |
| `FAILED` | `#F87171` (danger) | |
| `WAITING_CONFIG` | `#FCD34D` (amber-fg) | cần cấu hình |
| `REFUNDED` | `#22D3EE` (cyan) | đồng bộ REFUND |
| `CANCELLED` | `#4B4E61` (disabled) | |

---

## 2) GRADIENT & GLOW SYSTEM

```css
/* —— Brand linear (button, text-gradient, underline) —— */
--grad-brand: linear-gradient(135deg, #7C4DFF 0%, #6366F1 50%, #3B82F6 100%);
--grad-brand-soft: linear-gradient(135deg, rgba(124,77,255,.18), rgba(59,130,246,.18));

/* —— Radial hero glow (đặt sau WebGL hero, dưới CTA) —— */
--glow-radial: radial-gradient(60% 60% at 50% 0%, rgba(124,77,255,.35) 0%, rgba(99,102,241,.12) 40%, transparent 72%);

/* —— Conic (loader ring, spotlight card) —— */
--grad-conic: conic-gradient(from 210deg at 50% 50%, #7C4DFF, #3B82F6, #22D3EE, #7C4DFF);

/* —— Mesh background (section marketing, blur lớn) —— */
--mesh-bg:
  radial-gradient(40% 50% at 12% 18%, rgba(124,77,255,.28), transparent 60%),
  radial-gradient(35% 45% at 88% 12%, rgba(59,130,246,.22), transparent 62%),
  radial-gradient(45% 55% at 70% 90%, rgba(34,211,238,.16), transparent 60%),
  #06070D;

/* —— Border-gradient cho card glass (mask technique) —— */
--border-grad: linear-gradient(135deg, rgba(124,77,255,.55), rgba(59,130,246,.18) 50%, rgba(255,255,255,.04));
```

Glow blur tokens (box-shadow / filter):
| Token | Value | Dùng |
|---|---|---|
| `--glow-sm` | `0 0 16px rgba(124,77,255,.35)` | icon active, badge |
| `--glow-md` | `0 0 32px rgba(124,77,255,.45)` | button hover, focus |
| `--glow-lg` | `0 0 64px rgba(124,77,255,.40)` | hero CTA, modal accent |
| `--glow-blue` | `0 0 40px rgba(59,130,246,.40)` | stage RENDERING/COMPOSING |
| `--glow-success` | `0 0 28px rgba(52,211,153,.40)` | READY pulse |

Border-gradient card (CSS recipe):
```css
.glass-bordered { position: relative; border-radius: 16px; }
.glass-bordered::before {
  content:""; position:absolute; inset:0; border-radius:inherit; padding:1px;
  background: var(--border-grad);
  -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
  -webkit-mask-composite: xor; mask-composite: exclude;
  pointer-events:none;
}
```

---

## 3) TYPOGRAPHY

**Font chốt** (đều hỗ trợ tiếng Việt đầy đủ dấu, qua `next/font/google`):
- **Display / heading**: `Be Vietnam Pro` (weights 600/700/800) — tối ưu Việt, hình thể geometric-humanist hợp cinematic. Fallback hero numbers: `Space Grotesk` (cho con số credit/giá, tech-feel). 
- **Body / UI**: `Inter` (weights 400/500/600) — `--font-inter`, dùng `feature-settings: "cv11","ss01"` cho chữ số rõ.
- **Mono** (job_id, idempotency_key, ledger số): `Geist Mono` hoặc `JetBrains Mono`, weight 400/500.

Khai báo:
```css
--font-display: "Be Vietnam Pro", system-ui, sans-serif;
--font-body: "Inter", "Be Vietnam Pro", system-ui, sans-serif;
--font-mono: "Geist Mono", ui-monospace, monospace;
--font-numeric: "Space Grotesk", "Inter", sans-serif; /* tabular cho credit */
```

Type scale (1.250 major-third trên base 16, line-height/tracking cụ thể):
| Token | size | line-height | tracking | weight / font | Dùng |
|---|---|---|---|---|---|
| `display-2xl` | 72px / 4.5rem | 1.02 | -0.03em | 800 display | hero H1 |
| `display-xl` | 56px / 3.5rem | 1.05 | -0.025em | 800 display | landing section |
| `display-lg` | 44px / 2.75rem | 1.08 | -0.02em | 700 display | |
| `h1` | 34px / 2.125rem | 1.15 | -0.02em | 700 display | page title app |
| `h2` | 28px / 1.75rem | 1.2 | -0.015em | 700 display | |
| `h3` | 22px / 1.375rem | 1.3 | -0.01em | 600 display | card title |
| `h4` | 18px / 1.125rem | 1.35 | -0.005em | 600 body | |
| `body-lg` | 18px | 1.6 | 0 | 400 body | mô tả |
| `body` | 15px / 0.9375rem | 1.6 | 0 | 400 body | mặc định UI |
| `body-sm` | 13px / 0.8125rem | 1.5 | 0 | 400 body | caption |
| `label` | 13px | 1.2 | 0.01em | 500 body | form label |
| `overline` | 11px | 1.2 | 0.14em UPPERCASE | 600 body | eyebrow/section tag |
| `mono-sm` | 12.5px | 1.5 | 0 | 400 mono | id, hash |
| `credit-num` | 28px tabular | 1 | -0.01em | 600 numeric | số dư credit |

`font-variant-numeric: tabular-nums` cho mọi số credit/giá/ledger.

---

## 4) SPACING · RADIUS · BLUR · SHADOW · BORDER

**Spacing scale** (base 4px, thêm bậc lẻ cho mật độ app):
`0, 1=4, 1.5=6, 2=8, 3=12, 4=16, 5=20, 6=24, 8=32, 10=40, 12=48, 16=64, 20=80, 24=96, 32=128` (px). Section marketing dùng `py-24/py-32`; app density dùng `gap-3/gap-4`.

**Radius**:
| Token | px |
|---|---|
| `radius-xs` | 6 |
| `radius-sm` | 8 |
| `radius-md` | 12 (input, badge) |
| `radius-lg` | 16 (card) |
| `radius-xl` | 20 (modal, video card) |
| `radius-2xl` | 28 (hero panel) |
| `radius-full` | 9999 (pill, avatar) |

**Blur (glass backdrop)**:
| Token | value |
|---|---|
| `blur-glass-sm` | `blur(8px)` |
| `blur-glass` | `blur(16px)` |
| `blur-glass-lg` | `blur(28px)` |
| backdrop saturate kèm | `saturate(140%)` |

**Shadow / elevation trên nền tối** (đen sâu + ambient violet rất nhẹ, KHÔNG dùng shadow xám nhạt kiểu light theme):
```css
--shadow-1: 0 1px 2px rgba(0,0,0,.40);
--shadow-2: 0 4px 12px rgba(0,0,0,.45), 0 1px 0 rgba(255,255,255,.03) inset;
--shadow-3: 0 12px 32px rgba(0,0,0,.55), 0 0 0 1px rgba(255,255,255,.04);
--shadow-4: 0 24px 64px rgba(0,0,0,.6), 0 0 40px rgba(124,77,255,.10); /* modal/popover */
--shadow-glow-primary: 0 8px 24px rgba(124,77,255,.35);
```

**Border subtle**: mặc định card `1px solid rgba(255,255,255,.06)` + inset highlight `inset 0 1px 0 rgba(255,255,255,.04)` để tạo cạnh sáng "vật lý".

---

## 5) GLASSMORPHISM + FILM-GRAIN + NOISE (recipe cụ thể)

**Glass card** (chuẩn dùng lại):
```css
.glass {
  background: linear-gradient(180deg, rgba(255,255,255,.05), rgba(255,255,255,.02));
  backdrop-filter: blur(16px) saturate(140%);
  -webkit-backdrop-filter: blur(16px) saturate(140%);
  border: 1px solid rgba(255,255,255,.08);
  box-shadow: var(--shadow-3), inset 0 1px 0 rgba(255,255,255,.05);
  border-radius: var(--radius-lg);
}
.glass-strong { /* modal */ background: rgba(18,20,31,.72); backdrop-filter: blur(28px) saturate(150%); }
```

**Film-grain overlay** (toàn trang, pointer-events none, opacity thấp):
```css
.grain::after{
  content:""; position:fixed; inset:0; z-index:60; pointer-events:none;
  opacity:.05; mix-blend-mode:overlay;
  background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='160' height='160'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>");
}
```
- Grain động (hero): animate `background-position` ~8 steps/0.5s hoặc thay bằng canvas; tắt khi `prefers-reduced-motion`.

**Noise texture nền section** (mịn hơn grain, baseFrequency thấp `0.6`, opacity `.03`, `mix-blend-mode: soft-light`).

**Vignette cinematic** (bọc viewport):
```css
--vignette: radial-gradient(120% 120% at 50% 30%, transparent 55%, rgba(0,0,0,.45) 100%);
```

---

## 6) COMPONENT INVENTORY (variants + states)

States chuẩn cho mọi interactive: `default · hover · active/pressed · focus-visible · disabled · loading`. Focus-visible = `outline: 2px solid #7C4DFF; outline-offset: 2px` + `--glow-sm`.

**Button**
- Variants: `primary` (fill `--grad-brand`, text white, `--shadow-glow-primary`; hover sáng +`--glow-md`; pressed scale .98) · `secondary` (glass fill, border-default) · `outline` (transparent, border-strong, hover border-accent) · `ghost` (no bg, hover `rgba(255,255,255,.05)`) · `danger` (fill danger tint) · `link` (violet-300, underline gradient).
- Sizes: `sm 32px / md 40px / lg 48px / xl 56px (hero)`. Icon-only square cùng cao.
- Loading: spinner conic-gradient + label mờ; disabled `opacity .45, no glow`.

**Input / Textarea / Select**
- Fill `bg-surface-2`, border-subtle, radius-md, h-40. Focus: border-accent + `--glow-sm` + ring inset. Placeholder `text-low`. States: error (border danger + helper danger-fg), success (border success). Prefix/suffix icon slot. `Select` mở popover `bg-elevated` + shadow-4.

**Card (glass)**
- `.glass` base; variant `interactive` (hover: translateY(-2px) + shadow-4 + border-accent + subtle glow), `bordered` (border-gradient §2), `stat` (số credit lớn + sparkline). Header/body/footer slots.

**Badge / Pill**
- Shape pill (radius-full) hoặc tag (radius-md). Variants màu = semantic + ledger + stage (tint-bg + dot + text-fg). Sizes sm/md. Có `dot` leading + optional icon. "Đang giữ" badge = amber pulse nhẹ.

**Modal / Dialog**
- Backdrop `--bg-scrim` + `blur(8px)`. Panel `.glass-strong`, radius-xl, shadow-4, max-w-lg, accent top hairline gradient. Enter: Framer fade+scale .96→1, 180ms. Drawer (mobile) slide-up.

**Toast**
- Bottom-right, `.glass-strong`, border-left 3px theo semantic, icon + title + desc, auto-dismiss 4s + progress bar gradient. Stack tối đa 3, variants success/danger/info/warn.

**Tooltip**
- `bg-elevated` (rgba .96), text-sm, radius-sm, shadow-3, arrow, delay 200ms. Max-w 240px.

**Tabs**
- Underline gradient cho tab active (`--grad-brand`, animated indicator Framer layoutId). Variant `pill` (active fill glass + glow). Inactive text-low → hover text-medium.

**Stepper (Wizard 5 bước)**
- Horizontal connector line; node: done (fill success + check), current (fill gradient + `--glow-md` pulse), upcoming (border-subtle, text-low). Label dưới node. Progress line fill gradient theo % bước. Mobile: compact "B2/5" + dots.

**Progress**
- Linear: track `rgba(255,255,255,.06)`, fill `--grad-brand`, có shimmer overlay khi indeterminate. Ring/Circular: conic-gradient cho job render %. Segmented (stage timeline): mỗi segment màu stage §1.6, segment active glow + animated stripe.

**Table / Ledger row**
- Header `text-low overline`, row h-52, divider border-subtle, hover `rgba(255,255,255,.03)`. Ledger row: leading dot+icon entry_type, `delta_credits` tabular-nums (xanh +/đỏ −/xám settle), `balance_after` text-high, `note` text-medium, `created_at` text-low mono-sm. HOLD row có amber left-accent. Zebra tắt (dùng divider).

**Video card (Library)**
- radius-xl, aspect 9:16/16:9 thumbnail + gradient scrim bottom, hover: play overlay + scale 1.02 + shadow-4. Badge stage/READY góc trên; meta (seconds, resolution, credit) overline dưới. Action: tải MP4, tạo lại (ghost icon buttons hiện on-hover). Skeleton shimmer khi loading.

**Skeleton / Shimmer**
- Base `bg-surface-2`, overlay gradient sweep `linear-gradient(90deg, transparent, rgba(255,255,255,.06), transparent)` animate 1.4s. Shapes: text-line, avatar-circle, card, video-thumb. Tôn trọng reduced-motion → static `bg-surface-2`.

**Bổ sung (gắn product)**: `EngineCard` (so sánh Seedance/Veo/Kling/Hailuo: tier badge + chất lượng·tốc độ·giá credit, selected = border-gradient + glow), `VoiceChip` (play waveform mini, A/B blind toggle), `TransparencyPanel` ("3 khoảnh khắc": est → hold ceil(est×1.5) → settle/refund, mỗi mốc 1 màu: est=info, hold=amber, refund=cyan/success).

---

## 7) TAILWIND CONFIG + CSS VARIABLES (sẵn-sàng-đổ)

`globals.css`:
```css
:root{
  /* bg */
  --bg-base:#06070D; --bg-surface-1:#0B0D16; --bg-surface-2:#12141F;
  --bg-elevated:#1A1C2A; --bg-scrim:rgba(6,7,13,.72);
  /* violet */
  --violet-50:#F2EEFF;--violet-100:#E4DBFF;--violet-200:#C9B6FF;--violet-300:#A98CFF;
  --violet-400:#8B5CFF;--violet-500:#7C4DFF;--violet-600:#6A3CF0;--violet-700:#5A2FD6;
  --violet-800:#4322A8;--violet-900:#2E1772;
  --blue-400:#4C8DFF;--blue-500:#3B82F6;--blue-600:#2D6BE0;--indigo-500:#6366F1;--cyan-500:#22D3EE;
  /* text */
  --text-high:#F4F5FA;--text-medium:#B4B7C7;--text-low:#7E8298;--text-disabled:#4B4E61;
  /* border */
  --border-subtle:rgba(255,255,255,.06);--border-default:rgba(255,255,255,.10);
  --border-strong:rgba(255,255,255,.16);--border-accent:rgba(124,77,255,.45);
  /* semantic */
  --success:#34D399;--success-fg:#6EE7B7;--warn:#FBBF24;--warn-fg:#FCD34D;
  --danger:#F87171;--danger-fg:#FCA5A5;--info:#60A5FA;--info-fg:#93C5FD;
  /* gradients */
  --grad-brand:linear-gradient(135deg,#7C4DFF 0%,#6366F1 50%,#3B82F6 100%);
  --grad-conic:conic-gradient(from 210deg at 50% 50%,#7C4DFF,#3B82F6,#22D3EE,#7C4DFF);
  --glow-sm:0 0 16px rgba(124,77,255,.35);--glow-md:0 0 32px rgba(124,77,255,.45);
  --glow-lg:0 0 64px rgba(124,77,255,.40);
  /* fonts */
  --font-display:"Be Vietnam Pro",system-ui,sans-serif;
  --font-body:"Inter","Be Vietnam Pro",system-ui,sans-serif;
  --font-mono:"Geist Mono",ui-monospace,monospace;
  --font-numeric:"Space Grotesk","Inter",sans-serif;
  /* radius */
  --radius-sm:8px;--radius-md:12px;--radius-lg:16px;--radius-xl:20px;--radius-2xl:28px;
}
```

`tailwind.config.ts` (extend — trích phần token chính):
```ts
theme:{ extend:{
  colors:{
    bg:{ base:"#06070D", "surface-1":"#0B0D16", "surface-2":"#12141F", elevated:"#1A1C2A" },
    violet:{50:"#F2EEFF",100:"#E4DBFF",200:"#C9B6FF",300:"#A98CFF",400:"#8B5CFF",
      500:"#7C4DFF",600:"#6A3CF0",700:"#5A2FD6",800:"#4322A8",900:"#2E1772"},
    brandblue:{400:"#4C8DFF",500:"#3B82F6",600:"#2D6BE0"}, indigo:{500:"#6366F1"}, cyan:{500:"#22D3EE"},
    txt:{ high:"#F4F5FA", medium:"#B4B7C7", low:"#7E8298", disabled:"#4B4E61" },
    success:"#34D399", warn:"#FBBF24", danger:"#F87171", info:"#60A5FA",
    ledger:{ topup:"#34D399", bonus:"#7C4DFF", hold:"#FBBF24", settle:"#B4B7C7", refund:"#22D3EE" },
    stage:{ queued:"#7E8298", directing:"#A98CFF", imaging:"#8B5CFF", rendering:"#6366F1",
      voicing:"#22D3EE", composing:"#3B82F6", qa:"#FBBF24", ready:"#34D399",
      qafail:"#FB923C", failed:"#F87171", waiting:"#FCD34D", cancelled:"#4B4E61" },
  },
  fontFamily:{ display:["var(--font-display)"], sans:["var(--font-body)"],
    mono:["var(--font-mono)"], numeric:["var(--font-numeric)"] },
  fontSize:{
    "display-2xl":["4.5rem",{lineHeight:"1.02",letterSpacing:"-0.03em",fontWeight:"800"}],
    "display-xl":["3.5rem",{lineHeight:"1.05",letterSpacing:"-0.025em",fontWeight:"800"}],
    "display-lg":["2.75rem",{lineHeight:"1.08",letterSpacing:"-0.02em",fontWeight:"700"}],
    h1:["2.125rem",{lineHeight:"1.15",letterSpacing:"-0.02em"}],
    h2:["1.75rem",{lineHeight:"1.2",letterSpacing:"-0.015em"}],
    h3:["1.375rem",{lineHeight:"1.3",letterSpacing:"-0.01em"}],
    "body-lg":["1.125rem",{lineHeight:"1.6"}], body:["0.9375rem",{lineHeight:"1.6"}],
    "body-sm":["0.8125rem",{lineHeight:"1.5"}], overline:["0.6875rem",{lineHeight:"1.2",letterSpacing:"0.14em"}],
  },
  borderRadius:{ sm:"8px", md:"12px", lg:"16px", xl:"20px", "2xl":"28px" },
  backdropBlur:{ glass:"16px", "glass-lg":"28px" },
  boxShadow:{
    e1:"0 1px 2px rgba(0,0,0,.40)",
    e2:"0 4px 12px rgba(0,0,0,.45), inset 0 1px 0 rgba(255,255,255,.03)",
    e3:"0 12px 32px rgba(0,0,0,.55), 0 0 0 1px rgba(255,255,255,.04)",
    e4:"0 24px 64px rgba(0,0,0,.6), 0 0 40px rgba(124,77,255,.10)",
    "glow-primary":"0 8px 24px rgba(124,77,255,.35)",
  },
  backgroundImage:{
    "grad-brand":"linear-gradient(135deg,#7C4DFF 0%,#6366F1 50%,#3B82F6 100%)",
    "glow-radial":"radial-gradient(60% 60% at 50% 0%,rgba(124,77,255,.35),rgba(99,102,241,.12) 40%,transparent 72%)",
  },
  keyframes:{ shimmer:{ "100%":{ transform:"translateX(100%)" } },
    pulseGlow:{ "0%,100%":{ boxShadow:"var(--glow-sm)" }, "50%":{ boxShadow:"var(--glow-md)" } } },
  animation:{ shimmer:"shimmer 1.4s infinite", "pulse-glow":"pulseGlow 2s ease-in-out infinite" },
}}
```

---

Ghi chú thực thi: chạy `dark` mode mặc định (class strategy, set `<html class="dark">` cố định — app này dark-only). WCAG: mọi `text-medium/high` đã ≥4.5:1 trên `bg-surface-1`; tránh đặt `text-low` lên `bg-base` (#06070D) cho body dài. `prefers-reduced-motion`: tắt grain động, shimmer, pulse-glow, parallax — giữ fade tĩnh.

Không có file nào được tạo/sửa (đây là spec thuần). Toàn bộ token nằm trong câu trả lời này, sẵn sàng đổ vào `globals.css` và `tailwind.config.ts`.

---

# C. KIẾN TRÚC MOTION & TECH

Đây là nhiệm vụ thiết kế kiến trúc motion & tech, không cần đọc code (project mới, chỉ có thư mục rỗng). Tôi sẽ trả lời trực tiếp dựa trên spec đã cho.

# KIẾN TRÚC MOTION & TECH — VietVid

## 1) THƯ VIỆN + VERSION + VAI TRÒ

| Lib | Version (pin) | Vai trò | Lý do chọn |
|---|---|---|---|
| `next` | `14.2.x` | App Router, RSC, streaming | Server Components giảm JS, `loading.tsx` Suspense streaming sẵn |
| `react` / `react-dom` | `18.3.x` | base | concurrent, `useTransition` cho optimistic |
| `typescript` | `5.4.x` | type | — |
| `tailwindcss` | `3.4.x` | styling | utility, JIT, dark-first |
| `tailwindcss-animate` | `1.0.7` | keyframe utilities (`animate-in/out`, fade/zoom/slide) | shadcn dùng sẵn cho enter/exit, rẻ hơn JS cho micro-anim |
| `tailwind-merge` + `clsx` / `cva` | `2.3.x` / `2.1.x` / `0.7.x` | class merge + variants | chuẩn shadcn |
| shadcn/ui (Radix primitives) | latest snapshot | Dialog/Popover/Toast/Tooltip/Tabs | a11y + headless, gắn motion dễ |
| `framer-motion` | `11.3.x` | **APP motion engine**: page-transition, layout, stagger, spring, `useReducedMotion`, `AnimatePresence` | API tốt nhất cho layout/exit anim + `LazyMotion` để tách bundle |
| `lenis` (`@studio-freight/lenis` → đã rename `lenis`) | `1.1.x` | smooth-scroll toàn app + scroll-driven landing | sync với rAF, có React binding, hỗ trợ `prefers-reduced-motion` |
| `@react-three/fiber` | `8.16.x` | **LANDING hero** WebGL renderer trong React | React reconciler cho three, declarative |
| `@react-three/drei` | `9.108.x` | helpers (`shaderMaterial`, `Float`, `useTexture`, `PerformanceMonitor`, `AdaptiveDpr`, `Preload`) | giảm boilerplate shader + auto-throttle DPR |
| `three` | `0.166.x` | WebGL core | peer của R3F |
| `@react-three/postprocessing` | `2.16.x` | bloom/grain/vignette cho hero | glow + film-grain điện ảnh (chỉ load trên landing) |
| `gsap` + `ScrollTrigger` | `3.12.x` | **chỉ landing**: scroll-driven pin/scrub timeline phức tạp (product→video morph theo scroll) | ScrollTrigger mạnh hơn Framer cho scrub dài; gắn vào Lenis qua `lenis.on('scroll', ScrollTrigger.update)` |
| `lottie-react` | `2.4.x` | micro-illustration JSON (badge "đang giữ" pulse, voice waveform loop, empty-states) | nhẹ hơn tự code, designer xuất JSON |
| `@tanstack/react-query` | `5.51.x` | poll job 2.5s, cache, retry/backoff | spec yêu cầu |
| `zustand` | `4.5.x` + `persist`(sessionStorage) | wizard state | spec yêu cầu |
| `@supabase/ssr` + `supabase-js` | `0.4.x` / `2.45.x` | Auth email+Google | SSR cookie session |
| `sonner` | `1.5.x` | toast (motion sẵn, swipe, stacking) | đẹp + nhẹ, hợp dark theme |
| `next-intl` | `3.17.x` | i18n VI-first | App Router native |
| `nuqs` | `1.17.x` | URL state (filter library, tab) | sync query param, shareable |
| `lucide-react` | `0.408.x` | icon | spec yêu cầu |
| `@vercel/og` | — | OG image động | share video card |
| `embla-carousel-react` | `8.1.x` | engine-compare carousel mobile | nhẹ, momentum |

**Quy tắc bundle**: `framer-motion` qua `LazyMotion` + `domAnimation` (giảm ~25kb→~5kb core, lazy nạp features). R3F/three/gsap/postprocessing **CHỈ** import trong landing route group `(marketing)`, không bao giờ chạm app bundle.

---

## 2) LANDING WebGL HERO (maximalist WOW)

**Concept cảnh — "Aurora Product Forge":**
- **Layer 0 (background)**: full-screen **fragment shader plane** — fluid aurora gradient (electric violet `#7C3AED` → blue `#2563EB` → near-black `#08080C`) bằng domain-warped fBm noise (3 octave) chảy chậm. **Cursor-reactive**: uniform `uMouse` (lerp 0.06) tạo "vết kéo sáng" + parallax. `uTime` đẩy flow.
- **Layer 1 (particles)**: `~3000` GPU points (BufferGeometry + custom shader, additive blending, size attenuation) trôi như bụi điện ảnh, hút nhẹ về con trỏ.
- **Layer 2 (hero moment — product→video morph)**: plane mang texture ảnh sản phẩm, qua shader **displacement/dissolve** (noise mask theo `uProgress`) "vỡ" thành dải pixel rồi tái hợp thành khung video đang chạy — minh hoạ chính USP "1 ảnh → video". `uProgress` scrub bằng GSAP ScrollTrigger (pin section ~150vh).
- **Postprocessing**: `Bloom` (glow violet trên highlight) + `Noise`/`Grain` (opacity ~0.06, premultiply) + `Vignette` → đúng "dark cinematic". Postprocessing chỉ bật khi `dpr≥1` và không reduced-motion.

**Nhúng trong Next App Router:**
```tsx
// app/(marketing)/_components/HeroCanvas.tsx  -> "use client"
// app/(marketing)/page.tsx (RSC) render:
const HeroCanvas = dynamic(() => import('./_components/HeroCanvas'), {
  ssr: false,                       // WebGL không SSR
  loading: () => <HeroPoster />,    // <img>/<video poster> blur-up làm fallback tức thì
});
```
- Bọc `<Canvas frameloop="demand">`? Không — hero là continuous, dùng `frameloop="always"` **nhưng** pause qua IntersectionObserver.
- `<HeroPoster>` = static gradient PNG + LCP-friendly: render ngay, canvas fade-in (`opacity 0→1, 600ms`) sau khi `onCreated`. → LCP không phụ thuộc WebGL.

**Ngân sách hiệu năng:**
- **FPS target 60** desktop, **chấp nhận 30–45** mobile. `<PerformanceMonitor onDecline>` của drei → tự hạ DPR (`AdaptiveDpr`, `dpr={[1, 2]}` → clamp 1.5 mobile), giảm particle count, tắt postprocessing khi decline.
- **Lazy + pause**: IntersectionObserver — khi hero out-of-view, set `frameloop='never'` (qua `useThree().setFrameloop`) → 0% GPU khi scroll xuống.
- **Visibility API**: tab ẩn → pause rAF (Lenis + R3F).
- Texture ảnh sản phẩm: KTX2/compressed nếu nặng; particle dùng instanced points, không geometry mới mỗi frame.
- Mobile: dưới `768px` mặc định **fallback `<video>` loop (muted, playsInline, ~1.5MB H.265/AV1 + WebM)** thay R3F nếu thiết bị `deviceMemory<4` hoặc `hardwareConcurrency<4` (feature-detect client). Tránh tải three (~150kb) trên máy yếu.

**Reduced-motion fallback:**
- `matchMedia('(prefers-reduced-motion: reduce)')` → KHÔNG mount Canvas. Render `<HeroPoster>` tĩnh (gradient + ảnh hero) + **1 frame keyframe CSS** rất nhẹ (gradient shift 20s linear) hoặc đứng yên hẳn. ScrollTrigger scrub thay bằng simple fade.

---

## 3) APP MOTION SYSTEM (rich-nhưng-nhanh)

**Page-transition (App Router + Framer):**
- App Router không có exit-anim native → dùng pattern `template.tsx` (re-mount mỗi route) cho **enter** + `AnimatePresence mode="wait"` ở layout con với `key={pathname}` cho exit/enter.
```tsx
// app/(app)/template.tsx "use client"
<motion.div initial={{opacity:0, y:8}} animate={{opacity:1, y:0}}
  transition={{duration:0.28, ease:[0.22,1,0.36,1]}}>{children}</motion.div>
```
- Wizard B1→B5: dùng `AnimatePresence` directional slide (x: +24/−24 theo hướng next/back), `mode="popLayout"`. Step indicator dùng `layoutId="wizard-progress"` cho thanh chạy mượt.

**Scroll-reveal**: hook `useInView({ once:true, margin:'-12% 0px' })` → `whileInView` fade-up (y:16→0, 0.4s). Dùng cho dashboard cards, pricing rows.

**Stagger list** (Library grid, ledger rows):
- Parent `variants` + `staggerChildren: 0.04, delayChildren: 0.05`. Cap stagger ở 12 item đầu (item sau `delay:0`) để grid lớn không lag.
- Library card hover: `whileHover={{ y:-4, scale:1.02 }}` + thumbnail video `playbackRate` preview on-hover.

**Micro-interactions chuẩn (token hoá):**
- **hover**: `scale 1.02 / y -2`, `120ms`, glow border `box-shadow` violet.
- **press**: `scale 0.97`, `whileTap`, spring `stiffness 400 damping 25`.
- **focus**: ring `2px` violet `#7C3AED`/40 + offset (a11y, không chỉ màu).
- **button CTA**: gradient sheen sweep (mask-position) 1 lần on-hover.

**Optimistic UI cho `POST /jobs`:**
1. User bấm "Tạo" ở B5 → `useMutation`:
   - `onMutate`: tạo **optimistic job** `{id:tmpId, status:'QUEUED'}`, `queryClient.setQueryData(['jobs'])` chèn đầu list; điều hướng ngay sang timeline; **trừ tạm UI** số dư = `balance - hold_credits` và bật badge "đang giữ" (lấy `hold_credits` từ `/jobs/estimate` đã cache ở B4).
   - `onError`: rollback list + balance, toast lỗi, giữ user ở B5.
   - `onSuccess`: replace tmpId bằng `job_id` thật, đồng bộ `balance_credits/held_credits` từ response, bắt đầu poll.
- Idempotency: `idempotency_key = uuid` sinh tại onMutate, lưu Zustand để retry không tạo job đôi (`duplicated:true` được xử lý im lặng).

**Skeleton/shimmer + Suspense streaming:**
- Mỗi route có `loading.tsx` (RSC streaming) → khung skeleton dark (`#13131A` base, shimmer sweep `#1E1E29`, gradient `bg-[length:200%] animate-shimmer 1.4s`).
- TanStack `placeholderData: keepPreviousData` → filter Library không nháy trắng.
- Wallet ledger: skeleton rows = số rows ước lượng từ cache trước.

**Toast / inline error motion:**
- `sonner` position `top-center` (mobile) / `bottom-right`. Toast slide+fade `ease [0.22,1,0.36,1]`, auto-dismiss 4s, error 6s + nút "Thử lại".
- Inline form error (wizard): `AnimatePresence` height auto + `x` shake `[0,-6,6,-4,4,0]` 0.3s 1 lần. Field viền `#EF4444`.
- **Refund moment**: khi job `READY`/`FAILED` trả "HOÀN phần thừa" → toast đặc biệt + số dư count-up animation (`useMotionValue` + `animate`) + badge "đang giữ" co về 0 (layout animate). Đây là khoảnh khắc minh bạch (c) — phải nổi bật.

---

## 4) LOADING & POLLING (job timeline)

**TanStack Query polling:**
```ts
useQuery({
  queryKey:['job', id],
  queryFn: () => getJob(id),
  refetchInterval: (q) => {
    const s = q.state.data?.status;
    const TERMINAL = ['READY','QA_FAIL','FAILED','REFUNDED','CANCELLED','WAITING_CONFIG'];
    return TERMINAL.includes(s) ? false : 2500;     // dừng poll ở terminal
  },
  refetchIntervalInBackground: false,                // tab ẩn -> ngừng
});
```
- **Backoff**: nếu N lần liên tiếp lỗi mạng → tăng interval 2.5s→5s→10s (theo `failureCount` trong `refetchInterval`), reset khi thành công. Tránh đập API khi backend chậm.
- List Dashboard/Library: poll **chỉ khi** có ít nhất 1 job non-terminal (`refetchInterval` điều kiện), nếu toàn READY → `false`.

**Timeline stage animation:**
- 7 stage `QUEUED→DIRECTING→IMAGING→RENDERING_VIDEO→VOICING→COMPOSING→QA→READY` render thành vertical stepper.
- Dùng `stage_timings` để vẽ **progress bar có ETA**: width interpolate theo thời gian trung bình mỗi stage (ước lượng), không nhảy giật — `motion.div animate={{width}}` spring nhẹ.
- Stage hiện tại: icon pulse (Lottie hoặc `animate` scale 1↔1.08 loop) + dòng chữ động ("Đang dựng phân cảnh…"). Stage xong: check mark draw-on (`pathLength 0→1`, 0.4s). Stage chưa tới: mờ `opacity 0.35`.
- `QA_FAIL`/`FAILED`: stage đỏ + shake nhẹ + CTA "Hoàn 100% / Tạo lại"; số dư hoàn count-up.
- `events[]` mới về → `AnimatePresence` log lines stagger fade-in (như terminal log điện ảnh), `asset_url` preview thumbnail fade khi `IMAGING` xong.

**SSE drop-in (sau):**
- Trừu tượng hoá qua hook `useJobStream(id)` trả `{job, events}`. v1 implement bằng polling; v2 swap sang `EventSource('/v1/jobs/{id}/stream')` cùng interface → component không đổi. Khi SSE on: vẫn giữ 1 query `staleTime:Infinity` làm cache, SSE push `setQueryData`.

---

## 5) MOTION TOKENS + REDUCED-MOTION + PERF BUDGET

**Durations (ms):**
| token | ms | dùng |
|---|---|---|
| `instant` | 80 | press feedback |
| `fast` | 120 | hover, micro |
| `base` | 200 | toggle, tooltip |
| `medium` | 280 | page-transition, modal |
| `slow` | 450 | scroll-reveal, refund count-up |
| `hero` | 600–900 | canvas fade, morph |

**Easings (cubic-bezier):**
- `ease-out-expo` `[0.16, 1, 0.3, 1]` — enter/reveal (chủ đạo).
- `ease-out-quint` `[0.22, 1, 0.36, 1]` — page/toast.
- `ease-in-out-quart` `[0.76, 0, 0.24, 1]` — wizard slide.
- `ease-standard` `[0.4, 0, 0.2, 1]` — UI chung.
- **Tránh** `linear` (trừ shimmer/aurora flow & infinite loop).

**Spring configs (framer):**
- `snappy` (button/press): `{type:'spring', stiffness:400, damping:25, mass:0.6}`
- `smooth` (layout/drawer): `{stiffness:260, damping:30}`
- `gentle` (badge "đang giữ", number count-up): `{stiffness:120, damping:20}`
- `bouncy` (success refund pop): `{stiffness:300, damping:14}`

Export thành `lib/motion.ts` (`DURATION`, `EASE`, `SPRING`, `variants` dùng chung) — single source of truth.

**Reduced-motion rules (`useReducedMotion()` + CSS media):**
- Tắt: parallax, R3F canvas (không mount), scroll-scrub, stagger (→ đồng loạt), shake, count-up (hiện số cuối ngay), Lenis (dùng native scroll), Lottie loop (freeze frame 1), sheen.
- Giữ: opacity fade ≤150ms, instant state change, focus ring. Nguyên tắc: **chỉ opacity, không transform/loop**.
- Lenis: `if (reducedMotion) không init` → scroll thường.

**Mobile / perf budget:**
- **JS first-load app shell** (không gồm landing 3D): mục tiêu `< 180kb gzip`. Landing route được phép thêm three/gsap ~`+170kb` nhưng **code-split**, sau LCP.
- **LCP < 2.5s**: hero poster là LCP element (priority `<Image>`), canvas/video lazy.
- **Hydration**: dashboard/library dùng RSC tối đa; client island chỉ chỗ cần motion. `LazyMotion` để tránh full framer trên mọi trang.
- **Video**: thumbnail Library = `<video preload="metadata" muted playsInline>` poster trước, chỉ load khi in-view (IntersectionObserver) + hover phát. MP4 H.264 baseline + nguồn AV1/WebM nhỏ hơn.
- **Image**: `next/image`, AVIF/WebP, ảnh sản phẩm upload resize client trước khi gửi.
- **CLS ≈ 0**: skeleton đúng kích thước thật; aspect-ratio box cho mọi video/thumbnail.
- **Lighthouse mục tiêu**: Perf ≥85 (landing chấp nhận ≥75 do WebGL), a11y ≥95.
- **rAF chủ**: 1 Lenis rAF loop điều phối cả ScrollTrigger (`lenis.on('scroll', ScrollTrigger.update)` + `gsap.ticker` lái Lenis) → tránh nhiều loop cạnh tranh.

---

**File gợi ý kết tinh**: `lib/motion.ts` (tokens), `components/motion/` (PageTransition, RevealOnScroll, StaggerGrid, NumberCounter, HoldBadge), `app/(marketing)/_components/HeroCanvas.tsx` (R3F, ssr:false), `hooks/useJobStream.ts` (polling→SSE swap), `hooks/usePrefersReducedMotion.ts`, `providers/LenisProvider.tsx`, `providers/QueryProvider.tsx`.

---

# D. BẢN ĐỒ MÀN HÌNH

Tôi đã có toàn bộ contract API thực tế: pricing (1 credit=150đ, USD→VND 25400, seedance prices, est = image+video+0.01, hold=ceil(est×1.5)), JobStatus enum, LedgerKind, plan limits (free ≤480p/≤20s), voice config (Vbee/Gemini/edge/vieneu), engine routing. Lưu ý quan trọng: engine thực tế hiện chỉ là Seedance (route_video chỉ trả seedance-2-fast/seedance-2) — Veo/Kling/Hailuo là roadmap UI. Tôi sẽ vẽ bản đồ màn hình bám đúng các field/endpoint này.

---

# VIETVID — BẢN ĐỒ MỌI MÀN HÌNH (App Router, dark-only)

## 0. QUY ƯỚC NỀN (áp cho mọi màn)

**Dark-only.** Không light mode (xác nhận: aesthetic "dark cinematic" chốt; bỏ light tiết kiệm 50% QA + đúng tông Kling/Runway/Sora). Token nền 4 lớp: `--bg-0:#07070B` (base) · `--bg-1:#0C0C14` (surface) · `--bg-2:#12121C` (raised card) · `--bg-3:#1A1A28` (popover/menu). Accent gradient **Electric Violet→Blue**: `#7C3AED → #4F46E5 → #2563EB` (dùng cho CTA, ring focus, active nav, progress). Glow: `box-shadow: 0 0 40px -10px #7C3AED55`. Glass: `bg-white/[0.04] backdrop-blur-xl border border-white/[0.08]`. Film-grain: 1 lớp `<div>` noise SVG `opacity-[0.025] mix-blend-overlay fixed inset-0 pointer-events-none`.

**Font** (next/font): `Sora` (display/headings 600-800, hero), `Inter` (body/UI 400-600), `JetBrains Mono` (số credit, job_id, mã giao dịch, ledger delta — tabular-nums). i18n: `vi` mặc định (next-intl, namespace per-route), `en` fallback Product C.

**Routing groups**: `(marketing)` = Landing/Pricing/FAQ (WebGL maximalist, ko sidebar) · `(auth)` = Login/Signup (centered, ko shell) · `(app)` = Dashboard/Wizard/Library/Wallet/Settings/KOL (AppShell + sidebar) · `(admin)` = Admin (M3, role-gated).

| Token chung | Giá trị |
|---|---|
| Credit→video quy đổi hiển thị | 1 credit = 150đ. "1 video product_ad 15s/480p" ≈ est `0.08×15 + 0 + 0.01 = 1.21 USD` → `ceil(1.21×25400/150)=205 credit`. Hiển thị pack bằng "≈ N video" dùng số này. |
| Polling | TanStack Query `refetchInterval: 2500` CHỈ khi job ở `QUEUED/RUNNING` (status không terminal); dừng poll khi `READY/FAILED/QA_FAIL/CANCELLED/REFUNDED`. |
| Số dư | `useWalletStore` (Zustand) hydrate từ `GET /v1/wallet`; mọi POST /jobs trả `balance_credits/held_credits` → cập nhật optimistic. |

---

## 1. GLOBAL SHELL & STATES CHUNG

### AppShell `(app)/layout.tsx`
- **Mục đích**: khung mọi màn app sau đăng nhập; nơi đặt CreditBadge + nav + command palette.
- **Layout**: Sidebar trái glass `w-[248px]` collapse→`72px` (Zustand persist) · Topbar `h-14` glass sticky (breadcrumb trái · search ⌘K giữa · CreditBadge + avatar phải) · `<main>` Lenis smooth-scroll wrapper.
- **Sidebar items** (lucide icon): Dashboard `layout-dashboard` · Tạo video `wand-sparkles` (CTA gradient pill) · Thư viện `clapperboard` · Ví & Hóa đơn `wallet` · KOL Studio `users-round` (badge "M2") · Cài đặt `settings` · [role=owner/admin] Admin `shield`.
- **Component tái dùng**: `<CreditBadge balance held />` (số `JetBrains Mono` + chip "đang giữ {held}" amber `#F59E0B` khi `held>0`, tooltip giải thích 3-khoảnh-khắc) · `<CommandPalette>` (cmdk, ⌘K/Ctrl+K: nav nhanh + "Tạo video mới" + jump tới job theo id + "Nạp credit") · `<MobileNav>` (bottom tab bar 5 icon, sidebar→Sheet).
- **Data**: `GET /v1/auth/me` (1 lần, cache) → role/balance/held; `GET /v1/wallet` (poll 15s + invalidate sau job).
- **Motion**: page-transition `AnimatePresence` fade+`y:8` 180ms; sidebar active item layoutId underline gradient (Framer `layoutId="navGlow"`); CreditBadge số đổi → count-up `useMotionValue` + flash ring khi tăng (nạp tiền) / amber pulse khi held tăng.
- **reduced-motion**: tắt count-up, page-transition→fade-only 80ms.

### States dùng lại (component thư viện `components/states/`)
| State | Component | Hành vi |
|---|---|---|
| Loading list/grid | `<SkeletonGrid>` / `<SkeletonRow>` | shimmer gradient sweep `bg-[linear-gradient(90deg,#12121C,#1A1A28,#12121C)]` 1.4s; KHÔNG spinner cho list. |
| Loading nút | `<Button loading>` | spinner lucide `loader-2` + disable, giữ width. |
| Empty | `<EmptyState icon title desc cta>` | icon glass tròn glow, 1 CTA gradient. Mỗi màn có copy riêng (xem dưới). |
| Error fetch | `<ErrorState onRetry>` | icon `cloud-off`, "Tải lại", show requestId nếu có. |
| 402 hết credit | `<InsufficientCreditsDialog need have>` | parse 402 detail; "Cần X, có Y" + CTA "Nạp credit" → /pricing. |
| Toast | sonner | success violet-glow, error rgb `#EF4444`, info. |
| 401 | interceptor | → `/login?next=`; clear store. |

---

## 2. LANDING — `(marketing)/page.tsx` route `/`

- **Mục đích**: convert khách lạ → signup; phô diễn 2 wedge (giọng Việt thật, minh bạch giá) + chọn engine; aesthetic "wow" để không bị chê AI-slop.
- **Section (thứ tự scroll, Lenis + scroll-driven Framer `useScroll`)**:
  1. **Hero WebGL** — React-Three-Fiber + drei: shader plane (gradient violet→blue noise flow, `EffectComposer` bloom), cursor-reactive parallax (mesh nghiêng theo `pointer`), particle field (drei `Points` ~2k). H1 `Sora 72/800` "Một tấm ảnh sản phẩm. Một video bán hàng. 60 giây." · sub + 2 CTA: "Tạo video miễn phí" (gradient, →signup, nhấn "tặng 300 credit") + "Xem demo giọng" (scroll tới Voice A/B). Trust line "~300 credit free · không cần thẻ".
  2. **Voice A/B blind demo** (WEDGE 1) — 2 card cạnh nhau cùng kịch bản: trái "Giọng robot (TTS generic)" (edge-tts), phải "Giọng VietVid" (Vbee/clone). Nút play ↔ waveform animate (wavesurfer.js), nhãn ẩn (blind) → reveal sau khi nghe; mini-poll "giọng nào thật hơn?". Asset: 2 file mp3 tĩnh `/public/demo/voice-a.mp3` `voice-b.mp3`.
  3. **How-it-works 3 bước** — horizontal scroll pin: ① Tải ảnh + mô tả ② Chọn phong cách/giọng/engine ③ Nhận MP4. Card glass, icon line-art, parallax.
  4. **Engine showcase** — 4 card so sánh (Seedance "rẻ/nháp" · Veo 3.1 "hero" · Kling 3.0 "điện ảnh" · Hailuo "nhanh"): mỗi card loop video mẫu `<video muted loop>` + 3 chỉ số (Chất lượng/Tốc độ/Giá credit) dạng bar gradient. **GHI CHÚ THI CÔNG (quan trọng)**: backend `route_video` hiện CHỈ map Seedance (`seedance-2-fast`/`seedance-2`) → 4 engine là "coming"; card non-Seedance gắn badge "Sớm có" hoặc dùng flag `engineEnabled` từ config để tránh hứa hẹn sai.
  5. **Dải minh bạch giá "3 khoảnh khắc"** (WEDGE 2) — animated stepper ngang: (a) "Ước tính ~X credit TRƯỚC" (b) "Giữ tạm ceil(est×1.5)" với badge "đang giữ" (c) "Thực dùng + HOÀN phần thừa / hoàn 100% nếu lỗi hệ thống". Số minh họa chạy bằng `useInView` count-up, mock 1 job. Đối chiếu autovis "tự trừ tiền".
  6. **Social proof / trust** — logo strip (marquee) · counter "đã tạo N video" · testimonial cards · badge "thanh toán VNPay/Momo/VietQR/USDT".
  7. **Pricing teaser** — 3 pack rút gọn (xem §3 packs) "≈ N video" + "Xem bảng giá" →/pricing.
  8. **FAQ** — accordion (Radix), câu đinh: **"Lỗi có hoàn tiền không?"** → "Lỗi hệ thống hoàn 100% credit; phần est thừa luôn tự hoàn." + "Giọng có tự nhiên không / Engine nào chọn / Có watermark không (gói free có)".
  9. **Footer** — cột Sản phẩm/Giá/API (Product C)/Pháp lý; lang switch vi/en; social.
- **Component tái dùng**: `<GradientButton>`, `<GlassCard>`, `<SectionHeading>`, `<TransparencyStepper>` (tái dùng ở Wizard B4 + Pricing widget), `<VoiceABPlayer>`, `<EngineCompareCard>`, `<CountUp>`.
- **States**: WebGL fail/no-WebGL → fallback `<Image>` poster gradient tĩnh (feature-detect). Lazy: R3F + wavesurfer `dynamic(ssr:false)`; mobile = tắt particle, giảm DPR.
- **Hành động**: signup CTA, play voice, scroll demo, lang switch.
- **Data**: tĩnh (không auth). Có thể `GET /v1/health` cho counter giả-live; pricing teaser từ const FE.
- **Motion**: MAXIMALIST — shader hero, scroll-pin how-it-works, parallax sâu, marquee, count-up. reduced-motion → bỏ shader animate (giữ static frame), bỏ pin (stack dọc).

---

## 3. PRICING / TOP-UP — `(marketing)/pricing` (xem) + `(app)/billing/topup` (nạp khi đã login)

- **Mục đích**: chọn credit pack + nạp qua 4 cổng; nói giá bằng "video" thay vì con số trừu tượng; minh bạch.
- **Layout**: (1) Hero ngắn + toggle "Trả 1 lần / Tháng" (M2) · (2) **Bảng credit-pack** 3-4 card · (3) **Widget ước tính** "Tôi cần bao nhiêu?" · (4) **Chọn cổng thanh toán** (4 tab, UI riêng) · (5) FAQ thanh toán.
- **Credit packs (card)** — mỗi card: tên · giá VND · số credit (`JetBrains Mono`) · **"≈ N video product_ad 15s"** (tính `credit / 205`) + "≈ M video premium 720p" · "credit không hết hạn (M1)" · CTA "Nạp". Gợi ý 4 pack const FE (vd 50k/100k/300k/1tr đ → credit = `vnd/150`). Card "phổ biến" có ring gradient + glow.
- **Widget ước tính**: slider số video/tháng × dropdown loại (Nháp/Chuẩn/Premium) × thời lượng → tính est credit (gọi `POST /v1/jobs/estimate` với mode/purpose/seconds/resolution mẫu, hoặc mirror công thức FE) → "Bạn cần ~X credit/tháng → pack Y". Tái dùng `<TransparencyStepper>` mini.
- **Chọn cổng (4 tab — UI RIÊNG từng cổng)** — backend `payments.provider ∈ vnpay|momo|bank_qr|usdt`:

| Cổng | UI riêng | Flow + state |
|---|---|---|
| **VNPay** | logo VNPay, chọn pack → "Thanh toán qua VNPay" | redirect cổng → callback → poll `payment.status`; state: redirecting → PENDING → SUCCEEDED (toast + count-up balance) |
| **Momo** | logo Momo hồng, QR Momo hoặc deeplink app | tương tự, hiện QR + nút "Mở app Momo" mobile |
| **VietQR (PayOS/SePay)** | **QR bank hiện NGAY** (VietQR image: bank+số TK+amount+nội dung mã đơn) + "Quét bằng app ngân hàng" | **auto cộng credit khi tiền về**: poll `payment.status` 3s, khi `SUCCEEDED` → confetti nhẹ + balance count-up + "Đã cộng X credit". Có copy STK/nội dung + countdown hết hạn QR |
| **USDT/crypto (NOWPayments)** | chọn network (TRC20/ERC20/BEP20), hiện địa chỉ + `crypto_amount` + QR ví | **chờ N xác nhận**: progress "0/N confirmations" (field `payments.confirmations`), state PENDING (chờ block) → SUCCEEDED. Cảnh báo "gửi đúng network", rate_snapshot hiển thị tỉ giá khóa |

- **Component tái dùng**: `<CreditPackCard>`, `<PaymentMethodTabs>`, `<VietQRPanel>` (QR + countdown + auto-poll), `<CryptoPanel>` (confirmations progress), `<EstimateWidget>`.
- **States**: pack-loading skeleton · QR đang sinh (spinner trong khung QR) · QR hết hạn → "Tạo QR mới" · payment PENDING (poll, dot pulse) · FAILED (đỏ + thử lại) · SUCCEEDED (success state, link "Tạo video ngay"). Empty: chưa chọn pack → tab cổng disabled.
- **Hành động**: chọn pack → chọn cổng → tạo payment (POST payment endpoint M2) → poll → balance update.
- **Data**: packs (const FE M1 / `GET /v1/credit-packs` M2) · `POST /v1/payments` (M2) · `GET /v1/payments/{id}` poll · sau success invalidate `GET /v1/wallet`.
- **Motion**: card hover lift+glow; tab switch slide; VietQR "tiền về" = confetti + count-up; crypto confirmations = progress fill gradient. reduced-motion → bỏ confetti, count-up tức thì.

---

## 4. LOGIN / SIGNUP — `(auth)/login` · `(auth)/signup`

- **Mục đích**: đăng nhập/đăng ký, sau đó bootstrap workspace + tặng credit.
- **Layout**: centered glass card `max-w-[420px]` trên nền shader tĩnh (poster hero, KHÔNG R3F để nhanh); logo + tagline; tab Email / nút Google.
- **Signup nhấn quà**: badge "🎁 +300 credit miễn phí khi đăng ký" (số từ `FREE_GRANT_CREDITS`); checkbox điều khoản.
- **Flow**: Supabase Auth (`email+password` / OAuth Google) → có session JWT → **`POST /v1/tenants/bootstrap`** (idempotent: 201 tạo mới + `granted_credits`, 200 nếu đã có) → lưu org_id → redirect `?next` hoặc `/dashboard`. Dev-mode: dùng `POST /v1/dev/token` (chỉ khi `auth_mode=dev`).
- **Component**: `<AuthCard>`, `<GoogleButton>`, `<EmailPasswordForm>` (react-hook-form + zod), `<OtpResend>` (nếu email verify).
- **States**: idle · submitting (button loading) · error (sai mật khẩu/email tồn tại — đỏ inline) · "đang tạo workspace" (sau auth, trước bootstrap: full-screen "Đang dựng không gian làm việc + tặng credit…" với mini-stepper) · success → welcome toast "+300 credit".
- **Data**: Supabase client SDK · `POST /v1/tenants/bootstrap` · sau đó `GET /v1/auth/me`.
- **Motion**: card mount scale+fade; success → credit badge fly-in count 0→300. reduced-motion → fade.

---

## 5. DASHBOARD — `(app)/dashboard`

- **Mục đích**: trang chủ sau login; số dư + giữ tạm rõ ràng, tạo nhanh, theo dõi job đang chạy live.
- **Layout**: (1) Greeting + `<CreditBadge>` lớn (balance + "đang giữ {held}" amber) · (2) **Quick-create** card lớn (ô mô tả nhanh + nút "Tạo video" →wizard prefill, hoặc upload ảnh kéo-thả) · (3) **Rail "Job gần đây" live** (poll) · (4) stat mini (video tháng này / credit đã dùng — từ ledger) · (5) CTA nạp nếu balance thấp.
- **Rail job live**: hàng `<JobRow>` mỗi job: thumbnail/placeholder · kind · **stage badge live** (QUEUED/RUNNING + stage hiện tại từ `stage_timings`/events) · mini progress bar 8 stage · est_credits · thời gian. Click → Video detail. Job `READY` có nút "Xem"/"Tải".
- **Component tái dùng**: `<CreditBadge>` (shell) · `<QuickCreateCard>` · `<JobRow>` + `<StageMiniTimeline>` (tái dùng Library + Wizard B5 + Video detail) · `<StatTile>`.
- **States**: empty (chưa job nào) → `<EmptyState>` "Chưa có video nào — tạo video đầu tiên (đã tặng 300 credit)" CTA gradient · loading → skeleton rows · error → ErrorState · 402-aware (balance 0 → quick-create disable + nudge nạp).
- **Data**: `GET /v1/auth/me` + `GET /v1/wallet` · **`GET /v1/jobs?limit=8`** (poll 2.5s nếu có job non-terminal) · `GET /v1/wallet/ledger?limit` cho stat.
- **Motion**: stage badge pulse khi RUNNING; progress bar fill gradient theo stage; số credit count-up; row enter stagger. reduced-motion → no pulse.

---

## 6. CREATE WIZARD (5 bước) — `(app)/create` — *agent riêng, tóm tắt 1 dòng*

> 5 bước Zustand persist sessionStorage: **B1** nguồn ảnh/mô tả/URL → **B2** phong cách + engine + tỉ lệ (`aspect`) + thời lượng (`seconds`, clamp theo plan) → **B3** giọng (nghe-thử + "đọc thử câu của tôi") → **B4** xem trước với `<TransparencyStepper>` gọi `POST /v1/jobs/estimate` (est/hold/breakdown/clamp_notes) → **B5** `POST /v1/jobs` (idempotency_key) rồi poll `GET /v1/jobs/{id}` vẽ timeline live 8 stage tới READY.

---

## 7. LIBRARY — `(app)/library`

- **Mục đích**: kho video đã tạo; tải MP4 sạch, tạo lại, lọc trạng thái.
- **Layout**: toolbar (filter status chips + search + sort) · **grid `<VideoCard>`** responsive `2/3/4 col` · pagination/infinite (limit 30).
- **VideoCard**: poster/thumbnail (hoặc gradient placeholder) · hover→`<video>` autoplay muted preview · badge status · badge "watermark" (gói free, `has_watermark`) · kind + seconds + resolution + aspect · actions: ▶ xem · ⬇ "Tải MP4" (`GET /v1/jobs/{id}/video`) · ↻ "Tạo lại" (clone params → wizard B4 prefill, idempotency_key mới) · ⋯ (xóa M2).
- **Filter chips** (status): Tất cả · `READY` · `RUNNING/QUEUED` (đang xử lý, poll) · `QA_FAIL` · `FAILED` · `REFUNDED/CANCELLED`. → `GET /v1/jobs?status=`.
- **file_missing**: nếu `has_video=true` nhưng tải trả 404 `file_missing` → badge đỏ "Thiếu file" + nút "Tạo lại" (không tải được).
- **Component tái dùng**: `<VideoCard>` · `<StatusChip>` (tái dùng Dashboard/Wallet) · `<FilterBar>` · `<SkeletonGrid>`.
- **States**: empty ("Chưa có video — Tạo video đầu tiên") · loading skeleton grid · error · filtered-empty ("Không có video {status}"). RUNNING card có overlay mini-timeline + poll.
- **Data**: `GET /v1/jobs?limit=30&status=` (poll 2.5s nếu có item non-terminal) · `has_video` quyết định nút Tải · `GET /v1/jobs/{id}/video` cho download.
- **Motion**: grid stagger reveal; hover lift + video crossfade; status filter = layout animate. reduced-motion → no hover-play, fade only.

---

## 8. VIDEO DETAIL / PLAYER — `(app)/video/[jobId]` (= `(app)/jobs/[id]`)

- **Mục đích**: xem 1 video + chi tiết pipeline + chi phí thực; nơi timeline live của job đang chạy.
- **Layout**: 2 cột — **trái**: player lớn (poster→`<video controls>` từ `/v1/jobs/{id}/video`, 9:16 letterbox), dưới có nút Tải MP4 / Tạo lại / Chia sẻ(M2) · **phải**: panel chi tiết (status, kind, seconds, resolution, aspect, **est_credits vs actual_cost** quy ra credit, breakdown) + **`<StageTimeline>` đầy đủ 8 stage** (QUEUED→DIRECTING→IMAGING→RENDERING_VIDEO→VOICING→COMPOSING→QA→READY) với `stage_timings` (thời gian mỗi stage) + **events list** (`events[]`: stage/event_type/provider/cost_usd/asset_url/detail/created_at — provider cost minh bạch).
- **Khi job chưa READY**: player area = `<StageTimeline>` live (poll 2.5s), mỗi stage có spinner/check, ETA. `QA_FAIL` → banner "QA chưa đạt, đã tính phí thực" + tạo lại. `FAILED+system` → banner "Lỗi hệ thống — đã HOÀN 100% credit" (xanh trấn an) + nút thử lại. `WAITING_CONFIG` → "Thiếu cấu hình".
- **Component tái dùng**: `<VideoPlayer>` · `<StageTimeline>` (full) · `<CostBreakdown>` (est vs actual, hoàn phần thừa — tái dùng từ wizard) · `<EventLog>` · `<StatusChip>`.
- **States**: loading (skeleton player + timeline) · error/404 ("Không tìm thấy job") · file_missing (player thay bằng "Thiếu file, tạo lại") · live (poll). 
- **Data**: **`GET /v1/jobs/{id}`** (detail + events, poll nếu non-terminal) · `GET /v1/jobs/{id}/video`.
- **Motion**: stage check pop khi hoàn thành; cost count-up; player fade-in; READY → confetti nhẹ 1 lần. reduced-motion off.

---

## 9. WALLET / BILLING — `(app)/billing` (tabs: Tổng quan · Sổ cái · Lịch sử nạp)

- **Mục đích**: minh bạch dòng tiền credit — sổ cái + lịch sử nạp; cụ thể hóa wedge minh bạch.
- **Layout**: header `<CreditBadge>` lớn (balance + held + "= ~N video còn lại") + CTA Nạp · 3 tab.
  - **Tổng quan**: 2 KPI (số dư / đang giữ) + chart credit dùng theo ngày (từ ledger SETTLE) + "đang giữ cho job nào" list (HOLD chưa settle).
  - **Sổ cái (ledger timeline)**: bảng/timeline `GET /v1/wallet/ledger` — mỗi row `<LedgerRow>`: icon theo `entry_type` (TOPUP↑xanh · HOLD⏸amber · SETTLE↓ · REFUND↩xanh · BONUS🎁 · ADJUST/EXPIRE) · `delta_credits` (±, mono, màu) · `balance_after` · note · job_id link → video detail · created_at. Filter theo entry_type. Tooltip mô tả 3-khoảnh-khắc cho HOLD/SETTLE/REFUND.
  - **Lịch sử nạp**: payments (provider/amount_vnd/credits_granted/status/confirmations crypto/created_at) — link biên lai.
- **Component tái dùng**: `<CreditBadge>` · `<LedgerRow>` · `<EntryTypeIcon>` · `<UsageChart>` (recharts/visx) · `<PaymentHistoryRow>`.
- **States**: empty ledger ("Chưa có giao dịch — nạp credit để bắt đầu") · loading skeleton rows · error. Held=0 → ẩn block "đang giữ".
- **Data**: `GET /v1/wallet` · **`GET /v1/wallet/ledger?limit=50`** · payments list (M2 `GET /v1/payments`).
- **Motion**: row enter stagger; balance count-up; HOLD row amber pulse khi job đang chạy. reduced-motion → static.

---

## 10. SETTINGS — `(app)/settings` (tabs: Brand kit · Giọng mặc định · API keys · Tài khoản)

- **Mục đích**: cấu hình tái dùng cho wizard + cấp API key cho Product C (B2B).
- **Tabs**:
  - **Brand kit**: logo upload · màu thương hiệu (color picker) · font · CTA mặc định · watermark on/off (gói trả phí). Lưu vào `orgs.settings` / `brand_kits` (M2).
  - **Giọng mặc định**: chọn `voice_gender` + `voice_id` mặc định (kho Vbee nam/nữ từ `vbee_voice_code_male/female`, hoặc engine `gemini/edge/vieneu`) · slider tốc độ (`voice_speed`) · nút nghe-thử (tái dùng player B3). Áp vào wizard B3 làm default.
  - **API keys (Product C) — reveal-once**: tạo key → **hiện ĐÚNG 1 LẦN** (copy, sau đó chỉ còn prefix `vv_live_••••`), list key (tên/prefix/last_used/scope/revoke) · rate-limit/usage. Pattern reveal-once như `dashboard_api_key` kind=secret trong registry. (M3/Product C — gắn badge nếu chưa bật.)
  - **Tài khoản**: email, đổi mật khẩu (Supabase), ngôn ngữ vi/en, đăng xuất, xóa workspace (danger zone).
- **Component tái dùng**: `<SettingsTab>` · `<SecretRevealOnce>` (copy + mask) · `<VoicePicker>` (tái dùng wizard B3) · `<BrandKitForm>` · `<ColorPicker>` · `<DangerZone>`.
- **States**: loading form skeleton · saving (button loading + toast "Đã lưu") · error · key-created modal (reveal-once, cảnh báo "lưu ngay, không hiện lại").
- **Data**: `GET/PATCH org settings` (M2) · voice presets từ config · `POST /v1/api-keys` / `GET` / `DELETE` (Product C).
- **Motion**: tab slide; save → check pop; reveal-once → copy ripple. reduced-motion → fade.

---

## 11. KOL STUDIO (M2) — `(app)/kol`

- **Mục đích**: tạo persona KOL từ 1 ảnh + consent bắt buộc, dùng trong wizard mode `kol_full`.
- **Layout**: list persona đã tạo (grid) + nút "Tạo KOL mới" → form: upload **1 ảnh** (dropzone, crop) · tên · gender · style · `character_sheet` (mô tả persona text — khớp `KolIn`) · **consent block BẮT BUỘC** (checkbox "Tôi có quyền dùng hình ảnh này" + xác nhận không phải người thật/đã được phép) → không tick = disable lưu.
- **Lưu ý**: routing `kol_full` dùng **text persona, KHÔNG gửi ảnh mặt** tới provider (né kiểm duyệt deepfake — xem `routing.py`). UI nói rõ "ảnh chỉ để bạn tham chiếu phong cách; video tạo từ mô tả".
- **Component tái dùng**: `<KolCard>` · `<ImageDropzone>` (tái dùng B1) · `<ConsentGate>` · `<PersonaForm>`.
- **States**: empty ("Chưa có KOL — tạo persona đầu tiên") · loading · consent chưa tick (CTA disabled + lý do) · upload đang xử lý.
- **Data**: `kol_personas` CRUD (M2) · ảnh upload → image_path · feed vào `JobCreateRequest.kol`.
- **Motion**: card reveal, consent gate shake nhẹ nếu bấm lưu khi chưa tick. badge "M2" toàn module.

---

## 12. ADMIN (M3) — `(admin)/admin` (role=owner/admin gate)

- **Mục đích**: vận hành — duyệt video, hoàn credit thủ công, xem job lỗi.
- **Layout**: sidebar admin riêng + tabs: **Hàng đợi duyệt** (video `moderation_status=PENDING/FLAGGED` → Approve/Block) · **Job lỗi** (`FAILED/QA_FAIL`: lý do, provider, cost, retry/refund) · **Hoàn credit** (chọn org/job → REFUND/ADJUST ledger, lý do bắt buộc) · **Payments** (đối soát PENDING/treo, crypto confirmations) · **Tổng quan hệ thống** (jobs/ngày, doanh thu, lỗi rate).
- **Component tái dùng**: `<AdminTable>` (sortable, bulk action) · `<ModerationCard>` (preview video + Approve/Block) · `<RefundDialog>` (delta + note → ledger ADJUST/REFUND) · `<StatusChip>` · `<EventLog>`.
- **States**: empty queue ("Không có gì cần duyệt") · loading table · error · action-confirm (refund cần lý do, double-confirm).
- **Data**: admin endpoints (M3): `GET /admin/jobs?status` · `GET /admin/videos?moderation` · `POST /admin/videos/{id}/moderate` · `POST /admin/orgs/{id}/adjust` (ledger ADJUST/REFUND) · `GET /admin/payments`.
- **Motion**: tối giản/tốc độ; row select highlight; refund success toast. reduced-motion friendly.

---

## 13. GHI CHÚ THI CÔNG QUAN TRỌNG (đối chiếu code thực)

| Điểm | Thực tế trong code | Hệ quả UI |
|---|---|---|
| Engine video | `route_video` chỉ map **Seedance** (`seedance-2-fast` draft/product/kol, `seedance-2` premium). Không có Veo/Kling/Hailuo trong routing. | Engine showcase + B2 chọn engine: chỉ Seedance "live"; 3 engine kia = badge "Sớm có"/flag, KHÔNG để user chọn rồi job fail. |
| `mode` hợp lệ | `product_ad, premium, kol_full, long_narrative, film_recap` (validate). Plan ghi `product_ad/premium/kol_full`. | Wizard chỉ phơi 3 mode chính; long_narrative/film_recap ẩn (internal). |
| Plan limit Free | `free`: ≤20s, ≤480p (clamp + note). | B2 slider thời lượng/độ phân giải clamp theo plan; hiện `clamp_notes` ("→ trần gói") ở B4. |
| Resolution | chỉ `480p/720p/1080p`. Free cap 480p. | Dropdown 3 mức, disable theo plan. |
| Hold | `ceil(est_credits×1.5)`. | Badge "đang giữ" hiển thị đúng `hold_credits` từ estimate/job response. |
| Free grant | `FREE_GRANT_CREDITS=300`. | Mọi nơi nói "300 credit" lấy từ env, không hardcode. |
| Credit giá | `CREDIT_PRICE_VND=150`, `USD_TO_VND=25400`. | Quy đổi "≈ N video" và VND ở Pricing dùng đúng 2 hằng này. |
| Watermark | `Video.has_watermark` default true; bỏ khi gói trả phí. | VideoCard badge "watermark" cho free; `/video` endpoint nói "không watermark cho gói trả phí". |
| Voice | engine: `vbee`(thật) · `gemini` · `edge`(free robot) · `vieneu`(clone local). `voice_gender`+`voice_id` vào `params`. | Voice A/B landing: edge(robot) vs vbee/vieneu(thật). B3 + Settings picker theo kho nam/nữ. |
| Stage pipeline | DB chỉ lưu status enum (QUEUED/RUNNING/QA_FAIL/READY/FAILED/WAITING_CONFIG/REFUNDED/CANCELLED) + `stage_timings` JSONB + `events[].stage`. 8 stage label (DIRECTING…) là **nhãn từ events/stage_timings**, không phải status. | `<StageTimeline>` vẽ 8 stage từ keys của `stage_timings` + events, map vào status thô. |
| Payments | `provider ∈ vnpay\|momo\|bank_qr\|usdt`, có `confirmations`, `rate_snapshot`, `crypto_*`. Endpoint nạp = **M2** (model có, router chưa thấy). | Pricing 4 cổng UI sẵn; gọi endpoint khi M2 lên; VietQR=`bank_qr`. |
| Auth | dual-mode: Supabase JWT hoặc dev-token (`auth_mode()`). `/auth/me` trả `auth_mode`. | Login dùng Supabase; dev fallback `/v1/dev/token`. |

**Files đã đối chiếu**: `c:\Users\NTD\Desktop\vietvid\app_api\schemas.py` · `app_api\routers\{jobs,auth,wallet}.py` · `app_api\pricing.py` · `app_api\jobs.py` · `app_api\config.py` · `app_api\models.py` · `app_api\validate.py` · `video_engine\providers\routing.py` · `config\registry.py`.

---

# E. CREATE WIZARD (lõi) + minh bạch giá + timeline render

Repo là Python backend (video_engine, core). Task chỉ cần đặc tả UX bám API — không cần đọc thêm code. Tôi viết đặc tả ngay.

---

# ĐẶC TẢ UX — CREATE WIZARD 5 BƯỚC + 3 KHOẢNH KHẮC MINH BẠCH + CINEMATIC RENDER TIMELINE

## 0. KHUNG CHUNG (wizard shell — áp cho B1→B5)

**Layout shell**
- Grid 2 cột desktop ≥1024px: **trái 64%** = nội dung bước; **phải 36%** = `SummaryRail` sticky (ảnh khung i2v thu nhỏ + tóm tắt lựa chọn + `CreditBadge` + `EstimateBadge` từ B2 trở đi). Mobile <768px: 1 cột, `SummaryRail` co thành drawer kéo-lên ("Chi tiết & giá") + bottom-bar 64px (nút Tiếp tục + est credit).
- **Stepper trên cùng** (sticky, h-56px): 5 node `Nguồn · Phong cách · Giọng · Xem trước · Tạo`. Node trạng thái: `done` (check, fill gradient violet→blue), `current` (ring glow `0 0 0 3px rgba(124,58,237,.35)`), `todo` (viền `#27272A`, chữ `#71717A`). Click lùi bước done được; tiến chỉ qua nút.
- **Footer nav** (h-72px, `backdrop-blur-xl bg-[#0A0A0F]/80`): trái = `← Quay lại`; phải = `Tiếp tục →` (primary gradient). Phím tắt: `Enter`=tiếp, `Esc`=quay lại, `⌘/Ctrl+Enter` ở B4 = Tạo ngay.

**State store (Zustand, persist `sessionStorage` key `vietvid:wizard`)**
```
source{mode:'upload'|'describe'|'url', images:File[]|UploadedAsset[], frameImagePath, brief, scrapeUrl, productDraft}
style{template, video_engine, format_key, aspect, resolution, seconds}
voice{voice_gender, voice_id, tone, customPreviewText, fallbackConsent:boolean}
preview{scene_prompt(editable), structure_reference, lastEstimate}
meta{idempotency_key(uuid sinh ở B4), currentStep}
```
- `idempotency_key` sinh **1 lần** khi user lần đầu chạm nút Tạo ở B5 (uuid v4), giữ nguyên qua mọi retry/poll → chống double-charge.

**Tokens dùng xuyên suốt (đồng bộ aesthetic đã chốt)**
- Nền lớp: `#08080C` (base) → `#0F0F17` (panel) → `#16161F` (card). Viền `#27272A` (hairline) / `#3F3F46` (hover).
- Accent gradient: `linear-gradient(135deg,#7C3AED 0%,#4F46E5 50%,#2563EB 100%)`. Glow accent `rgba(124,58,237,.45)`.
- Trạng thái: success `#22C55E`, warn/hold `#F59E0B`, error `#EF4444`, info `#38BDF8`.
- Font: heading `Space Grotesk` (next/font), body `Inter`, số tiền/credit `Geist Mono` (tabular-nums). i18n VN mặc định.
- Radius card `16px`, control `12px`. Shadow card `0 8px 32px rgba(0,0,0,.4)`. Film-grain overlay `opacity .04`, `mix-blend-overlay`, tắt khi `prefers-reduced-motion`.
- Motion baseline: Framer Motion `spring{stiffness:260,damping:26}`; page-transition giữa bước = slide-x 24px + fade 180ms; Lenis smooth-scroll trong cột trái; mọi hiệu ứng có nhánh `useReducedMotion()` → chỉ fade opacity.

---

## 1. KHOẢNH KHẮC MINH BẠCH (xương sống — render ở B2/B4/B5)

| Khoảnh khắc | Vị trí | Component | Nguồn API |
|---|---|---|---|
| (a) ƯỚC TÍNH trước tiêu | B2 (realtime) + B4 (chi tiết) | `EstimateBadge` | `POST /jobs/estimate` → `est_credits, est_usd, breakdown, clamp_notes` |
| (b) GIỮ tối đa | B4 (banner) + B5 (chip live) | `HoldBanner` + `CreditBadge[held]` | `estimate.hold_credits` ≈ `ceil(est×1.5)`; xác nhận tại `POST /jobs` → `hold_credits, balance_credits, held_credits` |
| (c) THỰC DÙNG + HOÀN | B5 (kết thúc) | `SettleChip` | `GET /jobs/{id}` `actual_cost_usd` + `/wallet/ledger` entries `HOLD/SETTLE/REFUND` |

**`CreditBadge` (global, góc phải header + trong `SummaryRail`)**
- Layout: `[●] 1.250 cr` + (khi held>0) pill phụ `· đang giữ 12`.
- Số dư khả dụng = `balance_credits` (đã trừ held theo nghiệp vụ ví). Pill "đang giữ" màu `#F59E0B`, có dot pulse 2s khi có job đang chạy; tooltip: *"12 credit đang tạm giữ cho video đang tạo. Hoàn phần thừa khi xong, hoàn 100% nếu lỗi hệ thống."*
- Nguồn: `GET /auth/me` / `GET /wallet` → `{balance_credits, held_credits}`. TanStack Query `staleTime 0` khi có job active, invalidate sau mỗi mốc ledger.
- Motion: số chạy đếm (count-up 400ms, `tabular-nums`); khi held tăng → pill nảy `scale 1→1.12→1`; khi refund về → flash viền `#22C55E` 600ms + `+4 hoàn` bay lên fade.

**`EstimateBadge` (compact ở B2, expanded ở B4)**
- Compact (B2): pill `~8 credit` (~`est_usd` mờ nhỏ bên dưới `≈ 4.000đ`), trạng thái: `loading`=shimmer `~· credit` + skeleton; `stale`=opacity .5 trong lúc refetch; `clamped`=icon ⚠ vàng nếu `clamp_notes` không rỗng.
- Expanded (B4): card mở breakdown **theo stage** map từ `estimate.breakdown` (ví dụ keys: directing/imaging/video/voice/compose) → list `Dựng kịch bản · Tạo ảnh · Render video · Lồng giọng · Ghép & QA` với credit từng phần + bar tỉ lệ (gradient). Dòng tổng `Ước tính ~X credit` đậm. Nếu `clamp_notes`: callout vàng *"Đã điều chỉnh: {note}"* (ví dụ clamp thời lượng/độ phân giải theo gói).
- Debounce gọi estimate **350ms** sau thay đổi; hủy request cũ (AbortController); cache theo hash `{mode,purpose,seconds,resolution,engine}`.

---

## 2. B1 — NGUỒN (ảnh / mô tả / URL)

**Mục đích:** lấy nguyên liệu đầu vào; ảnh đầu tiên = **khung i2v** (`frameImagePath` → map `product.image_path`).

**Layout:** Tabs phân đoạn (segmented) `Tải ảnh · Mô tả · Dán URL`. Dưới là vùng tương ứng. Cột phải `SummaryRail` hiện preview khung i2v + form sản phẩm rút gọn (name/category/price/description → `product{}`).

**Component chính**
- `SourceTabs` (3 tab, underline gradient trượt).
- `ImageDropzone` (multi): drag-drop + click + paste. Grid thumbnail `96px`, ảnh **đầu tiên** có badge gradient `KHUNG i2v` + có thể kéo-thả đổi thứ tự (dnd-kit) để chọn khung. Mỗi thumb: nút xoá (X), progress ring khi upload.
- `DescribePanel`: textarea `brief` (auto-grow, 4→12 dòng) + counter; chips gợi ý nhanh ("Mỹ phẩm", "Đồ ăn", "Thời trang", "Điện tử") prefill category.
- `UrlScrapePanel`: input URL + nút `Lấy thông tin`; sau scrape → đổ ảnh + name/price/description vào form (review trước khi nhận).
- `ProductForm` (luôn hiện, collapse được): `name*`, `category`, `price`, `description`.

**Input / validation**
- Ảnh: jpg/png/webp, ≤10MB/ảnh, ≤8 ảnh; ít nhất 1 ảnh **HOẶC** `brief` ≥20 ký tự (mode describe) **HOẶC** URL scrape thành công. `name` bắt buộc nếu có ảnh (mặc định "Sản phẩm").
- URL: regex http(s), chống SSRF hiển thị (chỉ domain hợp lệ), timeout 15s.
- Nút Tiếp tục `disabled` tới khi điều kiện trên đạt; tooltip lý do.

**Trạng thái**
- *empty*: dropzone illustration (line-art sản phẩm) + "Kéo ảnh vào đây · hoặc dán (⌘V)".
- *loading*: upload → progress ring/thumb; scrape → skeleton form + dòng "Đang đọc trang…".
- *error*: ảnh quá nặng → toast đỏ + viền thumb đỏ; scrape fail → inline *"Không lấy được thông tin từ link này. Thử dán mô tả thủ công?"* + nút chuyển tab Mô tả.
- *disabled*: tab URL khi tổ chức tắt scrape.

**Micro-interaction & motion**
- Dropzone hover/drag-over: viền chuyển `dashed #3F3F46`→ gradient + glow, nền sáng nhẹ, scale 1.01.
- Thumb mới: pop-in `scale .8→1` + blur-up khi ảnh load.
- Badge "KHUNG i2v" trượt theo thumb khi đổi thứ tự (layout animation Framer `layoutId`).

**Copy mẫu (VN)**
- Tiêu đề: *"Bắt đầu từ sản phẩm của bạn"*.
- Sub: *"Tải ảnh sản phẩm — ảnh đầu tiên sẽ là khung hình gốc để AI dựng video (image-to-video)."*
- Empty CTA: *"Kéo & thả ảnh vào đây, hoặc bấm để chọn. Mẹo: ảnh nền sạch, sản phẩm rõ nét cho kết quả đẹp nhất."*

---

## 3. B2 — PHONG CÁCH + ENGINE + TỈ LỆ + THỜI LƯỢNG (realtime estimate)

**Mục đích:** chọn template + **engine video** + format → ra `est_credits` ngay (khoảnh khắc (a)).

**Layout:** 4 nhóm dọc, cuộn Lenis: `Template`, `Engine`, `Tỉ lệ & độ phân giải`, `Thời lượng`. `EstimateBadge` compact **dính** cuối cột (sticky bottom của panel) cập nhật realtime.

**Component chính**
- `TemplateGallery`: card 16:9 video-loop preview (autoplay muted, IntersectionObserver chỉ phát card trong viewport), nhãn `Quảng cáo sản phẩm` / `Premium` / `KOL` → map `mode = product_ad|premium|kol_full`. Card chọn: ring gradient + check.
- `EnginePicker` — **card so sánh** (trọng tâm):

| Engine | Nhãn VN | Chất lượng | Tốc độ | Giá credit (chip) | Khi chọn |
|---|---|---|---|---|---|
| Seedance | "Nháp / Tiết kiệm" | ●●○○ | ⚡⚡⚡ Nhanh | rẻ nhất | gọi estimate |
| Hailuo | "Nhanh cân bằng" | ●●●○ | ⚡⚡⚡ Rất nhanh | thấp | gọi estimate |
| Veo 3.1 | "Hero / Chất nhất" | ●●●● | ⚡⚡ Vừa | cao | gọi estimate |
| Kling 3.0 | "Điện ảnh" | ●●●● | ⚡ Chậm hơn | cao nhất | gọi estimate |

  - Mỗi card: tên + badge ("HERO"/"RẺ"/"NHANH"/"ĐIỆN ẢNH"), 3 thanh đo (Chất lượng·Tốc độ·Giá) dạng dot/bar, dòng `~X credit` **lấy từ estimate per-engine** (gọi estimate cho engine hiện chọn; các engine khác hiển thị est cache/ước lượng tương đối, badge "ước tính"). Card chọn → re-call `/jobs/estimate` với `params.video_engine` mới.
  - Tooltip mỗi card: 1 dòng "khi nào nên dùng" (vd Seedance: *"Thử ý tưởng nhanh, rẻ — chất lượng đủ xem"*).
- `AspectPicker`: chip `9:16 Dọc (TikTok/Reels)` · `1:1 Vuông` · `16:9 Ngang` → set `aspect` + `format_key`. `ResolutionPicker`: `720p · 1080p` (1080p chip phụ "+credit"); nếu gói clamp → estimate trả `clamp_notes`, hiện ⚠.
- `DurationPicker`: chips `15s · 30s · 45s · 60s`, mỗi chip annotate **delta** realtime: `30s · +2 credit` (tính từ chênh estimate so với mốc rẻ nhất). `seconds` clamp theo engine (nếu engine giới hạn → disable chip + tooltip).

**Input / validation**
- Bắt buộc chọn: template + engine + aspect + resolution + seconds (đều có default: product_ad / Hailuo / 9:16 / 720p / 30s).
- Mọi thay đổi → debounce 350ms → `POST /jobs/estimate {mode,purpose:'draft',seconds,resolution}` (purpose lấy theo template; engine vào params nhưng estimate nhận qua model routing).

**Trạng thái**
- *loading* (estimate): `EstimateBadge` shimmer; chip credit từng engine → skeleton dot.
- *error* estimate: badge hiện `Không tính được giá` + nút thử lại; **không** chặn Tiếp tục (dùng est mặc định, cảnh báo).
- *clamped*: chip resolution/seconds bị giới hạn → màu vàng + tooltip note.
- *disabled*: engine không hỗ trợ aspect/seconds nào → card mờ + lý do.

**Micro-interaction & motion**
- Đổi engine: card cũ→mới morph viền (layoutId), `EstimateBadge` số count-up tới giá trị mới + flash màu (tăng=vàng nhẹ, giảm=xanh nhẹ).
- Template video card: hover → play + tilt parallax nhẹ (max 4°), scrim tối ↑.
- Duration chip: chọn → delta credit trượt vào từ phải.

**Copy mẫu (VN)**
- Engine header: *"Chọn động cơ tạo video"* · sub *"Càng đẹp càng tốn credit và lâu hơn — chọn theo mục đích."*
- Estimate compact: *"Ước tính ~{est} credit ({≈đ}) — chưa trừ tiền, chỉ là dự kiến."*

---

## 4. B3 — GIỌNG (Nam/Nữ + tone + nghe-thử + đọc-thử + clone online/offline)

**Mục đích:** chọn giọng Việt thật (wedge #1); cho nghe-thử trước khi tiêu credit.

**Layout:** trên = toggle `Giới tính` (Nam/Nữ) + `Tone`; giữa = `VoiceGrid` list giọng; dưới = `CustomLineTester` ("đọc thử câu của tôi"); banner trạng thái clone server.

**Component chính**
- `GenderTone`: segmented Nam/Nữ → `voice_gender`. `ToneChips`: `Năng lượng · Thân thiện · Sang trọng · Nghiêm túc · Trẻ trung` → `tone` (ảnh hưởng chọn `voice_id` đề xuất).
- `VoiceCard` (mỗi giọng): avatar/waveform, tên ("Minh Anh", "Quốc Bảo"), tag vùng miền (Bắc/Trung/Nam), nút **play** preview (mẫu có sẵn, không tốn credit), badge `GIỌNG THẬT` (vs đối thủ TTS). Chọn → `voice_id`, ring gradient.
- `VoicePreview` (inline trong card): waveform animate khi phát; nút play/pause; cache audio đã nghe.
- `CustomLineTester`: input "Nhập câu muốn nghe thử" (≤120 ký tự) + nút `Đọc thử` → render preview ngắn bằng giọng đang chọn (đánh dấu là preview, không tính vào job). Lưu `customPreviewText`.
- `CloneStatusBanner`: trạng thái dịch vụ giọng-clone:
  - **online**: dot xanh *"Giọng Việt thật (clone) đang hoạt động"*.
  - **offline/degraded**: dot vàng + *"Hệ thống giọng thật đang bận. Bạn có muốn dùng giọng dự phòng (chất lượng vẫn tốt) để không phải chờ?"* + **switch ĐỒNG Ý** `fallbackConsent` (mặc định OFF — chỉ fallback khi user bật) + link "Chờ giọng thật".

**Input / validation**
- Bắt buộc `voice_gender` + `voice_id`. Nếu clone offline và `fallbackConsent=false` → cảnh báo ở B4: *"Giọng thật đang offline, video có thể chờ lâu — hoặc bật giọng dự phòng."* (không chặn, nhưng nổi bật).
- `CustomLineTester`: chặn rỗng; rate-limit 1 preview/3s (chống spam).

**Trạng thái**
- *empty/loading* danh sách giọng: skeleton 4 card + shimmer waveform.
- *loading* preview: nút play → spinner ring; *error* preview: *"Không phát được mẫu, thử giọng khác"*.
- *offline* clone: banner vàng như trên.
- *disabled* "Đọc thử" khi chưa chọn giọng.

**Micro-interaction & motion**
- Waveform: 24 thanh dao động (Framer/keyframes hoặc canvas) đồng bộ play; pause → đứng yên ở vị trí.
- Chọn giọng: card "thở" glow 1 nhịp.
- Banner offline xuất hiện: slide-down + dot pulse vàng.

**Copy mẫu (VN)**
- Header: *"Chọn giọng đọc — giọng Việt thật, không phải robot"*.
- Tester: *"Gõ đúng câu thoại của bạn rồi bấm Đọc thử để nghe trước — miễn phí, không tốn credit."*
- Consent: *"Tôi đồng ý dùng giọng dự phòng nếu giọng thật đang bận"*.

---

## 5. B4 — XEM TRƯỚC (3 khoảnh khắc: estimate chi tiết + HOLD + còn lại) ★

**Mục đích:** chốt kịch bản + trình bày **minh bạch giá** đầy đủ trước khi tiêu.

**Layout:** trái = `ScriptEditor` (kịch bản sửa được) + nút nghe bản thử; phải = khối minh bạch dọc: `EstimateBadge expanded` → `HoldBanner` → `AfterCreateLine`.

**Component chính**
- `ScriptEditor`: textarea giàu (`scene_prompt` editable) chia theo cảnh/câu thoại, hiện cấu trúc từ `structure_reference`. Nút `Tạo lại gợi ý` (re-suggest), `Hoàn tác`. Đếm câu/thời lượng ước tính khớp `seconds`.
- `ListenDraftButton` "Nghe bản thử": ghép preview giọng đã chọn đọc kịch bản hiện tại (preview, không tốn credit hoặc credit preview rất nhỏ nếu backend tính — nêu rõ). Player mini + waveform.
- `EstimateBadge` (expanded, mô tả §1): breakdown theo stage + tổng + clamp_notes. Gọi `/jobs/estimate` lần cuối với thông số chốt (`purpose:'final'` nếu template final).
- **`HoldBanner`** (khoảnh khắc b): card viền vàng nhạt + icon khoá:
  - Dòng 1 đậm: *"Chúng tôi sẽ tạm GIỮ tối đa {hold_credits} credit"* (= `estimate.hold_credits`).
  - Dòng 2: *"Thực dùng thường ~{est_credits}. Phần thừa được HOÀN ngay khi xong. Lỗi hệ thống → hoàn 100%."*
  - Mini sơ đồ: `Giữ {hold} ─▶ Dùng ~{est} ─▶ Hoàn ~{hold−est}` (3 pill nối mũi tên).
- **`AfterCreateLine`** "còn lại sau khi tạo": `Số dư hiện {balance} − giữ {hold} = còn dùng {balance−hold}` (đỏ nếu âm → chặn + link Top-up).

**Input / validation**
- `scene_prompt` không rỗng (đã có default từ structure). Nếu `balance_credits < hold_credits` → nút Tạo `disabled`, hiện CTA *"Nạp thêm credit"* → `/pricing`.
- Re-estimate khi user sửa kịch bản đáng kể (đổi seconds/độ dài) — debounce.

**Trạng thái**
- *loading* nghe bản thử: nút → "Đang tạo bản nghe thử…" + skeleton waveform.
- *loading* estimate cuối: badge shimmer, nút Tạo tạm disable 300ms tránh chốt giá cũ.
- *error* estimate: fallback est + cảnh báo *"Giá có thể chênh nhẹ"* (vẫn cho tạo, hold theo est an toàn).
- *insufficient*: banner đỏ thiếu credit.

**Micro-interaction & motion**
- `HoldBanner` xuất hiện: 3 pill nối tiếp slide-in trái→phải (stagger 80ms), mũi tên vẽ dần (SVG path draw).
- Breakdown bar: width grow từ 0 (stagger theo stage).
- Nút Tạo: idle = gradient + shimmer chạy; hover = glow nở; có hint phím `⌘↵`.

**Copy mẫu (VN)**
- Header: *"Xem trước & xác nhận chi phí"*.
- Hold chính: *"Tạm giữ tối đa {hold} credit — bạn KHÔNG bị trừ luôn. Xong việc, phần thừa hoàn về ví ngay."*
- Trust line nhỏ: *"Minh bạch tuyệt đối: thấy giá trước, giữ có giới hạn, hoàn phần thừa — không tự ý trừ tiền."*
- Nút: *"Tạo video · giữ tối đa {hold} cr"*.

---

## 6. B5 — TẠO (timeline live + idempotency + settle/refund + player) ★

**Mục đích:** chạy job, hiển thị tiến độ điện ảnh, chốt settle minh bạch, giao MP4.

**Flow API**
1. Khi vào B5 (lần đầu) → `POST /jobs {idempotency_key, mode, purpose, seconds, resolution, format_key, product{}, kol?, params{brief,clean_clip,voice_gender,voice_id,video_engine}, scene_prompt, structure_reference}`.
   - Trả `{job_id, status, hold_credits, est_credits, balance_credits, held_credits, duplicated, clamp_notes}`. Lưu `job_id`. Nếu `duplicated=true` (idempotency hit) → dùng job cũ, không tạo mới (toast *"Đang dùng lại video đang tạo, không trừ thêm"*).
2. Poll `GET /jobs/{job_id}` mỗi **2.5s** (TanStack Query `refetchInterval`, dừng khi status ∈ terminal). Đọc `stage_timings`, `events[]`, `actual_cost_usd`, `has_video`, `error`.
3. READY → `GET /jobs/{id}/video` (mp4, không watermark gói trả phí) vào player.

**Component chính**
- **`CinematicRenderTimeline`** (đặc tả §7) — KHÔNG phải spinner.
- `LiveCreditChip` (khoảnh khắc c): trong lúc chạy `đang giữ {hold_credits}`; khi READY/settle (đọc ledger `HOLD→SETTLE→REFUND`) → đổi `giữ {hold} → dùng {actual} · hoàn {hold−actual}` với animation. `CreditBadge` global đồng bộ (held giảm, balance tăng phần hoàn).
- `StagePreviewStrip`: khi `events[].asset_url` xuất hiện (ví dụ ảnh từ IMAGING, clip nháp từ RENDERING_VIDEO) → hiện thumbnail/clip preview cuộn ngang, blur-up.
- `ReadyPlayer`: video player (poster = frame i2v), nút **`Tải MP4 (không watermark)`** → `/jobs/{id}/video`, `Tạo lại`, `Chia sẻ`, `Lưu vào Library`.
- `ErrorPanel`: nếu `FAILED/QA_FAIL` → thông báo + *"Đã hoàn 100% credit"* (đọc ledger REFUND) + nút `Thử lại` (idempotency_key MỚI). `WAITING_CONFIG` → CTA chỉnh cấu hình. `CANCELLED/REFUNDED` xử lý tương ứng.

**Idempotency / chống double-charge**
- `idempotency_key` (uuid) sinh 1 lần, gửi kèm POST; mọi retry mạng dùng lại key → backend trả `duplicated=true` cùng `job_id`. UI **khoá nút Tạo** sau lần bấm đầu (chuyển sang trạng thái "Đang khởi tạo…"). Nếu reload trang giữa chừng: store còn `job_id` → vào thẳng poll, không POST lại.

**Trạng thái**
- *creating* (chờ POST trả): full-screen subtle → timeline skeleton + "Đang khởi tạo phiên tạo video…".
- *running*: timeline theo stage hiện tại từ `status`/`stage_timings`.
- *error*: `ErrorPanel` + refund notice; *terminal-ready*: player.
- *duplicated*: toast + tiếp tục poll job cũ.
- *poll error/timeout*: giữ trạng thái cuối + banner *"Mất kết nối, đang thử lại…"* (exponential backoff, không spam).

**Micro-interaction & motion**
- Chuyển stage: node sáng lên, đường nối "chảy" gradient (animated dash), camera nhẹ ken vào stage active.
- Settle: `LiveCreditChip` morph số (count-down dùng / count-up hoàn) + confetti-mảnh tối giản (tắt khi reduced-motion).
- READY: timeline thu gọn thành thanh "đã hoàn tất" + player fade-in scale.

**Copy mẫu (VN)**
- Đang chạy: *"AI đang dựng video của bạn… (~60 giây)"*.
- Settle: *"Giữ {hold} → thực dùng {actual} · đã HOÀN {hold−actual} credit về ví."*
- Lỗi: *"Có lỗi hệ thống khi tạo video. Chúng tôi đã HOÀN 100% credit. Bạn thử lại nhé?"*
- READY: *"Video đã sẵn sàng 🎬 — tải MP4 không watermark."*

---

## 7. CINEMATIC RENDER TIMELINE (chi tiết hình ảnh hoá)

**Ý tưởng:** "cuộn phim / dây chuyền điện ảnh" nằm ngang (desktop) / dọc (mobile), mỗi STAGE = 1 node có icon + nhãn VN + animation riêng; đường nối là "dải film" chảy sáng. Dữ liệu từ `status` + `stage_timings` (mốc thời gian từng stage) + `events[]` (asset preview).

**Map STAGE → nhãn VN + icon (lucide) + motion + preview**

| STAGE (API) | Nhãn VN | Icon | Animation node | Asset preview |
|---|---|---|---|---|
| QUEUED | Đang xếp hàng | `ListOrdered` | dot nhịp chờ | – |
| DIRECTING | Dựng kịch bản | `Clapperboard` | clapper "đập" 1 nhịp khi active; chữ kịch bản gõ-máy | – |
| IMAGING | Tạo hình ảnh | `ImagePlus` | khung ảnh blur→sharp | thumbnail ảnh (events.asset_url) |
| RENDERING_VIDEO | Render video | `Clapperboard`/`Film` | cuộn film chạy + grain | clip nháp loop (asset_url) |
| VOICING | Lồng giọng Việt | `Mic` | waveform chạy theo nhịp | audio scrubber preview |
| COMPOSING | Ghép & dựng | `Layers` | các lớp trượt chồng | – |
| QA | Kiểm tra chất lượng | `ShieldCheck` | quét tia ngang | – |
| READY | Hoàn tất | `CheckCircle2` | bùng glow xanh + tick vẽ | video final |
| QA_FAIL | QA chưa đạt | `AlertTriangle` | rung nhẹ vàng | – |
| FAILED | Lỗi | `XCircle` | đỏ + hoàn credit | – |
| WAITING_CONFIG | Chờ cấu hình | `Settings2` | xoay chậm | – |
| REFUNDED/CANCELLED | Đã hoàn/Huỷ | `RotateCcw` | – | – |

**Trạng thái mỗi node**
- `pending`: icon `#52525B`, viền hairline, mờ.
- `active`: ring glow gradient + icon trắng + nhãn sáng + sub "đang xử lý…" + **progress trong stage** ước lượng từ `stage_timings` (thời gian trôi / trung bình stage). Đường nối tới node tiếp = animated dashed flow.
- `done`: icon gradient fill + check nhỏ + thời gian thực `(3.2s)` từ `stage_timings`.
- `failed`: đỏ; các node sau mờ.

**Layout & hành vi**
- Desktop: 8 node ngang, đường nối "film strip" có lỗ phim (perforation) chạy. Node active auto-center (scroll/translate). Trên cùng: thanh tổng tiến độ `% = stage index hoàn tất` + `LiveCreditChip`.
- Mobile: dọc, mỗi node 1 dòng + đường nối dọc; node active phình to + preview ngay dưới.
- `StagePreviewStrip` dưới timeline: gom mọi `events.asset_url` đã có (ảnh IMAGING, clip nháp) → cuộn ngang, click phóng to (lightbox). Blur-up khi load.

**Motion**
- Đường nối: gradient `violet→blue` chạy theo hướng (CSS `background-position` animate hoặc SVG `stroke-dashoffset`).
- Active node: `Clapperboard`/waveform animation tương ứng stage (Framer keyframes / Lottie nhẹ). Film-grain overlay trên cả timeline (tắt reduced-motion).
- Chuyển node: cũ→done check pop, mới→active glow nở (spring).
- READY: toàn timeline "sáng dồn" từ trái sang phải (wave) rồi player xuất hiện.
- Reduced-motion: bỏ chảy/rung/grain → chỉ đổi màu + check tĩnh; vẫn cập nhật trạng thái rõ ràng.

**Empty/edge**
- Trước khi có `stage_timings`: tất cả node `pending` + node QUEUED active dot-nhịp.
- Mất poll: giữ node cuối, badge "đang đồng bộ…".
- Stage không có trong timings (skip): đánh dấu done mờ "(bỏ qua)".

---

## 8. BẢNG ÁNH XẠ API → UI (tóm tắt để thi công)

| UI element | Endpoint / field |
|---|---|
| `CreditBadge` balance/held | `GET /auth/me`, `GET /wallet` → `balance_credits, held_credits` |
| `EstimateBadge` compact/expanded | `POST /jobs/estimate` → `est_credits, est_usd, hold_credits, breakdown, clamp_notes, model_id, resolution` |
| Engine card giá realtime | re-call `/jobs/estimate` đổi `params.video_engine` (qua routing model) |
| Duration delta "+2 credit" | chênh `est_credits` giữa các `seconds` |
| `HoldBanner` | `estimate.hold_credits` ≈ `ceil(est×1.5)`; xác nhận `POST /jobs.hold_credits` |
| POST job | `POST /jobs {idempotency_key, mode, purpose, seconds, resolution, format_key, product, kol?, params{brief,clean_clip,voice_gender,voice_id,video_engine}, scene_prompt, structure_reference}` → `job_id, duplicated, hold_credits, balance_credits, held_credits, clamp_notes` |
| `CinematicRenderTimeline` | `GET /jobs/{id}` → `status, stage_timings, events[], has_video, error` (poll 2.5s) |
| `StagePreviewStrip` | `events[].asset_url` (per stage/provider) |
| `LiveCreditChip` settle | `actual_cost_usd` + `/wallet/ledger` `HOLD/SETTLE/REFUND` |
| `ReadyPlayer` / Tải MP4 | `GET /jobs/{id}/video` |
| Lịch sử / Library | `GET /jobs?limit&status` → `items[]` |

---

**File liên quan (repo backend Python, để FE bám đúng schema khi build):** `c:\Users\NTD\Desktop\vietvid\video_engine\pipeline.py`, `c:\Users\NTD\Desktop\vietvid\video_engine\worker.py`, `c:\Users\NTD\Desktop\vietvid\video_engine\providers\ledger.py`, `c:\Users\NTD\Desktop\vietvid\video_engine\providers\routing.py` (engine routing/model_id cho EnginePicker), `c:\Users\NTD\Desktop\vietvid\video_engine\voice\` (TTS/clone cho VoicePreview & CloneStatusBanner). Lưu ý: repo hiện chỉ có backend, chưa có FE Next.js — toàn bộ component trên là spec để dựng mới.

---

# F. SIGNATURE MOMENTS (tương tác đáng nhớ)

Đây là nhiệm vụ thiết kế thuần túy (signature moments) cho VietVid. Không cần đọc codebase hay chạy tool nào — tôi sẽ trả về trực tiếp bản thiết kế đậm đặc thông tin.

# VIETVID — 9 SIGNATURE MOMENTS

Stack giả định trong mọi mô tả: R3F/drei (hero WebGL), Framer Motion 11, Lenis 1.x, GSAP ScrollTrigger (scroll-driven), Web Audio API (visualize voice), TanStack Query (poll job 2.5s), Zustand. Tokens: `--bg #0A0A0F` → `#06060A`; accent gradient `#7C3AED` (electric violet) → `#3B82F6` (blue); glow `#A855F7`; hold/amber `#F59E0B`; success `#10B981`; refund/green-mint `#34D399`; danger `#EF4444`. Font: display `Clash Display` / `Cabinet Grotesk`, body `Inter` (hoặc `Be Vietnam Pro` cho tiếng Việt rõ dấu), mono `Geist Mono` (số credit/ledger). Mọi moment có `prefers-reduced-motion` fallback + mobile spec.

---

## 1. "Đoán Giọng" — Voice A/B Blind Duel (hero)
**Màn:** Landing hero (section 2, ngay dưới fold).
**Tương tác + motion:**
- Hai card kính (glassmorphism, `backdrop-blur-xl`, border `1px rgba(168,85,247,.18)`) tên ẩn danh **Giọng A** / **Giọng B**, cùng 1 kịch bản bán hàng ("Da bạn sẽ căng mướt sau 7 ngày…"). Một là TTS robot generic, một là VietVid voice-clone.
- Khi play: Web Audio `AnalyserNode` (FFT 256) đẩy **waveform/bars** real-time vào card đang phát; card kia dim `opacity .45 + grayscale`. Bars dùng gradient accent, height lerp bằng `requestAnimationFrame`.
- User bấm **"Cái nào là người thật?"** → reveal: card đúng (VietVid) nở `scale 1→1.04`, spring `stiffness 260 damping 20`, viền chạy **gradient shimmer** + confetti-grain nhẹ; card robot hiện nhãn đỏ "TTS generic — nghe là biết máy". Đoán sai → micro-shake `x:[-6,6,-4,4,0]` rồi vẫn reveal.
- Counter xã hội: "**87% người Việt phân biệt được** — bạn thì sao?" đếm lên bằng `useSpring`.
**Bán wedge:** Đây là **proof-by-ear**, không nói suông "giọng thật". Biến claim thành trải nghiệm 8 giây không thể chối. Bắt đúng nỗi đau "TTS robot" của đối thủ.
**Độ khó:** med. **Lib:** Web Audio API (native) + Framer Motion + `canvas-confetti` (grain mode). Reduced-motion: bỏ bars-animation, vẫn play audio + reveal tĩnh. Mobile: stack dọc, 1 nút play dùng chung toggle A/B.

---

## 2. "Đồng Hồ Nhiên Liệu Credit" — Hold Meter (wizard B4 + global badge)
**Màn:** Wizard B4 "Xem trước" (3 khoảnh khắc minh bạch) + badge thu nhỏ cạnh số dư ở mọi màn.
**Tương tác + motion:**
- Một **gauge bán nguyệt** (SVG arc, `stroke-dasharray` animate) như đồng hồ xăng, 3 trạng thái chạy nối tiếp:
  1. **Ước tính** — kim chỉ "~X credit", segment violet mờ pulse nhẹ.
  2. **GIỮ** — khi tạo job, segment **amber `#F59E0B`** đổ đầy tới `ceil(est×1.5)`, badge "đang giữ N" nảy vào cạnh số dư (`layoutId` shared → bay từ gauge lên header).
  3. **Hoàn** — job xong, phần thừa **rút ngược** về ví, tia green-mint `#34D399` chạy từ gauge → số dư, số dư `count-up` bằng `useSpring`.
- Tooltip ròng rọc: hover từng segment hiện đúng con số từ `/jobs/estimate` (`est_credits`, `hold_credits`) và `clamp_notes`.
**Bán wedge:** Hiện hình hóa **"3 khoảnh khắc minh bạch giá"** — đập thẳng vào lời chê autovis "tự trừ tiền". User *thấy* tiền được giữ rồi *thấy* hoàn, không phải đọc chữ.
**Độ khó:** med. **Lib:** Framer Motion (`layoutId`, `useSpring`) + SVG arc thủ công. Dữ liệu thật từ `estimate.hold_credits` + ledger `HOLD/SETTLE/REFUND`. Reduced-motion: gauge nhảy thẳng tới giá trị, không pulse. Mobile: gauge nhỏ hơn, badge luôn hiện ở app-bar.

---

## 3. "Phòng Dựng Phim Trực Tiếp" — Cinematic Render Timeline (wizard B5)
**Màn:** Wizard B5 "Tạo" (sau khi POST /jobs, poll /jobs/{id} 2.5s).
**Tương tác + motion:**
- Timeline ngang dạng **dải film strip** (perforations 2 bên), 7 stage: QUEUED → DIRECTING → IMAGING → RENDERING_VIDEO → VOICING → COMPOSING → QA → READY. Mỗi stage là 1 ô; ô đang chạy có **shimmer sweep** + spinner, ô xong **đóng dấu tick** (spring pop).
- **Tận dụng asset thật:** mỗi khi `events[].asset_url` xuất hiện (ví dụ IMAGING trả keyframe, RENDERING trả clip nháp) → thumbnail **fade+slide** vào ô đó như "rush footage" về phòng dựng. Stage VOICING hiện mini-waveform của giọng vừa render.
- Thanh tiến độ tổng tính từ `stage_timings` (đã có ms từng stage) → ETA "~còn 28s" đếm ngược thật.
- Khi READY: cả strip **dồn lại thành 1 frame**, poster video bung ra `scale + glow`, nút "Tải MP4 / Tạo lại".
**Bán wedge:** Biến 60s chờ thành **show**, chống bounce. "Xem phim của bạn đang được dựng" — cảm giác cao cấp như Kling/Runway, không phải spinner trống. Tận dụng `stage_timings` + `events.asset_url` có sẵn.
**Độ khó:** high. **Lib:** Framer Motion + TanStack Query polling + `layoutId` cho dồn-frame. Reduced-motion: bỏ shimmer/slide, chỉ đổi màu stage + tick. Mobile: strip cuộn ngang snap, stage active auto-center.

---

## 4. "Chọn Ống Kính" — Engine Comparison Lens Rack (wizard B2)
**Màn:** Wizard B2 "Phong cách + Engine".
**Tương tác + motion:**
- 4 engine (Seedance · Veo 3.1 · Kling 3.0 · Hailuo) là 4 **card-ống-kính** xếp như giá lens. Mỗi card mặt trước là vòng lens (radial gradient, glass), khắc 3 chỉ số: **Chất lượng · Tốc độ · Giá credit** (3 mini-bar).
- Hover/focus: card **tilt 3D** theo con trỏ (`rotateX/rotateY` từ pointer, `transform-style preserve-3d`), glow viền sáng lên, hiện loop preview 2s của engine đó (muted, autoplay).
- Chọn: lens "lắp vào" — `layoutId` bay lên slot "Đang dùng", các card khác lùi & dim. Đổi engine → con số credit ở gauge (Moment 2) và est ở B4 **cập nhật live** (gọi lại `/jobs/estimate`).
- Toggle so sánh: kéo 2 card cạnh nhau → **split-screen video** cùng prompt (nếu có sample), divider kéo được.
**Bán wedge:** Khác biệt "chọn được engine" thành ẩn dụ nhiếp ảnh sang trọng. User hiểu ngay rẻ/nháp (Seedance) vs hero (Veo) vs điện ảnh (Kling) — và **giá credit gắn liền lựa chọn** (nối thẳng wedge minh bạch).
**Độ khó:** med-high. **Lib:** Framer Motion (tilt + layoutId) hoặc `react-parallax-tilt`; video preview lazy. Reduced-motion: bỏ tilt/parallax, vẫn đổi card + preview tĩnh poster. Mobile: carousel snap, tap để lật mặt sau xem chỉ số.

---

## 5. "Ảnh Hóa Thành Phim" — Product → Video Morph (hero WebGL)
**Màn:** Landing hero (above the fold, R3F canvas).
**Tương tác + motion:**
- Một ảnh sản phẩm tĩnh (chai serum / giày) trôi giữa hero. **Cursor-reactive shader**: con trỏ như "đèn quay phim" — di tới đâu ảnh **bóc khỏi nền 2D, dựng parallax depth**, particle bay quanh, rồi morph thành **clip đang chuyển động** (dùng displacement/`dissolve` shader trên RTF plane, frame-blend giữa ảnh và video texture).
- Scroll-driven (Lenis + ScrollTrigger): cuộn xuống → ảnh "1 frame" kéo dài thành **timeline nhiều frame**, headline "**1 ảnh → phim bán hàng 60s**" reveal theo.
- Film-grain shader overlay nhẹ toàn hero, vignette điện ảnh.
**Bán wedge:** Dựng đúng **core promise** (1 ảnh + prompt → video ~60s) thành hình ảnh đầu tiên user thấy. Tông Sora/Kling, chống cảm giác "template rẻ tiền / AI-slop".
**Độ khó:** high. **Lib:** React-Three-Fiber + drei (`shaderMaterial`, `useTexture`), Lenis + GSAP ScrollTrigger. Reduced-motion / low-GPU: thay bằng **video loop poster** + cross-fade CSS (detect `navigator.hardwareConcurrency` + `prefers-reduced-motion`). Mobile: tắt shader nặng, dùng pre-rendered loop + parallax CSS nhẹ.

---

## 6. "Biên Lai Minh Bạch" — Living Ledger Receipt (Wallet/Billing)
**Màn:** Wallet/Billing (ledger từ `/wallet/ledger`).
**Tương tác + motion:**
- Ledger render như **cuộn biên lai giấy nhiệt** (mono font, đường răng cưa mép). Mỗi entry trượt vào theo scroll (Lenis), màu theo `entry_type`: TOPUP/BONUS xanh, HOLD amber, SETTLE trắng, REFUND green-mint với mũi tên ↩.
- **Kết nối nhân-quả:** hover 1 job → mọi entry cùng `job_id` (HOLD → SETTLE → REFUND) **sáng lên và nối bằng đường gân** (SVG path draw), cho thấy "giữ 90 → dùng 62 → hoàn 28". `balance_after` chạy như sổ cái thật.
- Lọc nhanh chip: "Chỉ hoàn tiền" → các REFUND nảy lên, tổng "**Bạn đã được hoàn N credit**" count-up — biến minh bạch thành điểm tự hào.
- Mỗi REFUND có dòng nhỏ "hoàn phần thừa" / "hoàn 100% lỗi hệ thống" lấy từ `note`.
**Bán wedge:** Bằng chứng **không bao giờ âm thầm trừ tiền** — đối lập trực tiếp autovis. Ledger thật biến thành tài liệu marketing sống.
**Độ khó:** low-med. **Lib:** Framer Motion (`AnimatePresence`, stagger) + SVG path-draw nối entry. Dữ liệu 100% thật từ ledger. Reduced-motion: bỏ slide, giữ highlight tĩnh. Mobile: card-list dọc, tap job để nối highlight.

---

## 7. "Đọc Thử Câu Của Tôi" — Live Voice Try-On (wizard B3)
**Màn:** Wizard B3 "Giọng".
**Tương tác + motion:**
- Lưới **giọng** (nam/nữ, vùng miền). Mỗi chip giọng có **mini-waveform tĩnh**; hover → autoplay 2s sample, waveform **sống dậy** (Web Audio analyser).
- Ô input "**Gõ câu của bạn**" + nút "Đọc thử" → render TTS/clone câu user nhập, **cùng 1 câu phát lần lượt 2-3 giọng** để so sánh trực tiếp; giọng đang nghe có **ring pulse** + bars.
- Chọn giọng: chip **lật** hiện meta (tông: ấm/trẻ/quyền lực), `layoutId` bay vào ô "Giọng đã chọn" của B4 preview.
- Micro-detail: nút play hình **sóng âm** morph thành pause (`pathLength` Framer Motion).
**Bán wedge:** Hạ gục hoài nghi "giọng có hợp brand tôi không?" bằng **chính câu của user, chính giọng thật**. Wedge giọng Việt được kiểm chứng tại điểm quyết định.
**Độ khó:** med. **Lib:** Web Audio API + Framer Motion (`layoutId`, `pathLength`) + TanStack Query (gọi render-preview). Reduced-motion: waveform tĩnh, vẫn play. Mobile: list dọc, swipe để duyệt nhanh, 1 player sticky đáy.

---

## 8. "Mở Khóa 300 Credit" — First-Run Reveal (post-signup → Dashboard)
**Màn:** Sau `/tenants/bootstrap` (lần đầu), overlay trên Dashboard.
**Tương tác + motion:**
- Modal kính tối: con số `granted_credits` (~300) **đổ vào ví** — coin/spark particles bay theo cung vào badge số dư, `count-up` 0→300 (`useSpring`, ease-out), glow violet→blue quét qua.
- Sau đó **3 thẻ "khoảnh khắc minh bạch"** lật ra tuần tự (ước tính → giữ → hoàn) như onboarding 1 màn, nút "Tạo video đầu tiên" pulse gọi hành động.
- Confetti-grain (không kẹo sến — hạt film, tông tím/xanh).
**Bán wedge:** Khoảnh khắc "aha" tặng tiền + dạy luôn **mô hình minh bạch giá** ngay giây đầu, set expectation đúng trước khi user tiêu credit đầu tiên.
**Độ khó:** low. **Lib:** Framer Motion + `useSpring` + `canvas-confetti`. Dữ liệu thật từ bootstrap `granted_credits`. Reduced-motion: count-up nhanh, bỏ particle. Mobile: full-screen sheet.

---

## 9. "Lật Trang Phim" — Library Hover Reel + Page Transition (Library)
**Màn:** Library (grid video) + chuyển trang toàn app.
**Tương tác + motion:**
- Grid video: hover card → **scrub preview** (video seek theo vị trí chuột ngang, như thước phim), poster→motion cross-fade, badge engine + thời lượng + credit-thực-dùng hiện lên glass.
- Card có **shimmer skeleton** lúc load (shimmer chạy chéo gradient violet).
- **Page-transition toàn app:** dùng `layoutId` chia sẻ — click 1 video → poster **bay & phình** thành player ở trang detail (shared-element transition), nền **dim + push** mượt qua Framer Motion `AnimatePresence`. Toàn app cuộn bằng Lenis, micro-parallax đầu trang.
- Nút "Tạo lại" trên mỗi card → bay thẳng vào Wizard với params cũ điền sẵn (`layoutId` nối card → wizard hero).
**Bán wedge:** Cảm giác **video-first, cao cấp, mượt** ở khu vực user quay lại nhiều nhất; "credit thực dùng" hiện trên mỗi card tái khẳng định minh bạch. Chống "tĩnh & chán".
**Độ khó:** med. **Lib:** Framer Motion (shared `layoutId`, `AnimatePresence`) + Lenis + native video seek. Reduced-motion: bỏ scrub/parallax, cross-fade tĩnh + cut transition. Mobile: tap-to-preview, transition rút gọn (fade thay shared-element nếu lag).

---

## Ưu tiên thi công (impact ÷ effort)
| Ưu tiên | Moment | Lý do | Effort |
|---|---|---|---|
| P0 | #1 Voice A/B Duel | bán wedge giọng ngay hero, viral | med |
| P0 | #2 Hold Meter | wedge minh bạch, dùng global | med |
| P0 | #3 Render Timeline | chống bounce 60s, dùng asset thật | high |
| P1 | #6 Ledger Receipt | data sẵn, effort thấp, proof mạnh | low-med |
| P1 | #4 Lens Rack | differentiator engine | med-high |
| P1 | #7 Voice Try-On | chốt deal tại B3 | med |
| P2 | #5 Hero Morph | WOW factor, nặng GPU | high |
| P2 | #8 300-Credit Reveal | onboarding aha, rẻ | low |
| P2 | #9 Library Reel | polish giữ chân | med |

**Sợi chỉ xuyên suốt (để human-crafted, không AI-slop):** mọi moment phản chiếu **một trong hai wedge**, dùng **chung 1 ngôn ngữ "phim"** (lens/frame/film-strip/grain/receipt) và **chung shared-element `layoutId`** giữa các màn — tạo cảm giác một thế giới liền mạch, không phải các trang rời rạc. Số liệu credit ở Moment 1/2/4/6/8 luôn kéo từ API thật (`estimate`, `wallet/ledger`, `bootstrap`) nên minh bạch là *thật*, không phải animation trang trí.