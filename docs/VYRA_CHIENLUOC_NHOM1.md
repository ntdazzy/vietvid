# VYRA — Chiến lược Nhóm 1: "Cỗ máy đẻ video bán hàng cho người bán Việt"

> Viết ngày 2026-07-01. Mũi nhọn #1 = người bán affiliate / TikTok Shop. Các nhóm khác làm sau.
> Nguồn: 3 mũi điều tra (đối thủ autovis, code Vyra hiện có, kỹ thuật + 62 repo + API). Ngôn ngữ: Việt, dễ hiểu.

---

## 0. TIN LỚN NHẤT (đọc dòng này trước)

**Thứ khách trả tiền — "dán link sản phẩm → ra video bán hàng chốt đơn giọng Việt" — Vyra ĐÃ XÂY GẦN XONG. Còn autovis (đối thủ) thì KHÔNG CÓ.**

→ Nên chiến lược không phải "build thêm cho nhiều", mà là: **đánh bóng + tiếp thị đúng cái mình đã có + thêm 2 vũ khí (mặt thật vào video, làm hàng loạt)** để bỏ xa autovis.

---

## 1. Đối thủ autovis.ai — họ mạnh gì, hở gì

**Họ làm gì:** tải 1 ảnh + gõ mô tả → video 60 giây → tự đăng lên TikTok/YouTube/FB. Bán thông điệp "**triệu view, 1 click**". Có 50k+ người dùng, có app mobile mạnh.

**Họ CÓ:** tải ảnh mặt làm KOL (hoặc chọn mặt AI có sẵn) — nhưng **thiên về nhảy/trend/biến hình**, mặt-nói-chuyện-bán-hàng chưa phải thế mạnh.

**Giá:** thuê bao + credit. Free (có logo chìm) · Standard ~199k/tháng · **Pro ~499k/tháng** (bỏ logo, nhân giọng, tự đăng) · Super ~1.499k · Business.

**HỞ (cửa cho mình thắng):**
| Autovis yếu | Vyra đánh vào |
|---|---|
| Không có "dán link SP → video" | **Mình đã có sẵn** |
| Bán "view/viral" | Mình bán "**chốt đơn**" (người bán cần đơn, không cần view) |
| Trang chủ = thẻ nhân vật (không show video thật) | Mình = **tường video thật** phân loại theo ngành |
| Mặt-nói-bán-hàng chưa mạnh | Mình làm **mặt thật nói bán hàng** xịn + khớp môi |
| — | **Làm hàng loạt** (20 link → 20 video) + **hóa đơn VAT** + giá credit minh bạch |

---

## 2. Ba việc — hiện trạng code Vyra (đã có gì / thiếu gì)

### Việc #1 — Dán link/ảnh SP → kịch bản chốt đơn → video 9:16 giọng Việt
**Trạng thái: GẦN XONG, chắc chắn (~90%).** Đã có: bóc link Shopee/TikTok, phân tích ảnh SP (AI đọc brand/màu/chữ), viết kịch bản 6 góc thuyết phục tiếng Việt (có hook + lời theo giây), quét câu quảng cáo cấm, render 9:16, giọng Việt, phụ đề khớp, trừ credit.
**Thiếu:** model mặt đang dùng bản hơi lộ AII (`1-5-pro`); chưa khoe cho user thấy "AI đã hiểu SP thế nào"; chưa có **làm hàng loạt**.
→ **Chỉ cần đánh bóng + thêm batch. Không viết lại.**

### Việc #2 — Studio tùy chỉnh sâu (chọn người/da/dáng/đồ/bối cảnh/hành động/intro-outro)
**Trạng thái: MỚI CÓ KHUNG (nông).** Có wizard 4 bước (nguồn → style → giọng → xem trước), chọn được thời lượng/tỉ lệ/độ nét/engine/brief/giọng.
**Thiếu ~70%:** số người trong clip, tùy biến da/dáng, chọn/upload quần áo, upload "ảnh đồ", hành động theo giây, intro/outro tùy chỉnh, chọn bối cảnh trong UI.
→ **Nặng nhất. Làm dần, thêm từng control.**

### Việc #3 — Đưa mặt thật / KOL cố định vào video bán hàng
**Trạng thái: HẠ TẦNG ĐỦ, nhưng LÕI mới là "tả bằng chữ".** Có: tạo KOL 3 cách, ô upload ảnh mặt + đồng ý (consent), thư viện KOL, mô tả nhân vật chi tiết. **NHƯNG:** ở luồng thường, ảnh mặt thật KHÔNG được nhét vào video — chỉ dùng chữ mô tả để AI tự vẽ người (cố ý làm vậy để né kiểm duyệt).
→ **Muốn "mặt thật nói bán hàng" thật thì phải MUA API** (xem mục 4).

---

## 3. Thứ tự mình ĐỀ XUẤT làm (tư vấn)

| Ưu tiên | Việc | Vì sao | Công sức |
|---|---|---|---|
| **1 (tuần này)** | **Đánh bóng Việc #1 + thêm "làm hàng loạt"** | Đã gần xong, ra tiền ngay, đúng cửa hở của autovis | Nhẹ–Vừa |
| **2** | **Việc #3: mặt thật nói bán hàng** (mua API Kling/OmniHuman) | Điểm bán gói cao + hơn hẳn autovis | Vừa |
| **3 (làm dần)** | **Việc #2: studio tùy chỉnh sâu** + đòn bẩy cảnh chữ HTML (cắt 40–70% chi phí) | Nặng nhất, làm từng phần | Nặng |

Xen kẽ (Nhóm B): gộp mục trùng trang chủ, tường video thật, menu chia rõ, sửa chữ đọc-giống-AI, tối ưu mobile.

---

## 4. Kỹ thuật + chi phí (nói bằng tiền)

**Việc #1 — kịch bản:** mượn gần như nguyên repo `clipforge` (đã có sẵn bộ ingest link + prompt viết kịch bản bán hàng đỉnh, chỉ cần dịch sang tiếng Việt). Chi phí ~vài trăm đồng/kịch bản. Lưu ý: trang Shopee/TikTok chặn bot → cần tải trang bằng trình duyệt ẩn + luôn cho user dán ảnh + vài gạch đầu dòng làm phương án dự phòng.

**Việc #2 — cảnh chữ MIỄN PHÍ:** cảnh chữ/số liệu/intro/outro **vẽ bằng HTML/CSS rồi quay lại** (mượn repo `AI-auto-generate-video` + `html-video`), tốn ~0đ thay vì ~$0.4/cảnh. Chỉ cảnh cần người/chuyển động thật mới gọi AI. → **cắt 40–70% tiền mỗi video.**

**Việc #3 — mặt thật vào video: MUA API, đừng tự dựng máy.** Tốt nhất qua **fal.ai** hoặc **CometAPI (mình đã có key sẵn)**:
| Cách | Giá | Ghi chú |
|---|---|---|
| Kling AI Avatar v2 (mặt nói chuyện) | ~$0.34 / clip 6s | rẻ nhất, dùng cho gói thường |
| OmniHuman 1.5 (cùng nhà Seedance) | ~$0.16/giây | cử chỉ/biểu cảm xịn, gói cao |
| Mặt KOL cố định từ 1 ảnh | vài cent/ảnh | InstantID / IP-Adapter qua fal.ai |

**Cả 1 video hoàn chỉnh (mặt nói + kịch bản + ghép):** ~**$0.65–$2** (số đo thật từ repo `openshorts`). Bán trên mức này = có lời.

**Kết luận kiến trúc 1 câu:** mượn `clipforge` cho kịch bản, dùng HTML/CSS cho cảnh chữ (0đ), **mua** phần mặt-nói-chuyện qua API (Kling/OmniHuman, ưu tiên CometAPI vì đã có key). Tự dựng máy GPU (`LivePortrait`) để dành sau khi đông khách. Repo `openshorts` là bản mẫu để copy cả quy trình.

---

## 5. Bước đi cụ thể tiếp theo (chờ user duyệt)

**Nếu duyệt thứ tự trên, việc đầu tiên mình làm cho Việc #1:**
1. Đổi model mặt sang bản đẹp hơn + show bước "AI đã hiểu sản phẩm của bạn".
2. Làm nổi bước chọn "góc chốt đơn" (đang bị giấu).
3. Thêm **làm hàng loạt**: dán nhiều link → ra nhiều video.
4. Vẽ lại màn hình tạo video cho trực quan (bấm chọn, không gõ lệnh).

Sau đó mới sang Việc #3 (mua API mặt-nói) rồi Việc #2 (studio sâu).
