---
name: real-qa
description: >-
  Kiểm thử/QA AffiliateBot bằng VẬN HÀNH THẬT — tuyệt đối không tin pytest/QA xanh.
  Mở thật TỪNG màn web, soi dữ liệu hiển thị có đúng không + UX/UI + thẩm mỹ + thân thiện
  + từ khó hiểu/lộ mã code; bấm TỪNG chức năng và verify xử lý phía sau (nút→request→
  response→DB→log); xem video output THẬT (trích khung hình + ASR nghe lại); rồi xuất
  BÁO CÁO checklist dạng roadmap (P0/P1/P2, ghi rõ lỗi ở màn nào, nguyên nhân file:dòng,
  cách sửa, cách kiểm chứng) để lên task fix và cho session sau nắm tình trạng.
  Dùng khi user nói: test, QA, kiểm tra, kiểm thử, dogfood, "test web/hệ thống/màn hình/video",
  hoặc khi cần kiểm chứng một fix có THẬT SỰ chạy đúng không.
---

# REAL-QA — Kiểm thử bằng vận hành thật (AffiliateBot)

## 0. NGUYÊN TẮC TỐI CAO (ghim — không bao giờ phá)
1. **Cấm** lấy kết quả **pytest / QA script xanh** làm bằng chứng "chạy được" hay "đạt chất lượng". Hệ thống có `USE_FAKE_CLIENTS` và web có chế độ `useMock` → xanh vẫn có thể là **dữ liệu giả**.
2. **Chỉ tin 3 nguồn:** (a) hành vi THẬT khi vận hành, (b) **mắt thấy tai nghe** (trích khung hình video + ASR, xem ảnh chụp màn), (c) **DB + log + HTTP response** thật.
3. **Kiểm chéo** mọi báo cáo của agent / đọc-code với `.env` + DB thật trước khi tin (đã từng có agent báo nhầm "V5 off, 0 sản phẩm" trong khi thực tế V5 on, 10 sản phẩm).
4. **Mọi kết luận phải kèm bằng chứng**: `file:dòng` HOẶC ảnh/khung hình/transcript/DB row/log. **Cấm viết "test pass"** suông.

## 1. CHUẨN BỊ (Bước 0)
- Xác nhận hệ thống đang chạy thật: dashboard `127.0.0.1:8000` (uvicorn `dashboard.api:app`), Postgres `5432`, và **orchestrator** (nếu cần test tự-vận-hành — kiểm màn Hệ thống "x/6 tiến trình đang chạy").
- DB thật: đếm trạng thái thật (`products/scripts/render_jobs/video_assets` theo `status`) để biết "đầy hay rỗng".
- Trình duyệt: **Playwright** (chạy được trên máy này) hoặc Claude-in-Chrome nếu kết nối được. Lưu ý môi trường: Claude-in-Chrome có thể lỗi tab-group; GStack Browser có thể lỗi sandbox Ubuntu → Playwright là phương án chắc.
- Login: lấy `DASHBOARD_API_KEY` trong `.env` để đăng nhập (ô "Mật khẩu" thực ra là API key).
- Đối chiếu `.env` ↔ `config/settings.py` (hay bị **lệch pha** mặc định) để biết cờ nào đang bật/tắt thật.

## 2. PHẦN A — QA WEB TỪNG MÀN (phủ TẤT CẢ, không sót)
Lấy danh sách route từ menu (`shell.js`/router). **Mở THẬT từng màn**, KHÔNG đọc code thay cho mở. Với MỖI màn làm đủ 5 việc:

1. **Mở + chụp ảnh** (`browser_take_screenshot fullPage` → Read ảnh) để chấm bằng mắt.
2. **Dữ liệu hiển thị có ĐÚNG không** — đối chiếu số trên màn với DB/nguồn thật (vd: cột hoa hồng, số đếm bộ lọc, KPI). Sai/0 bất thường → ghi lỗi.
3. **UX/UI + thẩm mỹ** — bố cục, khoảng cách, trạng thái rỗng/đang tải/lỗi, có chỗ nào rối/nửa vời/disabled vô nghĩa.
4. **Thân thiện với người dùng** — luồng có dễ hiểu không, nhãn có rõ không.
5. **Từ khó hiểu / jargon / lộ mã code** — liệt kê chuỗi tiếng Anh kỹ thuật (Render, Variant, Webhook, CTR…), **định danh code lộ ra** (`meta_ads_library`, `manual_seed`, `GROQ_API_KEY`, enum thô `APPROVED_AI`/`PENDING`…), viết tắt mơ hồ ("Điểm P", "sub_id ngầm"). Ghi kèm gợi ý Việt hóa.
6. **Console + network**: đọc `browser_console_messages(error)` + `browser_network_requests` xem có lỗi JS / API non-200 (vd `/config-status` 403).

Bắt buộc test cả **Login** (xoá token → phải bị chặn về /login → đăng nhập lại bằng API key → vào được). Đánh dấu mỗi màn: ✅ thật-OK · ⚠️ có vấn đề · ❌ hỏng/stub · 🔴 lỗi dữ liệu.

## 3. PHẦN B — BẤM TỪNG NÚT + VERIFY BACKEND (an toàn theo mức)
Với mỗi nút có hành động, verify **xử lý phía sau**: `nút → request gửi đi → response/status → DB đổi gì → log ghi gì`.

**Phân mức an toàn (BẮT BUỘC tuân thủ):**
- **Nút ĐỌC/an toàn** (Làm mới, Lọc, Tab, Xem, phân trang): bấm thoải mái, verify UI cập nhật + API 200.
- **Nút ĐỔI DỮ LIỆU hoàn-lại-được** (Duyệt/Từ chối/Tạo/Lưu/Đánh dấu đã đọc): bấm trên **1 bản ghi thử**, verify network+DB+log, rồi **HOÀN LẠI trạng thái** (SQL/endpoint) và ghi rõ đã hoàn lại.
- **Nút KHÔNG hoàn lại / RA NGOÀI** (Đăng thật lên YouTube/TikTok/FB, Gửi Telegram thật, Xoá vĩnh viễn, Launch Chrome đụng phiên thật): **KHÔNG tự ý bấm hàng loạt.** Làm 1 trong 2:
  - chạy ở **chế độ thử** (`DISPATCH_PROVIDER=mock`, `YOUTUBE_PRIVACY_STATUS=private`, chat Telegram test, dữ liệu thử) → verify tới ranh giới "sẵn sàng gửi";
  - hoặc **DỪNG, hỏi user 1 câu xác nhận** rồi mới bấm.
  Lý do: tránh đăng rác lên kênh thật + nguy cơ khoá tài khoản + mất dữ liệu.

## 4. PHẦN C — TEST OUTPUT (video / kịch bản) bằng mắt-tai
- **Trích khung hình** `ffmpeg` ở nhiều mốc thời gian → Read ảnh để thấy: ảnh có đúng/giống sản phẩm thật, chữ Shopee rác bị cắt, có chuyển động thật hay slideshow tĩnh, phụ đề đè bậy.
- **ASR** giọng đọc (`faster-whisper`, vi) → đọc transcript: TTS có đọc nhầm lời chỉ đạo cảnh (`(Cận cảnh…)`), sai số/từ Anh, sai thứ tự không.
- **Đối chiếu nguồn**: text thật đưa vào TTS lấy từ DB (`creative_variants.hook_text`, `variant_scenes.voiceover_text`) — đừng tin file `.json` trên đĩa (có thể khác bản render).

## 5. PHẦN D — VERIFY BACKEND (đối chiếu thật)
- Query DB **trước/sau** hành động để xác nhận hiệu ứng thật.
- Đọc **log** (`logs/*.log`, bảng `SystemEvent`, màn Nhật ký/Webhooks) xem backend thật sự làm gì + lỗi.
- Đọc **code route** xử lý nút để xác nhận logic (tìm `except` nuốt lỗi, đường dẫn không xử lý, redundancy).

## 6. ĐẦU RA — BÁO CÁO CHECKLIST (roadmap)
Ghi vào `docs/investigations/<YYYY-MM-DD>-qa-<chủ-đề>.md`:
- **Tóm tắt** top vấn đề + mức (P0 chặn vận hành / P1 nặng / P2 nên sửa).
- **Theo nhóm**: Đầu vào · Chất lượng đầu ra · Ổn định pipeline · Tự vận hành · Web/UX · Câu chữ/Jargon · Cảnh báo/Log · Bảo mật · Tài liệu.
- **Bảng TỪNG MÀN**: màn | trạng thái (✅/⚠️/❌/🔴) | dữ liệu đúng? | vấn đề UX/jargon | nút đã test + kết quả backend.
- Mỗi lỗi: **triệu chứng người dùng thấy** → **gốc rễ (file:dòng)** → **cách sửa** → **cách kiểm chứng sau khi sửa**.
- Mục đích: lên **task fix** + để **session sau** nắm nguyên nhân/tình trạng mà sửa tiếp.

## 7. HOÀN TẤT KHI
- ĐÃ mở thật + chụp + soi 5 điểm cho **mọi** màn (không sót màn nào, kể cả login).
- ĐÃ bấm thử chức năng từng màn theo mức an toàn ở §3, verify backend.
- ĐÃ xem video output thật bằng mắt-tai (nếu phạm vi gồm output).
- Báo cáo đủ bằng chứng (file:dòng / ảnh / DB / log), không có chỗ "test pass" suông.

> Trạng thái: DONE (kèm bằng chứng) · DONE_WITH_CONCERNS (liệt kê) · BLOCKED (nêu chặn ở đâu, đã thử gì).
