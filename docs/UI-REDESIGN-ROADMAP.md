# VYRA — ROADMAP NÂNG CẤP UI/UX TOÀN DIỆN (100% màn hình)

> Lộ trình "đập đi nâng cấp" toàn bộ giao diện Vyra lên chuẩn vượt autovis/Kling, giữ bản sắc riêng (chống generic AI), thành một **studio edit video**. Cần chủ dự án duyệt trước khi thực thi.
> Liên quan: [VISION.md](VISION.md) · [UI-UPGRADE-BLUEPRINT.md](UI-UPGRADE-BLUEPRINT.md) · [design-systems/vyra/DESIGN.md](../design-systems/vyra/DESIGN.md).

## 1. Nguyên tắc CHỐNG GENERIC (cốt lõi)

Vấn đề: web AI làm ra "đại trà, cùng 1 style" = nền tối + gradient tím + 3 thẻ kính căn giữa + Lucide + spinner. Vyra **không** được như thế. Giải pháp = một **bản sắc sở hữu được**:

**"Director's Studio" — giao diện như phòng dựng phim của đạo diễn, không phải SaaS dashboard:**
- **Khung ngắm (viewfinder) + nhãn slate phim** (● REC · TAKE · SCENE · CUT) — motif điện ảnh xuyên suốt (đã có `cinematic.tsx`).
- **Motif timeline/scrubber**: bước wizard = dải timeline phim; tiến trình = thước phim; hover thẻ video = **scrub** (tua) thật.
- **Hero full-bleed điện ảnh** + Ken-Burns, ảnh **thật sinh bằng fal** (đã có 10 ảnh showcase) — không stock, không picsum.
- **Bố cục bất đối xứng / bento** (VARIANCE 7-8), KHÔNG hàng-3-thẻ-căn-giữa.
- **Typography editorial** (chất gpt-taste): tiêu đề cỡ lớn Be Vietnam Pro, tracking chặt, từ-khoá nghiêng-gradient; số dùng Space Grotesk.
- **1 accent/màn** (7 màu) = mỗi màn là một "phòng" trong studio.
- **Copy trung thực, cụ thể** — không sáo AI, không số bịa.

→ Khác autovis: họ cũng dùng metaphor phim nhưng kèm **số bịa** ("5.000+ KOL", "triệu view") + ảnh bóng nhựa. Ta làm **tinh hơn + trung thực + tao nhã**. Cho phép học layout đối thủ (lưới content-type card, format reel, scene-preset grid) nhưng nâng cấp chất liệu/motion/typography.

## 2. Loading · Chuyển cảnh · Lazy-load (bắt buộc, làm thành hệ thống dùng chung)

| Hạng mục | Cách làm (Next.js App Router + framer-motion, KHÔNG đổi stack) |
|---|---|
| **Chuyển màn (route transition)** | `app/template.tsx` + `app/app/template.tsx` bọc `AnimatePresence` → hiệu ứng "cut phim" (fade + scale/slide nhẹ ~250ms, easing chữ ký). Template re-mount mỗi lần điều hướng → chuyển cảnh mượt. |
| **Loading từng màn** | `loading.tsx` mỗi route segment → **skeleton khớp layout** (không spinner tròn), tận dụng streaming của App Router. |
| **Thanh tiến trình điều hướng** | Top progress bar mảnh (kiểu nprogress) khi đổi route — cảm giác "đang dựng". |
| **Splash khởi động** | Logo Vyra vẽ-dần (đã có `.vyra-orbit/.vyra-stroke/.vyra-node` trong globals.css). |
| **Lazy-load** | `next/dynamic` cho component nặng/dưới màn (chart Reports, player Video-detail, bước nâng cao Create, thư viện casting KOL); ảnh `loading="lazy"`/next-image; reveal-on-scroll (`Reveal` đã có); skeleton chống CLS. |
| **A11y** | Tôn trọng `prefers-reduced-motion` (đã kill global) — tắt mọi animation khi user yêu cầu. |

→ Làm **1 lần** (template + loading pattern + dynamic helpers) → áp cho mọi màn.

## 3. Phủ 100% MÀN HÌNH (theo lô, có kiểm chứng)

Quy ước: ✅ xong · ▶ đang/kế · 🔜 chờ.

**Lô 0 — Nền dùng chung (✅ phần lớn)**
- ✅ Primitive điện ảnh `cinematic.tsx` (CineHero/CornerFrame/FilmLabel)
- ✅ 10 ảnh showcase (fal) · ✅ KOL casting `/app/kol`
- ▶ Bổ sung kit: ContentCard (card thể loại có ảnh), FormatReelCard (thẻ 9:16), SceneGrid, SectionHeader phim; **hệ thống loading/transition/lazy (mục 2)**

**Lô 1 — Mặt tiền & lõi (đập-vào-mắt nhất)**
1. ▶ Dashboard `/app` — launchpad cinematic + ảnh showcase + recent reel
2. 🔜 Create `/app/create` — **chọn THỂ LOẠI trước** → wizard nhánh, timeline phim
3. 🔜 Home `/` — bán "tạo mọi video AI", hero điện ảnh, showcase thể loại
4. 🔜 Mega-menu header (`site-header`) — "Tạo nội dung/Công cụ/Quản lý" kiểu autovis, mục "SẮP CÓ" style trung thực

**Lô 2 — App nội dung**
5. 🔜 Library `/app/library` (hover-scrub, filter thể loại)
6. 🔜 Video detail `/app/v/[id]` (player split + 3 nút)
7. 🔜 Series `/app/series/[group]`
8. 🔜 Studio tools: Image-gen `/app/image-gen` · Audio `/app/audio` · Compose `/app/compose`

**Lô 3 — Quản lý**
9. 🔜 Billing `/app/billing` · Reports `/app/reports` · Affiliate `/app/affiliate` · Team `/app/team`
10. 🔜 Templates `/app/templates` · Brand-kits `/app/brand-kits` · API `/app/api` · Settings `/app/settings`
11. 🔜 Admin `/app/admin` (nâng UI; chức năng đã chạy)

**Lô 4 — Marketing & phụ trợ**
12. 🔜 Pricing `/pricing` · Feature `/features/[key]` · Login `/login` · Share `/share/[id]/[token]`
13. 🔜 Pages phụ: Privacy/Terms · forgot/reset/verify-email/accept-invite · billing/return · **404 page** (custom)

→ **Tổng: ~28 màn + nav + hệ loading.** 100% được phủ.

## 4. Quy trình mỗi màn (real-qa, không tin code suông)
1. Đọc code màn + component thật.
2. Redesign theo design language §1 + dùng primitive + ảnh showcase.
3. `tsc --noEmit` sạch.
4. **Screenshot thật** desktop (1440) + mobile (390) qua Playwright, 0 lỗi console.
5. Đối chiếu chống-generic + anti-slop trước khi qua màn kế.

## 5. Pha BẢO MẬT (sau UI) — chống hack/can thiệp hậu quả nặng
Chạy qua skill `/cso` (OWASP Top 10 + STRIDE). Trọng tâm:
- Ví/credit ledger (đã ACID + RLS — verify không-trừ-oan, không cộng đôi).
- Auth/session, **cổng admin** (allowlist), rate limit, validate input.
- IPN chữ ký + idempotency (tiền vào), chống lạm dụng free-tier.
- RLS coverage (mọi bảng tenant), secrets (env, không commit), CORS, XSS/CSRF, audit log.
- Quét phụ thuộc (dependency) lỗ hổng.
→ Đầu ra: danh sách lỗ hổng + fix theo ưu tiên P0/P1/P2.

## 6. Thứ tự thực thi tổng
Lô 0 (nốt kit + loading) → Lô 1 → Lô 2 → Lô 3 → Lô 4 → **Pha bảo mật** → (song song) mở thể loại engine (VISION roadmap).
