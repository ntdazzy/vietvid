# VietVid — Kế hoạch vượt đối thủ (từ teardown 5-agent, 2026-06-27)

Tổng hợp từ phân tích sâu autovis · Arcads/Creatify · HeyGen/Synthesia/Captions · Kling/Runway/Pika/Luma/CapCut · admin/ops. **Đây là kế hoạch gốc cho sản phẩm của VietVid — không sao chép giao diện/nội dung ai.**

## VietVid ĐÃ ngang / HƠN đối thủ
Photo→video, giọng Việt, KOL persona (AI + **upload mặt thật có đồng ý + kiểm duyệt**), brand kit, **auto-series**, **affiliate short-link + đo click**, share page, **admin/audit**, MoMo/VNPay + ledger ACID, RLS đa-tenant. Trong đó **affiliate-attribution + consent/moderation + admin/ops VietVid HƠN autovis** (autovis không có lớp đo lường).

## 🏰 CÔNG NGHỆ LÕI VƯỢT TRỘI (moat — đồng thuận 5 agent)
**Vòng lặp doanh thu tự cải thiện** — thứ autovis *không thể copy nhanh* vì họ KHÔNG có lớp attribution:

> `tạo N biến thể → mỗi biến thể 1 short-link → đo click/đơn thật → xếp hạng → nhân bản bản THẮNG → học hook/giọng/persona nào bán được`

VietVid **độc quyền sở hữu** affiliate-link + click-tracking + ledger trong MỘT sản phẩm. Đây là moat #1. Phụ trợ:
- **Giọng/caption Việt frame-perfect:** vì mình TỰ sinh TTS từ kịch bản đã biết → có timing từng chữ → caption + lip-sync chuẩn khít, **0 lỗi ASR** (đối thủ phải ASR lại).
- **Product-lock:** giữ SKU (nhãn/logo/màu thật) pixel-accurate qua mọi khung/biến thể.
- **Router đa-provider** (đã xây): route draft→model rẻ, hero→model xịn; chấm Seedance/Kling/Veo theo VN-lip-sync/chi phí.

## Gap ưu tiên xây (không cần khoá, giá trị cao)
1. **[MOAT] Vòng lặp hiệu suất** — group auto-series + click attribution → xếp hạng biến thể → nhân bản bản thắng. *(xây trước)*
2. **Product URL → auto-ad** — dán link Shopee/TikTok-Shop/Lazada → scrape tên/giá/ảnh → prefill wizard. Onboarding "ah-ha" mạnh nhất.
3. **Giọng Việt đa persona** — nhiều giọng edge-tts (Bắc/Trung/Nam, nam/nữ) + nghe thử; provider premium khi có khoá.
4. **Caption Việt burned-in frame-perfect** (tận dụng kịch bản đã biết → timing chuẩn).
5. **Xuất đa tỉ lệ 1 job** (9:16 + 1:1 + 16:9, preset VN).
6. **API + webhook B2B** (generate / attach-link / fetch-analytics).
7. **Sửa cảnh nhẹ** (đổi 1 cảnh / re-voice 1 dòng, không tạo lại cả video).

## Cần khoá/nền tảng (sau)
Voice-clone (provider), auto-post OAuth (user đã chọn KHÔNG), trend/winning-ads dataset (ingestion lớn), app mobile (PWA là bước nhanh).

## Web admin mở rộng (user yêu cầu)
Đã có: stats/suspend/credit-adjust/KOL-moderation/audit. Thêm: **cấu hình router provider + chain** (đổi/A-B provider không cần deploy), **monitor hàng đợi render + chi phí/biên-lợi-nhuận mỗi video** (provider cost vs credit price), **feature-flag theo gói** (bật voice-clone/API/batch per tier), **kiểm duyệt nội dung sinh ra** (claim cấm: y tế/tài chính), **agency/sub-tenant** (workspace con + ví con + markup), **API-key quota**, **broadcast thông báo**.
