# Vyra — Chiến lược giá & gói cước (V0)

**Ngày:** 2026-06-29 · **Chế độ:** Office Hours (Startup) · **Trạng thái:** APPROVED (chờ chốt số cuối + triển khai)

> Deliverable từ phiên office-hours. Đây là design doc, KHÔNG phải code. Số liệu neo vào code thật (`app_api/config.py`, `video_engine/providers/routing.py`, `.env`) và giá đối thủ tra cứu 2026.

---

## 1. Vấn đề (đã chứng minh từ code)

Vyra đang bán render Seedance **đúng giá vốn → margin gộp ≈ 0%**.

- `CREDIT_PRICE_VND=150`, `USD_TO_VND=25.400` (= tỉ giá thật), bảng giá `VIDEO_SEEDANCE_PRICES_JSON` = $0.08–0.20/s ≈ đúng giá reseller thật (EvoLink fast $0.074–0.161, PiAPI $0.08+).
- settle thu `min(usd_to_credits(actual), hold)` = đúng chi phí provider. Không có markup ở đâu cả.
- Hệ quả: free-grant 300 credit (~11.400đ × 2-3 video = lỗ ~34k/user mới), phí thanh toán, hạ tầng, lợi nhuận **không có nguồn bù**.

**COGS thật/video** (fast 480p, 5s): video $0.40 + ảnh Gemini $0.039 + other $0.01 = **$0.449 ≈ 11.400đ**.

## 2. Khách hàng (chốt trong phiên)

**Wedge chính:** người bán online nhỏ (TikTok Shop/Shopee) — siêu nhạy giá, cần RẺ + NHANH + NHIỀU. Hôm nay họ dùng DIY CapCut (~0đ, tốn 1-3h) hoặc thuê freelance 200-500k/video.
**Upsell:** SME có ngân sách marketing, cần chất lượng ổn để chạy ads.

## 3. Đối thủ (chốt trong phiên: Autovis, Kling) — đều dùng Hybrid sub + breakage

| | Free | Tier thấp | Tier cao | đ/credit | Overage |
|---|---|---|---|---|---|
| **Autovis** (trực tiếp) | watermark, ít cr | 199k / 1.500cr | 1.499k / 11.200cr | ~133đ | — |
| **Kling** | 66cr/ngày, watermark, 5s, 720p, no-commercial | $6.99 / 660cr | $127 / 26.000cr | — | Spirit ~$0.0125/unit |
| **Vyra (hiện tại)** | 300cr KHÔNG watermark | — pay-as-you-go — | | 150đ | packs |

**Kết luận:** mô hình giá (sub tháng + credit reset = breakage + pack overage + free tier watermark) là **table-stakes** — cả 2 đối thủ đã chốt. Vyra đang thiếu cả 3: không sub, không breakage, free tier quá hào phóng.

## 4. Quyết định (chốt trong phiên)

**Mô hình:** Hybrid (subscription tháng + credit reset/breakage + pack nạp thêm cho overage).
**Định vị:** Kết hợp — tier thấp **đè giá Autovis** (ăn volume seller nhỏ) + tier premium **Seedance 2 chất lượng cao** (ăn margin từ SME).
**Đòn bẩy lợi nhuận:** hạ COGS bằng provider rẻ (áp cho mọi tier).

## 5. Đòn bẩy #1 — Đổi tài khoản provider (cú lớn nhất, KHÔNG đổi gì phía user)

Margin = (**bảng giá bill user**) − (**hoá đơn provider THẬT của tài khoản bạn**). Hiện 2 cái bằng nhau → margin 0.

**Hành động:** trỏ API key sang reseller Seedance rẻ nhất (Atlas Cloud **$0.022/s** vs $0.08 đang trả), GIỮ NGUYÊN bảng giá bill `$0.08/s`.

| | COGS thật/video (fast 5s) | User vẫn bill | Margin |
|---|---|---|---|
| Hiện tại ($0.08/s) | ~11.400đ | ~11.400đ | **0%** |
| Sau khi đổi ($0.022/s) | ~4.040đ | ~11.400đ | **~65%** |

→ **Đổi 1 tài khoản provider, không đổi UI/giá, margin nhảy từ 0% lên ~65%.** Làm trước tiên. (Cần QA chất lượng output của reseller rẻ trước khi chuyển toàn bộ.)

## 6. Gói cước đề xuất (đè giá Autovis + premium upsell)

Mỗi tier **rẻ hơn + nhiều credit hơn** tier tương ứng của Autovis (nhờ COGS thấp), reset hằng tháng (breakage):

| Tier | Giá/tháng | Credit/tháng | Model | Đối chiếu Autovis |
|---|---|---|---|---|
| **Free** | 0 | 150cr (1 lần), **watermark, 480p** | fast | (cắt từ 300cr no-watermark) |
| **Khởi đầu** | **149k** | 1.800cr | fast 480p | 199k/1.500cr → rẻ hơn + nhiều hơn |
| **Pro** | **399k** | 4.500cr | fast + 720p | 499k/3.700cr |
| **Studio** (premium) | **899k** | 9.000cr | **Seedance 2 720p/1080p** | 999k/7.500cr |
| **Pack nạp thêm** | theo gói | overage, đ/cr cao hơn sub | — | (như Kling Spirit Units) |

Credit/video giữ ~bảng hiện tại (fast ~80-100cr, premium ~220cr). Ví dụ Khởi đầu 1.800cr ≈ **18-22 video fast/tháng** với 149k → ~7-8k/video cho user, COGS ~4k → **margin ~45% + breakage** (đa số không dùng hết credit).

## 7. Hai knob cấu hình

1. **COGS** — tài khoản provider (ngoài code): chọn reseller rẻ nhất đạt chất lượng. Đòn bẩy lớn nhất.
2. **Markup tinh chỉnh** — nếu cần markup thêm ngoài gap provider: nâng `USD_TO_VND` (vô hình với UI "150đ/credit", chỉ làm video tốn nhiều credit hơn). Dùng dè dặt; ưu tiên đòn bẩy COGS trước.

## 8. Free tier — siết lại (theo Autovis/Kling)

Hiện 300cr không watermark = quá hào phóng (đối thủ đều watermark + cap chặt). Đổi: **150cr một lần, có watermark, 480p, không tải HD** → đủ "wow" để convert, không đủ để dùng chùa.

## 9. Rủi ro

- Reseller rẻ ($0.022/s) có thể kém chất/chậm/giới hạn → **QA trước khi chuyển toàn bộ**, giữ Seedance 2 xịn cho tier Studio.
- Chuyển pay-as-you-go → subscription làm user hiện tại (đã nạp lẻ) bối rối → cần migration: giữ credit đã mua, thêm gói sub song song.
- Đè giá Autovis có thể bị họ hạ giá theo → lợi thế bền là **COGS thấp hơn**, không phải giá niêm yết.

## 10. Alternatives đã cân nhắc (Phase 4)

- **A) Đè giá thuần** — rẻ nhất thị trường, ăn volume. Bị loại: margin mỏng, dễ bị đua giá.
- **B) Bằng giá Autovis, margin dày** — an toàn dòng tiền. Bị loại một phần: không chiếm được wedge nhạy giá.
- **C) Premium thuần** — chất lượng cao giá cao. Bị loại: bỏ lỡ phân khúc volume lớn.
- **D) KẾT HỢP (chốt)** — tier thấp đè giá (volume) + tier Studio premium (margin). Phủ cả thị phần lẫn lợi nhuận.

## 11. THE ASSIGNMENT (việc thật, làm tuần này)

1. **Đăng ký 1 tài khoản reseller Seedance rẻ** (Atlas Cloud / so 2-3 reseller), render thử **5 video THẬT** sản phẩm của bạn, so chất lượng + tốc độ với provider hiện tại. → Quyết định có chuyển không. *(Đây là cú margin 0%→65%, ưu tiên #1.)*
2. **Hỏi 5 người bán online thật:** "Bạn trả 149k/tháng cho 20 video AI có sẵn không?" — đo willingness-to-pay thật, không đoán.
3. Sau khi có (1)+(2): chốt số credit/tier cuối + giá, rồi tôi triển khai (gói sub + reset/breakage + free-tier watermark + migration credit cũ).

---

**Completion:** DONE_WITH_CONCERNS — chiến lược + gói cước đã chốt; còn 2 ẩn số cần xác minh thực tế (chất lượng reseller rẻ, willingness-to-pay 149k) trước khi code.
