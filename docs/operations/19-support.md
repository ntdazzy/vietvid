# Hỗ trợ người dùng

Luồng support cho **solo founder**: nhận yêu cầu (email/Zalo), phân loại, SLA khiêm tốn nhưng giữ lời, dùng web admin để tra & xử (hoàn credit, xem job), mẫu trả lời sẵn, biết khi nào leo thang cho Claude điều tra, và ghi lại lỗi lặp để fix gốc thay vì vá từng ca.

**Trạng thái:** ⚙️ một phần — công cụ xử lý đã có trong admin (`routers/admin.py`: tra user, hoàn/cộng credit, audit, broadcast). Quy trình + kênh nhận + mẫu trả lời + sổ lỗi lặp = 🔜 chưa dựng (file này là bản thiết kế để dựng).

**Liên quan:** [11-admin-panel.md](11-admin-panel.md) (công cụ xử lý) · [18-runbooks.md](18-runbooks.md) (sự cố hệ thống) · [12-logging-observability.md](12-logging-observability.md) (tra log theo user/request-id) · [10-payments.md](10-payments.md) (sự cố nạp tiền/đối soát) · [07-economics.md](07-economics.md) (hoàn credit ảnh hưởng biên) · [08-pricing-plans-credits.md](08-pricing-plans-credits.md) (credit/gói) · [09-free-tier-abuse.md](09-free-tier-abuse.md) (phân biệt khiếu nại thật vs lạm dụng) · [13-monitoring-uptime.md](13-monitoring-uptime.md) (sự cố nhiều người báo cùng lúc)

---

## 0. Nguyên tắc nền (đọc trước)

1. **Bạn là 1 người.** Support KHÔNG được nuốt hết thời gian build. Mục tiêu: xử nhanh ca dễ bằng công cụ có sẵn, gom ca khó thành 1 lần điều tra, biến lỗi lặp thành 1 lần fix gốc.
2. **Lời hứa khiêm tốn, giữ được.** Đừng cam kết "trả lời trong 1 giờ" khi bạn đang code. Cam kết SLA bạn chắc chắn giữ (xem §3). Vyra mới ra mắt — ít ca, đừng over-engineer.
3. **Trung thực với khách.** Lỗi hệ thống → nói thẳng "lỗi bên mình, đã hoàn 100% credit". KHÔNG đổ cho khách khi lỗi tại mình. (Bám luật ví: lỗi hệ thống = REFUND 100%, xem [07-economics.md](07-economics.md).)
4. **Mọi thao tác admin để lại dấu vết.** `credit-adjust`, `user.status`, `config.update` đều ghi `audit_log` (`admin.py:207,183,111`). Đây là sổ cái xử lý của bạn — sau này tra lại được "đã hoàn ai, bao nhiêu, vì sao".

---

## 1. Kênh nhận yêu cầu (🔜 cần dựng)

Solo founder nên **gom về ÍT kênh** để không bỏ sót. Đề xuất tối thiểu:

| Kênh | Vai trò | Trạng thái | Ghi chú |
|---|---|---|---|
| **Email** `support@<domain>` | Kênh chính, có vết, async | 🔜 cần lập | Forward về Gmail cá nhân (`progamingeasport@gmail.com`) để 1 hộp thư. Gắn nhãn Gmail "Vyra-support". |
| **Zalo OA** (Official Account) | Khách VN quen Zalo, phản hồi nhanh | 🔜 cân nhắc | Quen thuộc với user VN. Đặt auto-reply ngoài giờ. Đừng để chat 24/7 nuốt thời gian. |
| **Form trong app** | Đính kèm `request_id` + email tự động | 🔜 chưa có | Tốt nhất về lâu dài: form gửi kèm `org_id` + `request_id` của job lỗi → bạn tra ngay không cần hỏi lại. Xem [12-logging-observability.md](12-logging-observability.md) về request-id. |
| **Broadcast (1 chiều)** | Bạn → tất cả user (bảo trì, sự cố) | ✅ có | `POST /v1/admin/broadcast` (`admin.py:122`) — gửi notify tới mọi workspace. Dùng khi sự cố diện rộng, KHÔNG phải kênh nhận. |

**Khởi đầu gọn nhất (làm ngay):** chỉ 1 email forward về Gmail + 1 nhãn. Thêm Zalo OA khi có ≥ vài ca/ngày. Form trong app làm khi rảnh tay (nó tiết kiệm nhiều thời gian hỏi-đáp qua lại).

**Footer email mẫu (để khách gửi đúng thông tin):**
> Khi báo lỗi, vui lòng kèm: **email đăng nhập** + **thời điểm gặp lỗi** + ảnh chụp màn hình (nếu có). Có mã lỗi/`request_id` thì càng nhanh.

---

## 2. Phân loại yêu cầu (triage)

Mỗi ca rơi vào 1 trong các nhóm. Phân loại quyết định SLA và cách xử.

| Nhóm | Ví dụ | Ai xử | Độ ưu tiên |
|---|---|---|---|
| **P0 — Tiền/mất credit** | Nạp tiền không vào, credit bị trừ mà không ra video, ví sai số | Bạn, NGAY | Cao nhất — liên quan tiền, mất niềm tin |
| **P0 — Hệ thống sập** | Nhiều người báo "không tạo được video", web trắng | Bạn + [18-runbooks.md](18-runbooks.md) | Cao nhất |
| **P1 — Job lỗi 1 user** | "Video của tôi báo lỗi / kẹt mãi" | Bạn tra admin → hoàn nếu lỗi hệ thống | Cao |
| **P1 — Không hiểu cách dùng** | "Làm sao tạo KOL?", "credit là gì?" | Mẫu trả lời + link hướng dẫn | Trung bình |
| **P2 — Yêu cầu tính năng** | "Có xuất 4K không?", "thêm giọng X" | Ghi nhận, KHÔNG hứa | Thấp |
| **Lạm dụng / gian lận** | Tạo nhiều acc free, đòi hoàn vô lý | Đối chiếu [09-free-tier-abuse.md](09-free-tier-abuse.md), có thể SUSPEND | Tùy ca |

**Quy tắc vàng:** ca **P0 tiền** xử trước tất cả. Một user mất tiền mà im lặng sẽ kể cho người khác. Một user được hoàn nhanh + lời xin lỗi thật sẽ ở lại.

---

## 3. SLA khiêm tốn (cam kết giữ được)

Vyra solo + mới ra mắt. SLA dưới là **đề xuất**, đặt thấp để luôn giữ được, nâng dần khi có quy trình:

| Nhóm | Phản hồi đầu | Xử xong | Ghi chú |
|---|---|---|---|
| P0 tiền/sập | Trong ngày (best effort) | Trong 24h | Hoàn credit là thao tác 1 phút — xem §4 |
| P1 job lỗi | Trong 1-2 ngày làm việc | Khi tra xong | |
| P1 cách dùng | Trong 1-2 ngày làm việc | Trả lời = xong | Dùng mẫu §6 |
| P2 tính năng | "Đã ghi nhận" trong vài ngày | Không cam kết | Vào sổ idea |

> ⚠️ **KHÔNG hiển thị SLA cứng lên web khi chưa chắc giữ được.** Auto-reply email/Zalo nên nói "thường phản hồi trong 1-2 ngày làm việc" thay vì con số gây áp lực. Hứa ít, làm hơn.

---

## 4. Xử bằng admin — cầm tay chỉ việc

Mọi thao tác qua web admin `app/app/admin/page.tsx` (gọi `/v1/admin/*`). Bật quyền admin: env `VIETVID_ADMIN_EMAILS=progamingeasport@gmail.com` — chi tiết [11-admin-panel.md §1](11-admin-panel.md).

### 4.1 Tra user theo email ✅

`GET /v1/admin/users?q=<một phần email>` (`admin.py:149`) → trả `id, email, status, org_id, plan_code, created_at`.

- **`org_id` là chìa khóa** cho mọi thao tác tiếp theo (hoàn credit, tra job) vì dữ liệu RLS gắn theo org, không theo user. Nhớ copy `org_id`.

### 4.2 Hoàn / cộng / trừ credit ✅ (công cụ support quan trọng nhất)

`POST /v1/admin/orgs/{org_id}/credit-adjust` (`admin.py:195`), body:

```json
{ "amount": 150, "note": "hoàn ca job #abc lỗi render phía hệ thống" }
```

- `amount` > 0 = **cộng** (hoàn/đền), < 0 = **trừ** (thu hồi cấp nhầm), = 0 → 422.
- Ghi ledger `ADJUST` (kind riêng, không lẫn HOLD/SETTLE/REFUND của job) + `audit_log` action `credit.adjust` kèm `note`. → tra lại được "đã hoàn ai vì sao".
- **`note` luôn ghi lý do + mã ca.** Đây là bằng chứng khi đối soát biên (hoàn credit = giảm doanh thu thực thu, xem [07-economics.md](07-economics.md)).

> 💡 **Khi nào hoàn?** Lỗi **hệ thống** (render fail do provider/bug bên mình, job kẹt) → hoàn đủ phần credit đã tiêu. Lỗi **input của khách** (ảnh xấu, prompt sai) → giải thích, thường KHÔNG hoàn (job đã tốn tiền provider thật). Ranh giới này = `fault_class` trong RenderResult (xem [05-queue-worker-rendering.md](05-queue-worker-rendering.md)): nếu job đã auto-REFUND rồi thì KHÔNG cộng tay nữa (tránh hoàn đôi).

### 4.3 Xem job của user ⚙️ (drill-down theo user CHƯA có trên UI)

Hiện admin UI **chưa có** drill-down job/log theo từng user (`11-admin-panel.md §0` ghi rõ là việc còn thiếu). Tạm thời 2 cách:

1. **Số liệu tổng:** `GET /v1/admin/economics` (`admin.py:53`) trả `jobs_by_status` + `success_rate` toàn hệ thống → biết "có phải lỗi diện rộng không".
2. **Tra 1 job cụ thể:** cần `org_id` (từ §4.1), rồi truy DB qua `tenant_session(org_id)`. Lệnh thật (đọc-only, không sửa):

```bash
cd /c/Users/NTD/Desktop/vietvid
export VIETVID_DATABASE_URL="$(cat _vietvid_db_url.txt)"
PYTHONUTF8=1 /c/Python314/python - <<'PY'
import os
from app_api.db import tenant_session
from app_api.models import Job
from sqlalchemy import select, desc
ORG = "<org_id-từ-bước-4.1>"
with tenant_session(ORG) as s:
    for j in s.execute(select(Job).order_by(desc(Job.created_at)).limit(10)).scalars():
        print(j.id, j.status, j.fault_class, j.actual_cost_usd, j.created_at)
PY
```

> 🔜 **Nên build:** thêm `GET /v1/admin/orgs/{org_id}/jobs` vào `admin.py` để bạn không phải chạy script tay mỗi ca. Khi build, cũng nối tra `job_events`/log theo `request_id` (xem [12-logging-observability.md](12-logging-observability.md)) — đó là drill-down còn thiếu ở [11-admin-panel.md](11-admin-panel.md).

### 4.4 Suspend / khôi phục tài khoản ✅ (chống lạm dụng)

`POST /v1/admin/users/{user_id}/status` (`admin.py:176`), body `{"status":"SUSPENDED"}` (hoặc `ACTIVE`/`DELETED`). Ghi `audit_log`. Dùng cho ca gian lận đã xác nhận — xem tiêu chí [09-free-tier-abuse.md](09-free-tier-abuse.md). **Đừng suspend khi chưa chắc** — báo lỗi thật khác xa lạm dụng.

### 4.5 Sự cố nạp tiền — chuyển sang [10-payments.md]

Nạp tiền không vào ví là ca P0 hay gặp. KHÔNG cộng credit tay ngay khi chưa hiểu vì sao — có thể IPN đến trễ và sẽ tự cộng (idempotent). Tra theo `payment_id`/đối soát SePay trước, quy trình ở [10-payments.md](10-payments.md). Chỉ `credit-adjust` tay khi xác nhận tiền vào bank mà IPN không xử (lý do ghi rõ trong `note`).

---

## 5. Khi nào leo thang cho Claude điều tra

Đây là điểm mạnh đặc thù của Vyra: bạn KHÔNG cần tự debug. Khi ca vượt "hoàn credit là xong", giao cho 1 phiên Claude.

**Leo thang khi:**
- Lỗi **lặp lại** ở nhiều user (không phải ca lẻ) → có bug gốc.
- Job kẹt / fault_class không rõ → cần đọc log + code.
- Số liệu lệch (ví ≠ ledger, biên âm bất thường, success_rate tụt) → điều tra root-cause.
- Sự cố diện rộng → dùng [18-runbooks.md](18-runbooks.md) trước, nếu không khớp runbook nào → Claude.

**Cách giao việc cho Claude (gói gọn để phiên sau hiểu ngay):**
1. **Triệu chứng cụ thể:** "User X (org `...`) báo job kẹt CREATED 2 tiếng, không có video."
2. **Bằng chứng đã có:** `request_id` / `job_id` / ảnh / dòng log. Có request-id thì Claude xâu được toàn flow (xem [12-logging-observability.md](12-logging-observability.md)).
3. **Trỏ skill:** dùng `/investigate` (root-cause có hệ thống) cho bug, `/real-qa` để verify fix THẬT (không tin pytest xanh). Mọi kết luận của Claude phải kèm `file:dòng` + bằng chứng thật.
4. **Yêu cầu:** "tìm nguyên nhân + fix gốc + cách kiểm chứng" — KHÔNG vá từng ca.

> Claude sửa được vì hệ thống thiết kế cho điều tra: structured log + request-id xuyên suốt + audit_log. Nếu một ca thiếu request-id → đó là tín hiệu cần nối log tốt hơn ([12-logging-observability.md](12-logging-observability.md)).

---

## 6. Mẫu trả lời (copy-paste, sửa chỗ `[...]`)

Giọng: tiếng Việt, lịch sự, thẳng thắn, KHÔNG sáo rỗng, KHÔNG đổ lỗi khách.

**a) Job lỗi do hệ thống — đã hoàn credit:**
> Chào [tên], cảm ơn bạn đã báo. Mình đã kiểm tra: video bị lỗi do hệ thống bên mình, không phải do bạn. Mình đã **hoàn lại [N] credit** vào ví của bạn (kiểm tra mục Ví & Sổ cái). Bạn thử tạo lại giúp mình nhé, nếu còn lỗi cứ phản hồi lại email này. Xin lỗi vì bất tiện.

**b) Lỗi do input của khách (không hoàn):**
> Chào [tên], mình đã xem job [mã]. Video tạo được nhưng kết quả chưa như ý do [ảnh đầu vào mờ / mô tả chưa rõ]. Gợi ý: [ảnh rõ nét, đủ sáng / mô tả cụ thể hơn]. Credit cho lần này đã dùng vì hệ thống đã render thật, nhưng làm theo gợi ý trên lần sau sẽ ra tốt hơn nhiều.

**c) Nạp tiền chưa thấy credit (đang kiểm tra):**
> Chào [tên], mình đang đối soát giao dịch nạp của bạn. Giao dịch ngân hàng đôi khi vào chậm vài phút. Mình kiểm tra trong [khung giờ] và cập nhật lại ngay. Bạn gửi giúp mình ảnh chụp giao dịch + thời điểm chuyển để mình tra nhanh hơn nhé.

**d) Yêu cầu tính năng (ghi nhận, không hứa):**
> Cảm ơn góp ý của bạn về [tính năng]. Mình đã ghi vào danh sách phát triển. Hiện chưa có lịch cụ thể, nhưng đây là loại phản hồi giúp Vyra tốt lên. Nếu triển khai mình sẽ thông báo.

**e) Hướng dẫn dùng (kèm link):**
> Chào [tên], để [tạo KOL / nạp credit / ...], bạn làm theo: [bước 1, 2, 3] hoặc xem [link hướng dẫn]. Nếu vẫn vướng, gửi mình ảnh màn hình bạn đang ở để mình chỉ tiếp.

---

## 7. Sổ lỗi lặp → fix gốc (🔜 cần lập)

Mục tiêu: KHÔNG xử cùng 1 lỗi 5 lần. Lần thứ 2 trùng triệu chứng → ghi vào sổ; lần thứ 3 → đó là ưu tiên fix.

**Cách làm nhẹ nhất (1 file):** giữ 1 bảng (Google Sheet hoặc file `docs/operations/support-log.md` 🔜) với cột:

| Ngày | Email/org | Triệu chứng | Nhóm | Đã làm (hoàn N credit?) | Nghi nguyên nhân | Số lần đã gặp |
|---|---|---|---|---|---|---|

- Khi 1 dòng đạt **≥ 2-3 lần** → mở task fix gốc + giao Claude `/investigate` (§5).
- Sau khi fix → ghi rõ "fixed @commit" để ngừng đếm.

**Tận dụng cái đã có (không cần build mới):**
- `audit_log` (`GET /v1/admin/audit`, `admin.py:274`) đã ghi mọi `credit.adjust` — đọc `note` → thấy lý do hoàn lặp lại = tín hiệu lỗi gốc. Đây là "sổ lỗi" thô có sẵn; bảng trên chỉ là lớp tổng hợp dễ đọc.
- `economics.success_rate` tụt theo thời gian = lỗi render gốc đang lan → điều tra trước khi nhiều người báo.

> 💡 **Quy đổi support → roadmap:** mỗi tuần/2 tuần nhìn sổ lỗi + audit, hỏi: "ca nào lặp nhiều nhất?" → đó là việc fix tiếp theo, đáng giá hơn tính năng mới. Đây là cách 1 người chạy support mà vẫn tiến.

---

## 8. Diện rộng vs ca lẻ

Trước khi xử 1 ca như lỗi cá nhân, kiểm tra có phải sự cố chung không:

1. `GET /v1/admin/economics` → `success_rate` đột ngột thấp / `jobs_by_status` đầy FAILED = **diện rộng**.
2. Diện rộng → vào [18-runbooks.md](18-runbooks.md) (provider chết, queue tắc, R2 lỗi) + [13-monitoring-uptime.md](13-monitoring-uptime.md), KHÔNG hoàn credit từng người tay.
3. Khi sự cố diện rộng đã rõ → dùng `POST /v1/admin/broadcast` báo tất cả user 1 lần ("Hệ thống đang gặp sự cố render, credit các job lỗi sẽ được hoàn tự động"), thay vì trả lời từng email. Sau khi khôi phục, REFUND của các job lỗi hệ thống là tự động (luật ví) — không cần cộng tay.

---

## Việc cần làm (checklist)

- [ ] Lập email `support@<domain>` forward về Gmail + nhãn "Vyra-support" + auto-reply "phản hồi trong 1-2 ngày làm việc"
- [ ] Thêm footer "khi báo lỗi vui lòng kèm email + thời điểm + ảnh" vào email/trang liên hệ
- [ ] (Khi đủ ca) lập Zalo OA + auto-reply ngoài giờ
- [ ] Build `GET /v1/admin/orgs/{org_id}/jobs` trong `admin.py` (drill-down job theo user — bỏ script tay ở §4.3)
- [ ] Nối tra `job_events`/log theo `request_id` vào admin UI (đồng bộ [12-logging-observability.md](12-logging-observability.md))
- [ ] Build form báo lỗi trong app tự đính kèm `org_id` + `request_id`
- [ ] Lập sổ lỗi lặp (`support-log.md` hoặc Sheet) + lịch review 2 tuần/lần để chọn fix gốc
- [ ] Lưu sẵn 5 mẫu trả lời (§6) ở nơi dễ copy (Gmail templates / file ghi chú)
- [ ] Xác nhận quy tắc "job đã auto-REFUND thì KHÔNG cộng credit tay" để tránh hoàn đôi (kiểm với [05-queue-worker-rendering.md](05-queue-worker-rendering.md))
- [ ] Đo thật: trung bình bao nhiêu ca support/tuần + % ca P0-tiền (ước lượng, cần đo thật — dùng `audit_log` đếm `credit.adjust` theo tuần)
