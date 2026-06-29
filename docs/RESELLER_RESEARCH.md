# Reseller Seedance 2.0 cho Vyra — BẢN ĐÃ XÁC MINH (2026-06-29)

Đối chiếu 3 bộ nghiên cứu (workflow của tôi + GLM + Gemini), **verify lại từng số trên TRANG GỐC** của nhà cung cấp + audit đối kháng. Quy ước: ✅ = đọc được trên chính trang nhà cung cấp; ⚠️ = trang chặn bot/JS-render, chỉ có nguồn thứ cấp. Mọi số là **$/giây video OUTPUT**, Seedance **2.0 thật** (không phải 1.0/1.5), trừ khi ghi khác.

## Gỡ mâu thuẫn (số nào đúng/sai)
- **Atlas $0.022/s = SAI** (số "ma" từ blog cũ của chính Atlas, cấu trúc tier khác). Thật: **Mini $0.056/s, Fast $0.09/s, Std $0.112/s** (✅ catalog live, giá "from").
- **CometAPI: $0.0504/s (2.0-fast 480p) = ĐÚNG** ✅. "$0.063 flat" là tier **Standard** (không phải Fast, không flat).
- **Segmind "$0.0043/s GPU + bắt $39/mo" = SAI/gây hiểu lầm.** Thật: **$0.0562/s (fast 480p)** ✅, token-based tuyến tính, **min nạp $10**, $39/mo là gói TÙY CHỌN không bắt buộc. Không có tier "mini" cho 2.0.
- **Kie.ai:** số $0.05 là **tier MINI**; Standard 2.0 480p **~$0.09/s**. Trang 403 → ⚠️ chỉ nguồn thứ cấp. **Có khiếu nại Trustpilot "charged nhưng kẹt/không nhận video, không hoàn".**
- **Crun.ai: CÓ THẬT** nhưng rất mới, 0 review độc lập, backend không khai báo (nghi wrapper), giá không khoá. $0.0536/s (⚠️ via-proxy).
- **Novita: KHÔNG có Seedance 2.0** (chỉ V1.0/1.5) → **LOẠI**.
- **OpenRouter:** phí thẻ **+5.5% + tối thiểu $0.80/lần nạp** ✅; crypto +5% no-min. Là **first-party ByteDance host** (không wrapper).

## Bảng giá đã verify (Seedance 2.0 thật)

| Provider | 480p $/s | 720p $/s | Billing | Tin cậy | Verdict |
|---|---|---|---|---|---|
| **Runware** | **$0.06** | $0.13 | per-giây output, **KHÔNG input-multiplier** | ✅ own-page | **đáng tin + rẻ** |
| **OpenRouter** | **$0.0538** (from) | ~$0.12 | token, first-party | ✅ own-page | **đáng tin + rẻ** |
| **CometAPI** | **$0.0504** | $0.108 | per-giây output | ✅ own-page | rẻ nhất, nhưng reseller + payment chưa rõ |
| Crun.ai | $0.0536 | $0.116 | credits (input+output) | ⚠️ proxy | dark-horse rủi ro |
| Segmind | $0.0562 | $0.121 | token tuyến tính | ✅ own-page | OK, min $10, hold $1.21 |
| Atlas Cloud | $0.056 (Mini) | ~$0.056 | token, **input-bẫy 2x ở i2v/v2v** | ✅ (giá "from") | non-refundable |
| **PiAPI (nay)** | $0.07–0.08 | $0.14–0.16 | per-giây | ✅ own-page | wrapper Dreamina, **ban-risk** |
| Kie.ai | ~$0.05 (Mini)/~$0.09 (Std) | $0.165–0.205 | credits (input+output) | ⚠️ 403 | khiếu nại tiền |
| fal.ai | ~$0.108 | $0.2419 | token | ⚠️ 480p không quote | host chính thống nhưng ĐẮT |
| Replicate | ⚠️ không đọc được | ⚠️ | per-giây | ⚠️ JS-render | chưa verify |
| Novita | ❌ không 2.0 | ❌ | — | ✅ | **LOẠI** |

## Bảng THANH TOÁN & phí Visa (trả từ VN)

| Provider | Nhận | Phụ phí thẻ | Min nạp | Thẻ VN? | Cổng |
|---|---|---|---|---|---|
| **Runware** | Card (Visa/MC/Amex/JCB/UnionPay) | **Không** | $20 | ⚠️ Stripe — thẻ VN bật QT thường chạy | Stripe |
| **OpenRouter** | Card, Alipay, **Crypto USDC** | **Card +5.5% +$0.80**; crypto +5% | không min | ⚠️ Stripe hay từ chối thẻ VN → **crypto là đường thoát** | Stripe + Coinbase |
| **CometAPI** | Card, PayPal, Crypto, **VietQR(?)** | chưa công bố | card: 0; crypto: $20 | ⚠️ **tín hiệu VietQR** (chỉ affiliate, phải verify) | Stripe ⚠️ |
| **Atlas Cloud** | Card, Alipay, WeChat, **Crypto** | **Không** | $10 | ⚠️ Stripe ok; **tiền NON-REFUNDABLE** | Stripe |
| PiAPI (nay) | **Stripe + Crypto** | Không (có volume bonus) | — | ⚠️ Stripe | Stripe + crypto |
| Segmind | Card | chưa công bố | $10 | ⚠️ nhận card Ấn (tốt) | — |
| WaveSpeed | Card, PayPal, Alipay, WeChat | chưa công bố | $1 free | ⚠️ **TẮT auto-topup** (phốt charge bất ngờ) | Stripe |
| Novita | Card + PayPal | chưa công bố | >$10 | ⚠️ Stripe hay risk-decline | Stripe |

**Mấu chốt VN:** chỗ có **crypto (USDC/USDT)** = đường thoát chắc khi Visa/MC VN bị soft-decline: **OpenRouter, CometAPI, Atlas, PiAPI**. CometAPI là chỗ DUY NHẤT có tín hiệu VietQR (chưa verify chính thức).

## Chi phí thực @10.000 giây/tháng (gồm phí thẻ)

| Hạng | Provider | $/s landed | $/tháng | vs PiAPI |
|---|---|---|---|---|
| 🥇 | CometAPI | $0.0504 | **$504** | −37% |
| 🥈 | Crun.ai | ~$0.0509–0.0536 | $509–536 | −33–36% |
| 🥉 | OpenRouter | $0.0568 (card) / $0.0565 (crypto) | $565–568 | −29% |
| 4 | Runware | $0.06 | $600 | −25% |
| — | PiAPI (nay) | $0.08 | $800 | baseline |

> Nạp NHỎ đổi thứ hạng OpenRouter: $0.80 floor thành 7–16% nếu nạp <$50. Vyra volume cao nạp ≥$500 → phí ≈ 5.5%.
> ⚠️ **Bẫy input-multiplier:** nếu dùng **video-to-video** (clip tham chiếu), Atlas/Kie/Crun/EvoLink tính cả giây input → đắt hơn bảng. **Runware + OpenRouter KHÔNG có** → giá thật bất kể chế độ. (Ảnh-1-khung-đầu của Vyra là image, không phải video clip → bẫy này chủ yếu hại v2v, cần verify tận mắt.)

## TOP PICK
- 🏆 **Runware $0.06/s** — đáng tin + rẻ thật, **host hợp pháp** (peer fal.ai, KHÔNG wrapper → không ban-risk như PiAPI/Kie/Crun), KHÔNG phí ẩn, KHÔNG input-multiplier, verified-on-own-page. Cắt 25% ($600 vs $800). Đánh đổi: min nạp $20, card-only.
- 🥈 **OpenRouter $0.0538 (+5.5%→~$0.0568)** — first-party, **có crypto USDC = payability VN tốt nhất** khi thẻ bị từ chối. Cắt 29%.
- 🥉 **CometAPI $0.0504** — RẺ NHẤT verified + tín hiệu VietQR/crypto, nhưng là reseller + chi tiết thanh toán chỉ từ affiliate → phải verify in-dashboard.
- **Crun.ai** rẻ tương đương nhưng quá mới + backend mờ + giá không khoá → chỉ test thử, đừng dồn spend.

## QA bắt buộc trước khi chuyển spend
1. **Test thanh toán VN trước** (rào cản lớn nhất): nạp nhỏ bằng Visa/MC VN bật thanh toán quốc tế. Runware $20 (non-refund nhưng credit không hết hạn); OpenRouter $50 → **decline thì thử crypto USDC ngay**; CometAPI $10 + **kiểm VietQR có thật trong dashboard không**.
2. **Verify giá trong console** khi submit job (đặc biệt chế độ i2v/v2v — có tính giây input không).
3. **Verify chất lượng THẬT:** chạy 5-10 job y prompt Vyra đang dùng, **trích khung hình xem mắt** — đảm bảo là Seedance 2.0 thật (không bị route ngầm sang mini/1.x).
4. **Test độ tin job:** ~50 job liên tiếp, đo fail-rate + thời gian. Kie soi kỹ (phốt kẹt/không hoàn).
5. **Tắt auto-topup** ở mọi provider (WaveSpeed có phốt charge bất ngờ).
