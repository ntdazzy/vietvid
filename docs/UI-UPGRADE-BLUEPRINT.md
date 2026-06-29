# BLUEPRINT NÂNG CẤP UI/UX — Vyra (studio video AI đa-thể-loại)

> Sinh từ audit tự động 23 màn (workflow `vyra-ui-upgrade-audit`, 2026-06-28). Nguồn-sự-thật cho **Sóng UI** trong [VISION.md §8](VISION.md). Visual system theo [design-systems/vyra/DESIGN.md](../design-systems/vyra/DESIGN.md).
> Mục tiêu: vượt autovis/Arcads/Kling/CapCut. Nguyên tắc: làm **primitives dùng chung trước** (1 lần, hưởng 23 màn), rồi đập vào 3 màn "mặt tiền" (Home, Create, Dashboard), rồi quét phần còn lại. Tất cả dùng `ACCENTS` (`lib/accents.ts`) + `Reveal` (`components/marketing/reveal.tsx`) sẵn có — **không chế token mới**.

---

## 1. Bảng tổng quan (23 màn)

| # | Màn | Score | Rủi ro slop nặng nhất | Nâng cấp P0 quan trọng nhất |
|---|---|:--:|---|---|
| 1 | Home `page.tsx` | 6.5 | Cùng 1 recipe glass+violet cho 5+ section | Hero stat cards → rich value cards có ngữ cảnh; capability grid bỏ scale-down |
| 2 | Pricing | 5.0 | 3 thẻ hàng ngang y hệt (VARIANCE<3) | Hero grid-3 → split 60/40 + demo reel; bán "7 thể loại" |
| 3 | Feature `/features/[key]` | 7.0 | 4 thẻ highlight giống hệt + steps lặp lại | Steps → timeline so le; highlights → 2×2 lệch |
| 4 | Login | 6.5 | Copy cũ "1 ảnh → chốt đơn", showcase 3 ảnh tĩnh | **Đổi value-prop sang multi-genre** |
| 5 | Share `/share/[id]/[token]` | 4.0 | Glass trên hư không, layout header+video+2 nút | Metadata + accent theo video-type; split 60/40 |
| 6 | Dashboard `/app` | 6.0 | Grid 6 thẻ launchpad đều nhau + copy "chốt đơn" | Launchpad asymmetric (hero + supporting) + genre pills |
| 7 | Create wizard | 6.0 | Launchpad 4 thẻ giống nhau, toàn violet | Launchpad → split hero; accent theo thể loại |
| 8 | Library | 5.5 | Hover quá nhẹ, không scrub/play, ít motion | Hover-to-scrub + play overlay (Pattern 4) |
| 9 | KOL casting | 5.0 | 2 grid 4-cột giống hệt, ZERO accent | ScreenHero + emerald accent; hero split + live portrait |
| 10 | Billing & Ví | 6.0 | Glass-on-everything; method grid 5 nút không phân cấp | Hero split 60/40 + reel "làm được ~N video"; **MoMo lên đầu** |
| 11 | Reports | 5.5 | 4 StatTile đều nhau (vi phạm anti-slop) | Hero split 60/40 nhấn success-rate |
| 12 | Affiliate | 5.0 | 3 tile đối xứng, link list phẳng "admin panel" | Hero split + funnel click→conv |
| 13 | Team | 5.0 | 2 StatTile y hệt + 3 GlassCard nhập nhèn | **Confirm popover khi remove** (P0 an toàn) |
| 14 | Templates | 5.0 | Grid 3 cột y hệt = AI generic | Hero 2-zone + 5 category pill accent riêng |
| 15 | Brand Kits | 5.0 | Grid 3 thẻ giống template default | Hero split + live brand preview carousel |
| 16 | API & Webhook | 5.0 | Glass×3 + divider y hệt + icon toàn violet | Hero split 60/40, phải = code snippet + copy |
| 17 | Settings | 6.0 | 5 GlassCard stack giống hệt, không nhóm | Nhóm theo category (border màu) + StatTile vào hero |
| 18 | Admin | 4.0 | 5 stat card đối xứng + `prompt()` cũ | Hero split 70/30; bỏ `prompt()` → modal |
| 19 | Image-gen | 4.5 | Không ScreenHero, empty state nhạt, 0 motion | ScreenHero + accent; empty state → reel ảnh mẫu |
| 20 | Audio | 5.0 | 1 glass card đơn, không hero/stats/demo | ScreenHero + rose accent + StatTile |
| 21 | Compose | 5.0 | Grid tuyệt đối, không accent, copy nói "chuyển cảnh" mà UI không có | ScreenHero emerald; tách 2 bước (chọn ảnh → render) |
| 22 | Series detail | 4.0 | Bảng số trần trụi, video chỉ là text | ScreenHero amber + StatTile; demo reel thumbnail |
| 23 | Video detail `/app/v/[id]` | 4.0 | Tối giản hơn cả library card; không accent | Accent sky/cyan; player split 60/40 + 3-button bar |

**Điểm trung bình ~5.3** → phần lớn ở mức "đúng chức năng, chưa premium". Đòn bẩy lớn nhất là **primitives dùng chung** (mục 2) vì 14/23 màn lặp đúng 4 lỗi giống nhau.

---

## 2. Ngôn ngữ nâng cấp DÙNG CHUNG (cross-cutting — làm 1 lần, hưởng nhiều màn)

Đây là phần ROI cao nhất. 5 lỗi/cơ hội dưới đây lặp ở 10+ màn.

### C1 — "Asymmetric hero" primitive (đập vào ~15 màn)
Lỗi phổ biến nhất toàn app: **grid N-thẻ-StatTile đối xứng** ở hero (Reports 4, Admin 5, Team 2, KOL 2, Pricing 3, Affiliate 3...). Vi phạm trực tiếp `DESIGN_VARIANCE 7-8`.
- **Việc:** mở rộng `ScreenHero` nhận layout `split` (trái: 1 metric VIP lớn + tiêu đề; phải: 2-3 StatTile nhỏ HOẶC slot demo/action). CSS Grid `60/40` (không flex %-math).
- **Áp cho:** Reports, Admin, Pricing, Affiliate, KOL, Billing, Series, Settings, Audio, Image-gen, Compose, Video-detail.
- **Effort:** M (1 component) → S mỗi màn sau đó.

### C2 — Motion preset chuẩn (đập vào toàn app)
12+ màn "0 motion" hoặc easing linear. Định nghĩa **2 preset duy nhất** rồi tái dùng, tránh mỗi màn tự chế:
- `springSoft = { type: "spring", stiffness: 180, damping: 20 }` cho CTA/badge/number pop.
- `revealUp = { y: 14→0, opacity: 0→1, dur 0.5, stagger 0.08 }` cho list/section.
- **Đưa `Reveal` (đang ở `marketing/`) thành dùng được trong `/app`** — hiện app screens không xài. Đây là 1 import đổi, mở khoá reveal-on-scroll cho mọi màn quản trị.
- **Quy tắc:** stagger 0.08–0.12 (không 0.04–0.06 — quá nhanh, mất cảm giác premium). 1 màn ~1 glow.

### C3 — Hover-depth chuẩn cho card (đập vào Library, KOL, Templates, Brand Kits, Series, Dashboard grid)
Hover hiện quá nhẹ (`-translate-y-0.5/1`). Chuẩn hoá 1 class:
- `hover: -translate-y-1 + scale-[1.02] + ring-[accent]/30 (grow 200ms) + shadow-glow-sm`, `active:scale-[0.98]`.
- **Pattern 4 "hover-to-scrub/play"** cho mọi card có video (Library P1, Templates, Series, KOL): chuột ngang → `video.currentTime` seek. Đây là moment phân biệt "studio thực lực" vs generic player — làm 1 hook `useHoverScrub`, dùng lại.

### C4 — Skeleton / Empty / Error pattern thống nhất (đập vào ~12 màn)
Nhiều màn: skeleton lệch aspect (jank), empty state "text + icon" chết, error dùng `prompt()`/`alert()`/inline span.
- **Skeleton:** match đúng aspect của card thật (khoá layout, tránh CLS).
- **Empty state:** thay "Chưa có X" bằng mini-onboarding (icon thương hiệu + 2-4 bước + CTA chính). Áp Library, Brand Kits, Templates, Series, Dashboard.
- **Error/confirm:** 1 component toast + 1 confirm-popover dùng chung. **Xoá `prompt()` ở Admin và remove-không-confirm ở Team** (đây là rủi ro thật, không chỉ thẩm mỹ).

### C5 — Accent discipline (đập vào ~10 màn dùng default violet)
`ACCENTS` có 7 màu nhưng nhiều màn vẫn violet. Gán cố định 1 lần (đề xuất, theo audit):
`Home=violet · Pricing=emerald · Billing=emerald · Reports=emerald · Affiliate=amber · KOL=rose · Audio=rose · API=sky · Video-detail=sky/cyan · Settings=slate · Admin=slate · Series=amber · Compose=emerald · Image-gen=amber/sky`.
Mỗi accent dẫn 1 glow + 1 line + chip — **không rải gradient tím vô tội vạ** (anti-slop).

> **Làm C1–C5 trước = nâng nền ~10 màn từ 5.0 lên ~6.5 chỉ với 1 đợt component work.**

---

## 3. Thay đổi IA cho PIVOT (studio đa-thể-loại)

Vấn đề xuyên suốt: **copy + flow vẫn bán "1 ảnh sản phẩm → chốt đơn 60s"**, mâu thuẫn với định vị mới "tạo MỌI loại video AI". Cần sửa theo thứ tự ảnh hưởng:

**A. Create — bắt buộc đổi flow (lõi của pivot).**
Hiện thể loại chỉ là 1 chip toggle (`product_ad` / `kol_full`) chìm trong form step 1. Phải: **chọn THỂ LOẠI trước → flow tuỳ chỉnh theo loại**.
- Moment 0 = genre picker (Quảng cáo/Affiliate · KOL · Trend · Phim ngắn · Explainer), mỗi loại 1 accent + 1 demo reel.
- Sau khi chọn: stepper/labels/PreviewRail/HoldMeter đổi accent theo loại (sửa `PreviewRail.tsx` + `stepper.tsx` nhận `accent` prop).
- KOL không hỏi brief sản phẩm; explainer cần voice+subtitle; phim ngắn cần scene/talent — flow phải nhánh.

**B. Home — đổi pitch.**
Hero hiện "Gõ tên sản phẩm → kịch bản → video". Đổi sang **"Chọn loại video (KOL/review/trend/quảng cáo/phim) → tài liệu → video"**. UseCases (9 loại) đang chìm giữa trang — kéo lên thành lõi pitch. ScriptPlayground nên có genre-selector trước khi gõ.

**C. Dashboard + Login — đổi copy + thêm genre entry.**
Cả hai vẫn "Biến 1 ảnh sản phẩm thành video chốt đơn". Đổi → "Tạo video AI cho mọi kênh" + genre pills deep-link `create?type=<thể loại>`. Login stats nên nhấn breadth: "7 giọng · 6 loại nội dung · 300 credit tặng".

**D. Surface phụ — gắn video-type vào dữ liệu (future-proof).**
- **Share + Video-detail + Library + Series + Reports:** thêm `type` (AFFILIATE/KOL/SHORT_FILM/EXPLAINER/TREND) → accent + CTA + filter theo loại. Nếu backend chưa có field, fallback `AFFILIATE`, nhưng FE viết theo enum để không phải rewrite. Library/Reports thêm category filter cạnh status filter.
- **Pricing/Billing:** gắn credit-cost vào loại nội dung ("gói đủ 2 quảng cáo HOẶC 1 phim ngắn") thay vì "100–180 credit/video" generic. Cân nhắc subscription tier.

**E. Không cần đổi IA:** Admin (back-office), API/Webhook (dev), Compose/Image-gen/Audio (công cụ generic — chỉ thêm context "loại video" để gợi ý tốt hơn, không bắt buộc).

> Quan trọng: **PIVOT không đụng design system** — vẫn token màu/motion cũ. Chỉ đổi copy, thứ tự IA, và thêm `type` field.

---

## 4. THỨ TỰ THỰC THI (ưu tiên giá trị/đập-vào-mắt)

### 3 màn "ĐẬP VÀO MẮT NHẤT" — làm trước
1. **Home** — mặt tiền, quyết định "đây có phải autovis nữa không". Pitch multi-genre + hero rich cards + accent variance.
2. **Create** — lõi sản phẩm + lõi pivot (genre-first flow). Đây là nơi pivot sống/chết.
3. **Dashboard** — màn user thấy mỗi phiên; copy "chốt đơn" + grid 6 thẻ đều nhau là 2 lỗi to nhất.

### Danh sách đánh số

**Giai đoạn 0 — Primitives dùng chung (làm 1 lần)**
1. C2 Motion preset + đưa `Reveal` vào `/app` · P0 · M · mở khoá motion cho 20+ màn.
2. C1 `ScreenHero` thêm layout `split` · P0 · M · phá grid đối xứng ~15 màn.
3. C3 Hover-depth class + `useHoverScrub` hook · P1 · M · nâng mọi card grid.
4. C4 Skeleton/Empty/Error/confirm components · P1 · M · xoá `prompt()`/`alert()` + CLS.
5. C5 Gán accent cố định/màn · P1 · S · phá monotone violet.

**Giai đoạn 1 — 3 màn mặt tiền**
6. Home: pitch multi-genre + UseCases lên hero · P0 · M.
7. Home: hero stat → rich value cards; capability grid bỏ scale-down · P0 · L.
8. Create: genre-picker Moment 0 + flow nhánh theo loại · P0 · M.
9. Create: accent động theo thể loại (PreviewRail/stepper nhận prop) · P1 · M.
10. Dashboard: launchpad asymmetric (hero emerald + supporting grid) · P0 · M.
11. Dashboard: copy → "Tạo video AI cho mọi kênh" + genre pills · P0 · M.

**Giai đoạn 2 — màn điểm thấp, đòn bẩy cao (4.0–5.0)**
12. Team: confirm-popover khi remove member · P0 · S · **rủi ro thật**.
13. Admin: bỏ `prompt()` → modal moderation + hero split 70/30 · P0/P1 · M.
14. Templates: hero 2-zone + 5 category pill accent (lõi pivot showcase) · P0 · M.
15. KOL: ScreenHero + emerald + hero split + live portrait · P0 · M.
16. Video-detail: accent + player split 60/40 + 3-button bar · P0 · M.
17. Series: ScreenHero amber + StatTile + demo reel thumbnail · P1 · M.
18. Share: metadata + accent-theo-type + split 60/40 · P1 · M/L.
19. Image-gen / Audio / Compose: ScreenHero + accent + empty-state reel · P0–P1 · S–M (gộp 1 đợt vì cùng pattern "công cụ").

**Giai đoạn 3 — màn đã ổn, polish**
20. Pricing: split 60/40 + bán "7 thể loại" + Reveal · P0/P1 · L.
21. Billing: MoMo-first method picker + hero reel + accent emerald · P1 · S–M.
22. Reports: hero split nhấn success-rate + chart animate + category segment · P1 · M.
23. Affiliate: hero split + funnel + link-card hover · P1 · M.
24. Settings: nhóm category (border màu) + StatTile hero · P0/P1 · M.
25. Login: value-prop multi-genre + showcase reel · P0/P1 · M.
26. Feature pages: steps timeline so le + highlights 2×2 + cross-link "studio" · P1 · M.
27. Library: hover-scrub (từ C3) + engine badge + category filter · P1 · S–M.

---

## 5. Cảnh báo trung thực (cần live QA bằng screenshot khi thực thi)

- **Audit là tĩnh (đọc code), chưa render.** Score premium là phán đoán từ source, không phải nhìn thật. **Bắt buộc chụp screenshot 375/390px + desktop từng màn** sau khi sửa — nhiều "rủi ro" (grid rơi cột mobile, QR 180px quá nhỏ, text "100–180 credit" bị cắt ở Billing line 71-72) chỉ lộ khi render.
- **Một vài đề xuất tự mâu thuẫn anti-slop:** Affiliate gợi "empty state Lottie/SVG character", Share gợi "social proof shares/likes plausible" — **cờ đỏ**: Vyra mới ra mắt, **CẤM số liệu bịa** (anti-slop). Khi thực thi: chỉ dùng count thật từ DB, không thì bỏ. Tương tự Home/API "5.000+ creator / 5,000+ video" — audit có chỗ vẫn lỡ viết số bịa, **không được dùng**.
- **Phụ thuộc backend chưa xác minh:** `type` field trên media (Share/Video-detail/Library/Series), `/v1/media/metadata/{id}`, voice `use_cases`, usage-stats cho Audio/Settings StatTile — audit *giả định* có. **Phải kiểm schema thật** trước khi build UI bám vào; nếu thiếu, làm fallback enum ở FE, đừng chặn UI chờ API.
- **`Reveal` hiện ở `components/marketing/`, chưa dùng trong `/app`** (đã xác minh). Đưa sang dùng app-wide có thể kéo theo `"use client"`/SSR boundary — test build, không assume.
- **Create flow nhánh theo thể loại** là thay đổi lớn nhất (đụng wizard state, PreviewRail, stepper). Audit chỉ thấy bề mặt UI; **logic state máy + cost/hold theo từng loại cần đọc kỹ `create/page.tsx` + components trước khi đổi** — đừng refactor mù.
- **KOL hero art "3D studio illustration", Brand-kit "video mockup scale thật"** là asset chưa tồn tại — cần design/asset, không phải pure code; đánh dấu là phụ thuộc, không gộp vào "S/M effort".

Files tham chiếu load-bearing: `apps/web/src/lib/accents.ts` (7 accent đã có), `apps/web/src/components/app/screen-hero.tsx` (ScreenHero + StatTile), `apps/web/src/components/marketing/reveal.tsx` (Reveal — cần promote sang app).
