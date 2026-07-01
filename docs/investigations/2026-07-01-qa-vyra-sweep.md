# QA vận hành thật — Vyra (2026-07-01)

Quét bằng Playwright thật (chromium), auth dev-token, **an toàn tiền** (chặn
`/v1/products/import` + `/v1/batch` trả mock — KHÔNG render đốt credit). Backend
`:8099` (dev/inline), frontend `:3000`. Bằng chứng: ảnh chụp `scratchpad/qa-*.png`
+ `qa-report.json`.

## Tóm tắt (verdict)

**Không có P0/P1.** Bug thật duy nhất (batch rớt ảnh SP) đã fix + nghiệm thu trong
trình duyệt. App polish tốt trên mọi màn lõi. Còn lại là polish nhỏ (P2) + việc
enhancement cần chốt hướng.

## Bảng từng màn

| Màn | Trạng thái | Dữ liệu đúng? | Ghi chú |
|---|---|---|---|
| `/` (trang chủ) | ✅ | có | Reveal-on-scroll: fullPage headless ra đen là artifact, cuộn thật đủ section (lưới SP, "Bốn bước", CTA). Asset `gaixinh.mp4` ERR_ABORTED = huỷ-khi-điều-hướng, file CÓ tồn tại. |
| `/login` | ✅ | — | 0 lỗi JS, 0 network xấu. |
| `/app` (studio) | ✅ | có | Sidebar studio (Video/Hàng loạt/Ảnh/KOL/Nhân vật/Âm thanh/Dự án) + header marketing. Sạch. |
| `/app/create` | ✅ | có | 6 thẻ thể loại ảnh đẹp, phân cấp rõ. Tag in hoa lộ tiếng Anh (AFFILIATE, IMG→VIDEO) — jargon nhẹ P2. |
| `/app/billing` | ✅ | có | Ví, 4 gói tháng, 4 cách thanh toán (USDT "Bảo trì"), 3 gói credit + nạp tuỳ ý (1 credit=150đ). Khớp chiến lược giá. |
| `/app/batch` | ✅ (đã fix) | có | "2/2 sản phẩm sẵn sàng", chip cài đặt đủ. **Payload `/v1/batch` mang `image_url`** (nghiệm thu fix). |
| Guard `/app/*` chưa auth | ✅ | — | `/app/batch` → redirect `/login?next=%2Fapp%2Fbatch`. |

## Đã fix trong session này (code + test + real-QA)

1. **Batch rớt ảnh SP** — `apps/web/src/app/app/batch/page.tsx` từng gửi
   `/v1/batch` mà bỏ `image_url` (dù có sẵn + hiện thumbnail) → engine
   `_ensure_product_image` (pipeline.py:808) không có ảnh → mọi clip fail+refund.
   - Fix: truyền `image_url` + `image_path`; thêm upload ảnh từng SP (link Shopee
     hay chặn scrape ảnh); bắt buộc có ảnh mới "sẵn sàng"; báo rõ SP thiếu ảnh.
   - Test: `tests/test_batch.py` (3 test: hold/SP, round-trip ảnh, 402 rollback).
   - Nghiệm thu browser: payload `/v1/batch` xác nhận `image_url` không còn bị rớt.

## P2 (polish — nên sửa, không chặn)

1. **Trang series khi group không tồn tại** ném ~17 lỗi JS (thấy khi mock group giả).
   Nên xử "không tìm thấy" mượt (empty/404 state). Gốc: `/app/series/[group]`.
2. **Tag thể loại in hoa lộ tiếng Anh** ở `/app/create` (AFFILIATE, IMG→VIDEO...).
   Có phụ đề Việt nên nhẹ. Cân nhắc Việt hoá hoặc bỏ tag kỹ thuật.
3. **Tên asset `gaixinh`** lộ trên URL mạng (`/showcase/gaixinh.*`). Nit thẩm mỹ —
   đổi sang tên trung tính (`beauty-sample`) nếu để ý hình ảnh thương hiệu.
4. **Empty state người dùng mới**: "0 credit / ~0 video" hơi trơ. Có thể nhắc
   thưởng nạp lần đầu (+300) để đẩy chuyển đổi.

## Việc enhancement còn lại (cần chốt hướng, không phải bug)

- #2 Vẽ lại 4 bước configurator (sâu sau khi chọn thể loại ở `/app/create`).
- #4 Menu công cụ kiểu OpenArt — cần chốt taxonomy.
- #3 Nối API tính năng (mặt-nói/thử-đồ/tạo ảnh KOL/nhập-vai) — activation-tier:
  cần API key + tốn tiền provider để verify thật.
- #5 Optimize: mobile/tốc độ, gộp mục trùng trang chủ, PWA.
