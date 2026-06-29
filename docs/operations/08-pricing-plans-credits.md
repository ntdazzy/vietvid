# Giá, gói cước & credit

Cách Vyra định giá: quy đổi USD→credit, gói thuê bao (Free/Pro/Business), credit pack mua thêm, mô hình "mua sỉ API render → bán lại qua credit". File này nói rõ con số nào ĐÃ nằm trong code/DB, con số nào là ƯỚC LƯỢNG cần đo, và cách chủ dự án chỉnh giá an toàn.

**Trạng thái:** ⚙️ một phần — bảng `plans`/`credit_packs` đã seed trong DB; quy đổi credit (`pricing.py`) đã chạy; clamp theo gói (`validate.py`) còn lệch với seed DB (xem mục mâu thuẫn). Biên lợi nhuận = ước lượng, **chưa đo chi phí render thật**.

**Liên quan:**
- [07-economics.md](07-economics.md) — đơn vị kinh tế 1 video (chi phí thật/biên)
- [06-providers.md](06-providers.md) — giá API render (nguồn của cột chi phí)
- [09-free-tier-abuse.md](09-free-tier-abuse.md) — siết Free tier & chống lạm dụng
- [10-payments.md](10-payments.md) — nạp tiền (VietQR/SePay/MoMo) → cộng credit
- [21-financial-model.md](21-financial-model.md) — mô hình tài chính, điểm hoà vốn

---

## 1. Nguyên tắc: 1 credit = 150đ (điểm quy đổi DUY NHẤT)

✅ **Đã có.** Mọi quy đổi USD→credit đi qua MỘT hàm: `usd_to_credits()` trong [`app_api/pricing.py`](../../app_api/pricing.py).

```python
# app_api/pricing.py:10
def usd_to_credits(usd: float) -> int:
    # credits = ceil(usd * USD_TO_VND / CREDIT_PRICE_VND) — làm tròn LÊN
    return math.ceil(float(usd) * USD_TO_VND / CREDIT_PRICE_VND)
```

Hai biến cấu hình ở [`app_api/config.py`](../../app_api/config.py):

| Env var | Mặc định | Ý nghĩa | File:dòng |
|---|---|---|---|
| `CREDIT_PRICE_VND` | `150` | 1 credit = 150đ (giá BÁN cho user) | config.py:46 |
| `USD_TO_VND` | `25400` | Tỉ giá USD→VND (quy đổi chi phí API ngoại tệ) | config.py:47 |

**Vì sao làm tròn LÊN (`ceil`):** nền tảng không bao giờ chịu lỗ lẻ. 1 video tốn $0.12 → `0.12 × 25400 / 150 = 20.32` → tính user **21 credit**, không phải 20.

**Snapshot rate vào ledger:** mỗi dòng sổ cái lưu lại tỉ giá tại thời điểm đó (xem [`wallet.py`](../../app_api/wallet.py) / [03-database.md](03-database.md)). Đổi `USD_TO_VND` mai sau KHÔNG làm sai lịch sử.

> ⚠️ **Chỉnh `CREDIT_PRICE_VND` = đổi giá bán toàn hệ thống.** Tăng lên 200 nghĩa là user trả 200đ/credit (đắt hơn), KHÔNG phải user nhận ít credit hơn khi nạp. Số credit khi nạp do bảng `credit_packs` quyết định riêng (mục 3). Đừng nhầm hai thứ.

---

## 2. Gói thuê bao — Free / Pro / Business

✅ **Đã seed trong DB.** Migration [`alembic/versions/20260627_0004_billing_catalog.py`](../../alembic/versions/20260627_0004_billing_catalog.py) seed bảng `plans`. Đây là **nguồn sự thật** (DB chỉnh được), KHÔNG hardcode trong code:

| Gói | `monthly_price_vnd` | `monthly_credit_grant` | Job song song | Độ phân giải | Thời lượng tối đa | Hết watermark? |
|---|---|---|---|---|---|---|
| **free** | 0 | 300 | 1 | 720p | 30s | ❌ Không |
| **pro** | 199.000 | 3.000 | 3 | 1080p | 60s | ✅ Có |
| **business** | 599.000 | 10.000 | 6 | 1080p | 120s | ✅ Có |

Giá năm (`yearly_price_vnd`): free 0 · pro 1.990.000 (≈ 10 tháng, tặng 2) · business 5.990.000.

### Xem / sửa gói trong DB (không cần deploy lại)

Sửa giá hay grant chỉ là `UPDATE` 1 dòng — KHÔNG đụng code:

```bash
# Xem gói hiện tại
psql "$VIETVID_DB_URL" -c \
  "SELECT code,monthly_price_vnd,monthly_credit_grant,max_resolution,max_seconds,watermark_free FROM plans ORDER BY sort_order;"

# Ví dụ: nâng grant của Pro lên 3500 credit/tháng
psql "$VIETVID_DB_URL" -c \
  "UPDATE plans SET monthly_credit_grant=3500 WHERE code='pro';"
```

> `VIETVID_DB_URL` đọc từ file bí mật gitignored (`_vietvid_db_url.txt`) hoặc env — xem [15-security.md](15-security.md). KHÔNG in giá trị ra log.

### ⚠️ MÂU THUẪN cần thống nhất (đang lệch giữa 3 nơi)

| Nguồn | Free resolution | Free thời lượng |
|---|---|---|
| DB seed (plans) — migration 0004 | **720p** | **30s** |
| `validate.py:18` (`_PLAN_LIMITS`) | **480p** | **20s** |
| [DECISIONS_RESOLVED.md](../designs/DECISIONS_RESOLVED.md) | 720p | 20s |

[`app_api/validate.py`](../../app_api/validate.py) là nơi THỰC THI clamp khi tạo job (`validate_and_clamp(spec, plan_code)`), nhưng `_PLAN_LIMITS` đang **hardcode** và KHÔNG đọc bảng `plans`. Hệ quả: dù DB ghi Free=720p, code vẫn ép Free xuống 480p/20s.

**Quyết định vận hành (theo kinh tế render):** Free nên là **480p/≤20s** để chi phí render thấp nhất (xem [09-free-tier-abuse.md](09-free-tier-abuse.md)). Việc cần làm:
1. Sửa DB seed Free về 480p/20s (cho khớp ý đồ siết), HOẶC
2. Sửa `validate.py` đọc giới hạn TỪ bảng `plans` thay vì hardcode (đúng kiến trúc hơn, nhưng là việc code).

Đến khi thống nhất, **giới hạn thật user gặp = `validate.py` (480p/20s)** vì đó là nơi chặn input. Đừng quảng cáo Free 720p trên trang giá khi code chặn 480p.

---

## 3. Credit pack — mua thêm khi hết grant

✅ **Đã seed trong DB.** Bảng `credit_packs` (cùng migration 0004). Pack là cách user **nạp tiền lấy credit** ngoài grant tháng:

| Pack | `amount_vnd` | `credits` | Giá thực mỗi credit | So với 150đ |
|---|---|---|---|---|
| **starter** (Khởi đầu) | 100.000 | 700 | ~142,9đ | rẻ hơn ~5% |
| **popular** (Phổ biến) | 300.000 | 2.000 | 150đ | đúng giá |
| **pro** (Chuyên nghiệp) | 900.000 | 7.000 | ~128,6đ | rẻ hơn ~14% |

> Lưu ý: bảng giá thực mỗi credit ở trên cho thấy **thưởng nạp đang nằm SẴN trong tỉ lệ credit/đồng** (pack to → mỗi credit rẻ hơn), KHÔNG phải cột "bonus" riêng. starter hơi rẻ hơn giá niêm yết, pro rẻ nhất → khuyến khích nạp nhiều. Đây là cơ chế "thưởng nạp gói lớn" mà [docs/HANDOFF.md](../HANDOFF.md) (mục product decisions) nhắc tới.

Khi user trả tiền 1 pack, [`app_api/billing.py`](../../app_api/billing.py) tạo payment với `credits_granted = pack.credits` (billing.py:88), IPN xác nhận → cộng credit vào ví (idempotent). Chi tiết luồng tiền: [10-payments.md](10-payments.md).

### Sửa / thêm pack

```bash
# Xem pack
psql "$VIETVID_DB_URL" -c \
  "SELECT code,amount_vnd,credits FROM credit_packs ORDER BY sort_order;"

# Thêm pack "mega" 2.000.000đ = 16.000 credit (125đ/credit)
psql "$VIETVID_DB_URL" -c \
  "INSERT INTO credit_packs (code,name,amount_vnd,credits,sort_order) VALUES ('mega','Đại lý',2000000,16000,3) ON CONFLICT (code) DO NOTHING;"
```

UI hiển thị pack qua component `PackCard` (xem [docs/HANDOFF.md](../HANDOFF.md), apps/web billing).

---

## 4. Mô hình "mua sỉ API → bán lại qua credit" (markup hợp lệ)

Cốt lõi kinh tế của Vyra:

```
Vyra mua sỉ API render (PiAPI/fal/Vbee, tính bằng USD)
        ↓  usd_to_credits()  (×25400 / 150, ceil)
User tiêu CREDIT để nhận VIDEO (không nhận quyền API)
        ↓
Biên gộp = (credit user trả × 150đ) − (chi phí API thật)
```

**Vì sao hợp lệ:** user mua **sản phẩm video**, không mua/không được cấp quyền gọi API của bên thứ 3. Markup là giá trị Vyra cộng thêm (UI, giọng Việt, orchestration, lưu trữ). Điều kiện bắt buộc: **mua đúng gói API thương mại** của provider và đọc ToS (đặc biệt Vbee về giọng) — xem [06-providers.md](06-providers.md) và [15-security.md](15-security.md).

**Cách markup được áp tự động:** [`video_engine/providers/routing.py`](../../video_engine/providers/routing.py) `estimate_job_cost()` tính `total_usd` (image + video + voice/compose), rồi `usd_to_credits(total_usd)` ra số credit. Vì 1 credit = 150đ và chi phí gốc tính theo USD, biên nằm trong khoảng cách giữa giá-bán-credit và chi-phí-USD. **Markup ratio = `CREDIT_PRICE_VND` so với chi phí thật**, không phải một hệ số riêng.

> 🔢 **Biên thật CHƯA đo** vì chưa có chi phí render production thật. Cách đo: chạy 1 job thật mỗi loại, đọc `estimate_job_cost(...)["total_usd"]` từ log (xem [12-logging-observability.md](12-logging-observability.md)), so với số credit user bị trừ. Bảng ước lượng ở mục 6.

---

## 5. HOLD / SETTLE — giá hiện TRƯỚC khi tiêu

✅ **Đã có** (ví ACID, [`app_api/wallet.py`](../../app_api/wallet.py)). Liên quan giá vì nó quyết định user bị trừ bao nhiêu:

- **HOLD** (lúc tạo job): `hold = ceil(est_credits × 1.5)` — giữ chỗ rộng 1.5× để không vỡ nếu render đắt hơn dự kiến.
- **SETTLE** (render xong): `final = min(usd_to_credits(actual), hold)` — KHÔNG bao giờ tính quá báo giá; phần thừa hoàn lại.
- **REFUND**: lỗi hệ thống → hoàn 100% (lời hứa wedge "hoàn 100% khi lỗi hệ thống", [docs/HANDOFF.md](../HANDOFF.md)).

Chi tiết: [05-queue-worker-rendering.md](05-queue-worker-rendering.md) và [07-economics.md](07-economics.md).

---

## 6. Bảng giá đề xuất + biên mỗi gói (ƯỚC LƯỢNG — cần đo thật)

> ⚠️ **TẤT CẢ số biên dưới đây là ước lượng**, dựa trên giả định chi phí render **3.000–12.000đ/video** ([docs/HANDOFF.md] + quyết định vận hành). Vyra mới ra mắt, **chưa có chi phí production thật**. Cách đo: mục 4 + [07-economics.md](07-economics.md).

### Giả định để tính (ghi rõ để dễ thay khi có số thật)

| Tham số | Giá trị giả định | Nguồn |
|---|---|---|
| Chi phí render trung bình 1 video | ~6.000đ (giữa khoảng 3k–12k) | ước lượng, cần đo |
| Giá bán mỗi credit | 150đ | ✅ config.py:46 |
| Credit trung bình 1 video tiêu | ~40 credit (= 6.000đ) | ước lượng theo giả định trên |

### Biên theo gói (nếu user dùng HẾT grant tháng)

| Gói | Giá/tháng | Credit grant | Doanh thu/cr (150đ) | Chi phí render nếu xài hết¹ | Biên gộp ước lượng |
|---|---|---|---|---|---|
| Free | 0đ | 300 | 0đ | ~1.800đ (300cr×6đ chi phí thật)² | **ÂM** (chi phí marketing — phải siết) |
| Pro | 199.000đ | 3.000 | 3.000cr "trị giá" 450.000đ³ | ~18.000đ nếu xài hết 3.000cr | ~181.000đ (~91%) nếu dùng ít; mỏng hơn nếu xài kiệt |
| Business | 599.000đ | 10.000 | 10.000cr "trị giá" 1.500.000đ³ | ~60.000đ nếu xài hết | ~539.000đ nếu dùng ít |

¹ Giả định mỗi credit ứng ~6đ chi phí render thật khi user tiêu (vì 1 video ~40cr ~6.000đ → ~150đ bán/cr, ~6đ... **sai số lớn, phải đo**).
² Free: chi phí thật khi user render 300cr. Đây là khoản **lỗ có chủ đích** để thu hút — lý do Free PHẢI siết (480p/watermark/provider rẻ), xem [09-free-tier-abuse.md](09-free-tier-abuse.md).
³ "Trị giá" = số credit × 150đ giá niêm yết. Thực tế **biên phụ thuộc user dùng bao nhiêu %** grant. Nếu Pro chỉ dùng 20% grant, biên ~95%; nếu dùng 100% grant, biên co lại theo chi phí render thật.

> ❗ **Rủi ro lớn nhất:** nếu chi phí render thật gần đầu trên (12.000đ/video), 1 video ~80 credit, thì Pro 3.000cr ≈ 37 video, chi phí ~450.000đ > giá 199.000đ → **lỗ**. Vì vậy **đo chi phí render trước khi mở bán** là việc P0. Nếu chi phí cao, hoặc giảm grant, hoặc tăng giá gói, hoặc ép provider rẻ hơn cho gói thấp.

### Mục tiêu biên (theo quyết định vận hành)

Biên gộp mục tiêu **40–60%** nếu định giá đúng. Công thức kiểm tra nhanh khi có chi phí thật:

```
biên_gộp_% = (1 − chi_phí_render_trung_bình / (credit_trung_bình × 150)) × 100
```

Nếu < 40% → tăng số credit/video (sửa routing/estimate), hoặc giảm grant gói, hoặc đổi provider rẻ hơn.

---

## 7. Reset Free hàng tháng & cấp grant theo chu kỳ

⚙️ **Một phần.** Mô hình đã chốt ([DECISIONS_RESOLVED.md](../designs/DECISIONS_RESOLVED.md)): mỗi gói tặng `monthly_credit_grant` credit/chu kỳ; Free reset hàng tháng.

- **Cơ chế:** cần job định kỳ (cron/scheduler) cấp lại `monthly_credit_grant` đầu mỗi chu kỳ, dựa trên bảng `subscriptions`/`entitlements` (kế hoạch trong DECISIONS_RESOLVED mục "grant theo chu kỳ"). 🔜 **Cần xác minh đã có cron grant chưa** — nếu chưa, đây là việc cần làm trước khi mở thuê bao.
- **Free reset:** credit Free **KHÔNG cộng dồn** (reset = đặt lại 300, không +300 chồng lên dư cũ) để tránh tích trữ rồi render ồ ạt. Cần xác nhận logic reset (set vs add).
- **Lần đầu (bootstrap):** org mới được 300 credit khi `POST /v1/tenants/bootstrap` ([docs/HANDOFF.md] mục đăng nhập dev). `FREE_GRANT_CREDITS=300` (config.py:74).

> ⚠️ **FREE_GRANT phải > HOLD job rẻ nhất.** Memory `free-grant-min-hold`: nếu grant Free thấp hơn HOLD của job rẻ nhất (~105cr với hệ số 1.5×), user free dính 402 ngay lập tức. Đó là lý do mặc định nâng lên 300. **Khi đổi `FREE_GRANT_CREDITS` hay grant Free trong DB, luôn kiểm `grant ≥ ceil(est_rẻ_nhất × 1.5)`.** Cách đo est rẻ nhất: gọi `estimate_job_cost` cho spec Free tối thiểu (480p/10s/1 ảnh).

---

## 8. Hoàn tiền & referral (liên quan giá)

Theo [DECISIONS_RESOLVED.md](../designs/DECISIONS_RESOLVED.md):

- **Hoàn tiền:** 7 ngày, **chỉ phần credit chưa dùng**, yêu cầu `balance ≥ credits_granted`. (Khác với REFUND tự động khi lỗi hệ thống ở mục 5.)
- **Referral:** tính khi referee **thanh toán lần đầu** (chống tự cày). Tạm: referrer +200cr / referee +100cr. Có thể chỉnh.

---

## Việc cần làm (checklist)

- [ ] **P0 — Đo chi phí render thật** mỗi loại video (đọc `estimate_job_cost(...)["total_usd"]` từ log), thay vào bảng mục 6 → xác nhận biên 40–60%. Xem [07-economics.md](07-economics.md).
- [ ] **P0 — Thống nhất giới hạn Free** giữa DB seed (720p/30s), `validate.py` (480p/20s), DECISIONS (720p/20s). Chọn 480p/20s rồi sửa cho khớp ở cả 2 nơi (hoặc cho `validate.py` đọc bảng `plans`).
- [ ] **P0 — Xác minh cron cấp grant theo chu kỳ** đã tồn tại chưa; nếu chưa, build trước khi mở thuê bao.
- [ ] Xác nhận logic **reset Free = SET 300** (không cộng dồn).
- [ ] Kiểm `FREE_GRANT_CREDITS (300) ≥ ceil(est_rẻ_nhất × 1.5)` sau mọi lần đổi giá/estimate.
- [ ] Quyết định cuối: giữ nguyên giá gói (199k/599k) hay điều chỉnh sau khi có chi phí thật.
- [ ] Đọc ToS Vbee + provider video về quyền bán lại sản phẩm video (mục 4) — ghi kết luận vào [06-providers.md](06-providers.md).
- [ ] Trang giá public (apps/web) hiển thị ĐÚNG giới hạn Free thực thi (không quảng cáo 720p khi code chặn 480p).
- [ ] Khi có MoMo merchant: nối pack → MoMo (xem [10-payments.md](10-payments.md)).
