# VYRA — MỤC ĐÍCH & ĐỊNH HƯỚNG DỰ ÁN · cập nhật 2026-06-28

> Tài liệu ĐỊNH VỊ + ROADMAP nguồn-sự-thật cho Vyra sau khi **PIVOT**.
> Bổ sung cho [HANDOFF.md](HANDOFF.md) (ngữ cảnh kỹ thuật) — khi định vị/roadmap mâu thuẫn, **file này thắng**.
> Quyết định pivot: chủ dự án chốt 2026-06-28 (mở rộng từ "clone autovis chốt đơn" → "studio tạo mọi video bằng AI").

---

## 1. MỘT CÂU ĐỊNH VỊ

**Vyra là nền tảng web tạo MỌI loại video bằng AI cho người Việt — giọng Việt thật, chất lượng điện ảnh, giá minh bạch.**

Không còn là công cụ hẹp "1 ảnh sản phẩm → video chốt đơn". Affiliate/quảng cáo giờ chỉ là **một thể loại flagship** trong một studio sáng tạo đa-thể-loại: quảng cáo, video trend, **phim ngắn tạo từ AI**, KOL, kể chuyện/giải thích, và mở rộng tiếp.

---

## 2. VYRA LÀ GÌ BÂY GIỜ

Một studio video AI self-serve: người dùng vào web, **chọn thể loại** muốn làm, đưa input (ý tưởng/ảnh/link/kịch bản), Vyra dựng video hoàn chỉnh — có hình, giọng Việt thật, nhạc, phụ đề — tải về hoặc chia sẻ.

### Điều ĐỔI (do pivot)
- **Định vị:** từ "clone autovis" → **studio video AI tổng quát** (đối sánh CapCut AI, Kling, Pika, Runway, Arcads, autovis — Vyra là bản Việt-first vượt trội).
- **Information architecture:** create flow **bắt đầu bằng chọn thể loại**, không mặc định product-ad. Home bán "tạo mọi video bằng AI", không chỉ "chốt đơn".
- **Thư viện template + KOL + đối tượng người dùng** mở rộng theo thể loại.

### Điều KHÔNG đổi (tài sản thật, giữ nguyên làm lợi thế)
- **Giọng Việt thật** (clone VieNeu, 7 giọng) — khác biệt cốt lõi so với TTS generic của đối thủ ngoại.
- **Ví credit ACID + giá minh bạch** — hiện credit TRƯỚC khi tiêu, hoàn 100% khi lỗi hệ thống, gói trả phí không watermark.
- **Hạ tầng đa-tenant (RLS fail-closed) + engine stateless `render(spec, sink)`** — nền vững đã verify thật, dùng chung cho mọi thể loại.
- **Vòng lặp doanh thu affiliate** (short-link + đo click + nhân bản bản thắng) — vẫn là moat cho **các thể loại thương mại**; không vứt đi, mà thành một tính năng mạnh của nhánh quảng cáo/affiliate.
- **Thanh toán VN** (VietQR + SePay đã chạy thật; MoMo/VNPay khi có merchant).
- **Không auto-post** (M1) — tập trung tạo + tải + chia sẻ; lịch đăng thủ công.

---

## 3. THƯ MỤC THỂ LOẠI (genre catalog)

Engine `mode` hiện có: `product_ad | premium | kol_full | long_narrative | film_recap`. Trạng thái nối-vào-sản-phẩm THẬT (xác minh tại [render_service.py](../video_engine/render_service.py)):

| Thể loại (UX) | mode engine | Code engine | Stateless `render()` | Lộ ra web | Ưu tiên |
|---|---|---|---|---|---|
| Quảng cáo / Affiliate | `product_ad` / `premium` | ✅ đầy đủ | ✅ chạy thật | ✅ | Giữ + polish |
| KOL bán hàng | `kol_full` | ✅ | ✅ (nhánh product_ad) | ✅ | Giữ + polish |
| Video trend | `director/trend_distiller.py` | ✅ (1 bước directing) | ⚠️ chưa thành mode riêng | ❌ | Cao |
| **Phim ngắn AI (nguyên gốc)** | `long_narrative` (cinematic) | ✅ subsystem lớn | ❌ `NotImplementedError` | ❌ | **Cao** (yêu cầu chủ) |
| Kể chuyện / Giải thích | `long_narrative` | ✅ subsystem | ❌ `NotImplementedError` | ❌ | Trung |
| Recap / Tóm tắt phim | `film_recap` | ✅ subsystem | ❌ `NotImplementedError` | ❌ | Trung |

**Thực trạng:** bộ xương đa-thể-loại ĐÃ CÓ (di sản project "affiliatebot") nhưng `long_narrative`/`film_recap` còn phụ thuộc `core.*`/`config.settings`/`pipeline.*` và `module4_dispatch`/`module5_revenue` (2 module sau **không có trong repo** → đường publish cũ đã chết). Việc thật để mở thể loại = **port sang stateless `render(spec, sink)`, cắt phụ thuộc DB cũ, thêm mode + template + UX**.

> "Phim ngắn" theo chốt của chủ = **tạo phim nguyên gốc từ AI** (ý tưởng/kịch bản → sinh cảnh AI điện ảnh nối thành phim ngắn), gần `long_narrative` nhưng thiên cinematic — KHÔNG phải recap phim có sẵn.

---

## 4. NGƯỜI DÙNG MỤC TIÊU

1. **Creator / nhà sáng tạo VN** — làm video trend, phim ngắn, kể chuyện để lên kênh (TikTok/YT/FB). Cần nhanh, đẹp, giọng Việt tự nhiên.
2. **Người bán hàng / affiliate** — video chốt đơn + vòng lặp đo hiệu suất (nhánh thương mại, moat attribution).
3. **Agency / SME** — brand kit, team, sản xuất hàng loạt, sub-tenant.
4. **B2B / lập trình viên** (Product C, sau) — API/white-label engine.

---

## 5. LỢI THẾ CẠNH TRANH (thế trận mới)

Trong sân chơi studio video AI (đông hơn sân affiliate-ad), Vyra thắng bằng **Việt-first + chiều sâu**:

- **Giọng Việt thật, frame-perfect** — tự sinh TTS từ kịch bản đã biết → có timing từng chữ → caption + lip-sync khít, 0 lỗi ASR. Đối thủ ngoại phải ASR lại, giọng Việt máy móc.
- **Giá minh bạch + ví ACID** — hiện chi phí trước, hoàn 100% khi lỗi hệ thống. Đối thủ tính phí mờ.
- **Attribution cho thể loại thương mại** — short-link + đo click + nhân bản bản thắng. Không đối thủ nào gộp tạo-video + đo-doanh-thu trong một sản phẩm.
- **Router đa-provider** — route draft→model rẻ, hero→model xịn (Seedance/Kling/Veo) theo VN-lip-sync/chi phí.
- **Đa-tenant + white-label** — bán engine làm API (Product C).
- **UI/UX cao cấp Việt-hoá toàn bộ** — bar thẩm mỹ vượt autovis/Arcads, không "AI generic".

---

## 6. NGUYÊN TẮC BẤT DI BẤT DỊCH

1. **Trung thực tuyệt đối — KHÔNG bịa.** Vyra mới ra mắt: CẤM số liệu giả ("5.000+ creator", "triệu view"). Option chỉ hiện khi backend xử lý THẬT. "Đang bảo trì" trung thực hơn nút giả.
2. **real-qa — chỉ tin hành vi thật.** Không lấy pytest/tsc xanh làm bằng chứng "chạy được". Mỗi kết luận kèm bằng chứng (file:dòng / ảnh / DB row).
3. **Anti-slop** là cốt lõi UI (xem [HANDOFF.md §9](HANDOFF.md)).
4. **Tiếng Việt toàn bộ** UI + trả lời chủ dự án.
5. **Surgical + bisect commit**, chỉ commit khi được phép rõ.

---

## 7. BẮC ĐẨU THIẾT KẾ (design north-star)

Mỗi màn phải đạt: **cao cấp, có bản sắc riêng, chuyển động sống động, mobile mượt, đủ trạng thái, a11y**. Bar so sánh: nếu đặt cạnh autovis/Arcads/Kling/CapCut, người xem phải thấy Vyra "xịn hơn, Việt hơn, rõ ràng hơn". Chi tiết token/font/utilities/accent: [HANDOFF.md §9](HANDOFF.md). Design dials mặc định: VARIANCE 7-8 · MOTION 6-7 · DENSITY 4. Blueprint nâng cấp chi tiết: `docs/UI-UPGRADE-BLUEPRINT.md` (sinh từ audit toàn bộ màn).

---

## 8. LỘ TRÌNH (roadmap)

### Sóng UI — VƯỢT ĐỐI THỦ (NGAY — đang làm)
Nâng cấp **toàn bộ UI/UX mọi màn** lên chuẩn vượt đối thủ + chuyển IA sang studio đa-thể-loại.
- Audit toàn bộ màn → blueprint có ưu tiên (`docs/UI-UPGRADE-BLUEPRINT.md`).
- Thực thi theo blueprint: design primitives dùng chung (motion/depth/micro-interaction/states) → Home (bán "tạo mọi video AI") → Create (chọn thể loại trước) → Dashboard → các màn còn lại.
- Gộp việc dở dang: mặt KOL chân thực hơn, hover ZOOM, i2v nét hơn (Kling/Veo), 3 tool screen + dashboard lên chuẩn accent/ScreenHero.
- Verify từng màn: `tsc --noEmit` sạch + live QA Playwright (screenshot, 0 lỗi console).

### Sóng Multi-genre engine — MỞ THỂ LOẠI
- Port `long_narrative` (phim ngắn AI nguyên gốc) + `film_recap` sang stateless `render(spec, sink)`, cắt phụ thuộc `core.*`/`pipeline.*`/`module4-5`.
- Nâng `trend_distiller` thành mode/thể loại riêng.
- Mỗi thể loại: spec + template + UX create + giá/credit + QA thật.

### Sóng Activation — RENDER THẬT
- Điền GEMINI/GROQ/PIAPI key → render video/ảnh + kịch bản thật (đang mock).
- Queue mode (Arq + Redis + worker fleet) cho prod; R2 storage + GC video quá hạn.
- Productionize VieNeu (health-check + fallback có đồng ý).

### Sóng Growth (M3+)
- MoMo + gói cước/hoá đơn (khi có merchant). Admin mở rộng (router provider, monitor chi phí/biên-lợi-nhuận, feature-flag theo gói, agency/sub-tenant). Mobile (Flutter/PWA). Product C (API + white-label).

---

## 9. ĐỊNH NGHĨA "XONG"

- **Sóng UI xong khi:** mọi màn đạt premiumScore mục tiêu trong blueprint, 0 vi phạm anti-slop nặng, mobile 375/390px không tràn, đủ loading/empty/error, live QA screenshot sạch — và đặt cạnh đối thủ thấy rõ hơn.
- **Một thể loại xong khi:** chọn được ở web → render ra video đúng thể loại (thật, không mock) → ví HOLD/SETTLE/REFUND đúng → tải/chia sẻ được → QA thật bằng xem video output (trích khung hình + nghe lại giọng).
