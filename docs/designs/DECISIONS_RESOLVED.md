# Quyết định sản phẩm đã chốt (2026-06-27)

Bổ sung cho [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md) — chốt các câu hỏi mở (Phụ lục E).

## 4 quyết định người dùng chốt

1. **Mô hình kiếm tiền: Thuê bao + credit.** Gói Free/Pro/Business, mỗi gói tặng X credit/tháng + mua thêm pack khi hết. → xây `plans` + `subscriptions` + `entitlements` + `credit_packs` + grant theo chu kỳ.
2. **Cổng thanh toán nối trước: MoMo.** Dựng adapter MoMo (mới) + webhook idempotency + reconcile số tiền. (VNPay adapter đã có sẵn, giữ làm cổng thứ 2.) Kích hoạt khi có mã merchant MoMo.
3. **KOL: cả 2 (như autovis).** Persona AI sinh + **upload mặt thật**. Mặt thật đi qua đường reference-image sẵn có (ảnh → i2v Seedance) — KHÔNG cần nhà cung cấp deepfake riêng; kèm **luồng đồng ý + kiểm duyệt** (Gemini safety) trước khi render. Voice-clone vẫn là tính năng cần provider ngoài (stub request+status).
4. **Không auto-post.** Bỏ TikTok/YT auto-publish. Tập trung **trang chia sẻ công khai** + **tải MP4** + lịch đăng thủ công.

## Mặc định hợp lý cho các câu hỏi còn lại (có thể chỉnh sau)

| Chủ đề | Mặc định chọn |
|---|---|
| Gói cước (seed) | Free 300cr/th, 1 job, 720p, có watermark · Pro ~199k/th, 3 job, 1080p, không watermark, ~3.000cr/th · Business ~599k/th, 6 job, ~10.000cr/th |
| Credit packs | Giữ starter/popular/pro hiện có |
| Hoá đơn VAT | MISA meInvoice (adapter sau); chỉ xuất khi khách công ty yêu cầu; VAT 10% (cấu hình được) |
| Hoàn tiền | 7 ngày, chỉ phần credit chưa dùng, yêu cầu balance ≥ credits_granted |
| Referral | Tính khi referee **thanh toán lần đầu** (chống self-farm); referrer 200 / referee 100 (tạm) |
| Kiểm duyệt nội dung | Tái dùng Gemini safety (không thêm vendor) |
| Audit log giữ | 24 tháng |
| Voice-clone | Hoãn (cần provider) — stub request+status |
| Thư viện biểu đồ | SVG tự vẽ (0 dependency) cho analytics v1 |
| Hạ tầng | Render (API+worker) · Neon PG · Upstash Redis · R2+Cloudflare CDN |
| Fallback provider video | seedance + retry (tới khi có vendor 2) |

## Thứ tự xây đã chốt

**Sóng 5** (test + CI, khoá nền tảng tiền) → **Sóng 4** (migrations 0004+ cho data model mới → admin → templates/KOL/brand-kit/auto-series/share → analytics + affiliate loop) → **Sóng 3** (MoMo + gói cước + hoá đơn, khi có mã merchant). Arq+Redis / lưu R2 bật khi có hạ tầng.
