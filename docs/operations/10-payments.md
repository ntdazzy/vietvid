# 10 — Thanh toán & đối soát

Cách tiền thật vào hệ thống (nạp credit) và cách Vyra **đối soát** để không cộng nhầm, không cộng đôi, không "rơi tiền". File này bám đúng code thật trong `app_api/billing.py` + `app_api/routers/billing.py`.

**Trạng thái:** ⚙️ một phần — code 4 cổng đã có (dev/VietQR+SePay/VNPay/MoMo); VietQR+SePay đã verify e2e thật; VNPay/MoMo code xong nhưng **chưa cắm key thật**; Stripe/Visa quốc tế 🔜 chưa làm.

**Liên quan:** [08-pricing-plans-credits.md](08-pricing-plans-credits.md) (giá credit, gói) · [07-economics.md](07-economics.md) (chi phí/credit) · [09-free-tier-abuse.md](09-free-tier-abuse.md) (free grant) · [11-admin-panel.md](11-admin-panel.md) (admin đối soát thủ công) · [12-logging-observability.md](12-logging-observability.md) (log webhook) · [15-security.md](15-security.md) (bí mật cổng) · [03-database.md](03-database.md) (bảng `payments`, ledger).

---

## 1. Nguyên tắc cốt lõi: TÁCH ĐÔI "tiền vào" khỏi "credit → video"

Đây là quyết định kiến trúc quan trọng nhất của thanh toán. Hai dòng tách bạch, KHÔNG được trộn:

| Dòng | Là gì | Tin cái gì | Code |
|---|---|---|---|
| **(A) Tiền vào** | User chuyển khoản / quẹt thẻ → credit cộng vào ví | **IPN webhook server-to-server** (KHÔNG tin redirect trình duyệt) | `apply_topup()` → `wallet.topup()` |
| **(B) Credit → video** | User tiêu credit để render | `POST /jobs` HOLD credit → render → SETTLE/REFUND | `wallet.py` (xem [05-queue-worker-rendering.md](05-queue-worker-rendering.md)) |

**Vì sao tách:** Nếu tin redirect trình duyệt ("user quay lại trang `/billing/return` nghĩa là đã trả tiền") thì kẻ gian tự gọi URL đó là được credit free. Tiền chỉ được công nhận khi **cổng thanh toán gọi thẳng server Vyra** (IPN — Instant Payment Notification) với **chữ ký hợp lệ** (VNPay/MoMo) hoặc **token + đúng số tiền** (SePay).

> Redirect trình duyệt CHỈ để hiển thị "đang xử lý..." cho user; frontend poll `GET /v1/billing/payment/{id}` tới khi `status=succeeded`. Việc cộng credit luôn do IPN làm.

---

## 2. Bốn cổng nạp — trạng thái thật

Tất cả đi qua một endpoint: `POST /v1/billing/topup` (`routers/billing.py:35`). Body:

```json
{ "pack_id": "starter", "provider": "bank_qr" }
// hoặc số tiền tuỳ ý:
{ "amount_vnd": 100000, "provider": "bank_qr" }
```

| Cổng (`provider`) | Trạng thái | Cách hoạt động | Bật bằng |
|---|---|---|---|
| `dev` | ✅ chỉ local | Cộng credit TỨC THÌ trong cùng transaction (không qua bank). Test luồng. | `VIETVID_BILLING_DEV=1` (mặc định bật khi không phải prod) |
| `bank_qr` (VietQR + SePay) | ✅ verify e2e thật | Sinh ảnh VietQR keyless → user chuyển khoản với memo `VYRAxxxxxxxx` → SePay đọc biến động số dư → POST `/ipn/sepay` → đối soát memo + **số tiền** → cộng credit | `VIETVID_BANK_*` + `VIETVID_SEPAY_TOKEN` |
| `vnpay` | ⚙️ code xong, chưa key | Tạo URL ký HMAC-SHA512 → user trả trên VNPay → VNPay gọi `/ipn/vnpay` → verify chữ ký + số tiền → cộng | `VNPAY_TMN_CODE` + `VNPAY_HASH_SECRET` |
| `momo` | ⚙️ code xong, chưa key | Gọi MoMo createPayment server-to-server → `payUrl` → MoMo gọi `/ipn/momo` (JSON) → verify chữ ký HMAC-SHA256 + số tiền → cộng | `VIETVID_MOMO_PARTNER_CODE/ACCESS_KEY/SECRET_KEY` |
| `usdt` (crypto) | 🔜 đang bảo trì | Cột DB có (`crypto_asset/network/amount`) nhưng KHÔNG có adapter. UI hiện "đang bảo trì" (trung thực, không giả nút). | — |

> **MoMo-first là định hướng sản phẩm** ([product-decisions]), nhưng hiện code đầy đủ và đã VERIFY là **VietQR+SePay**. MoMo cần đăng ký merchant + key thật mới bật được.

---

## 3. Luồng VietQR + SePay (cổng đã chạy thật) — cầm tay chỉ việc

Đây là cổng VN rẻ nhất, **keyless ở phía sinh QR** (không cần API key VietQR), chỉ cần SePay đọc biến động số dư tài khoản ngân hàng.

### Bước 1 — User bấm nạp → backend tạo Payment PENDING + ảnh QR

`routers/billing.py:84-96` trả về:

```json
{
  "payment_id": "…", "provider": "bank_qr", "status": "pending",
  "amount_vnd": 100000, "credits": 667,
  "qr_image_url": "https://img.vietqr.io/image/970436-9988776655-compact2.png?amount=100000&addInfo=VYRA1A2B3C4D&accountName=CONG%20TY%20VYRA",
  "memo": "VYRA1A2B3C4D",
  "bank": { "name": "Vietcombank", "bin": "970436", "account_number": "9988776655", "account_name": "CONG TY VYRA" }
}
```

- **`memo` = `ext_ref` = nội dung chuyển khoản** (`billing.py:53-55`, format `VYRA` + 8 hex hoa). Đây là khoá đối soát.
- Ảnh QR sinh từ napas247 (`vietqr_image_url`, `billing.py:93`) — không cần key.

### Bước 2 — User chuyển khoản (quét QR bằng app bank bất kỳ)

Memo đã nhúng sẵn → user không gõ tay. Số tiền cũng đã fix trong QR.

### Bước 3 — SePay đọc tiền về → POST `/v1/billing/ipn/sepay`

`routers/billing.py:135`. SePay là dịch vụ đọc SMS/biến động số dư ngân hàng và bắn webhook. Đối soát 3 lớp:

1. **Auth token:** header `Authorization: Apikey <SEPAY_API_TOKEN>`, so bằng `hmac.compare_digest` (chống timing attack). Sai → 401.
2. **Chỉ tiền VÀO:** `transferType == "in"`, tiền ra bỏ qua.
3. **Bóc memo:** regex `VYRA[0-9A-F]{8}` từ nội dung (`parse_sepay_memo`). Không có memo → ack "không phải của ta" (không lỗi).
4. **Resolve org** theo memo (`resolve_bank_payment_org`, `billing.py:114`).
5. **Đối soát SỐ TIỀN:** `amount == p.amount_vnd`? Lệch → **KHÔNG tự cộng**, log cảnh báo, để admin xử lý (`routers/billing.py:175-181`).
6. Khớp hết → `apply_topup()` cộng credit.

### Bước 4 — Frontend poll `GET /v1/billing/payment/{id}` → thấy `succeeded` → cập nhật ví.

> **Test local khi chưa có SePay:** `POST /v1/billing/payment/{id}/dev-confirm` giả lập "đã nhận tiền" (chỉ bật khi `BILLING_DEV_ENABLED`).

---

## 4. Chống cộng tiền đôi (idempotent) — bất biến tiền-bạc

Webhook MẶC ĐỊNH gửi lại (retry) khi không nhận được 200, hoặc gửi trùng. Nếu cộng credit mỗi lần gọi = mất tiền. Vyra chặn ở **2 lớp**:

### Lớp 1 — `apply_topup` idempotent (`billing.py:138`)

```python
p = SELECT Payment WHERE provider, ext_ref FOR UPDATE      # khoá hàng
if p.status == SUCCEEDED:  return p                         # đã cộng → bỏ qua (replay)
wallet.topup(...)                                            # cộng ĐÚNG 1 lần
p.status = SUCCEEDED; p.settled_at = now()
```

`SELECT ... FOR UPDATE` + check `status == SUCCEEDED` → dù IPN gọi N lần, credit cộng đúng 1 lần. Hai request đồng thời: request thứ hai chờ khoá, thấy `SUCCEEDED` → no-op.

### Lớp 2 — UNIQUE constraint ở DB (lưới cuối)

`models.py:519`: `UniqueConstraint("provider", "ext_ref")`. Hai payment cùng provider không thể trùng `ext_ref` → memo/orderId là khoá tự nhiên. Kể cả logic app lỗi, DB vẫn chặn.

### Đối soát SỐ TIỀN — chống "trả ít, nhận đủ credit"

Mọi IPN đều so `amount` nhận được với `amount_vnd` đã tạo:
- **SePay:** lệch → không cộng, log, admin xử lý (`routers/billing.py:175`).
- **VNPay:** `vnp_Amount` = số tiền × 100, lệch → set `FAILED` + `RspCode 04` (`routers/billing.py:235`).
- **MoMo:** lệch → set `FAILED` + `resultCode 99` (`routers/billing.py:271`).

> Trạng thái `payments.status`: `PENDING | SUCCEEDED | FAILED | REFUNDED` (`models.py:52`).

---

## 5. VNPay & MoMo (code xong, cần key) — cách bật

Cả hai nhúng `org_id` vào `ext_ref`/`orderId` (32 hex đầu) để IPN **không-auth** resolve được org mà không lộ (đã được HMAC ký nên tin được sau verify) — `billing.py:198`, `:268`.

### VNPay
- Tạo URL: `build_vnpay_url` ký HMAC-SHA512 (`billing.py:175`).
- IPN: `/v1/billing/ipn/vnpay` (GET/POST). **Nếu chưa cấu hình → từ chối** (`RspCode 97`), KHÔNG verify bằng secret rỗng (kẻ gian sẽ giả chữ ký được) — `routers/billing.py:204`.
- Trả về RspCode chuẩn VNPay: `00` ok, `01` không thấy đơn, `02` đã xác nhận, `04` sai tiền, `97` chữ ký sai.

### MoMo
- Tạo: `build_momo_payment` gọi server-to-server lấy `payUrl`, ký HMAC-SHA256 (`billing.py:211`).
- IPN: `/v1/billing/ipn/momo` (JSON), verify field theo thứ tự cố định MoMo yêu cầu (`verify_momo_ipn`, `billing.py:249`).

---

## 6. Hoá đơn VAT 🔜

**Trạng thái:** chưa làm. Hiện chỉ có lịch sử payment (`GET /v1/billing/payments`).

Kế hoạch khi khách công ty yêu cầu:
- Thu thêm thông tin xuất hoá đơn (tên công ty, MST, địa chỉ) ở bước nạp/profile.
- VN: hoá đơn điện tử qua nhà cung cấp (VD MISA meInvoice / Viettel) — phát hành khi `payment.status=SUCCEEDED`.
- Lưu link hoá đơn vào `payments.raw_payload` (cột JSONB đã có, `models.py:515`).
- Giá hiển thị: làm rõ "đã gồm VAT" hay "chưa gồm" trên trang giá ([08-pricing-plans-credits.md](08-pricing-plans-credits.md)).

> Không cần làm trước khi có khách công ty đầu tiên. Đừng over-build.

---

## 7. Hoàn tiền (refund)

Phân biệt 2 loại refund — **đừng nhầm**:

| Loại | Là gì | Tự động? | Code |
|---|---|---|---|
| **Refund credit** (render lỗi hệ thống) | Job fail do lỗi Vyra → hoàn 100% credit đã HOLD vào ví | ✅ TỰ ĐỘNG, idempotent | `wallet.refund()` (`wallet.py:110`) — xem [05-queue-worker-rendering.md](05-queue-worker-rendering.md) |
| **Refund tiền** (trả lại VND đã nạp) | User đòi tiền mặt cho credit chưa dùng | 🔜 chưa có flow tự động | Admin xử lý thủ công |

**Refund tiền nạp 🔜:** chưa có endpoint. Khi cần:
- Status `REFUNDED` đã có sẵn (`models.py:53`).
- Cần: trừ credit chưa dùng (`wallet.topup` với credits âm / `ADJUST`) + chuyển khoản tay + set `payment.status=REFUNDED`.
- Phải kiểm: credit đó đã tiêu chưa (không hoàn tiền cho credit đã render thành video).
- Chính sách refund nên ghi rõ ở [19-support.md](19-support.md) trước khi bán.

---

## 8. Bật cổng thật khi deploy — checklist env

**VietQR + SePay (cổng VN chính, ưu tiên bật đầu tiên):**
```bash
VIETVID_BANK_BIN=970436                 # mã BIN ngân hàng (VD 970436 = VCB) — tra trên napas
VIETVID_BANK_ACCOUNT=9988776655         # số tài khoản nhận tiền doanh nghiệp
VIETVID_BANK_ACCOUNT_NAME="CONG TY VYRA"  # tên không dấu, IN HOA (trùng tài khoản)
VIETVID_BANK_NAME="Vietcombank"
VIETVID_SEPAY_TOKEN="<token mạnh, random>"  # cấu hình TRÙNG trong dashboard SePay
VIETVID_BILLING_DEV=0                    # TẮT cổng dev ở prod (bắt buộc)
```
Sau đó vào dashboard SePay: trỏ webhook về `https://<domain>/v1/billing/ipn/sepay`, header `Authorization: Apikey <token>`, kết nối tài khoản ngân hàng nhận tiền.

**VNPay (nếu bật):**
```bash
VNPAY_TMN_CODE=...  VNPAY_HASH_SECRET=...
VNPAY_URL=https://pay.vnpay.vn/vpcpay.html        # PROD, bỏ sandbox
VNPAY_RETURN_URL=https://<domain>/billing/return
```

**MoMo (nếu bật):**
```bash
VIETVID_MOMO_PARTNER_CODE=...  VIETVID_MOMO_ACCESS_KEY=...  VIETVID_MOMO_SECRET_KEY=...
VIETVID_MOMO_ENDPOINT=https://payment.momo.vn/v2/gateway/api/create   # PROD
VIETVID_MOMO_RETURN_URL=https://<domain>/billing/return
VIETVID_MOMO_IPN_URL=https://<domain>/v1/billing/ipn/momo
```

**Giới hạn số tiền nạp tuỳ ý** (đã có default an toàn):
```bash
VIETVID_TOPUP_MIN_VND=20000      # mặc định 20k
VIETVID_TOPUP_MAX_VND=50000000   # mặc định 50tr
```

> Bí mật KHÔNG commit. Đặt qua env của PaaS (Railway/Vercel) — xem [15-security.md](15-security.md) + [17-deployment-cicd.md](17-deployment-cicd.md).

---

## 9. Cách KIỂM CHỨNG sau khi bật (verify thật, không tin xanh)

1. **Test webhook idempotent:** POST `/ipn/sepay` (hoặc dev-confirm) 1 lần → credit +N. POST LẠI cùng payload → credit KHÔNG đổi. (Đã verify với VietQR.)
2. **Test sai số tiền:** gửi IPN với `transferAmount` lệch → credit KHÔNG cộng, có dòng log `WARNING sepay: ... số tiền lệch`.
3. **Test token sai:** POST `/ipn/sepay` không header / sai token → 401.
4. **Đối soát cuối ngày:** so tổng `payments.amount_vnd WHERE status=SUCCEEDED` (admin dashboard, `routers/admin.py:76`) với sao kê ngân hàng/MoMo thật. Lệch → tra log webhook ([12-logging-observability.md](12-logging-observability.md)).
5. **Cron audit ví:** `cache balance == SUM(ledger)` phải khớp tuyệt đối (bất biến ví ACID).

---

## 10. Giới hạn đã biết (đọc trước khi scale)

- **`resolve_bank_payment_org` quét O(số org)** (`billing.py:114`): vòng lặp mọi org tìm payment PENDING khớp memo. Chấp nhận được khi webhook tần suất thấp. **Trước khi mở bán rộng**, thay bằng bảng GLOBAL `memo → org` (mẫu `webhook_events` trong SYSTEM_DESIGN). TODO đã ghi trong code.
- **VietQR amount fix trong QR**: user sửa tay số tiền khi chuyển → IPN bắt lệch → không cộng (an toàn nhưng cần admin gỡ). Cân nhắc cho phép memo-không-amount sau này.
- **Stripe/Visa quốc tế** 🔜: chưa có adapter. Khi làm pha sau, theo đúng pattern: tạo Payment PENDING → webhook Stripe (`checkout.session.completed`) verify `Stripe-Signature` → `apply_topup`. KHÔNG tin redirect.

---

## Việc cần làm (checklist)

- [ ] Đăng ký tài khoản ngân hàng doanh nghiệp + SePay → set `VIETVID_BANK_*` + `VIETVID_SEPAY_TOKEN`, trỏ webhook SePay về prod.
- [ ] **TẮT `VIETVID_BILLING_DEV` ở prod** (`=0`) — cổng dev cộng tiền không cần bank.
- [ ] Verify e2e trên prod: nạp thật 1 lần nhỏ → credit cộng đúng → poll thấy `succeeded`.
- [ ] Verify idempotent + sai-tiền + sai-token trên prod (mục 9.1-9.3).
- [ ] Đăng ký MoMo merchant → set 3 key MoMo → test sandbox → chuyển PROD endpoint.
- [ ] (Tuỳ chọn) Đăng ký VNPay → set TMN_CODE/HASH_SECRET → đổi URL prod.
- [ ] Thay `resolve_bank_payment_org` O(org) bằng bảng GLOBAL `memo→org` TRƯỚC khi traffic webhook cao.
- [ ] Thiết lập đối soát cuối ngày: so doanh thu admin dashboard vs sao kê thật.
- [ ] 🔜 Flow refund tiền nạp (status REFUNDED + trừ credit chưa dùng + chính sách ở [19-support.md](19-support.md)).
- [ ] 🔜 Hoá đơn VAT (chỉ khi có khách công ty yêu cầu) — nhà cung cấp HĐĐT + lưu link vào `raw_payload`.
- [ ] 🔜 Stripe/Visa cho quốc tế (pha sau) — webhook + verify chữ ký, không tin redirect.
