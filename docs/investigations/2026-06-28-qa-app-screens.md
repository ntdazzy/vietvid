# QA vận-hành-thật — 18 màn web Vyra (2026-06-28)

**Phương pháp:** mở THẬT từng màn bằng Playwright (Chromium) trên stack chạy thật
(frontend `localhost:3000` + backend `127.0.0.1:8099` + Postgres thật), chụp fullPage,
bắt console/network lỗi, đối chiếu dữ liệu hiển thị với DB/endpoint thật. Bổ sung: 107 test
vận-hành-thật (boot server + DB + verify) + smoke test curl các luồng lõi.

## Tóm tắt — trạng thái: **DONE_WITH_CONCERNS** (1 P0 đã fix, 1 P2 đã fix, vài note)

**Kết luận: hệ thống là THẬT, không phải khung.** 18/18 màn load sạch (0 lỗi console/network sau
khi auth đúng). Dữ liệu hiển thị là dữ liệu DB thật (admin: 1.543 user · 408 job · 512.900 credit
phát · doanh thu 6,8tr). Xử lý phía sau chạy thật (bootstrap tạo ví + 300 credit; admin economics
tính từ payment/job thật; kiểm duyệt KOL từ dữ liệu thật).

| Mức | Lỗi | Trạng thái |
|---|---|---|
| **P0** | Đăng nhập lỗi — backend (:8099) không chạy → mọi call mạng fail | ✅ ĐÃ FIX (khởi động backend; CORS=* cho phép browser) |
| **P2** | Admin economics "Credit tiêu thụ" ÂM (-1242) — `consumed = -sum(SETTLE)` sai dấu (SETTLE là refund dương) | ✅ ĐÃ FIX (`admin.py` economics; live: -1242 → 93) |

## Bảng từng màn (18)

| # | Màn | Load | Dữ liệu đúng | Ghi chú |
|---|---|---|---|---|
| 1 | /login | ✅ | — | split layout + showcase ảnh thật; dev-login OK |
| 2 | / (home) | ✅ | — | intro + 12+ section, marquee hover-clip chạy |
| 3 | /app (dashboard) | ✅ | ✅ 300 credit, empty-state đúng | chào "dev-xxxx" (artifact dev, user thật ra tên) |
| 4 | /app/create | ✅ | ✅ wizard 5 bước, hint disabled đúng | dán-link + upload + product fields |
| 5 | /app/library | ✅ | ✅ | empty-state đúng cho user mới |
| 6 | /app/kol | ✅ | ✅ | tạo persona AI / mặt thật → kiểm duyệt |
| 7 | /app/templates | ✅ | ✅ | 4 mẫu hệ thống |
| 8 | /app/brand-kits | ✅ | ✅ | empty đúng |
| 9 | /app/affiliate | ✅ | ✅ | short-link + stats |
| 10 | /app/reports | ✅ | ✅ | thống kê click |
| 11 | /app/team | ✅ | ✅ | mời thành viên + RLS |
| 12 | /app/settings | ✅ | ✅ | đổi mật khẩu / hồ sơ |
| 13 | /app/api | ✅ | ✅ | khoá API + webhook + curl mẫu |
| 14 | /app/billing | ✅ | ✅ | gói credit; thanh toán thật cần khoá MoMo/VNPay |
| 15 | /app/admin | ✅ | ✅ **chặn non-admin đúng** + admin thấy data thật | economics/kiểm duyệt/config/user |
| 16 | /app/audio | ✅ | ✅ | nghe thử giọng (edge-tts, cần mạng) |
| 17 | /app/compose | ✅ | ✅ | ghép ảnh→video (ffmpeg) |
| 18 | /app/image-gen | ✅ | ✅ empty-state | tạo ảnh cần GEMINI key |

## Bằng chứng xử-lý-thật (không mock)
- Bootstrap LIVE: `POST /v1/tenants/bootstrap` → 201, tạo org + ví + tặng 300 credit (DB ghi thật).
- `GET /v1/auth/me` → 200, balance 300, is_admin theo email.
- `GET /v1/admin/economics` LIVE → doanh thu 6.800.000đ, biên 6.798.984đ, từ payment/job thật.
- 107 test vận-hành-thật pass (boot uvicorn + DB + verify ghi DB).

## Cần khoá để "thật 100%" (đang mock/đợi cấu hình — KHÔNG phải lỗi)
1. Render video thật — fal/Kling/Seedance/PIAPI key (giờ tạo job + giữ credit thật, output mock).
2. Tạo ảnh AI — GEMINI key.
3. Thanh toán thật — MoMo/VNPay merchant key (giờ topup dev-mode).
4. Nghe thử giọng — edge-tts cần mạng.

## Note (không chặn, cân nhắc sau)
- **Dev greeting "dev-14d52b3e"**: dev-login sinh username thô; user đăng ký thật sẽ hiện tên thật. (cosmetic)
- **`/v1/dev/token` sinh uid ngẫu nhiên mỗi lần gọi không kèm user_id** (`auth.py:330`): dev-login thật OK vì backend đặt email duy nhất `dev-<uid>@`; chỉ vướng nếu test truyền email cố định đã tồn tại (bootstrap conflict). (dev-only robustness)
- **success_rate 1.5%**: phản ánh DB test (374/408 job CANCELLED do render mock), không phải lỗi sản phẩm.
