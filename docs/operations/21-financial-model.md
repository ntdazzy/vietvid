# Mô hình tài chính & điểm hoà vốn

P&L đơn giản cho Vyra: chi phí cố định (hạ tầng) + biến phí (render mỗi video) đặt cạnh doanh thu (gói thuê bao + bán credit), tính **cần bao nhiêu user trả phí để hoà vốn**, 3 kịch bản (nhỏ/vừa/lớn), và đòn bẩy tối ưu lợi nhuận. File này để chủ dự án nhìn toàn cảnh tiền ra/tiền vào, **không bịa số** — mọi con số biến phí đều dẫn về file 07 và phải đo thật trước khi tin.

**Trạng thái:** ⚙️ một phần — giá bán (gói + credit) ĐÃ nằm trong DB/code; chi phí cố định hạ tầng là **mục tiêu PaaS** (chưa deploy, chưa có hoá đơn thật); biến phí render là **ước lượng từ config**, CHƯA đo trên hoá đơn provider (Vyra mới ra mắt, render trong app đang mock — [HANDOFF.md §7](../HANDOFF.md)). **Toàn bộ kết quả hoà vốn dưới đây là khung tính, không phải dự báo.**

**Liên quan:** [07-economics.md](07-economics.md) (giá vốn 1 video — nguồn của biến phí), [08-pricing-plans-credits.md](08-pricing-plans-credits.md) (giá gói + credit pack — nguồn của doanh thu), [02-infrastructure.md](02-infrastructure.md) (hạ tầng PaaS — nguồn của chi phí cố định), [06-providers.md](06-providers.md) (giá API render), [09-free-tier-abuse.md](09-free-tier-abuse.md) (free tier tốn tiền thật → phải siết), [13-monitoring-uptime.md](13-monitoring-uptime.md) (giám sát chi phí), [20-roadmap.md](20-roadmap.md) (lộ trình).

---

## 1. TL;DR — 5 điều phải nhớ

1. **Công thức hoà vốn:** `Số user trả phí cần có = Chi phí cố định ÷ (Doanh thu mỗi user − Biến phí mỗi user)`. Mẫu số = **đóng góp biên/user (contribution margin)**. Nếu mẫu số ≤ 0 → bán càng nhiều càng lỗ, **không bao giờ hoà vốn**.
2. **Chi phí cố định nhỏ.** Hạ tầng PaaS mục tiêu **~$10-20/tháng** (~250k-510k đ) — Railway/Vercel free-tier + Neon + Upstash + R2. Đây KHÔNG phải rào cản hoà vốn. Rào cản thật là **biến phí render** (xem [02-infrastructure.md](02-infrastructure.md)).
3. **Biến phí render là biến số sống-còn.** COGS mỗi video là cột chi phí chính (80-95% giá vốn). Nếu user trả phí render nhiều hơn lượng credit họ mua tương ứng → đóng góp biên âm. **Phải đo `actual_cost_usd` thật** ([07 §6](07-economics.md)) trước khi tin bất kỳ số hoà vốn nào.
4. **Free tier là chi phí thuần, không doanh thu.** Mỗi free user tiêu credit tặng = render thật = tiền ra, doanh thu vào = 0. Free user là **chi phí cố định biến tướng** — phải tính vào P&L, phải siết cứng ([09-free-tier-abuse.md](09-free-tier-abuse.md)).
5. **Tất cả số dưới đây là KHUNG TÍNH với số ước lượng.** Thay ô vàng (⚠️) bằng số đo thật rồi mới ra quyết định giá. Bảng tính mẫu ở §6 có sẵn công thức để chủ tự thay số.

---

## 2. P&L đơn giản (một tháng)

```
Doanh thu  =  (Σ gói thuê bao bán được)  +  (Σ credit pack bán thêm)
   − Biến phí  =  Σ COGS render mọi video (gói trả phí)  +  Σ COGS render free tier
   − Chi phí cố định  =  hạ tầng PaaS  +  phí cổng thanh toán  +  (lương/chi khác = 0 lúc solo)
   ───────────────────────────────────────────────
   = Lợi nhuận trước thuế
```

### 2.1 Ba khối — trạng thái & nguồn

| Khối | Thành phần | Trạng thái | Nguồn sự thật |
|---|---|---|---|
| **Doanh thu** | Gói Pro 199k / Business 599k + credit pack | ✅ giá đã có trong DB | bảng `plans` ([08 §2](08-pricing-plans-credits.md)), `credit_packs` ([08 §3](08-pricing-plans-credits.md)) |
| **Biến phí** | COGS render/video (video+ảnh+giọng) | ⚠️ ước lượng, cần đo | `estimate_job_cost` + `actual_cost_usd` ([07-economics.md](07-economics.md)) |
| **Cố định** | Hạ tầng PaaS ~$10-20/th | 🔜 mục tiêu, chưa deploy | [02-infrastructure.md](02-infrastructure.md) |
| **Cố định** | Phí cổng thanh toán (% giao dịch) | ⚠️ tuỳ cổng, cần xác nhận | [10-payments.md](10-payments.md) |

> **Lương = 0 lúc này:** chủ dự án là solo founder, 1 laptop làm máy dev. Khi tính "có lãi để sống" thì cộng chi phí cơ hội của chủ vào — nhưng đó là quyết định cá nhân, không phải dòng P&L bắt buộc của hệ thống.

---

## 3. Chi phí cố định (ước lượng — mục tiêu PaaS)

🔜 **Chưa deploy → chưa có hoá đơn thật.** Đây là mục tiêu kiến trúc đã chốt (xem [02-infrastructure.md](02-infrastructure.md)).

| Hạng mục | Nhà cung cấp | Chi phí/tháng (ước lượng) | Ghi chú |
|---|---|---|---|
| Backend FastAPI + worker | Railway (hoặc free-tier khởi đầu) | $5-10 | có thể chứa cả Next.js |
| Frontend Next.js | Vercel (Hobby free → Pro $20 khi cần) | $0-20 | Hobby đủ lúc đầu |
| Postgres | Neon free → trả phí khi lớn | $0-5 | free tier khởi đầu |
| Redis (queue Arq) | Upstash free → trả phí | $0-5 | free tier khởi đầu |
| Lưu video | Cloudflare R2 | ~$3 / 200GB, **egress 0đ** | xem [04-storage-media.md](04-storage-media.md) |
| **TỔNG cố định** | | **~$10-20/tháng (~250k-510k đ)** | ước lượng, cần xác nhận khi deploy |

**Phí biến đổi theo giao dịch (xếp vào "gần cố định"):**
- Cổng thanh toán VN (VietQR/SePay/MoMo) thu **% trên mỗi giao dịch nạp tiền** — ⚠️ con số % tuỳ hợp đồng từng cổng, **cần xác nhận khi ký** (xem [10-payments.md](10-payments.md)). Khi tính chính xác, trừ phí này khỏi doanh thu nạp.

> **Cách đo thật:** sau 1 tháng deploy, lấy hoá đơn Railway/Vercel/Neon/Upstash/R2 + sao kê phí cổng → cộng lại = chi phí cố định THẬT. Thay vào §6.

---

## 4. Biến phí & doanh thu mỗi user (đơn vị tính hoà vốn)

### 4.1 Doanh thu mỗi user trả phí (ARPU)

Từ bảng `plans` ([08 §2](08-pricing-plans-credits.md)) — ✅ số đã có trong DB:

| Gói | Giá tháng | Credit tặng/tháng | Doanh thu/user/tháng |
|---|---|---|---|
| Pro | 199.000đ | 3.000 | **199.000đ** |
| Business | 599.000đ | 10.000 | **599.000đ** |

> ARPU thực tế = trung bình có trọng số theo tỉ lệ Pro/Business + credit pack mua thêm. Lúc chưa có user → giả định **chỉ Pro** cho kịch bản thận trọng (199k/user).

### 4.2 Biến phí mỗi user trả phí (COGS render họ tiêu)

Đây là chỗ **dễ sai nhất**. User Pro được tặng 3.000 credit/tháng. Nếu họ dùng hết để render, biến phí = COGS thật của số video render bằng 3.000 credit đó.

⚠️ **Ước lượng từ config (CẦN ĐO THẬT — [07 §3](07-economics.md)):**
- 1 video product_ad 480p 15s ≈ **205 credit** giá vốn ([07 §5.2](07-economics.md)).
- 3.000 credit ÷ 205 ≈ **~14 video/tháng** nếu tiêu hết.
- COGS 14 video × ~31.700đ (ước lượng [07 §4](07-economics.md)) ≈ **~444.000đ biến phí** cho 1 user Pro tiêu hết grant.

> 🚨 **Cảnh báo nghiêm trọng:** nếu user Pro (trả 199k) tiêu hết 3.000 credit tặng vào render premium đắt, biến phí có thể **VƯỢT** doanh thu → **đóng góp biên ÂM** → bán Pro càng nhiều càng lỗ. Đây KHÔNG phải kết luận chắc (số COGS chưa đo), nhưng là **rủi ro số-một phải kiểm bằng số thật** trước khi mở bán.

### 4.3 Đóng góp biên/user = ARPU − biến phí

| Gói | ARPU (✅) | Biến phí nếu tiêu hết grant (⚠️ ước lượng) | Đóng góp biên (⚠️) |
|---|---|---|---|
| Pro | 199.000đ | ~444.000đ | **−245.000đ** ⚠️ ÂM (ước lượng) |
| Business | 599.000đ | ~1.480.000đ (10.000cr) | **−881.000đ** ⚠️ ÂM (ước lượng) |

> **Hai con số âm trên là DẤU HIỆU ĐỎ.** Hoặc (a) COGS thật thấp hơn nhiều ước lượng config (rất có thể — "3-12k/video" trong quyết định vận hành thấp hơn ~31.700đ ước lượng); hoặc (b) credit grant đang **quá hào phóng** so với giá gói; hoặc (c) thực tế user không tiêu hết grant. **Phải đo cả 3** trước khi tin. Đừng mở bán gói với đóng góp biên âm.

**Hai đòn xử lý nếu đóng góp biên âm sau khi đo:**
1. **Giảm credit grant** theo gói (UPDATE bảng `plans.monthly_credit_grant` — không cần deploy, [08 §2](08-pricing-plans-credits.md)).
2. **Tăng giá gói** hoặc **giảm COGS** (clip ngắn hơn / model rẻ hơn theo gói — [07 §5.3](07-economics.md)).

---

## 5. Điểm hoà vốn — công thức & 3 kịch bản

### 5.1 Công thức

```
Số user trả phí cần để hoà vốn  =  Chi phí cố định / tháng
                                  ───────────────────────────────
                                  Đóng góp biên mỗi user / tháng
                                  (= ARPU − biến phí − chi phí free tier phân bổ)
```

**Điều kiện tiên quyết:** mẫu số (đóng góp biên) **phải dương**. Nếu âm (như §4.3 ước lượng hiện tại), công thức vô nghĩa — sửa giá/grant trước.

### 5.2 Ba kịch bản (KHUNG TÍNH — số phải thay bằng số đo thật)

Giả định để minh hoạ công thức (KHÔNG phải dự báo): cố định = $15/th ≈ **380.000đ**; ARPU = 199.000đ (chỉ Pro). Biến phí/user thay theo 3 mức COGS giả định để thấy độ nhạy:

| Kịch bản | Giả định biến phí/user/tháng | Đóng góp biên/user | User trả phí để hoà vốn |
|---|---|---|---|
| **Lạc quan** (COGS thấp, user dùng ít) | 50.000đ | 149.000đ | 380.000 / 149.000 ≈ **3 user** |
| **Vừa** (COGS trung bình) | 120.000đ | 79.000đ | 380.000 / 79.000 ≈ **5 user** |
| **Bi quan** (COGS cao / user tiêu nhiều) | 199.000đ | ~0đ | **∞ — không hoà vốn** (biên ≈ 0) |

> **Đọc bảng này thế nào:** chi phí cố định nhỏ nên hoà vốn chỉ cần **vài user** — MIỄN LÀ đóng góp biên dương. Toàn bộ rủi ro nằm ở cột "biến phí/user". Kịch bản bi quan cho thấy: nếu để user tiêu hết grant đắt mà giá gói không đủ bù → biên về 0 → **vô số user vẫn lỗ**. Đây là lý do §4.2 là chỗ phải đo trước nhất.

> ⚠️ Cả 3 số biến phí (50k/120k/199k) là **giả định minh hoạ**, không phải đo thật. Đo `actual_cost_usd` + theo dõi credit tiêu thật/user → thay vào.

### 5.3 Đừng quên: free tier ăn vào hoà vốn

Free user không trả tiền nhưng tiêu credit tặng = render thật = chi phí. Nếu có N free user, mỗi người tiêu trung bình C đồng COGS/tháng → cộng **N × C** vào tử số (chi phí cố định) của công thức hoà vốn:

```
User trả phí cần  =  (Cố định  +  N_free × COGS_free_trung_bình) / Đóng góp biên/user
```

- ⚠️ `COGS_free_trung_bình` cần đo: query `actual_cost_usd` cho job của org gói free ([07 §6.2](07-economics.md)).
- Đây là lý do free tier PHẢI siết cứng (480p/≤20s/watermark/giới hạn số video) — mỗi free user là một dòng chi phí. Chi tiết [09-free-tier-abuse.md](09-free-tier-abuse.md).

---

## 6. Bảng tính mẫu (công thức — thay số đo thật vào)

Dán vào Google Sheets/Excel. **Ô có ⚠️ là số phải thay bằng số đo thật.** Công thức tự tính phần còn lại.

| Ô | Tên | Giá trị (mẫu) | Nguồn |
|---|---|---|---|
| A1 | Chi phí cố định/tháng (đ) | 380.000 ⚠️ | hoá đơn PaaS thật ([02](02-infrastructure.md)) |
| A2 | Phí cổng thanh toán/tháng (đ) | 0 ⚠️ | sao kê cổng ([10](10-payments.md)) |
| B1 | ARPU — doanh thu/user trả phí (đ) | 199.000 | `plans` ([08](08-pricing-plans-credits.md)) ✅ |
| B2 | Biến phí render/user trả phí (đ) | 120.000 ⚠️ | đo `actual_cost_usd` + credit tiêu thật ([07 §6](07-economics.md)) |
| C1 | Số free user | 0 ⚠️ | analytics |
| C2 | COGS trung bình/free user (đ) | 0 ⚠️ | đo job org free ([07 §6.2](07-economics.md)) |
| **D1** | **Đóng góp biên/user** | `=B1-B2` | tự tính |
| **D2** | **Tổng chi phí cố định** | `=A1+A2+C1*C2` | tự tính |
| **D3** | **User trả phí để hoà vốn** | `=IF(D1<=0,"KHÔNG HOÀ VỐN — sửa giá/grant",CEILING(D2/D1))` | tự tính |
| **D4** | **Biên gộp/user (%)** | `=IF(B1=0,0,D1/B1)` | mục tiêu 40-60% ([07 §5.3](07-economics.md)) |

**Kiểm nhanh bằng dòng lệnh** (xem báo giá hệ thống đang tính cho 1 video, [07 §6.1](07-economics.md)):

```bash
cd /c/Users/NTD/Desktop/vietvid
PYTHONUTF8=1 /c/Python314/python -c "from video_engine.providers.routing import estimate_job_cost as e; import json; print(json.dumps(e('product_ad','final',15,'480p'), indent=2, ensure_ascii=False))"
```

→ lấy `total_vnd` làm điểm khởi đầu cho B2 (nhưng vẫn là ước lượng config — chỉ `actual_cost_usd` mới là thật).

---

## 7. Đòn bẩy tối ưu lợi nhuận (theo độ ảnh hưởng)

Lợi nhuận = `(ARPU − biến phí) × user trả phí − cố định − chi phí free`. Bốn đòn bẩy, lớn → nhỏ:

1. **Biến phí render/user (đòn bẩy số 1).** Đây là cột chi phí chính. Ba cách giảm (chi tiết [07 §5.3](07-economics.md)):
   - Giảm độ dài clip mặc định (15s → 8s cắt ~½ chi phí lớn nhất).
   - Gán model/res đúng theo gói (free 480p fast, premium mới 720p pro — chênh ~2,5×).
   - Route draft → model rẻ; chỉ video "hero" dùng model xịn (router đa-provider, [06](06-providers.md)).
2. **Credit grant theo gói (đòn bẩy số 2).** Grant quá hào phóng = biến phí phình. Cân `monthly_credit_grant` sao cho user tiêu hết vẫn còn biên dương. Chỉnh bằng `UPDATE plans` — không cần deploy ([08 §2](08-pricing-plans-credits.md)).
3. **Giá gói / ARPU (đòn bẩy số 3).** Tăng giá hoặc bán thêm credit pack. Nhưng đừng đua giá đáy — lợi thế Vyra là giá minh bạch + giọng Việt thật, không phải rẻ nhất ([VISION.md §5](../VISION.md)).
4. **Tỉ lệ free→trả phí + siết free (đòn bẩy số 4).** Free là chi phí thuần; mỗi free chuyển thành Pro vừa bỏ một dòng chi phí vừa thêm một dòng doanh thu (đòn bẩy kép). Siết free để giảm chi phí + tạo lý do nâng cấp ([09-free-tier-abuse.md](09-free-tier-abuse.md)).

**Đòn bẩy LỖ phải canh (đừng để âm thầm):**
- **Báo giá < chi phí thật:** SETTLE bị kẹp `min(actual, hold)` → nền tảng nuốt phần vượt. Theo dõi `actual_cost_usd / est_cost_usd`; > 1,2 đều đặn → tăng đơn giá config ([07 §5.3](07-economics.md)).
- **Tỉ lệ job REFUND cao:** lỗi hệ thống → hoàn 100% credit nhưng đã tốn tiền gọi provider một phần → lỗ thầm. Theo dõi % REFUND trong admin ([11-admin-panel.md](11-admin-panel.md)).

---

## 8. Việc cần làm (checklist)

- [ ] Deploy PaaS 1 tháng → lấy hoá đơn Railway/Vercel/Neon/Upstash/R2 → ghi **chi phí cố định THẬT** vào §3/ô A1 ([02-infrastructure.md](02-infrastructure.md)).
- [ ] Xác nhận **% phí cổng thanh toán** khi ký hợp đồng VietQR/SePay/MoMo → ô A2 ([10-payments.md](10-payments.md)).
- [ ] Đo **biến phí render/user thật**: query `actual_cost_usd` + credit tiêu trung bình/user trả phí → ô B2 ([07 §6.2](07-economics.md)).
- [ ] Đo **COGS trung bình/free user** (job của org gói free) → ô C2; kiểm free tier có đang ăn quá nhiều không ([09-free-tier-abuse.md](09-free-tier-abuse.md)).
- [ ] Tính **đóng góp biên/user** (ô D1). Nếu ÂM → KHÔNG mở bán; giảm credit grant hoặc tăng giá/giảm COGS trước (§4.3).
- [ ] Thay 3 kịch bản (§5.2) bằng số đo thật → biết **số user trả phí cần để hoà vốn** thật.
- [ ] Khoá **biên gộp mục tiêu 40-60%/gói** sau khi có COGS thật → đẩy ngược vào [08-pricing-plans-credits.md](08-pricing-plans-credits.md).
- [ ] Dựng bảng tính §6 trong Sheets, gắn vào quy trình review hàng tháng (theo nhịp đo COGS [07 §6.2](07-economics.md)).
- [ ] Theo dõi `actual_over_est` và % REFUND trong admin để bắt **đòn bẩy lỗ âm thầm** (§7).
