# Đơn vị kinh tế (unit economics)

Bóc tách giá vốn (COGS) MỖI video theo provider, vì sao **video là cột chi phí chính**, biên gộp ra sao, và — quan trọng nhất — **cách ĐO chi phí thật** từ chính code đang chạy (`estimate_job_cost` trước render, `actual_cost_usd` sau render). Đây là file để chủ dự án quyết giá tỉnh táo, không bịa số.

**Trạng thái:** ⚙️ một phần — công thức + estimator + ledger đã code & verify thật; CON SỐ provider còn là **ước lượng từ config default**, CHƯA đo trên hoá đơn provider thật (Vyra mới ra mắt, render trong app đang mock vì thiếu key — xem [HANDOFF.md §7](../HANDOFF.md)).

**Liên quan:** [06-providers.md](06-providers.md) (provider & key), [08-pricing-plans-credits.md](08-pricing-plans-credits.md) (định giá credit), [09-free-tier-abuse.md](09-free-tier-abuse.md) (siết free vì render tốn tiền), [21-financial-model.md](21-financial-model.md) (hoà vốn), [05-queue-worker-rendering.md](05-queue-worker-rendering.md) (vòng render → settle).

---

## 1. TL;DR — 3 điều phải nhớ

1. **Video là ~80-95% giá vốn mỗi clip.** Giọng Vbee và ảnh Flux/Gemini rẻ hơn một bậc. Muốn cải thiện biên → tối ưu CHI PHÍ VIDEO trước, đừng phí sức tối ưu giọng.
2. **Chưa có số thật.** Mọi con số dưới đây tính từ **config default** (`config/registry.py`), KHÔNG phải hoá đơn provider. Phải đo bằng `actual_cost_usd` trên ≥30 job thật trước khi khoá giá.
3. **Hệ thống đã có sẵn 2 mốc đo:** `estimate_job_cost` (báo giá TRƯỚC) và `job.actual_cost_usd` (chi phí THẬT sau render, ghi vào DB). Đo thật = query cột này, không cần thêm hạ tầng.

---

## 2. Giá vốn (COGS) một video gồm những gì

Nguồn sự thật: hàm `estimate_job_cost()` tại [`video_engine/providers/routing.py:72`](../../video_engine/providers/routing.py) (báo giá) và biến `actual_cost` cộng dồn trong [`video_engine/render_service.py`](../../video_engine/render_service.py) (chi phí thật). Một video = tổng của:

| Thành phần | Provider | Cộng ở đâu (code) | Tính theo |
|---|---|---|---|
| **Video clip** | Seedance (PiAPI) / Kling/Veo (fal) | `render_service.py:278` `video_cost = seconds × route.usd_per_second` | **giây × đơn giá/giây** ← cột chính |
| Ảnh khung đầu / hero | Flux (fal) / Gemini | `render_service.py:240,476` `+= video_image_cost_usd` | mỗi ảnh sinh ra |
| Clean-plate (tách SP) | local crop/seg | `render_service.py:113` `+= clean_result.cost` | thường ~$0 (crop pixel gốc) |
| Giọng đọc | Vbee | gộp trong `other_usd` của estimate | rất rẻ (vài trăm đồng) |
| Compose / QA / ffmpeg | máy worker | gộp trong `other_usd` | ~0 (CPU local) |
| Finishing | local | `render_service.py:306` `+= finishing_cost` | ~0 |

> Trong estimator, giọng + compose + QA bị gộp thành **một hằng `other_usd = 0.01` USD** ([`routing.py:87`](../../video_engine/providers/routing.py)) — tức ~250đ, là **ước lượng thô**, chưa tách riêng Vbee. Cần đo Vbee thật (xem §6).

---

## 3. Đơn giá provider — số ƯỚC LƯỢNG (từ config default)

⚠️ **TẤT CẢ số dưới đây là config default, KHÔNG phải giá thật trên hoá đơn.** Đánh dấu rõ "ước lượng, cần đo thật".

### 3.1 Video — đơn giá/giây (cột chi phí chính)

Nguồn: key `video_seedance_prices_json` tại [`config/registry.py:669`](../../config/registry.py). Đây là USD **mỗi giây** video:

| Model | 480p | 720p | 1080p |
|---|---|---|---|
| `seedance-2-fast` (draft, product_ad, kol_full) | $0.08 | $0.16 | — |
| `seedance-2` (premium) | $0.10 | $0.20 | $0.50 |

> Các dòng `*-less-restriction` trong config đã **không còn dùng** (xem ghi chú đầu `routing.py`: autovis né kiểm duyệt bằng text-prompt, không gửi mặt → policy `strict`).

**Ví dụ video 15 giây** (mặc định `seconds=15`, xem [`jobs.py:41`](../../app_api/jobs.py)):

| Loại | Model/res | Phép tính | Chi phí video (ước lượng) |
|---|---|---|---|
| product_ad / kol_full | fast 480p | 15 × $0.08 | **$1.20 ≈ 30.500đ** |
| premium | pro 720p | 15 × $0.20 | **$3.00 ≈ 76.200đ** |
| draft (xem trước) | fast 480p | 5 × $0.08 | $0.40 ≈ 10.200đ |

(Quy đổi VND: `fx_vnd_per_usd = 25400`, [`registry.py:652`](../../config/registry.py).)

> ⚠️ **Con số này CAO hơn nhiều** so với mốc "~3.000-12.000đ/video" trong quyết định vận hành. Lý do: (a) config default Seedance có thể KHÔNG khớp giá PiAPI/fal thật hiện tại; (b) "3-12k" có thể giả định clip ngắn hơn (5-8s) hoặc provider rẻ hơn. **→ Đây chính là lý do PHẢI đo thật trước khi định giá.** Đừng tin con số ước lượng này, kể cả con số "3-12k". Xem §6 để đo.

### 3.2 Ảnh — Flux / Gemini

- `video_image_cost_usd = 0.039` USD/ảnh ≈ **990đ/ảnh** ([`registry.py:651`](../../config/registry.py)).
- Số ảnh mỗi video: **0 hoặc 1** (`n_images`, [`routing.py:80`](../../video_engine/providers/routing.py)). premium hoặc khi bật `video_clean_plate_enabled` → 1 ảnh; còn lại 0 (dùng thẳng ảnh SP user upload làm khung đầu).
- → Ảnh đóng góp tối đa ~990đ, **bằng ~1-3% chi phí video**.

### 3.3 Giọng — Vbee (RẺ)

- Estimator hiện gộp giọng vào `other_usd = 0.01` USD (~250đ) — **chưa tách riêng, chưa đo Vbee thật**.
- Key chi phí giọng có sẵn nhưng để 0: `tts_estimated_cost_per_call_usd = 0.0` ([`registry.py:562`](../../config/registry.py)) → **chưa cấu hình giá Vbee**.
- Quyết định vận hành: giọng Vbee ~vài trăm đồng/video → **không phải cột chi phí**. Đúng về bậc độ lớn, nhưng **vẫn cần đo** (xem §6.3).

---

## 4. Tổng giá vốn một video (ước lượng) + vì sao video là cột chính

Ghép §3 cho video **15s** (giả định 1 ảnh + giọng + local):

| Thành phần | product_ad 480p | premium 720p | % của tổng (premium) |
|---|---|---|---|
| Video clip | 30.500đ | 76.200đ | **~95%** |
| Ảnh (1) | 990đ | 990đ | ~1% |
| Giọng + compose (`other_usd`) | 250đ | 250đ | ~0,3% |
| **TỔNG COGS/video** | **~31.700đ** | **~77.400đ** | 100% |

(Tất cả ước lượng từ config default — **cần đo thật**.)

**Vì sao video chiếm gần hết:** chi phí video = `giây × đơn_giá_giây`, tỉ lệ tuyến tính với độ dài + độ phân giải + cấp model. Ảnh là **một lần** (≤1 ảnh), giọng tính theo ký tự nhưng đơn giá Vbee thấp. Clip càng dài / res càng cao / model càng "pro" → chi phí phình theo video, không theo giọng/ảnh.

**Hệ quả vận hành (đã phản ánh trong các file khác):**
- Free tier PHẢI siết video: 480p / ≤20s / provider rẻ nhất / watermark / giới hạn số clip — xem [09-free-tier-abuse.md](09-free-tier-abuse.md).
- Đòn bẩy biên lợi nhuận nằm ở **chọn model + giây + res theo gói**, không ở giọng. Router đa-provider (draft→rẻ, hero→xịn) là công cụ chính — xem [06-providers.md](06-providers.md).

---

## 5. Biên gộp & đòn bẩy lãi/lỗ

### 5.1 Cơ chế credit (đã code, verify thật)

- Giá bán: **1 credit = 150đ** (`CREDIT_PRICE_VND`, [`app_api/config.py:46`](../../app_api/config.py)).
- Quy đổi USD→credit DUY NHẤT: `credits = ceil(usd × 25400 / 150)` ([`pricing.py:10`](../../app_api/pricing.py)). Làm tròn **LÊN** → nền tảng không lỗ lẻ.
- Vòng tiền: **HOLD** (giữ `ceil(est_credits × 1.5)`) → render → **SETTLE** `min(credit_thật, hold)` hoặc **REFUND** 100% nếu lỗi hệ thống ([`jobs.py:37,132`](../../app_api/jobs.py)). Chi tiết: [05-queue-worker-rendering.md](05-queue-worker-rendering.md).

### 5.2 Giá vốn quy ra credit (ước lượng)

`credits_cost = ceil(COGS_usd × 25400 / 150)`:

| Loại (15s) | COGS ước lượng | → credit (giá vốn) | Bán bao nhiêu credit để có biên? |
|---|---|---|---|
| product_ad 480p | $1.21 | ceil(1,21×169,3) = **205 credit** | xem [08](08-pricing-plans-credits.md) |
| premium 720p | $3.05 | ceil(3,05×169,3) = **517 credit** | xem [08](08-pricing-plans-credits.md) |

(169,3 = 25400/150 = số credit/USD.)

> **Cảnh báo free tier:** `FREE_GRANT_CREDITS = 300` ([`config.py:74`](../../app_api/config.py)). Nếu giá vốn 1 video premium ~517 credit, free user **không đủ** làm 1 premium (đúng ý đồ — free phải bị ép xuống 480p rẻ ~205 credit, vẫn để dư). Đây là lý do memory `free-grant-min-hold` yêu cầu FREE_GRANT > HOLD của job rẻ nhất. **Kiểm lại sau khi đo COGS thật** — nếu giá vốn thật thấp hơn nhiều, 300 credit có thể quá rộng.

### 5.3 Biên gộp & đòn bẩy

Biên gộp/video = `(giá_bán_credit − COGS_credit) / giá_bán_credit`. Mục tiêu vận hành **40-60%**.

Ba đòn bẩy (theo độ ảnh hưởng, lớn→nhỏ):
1. **Giây video** — tuyến tính. Giảm độ dài mặc định free từ 15s→8s cắt ~½ chi phí lớn nhất.
2. **Model + res** — fast 480p vs pro 720p chênh ~2,5× (§3.1). Gán đúng model theo gói.
3. **Provider** — route draft sang model rẻ; chỉ hero dùng model xịn. Số thật quyết định nên giữ Seedance hay chuyển Kling/Veo.

**Đòn bẩy LỖ (cảnh báo):**
- Báo giá thấp hơn chi phí thật → SETTLE bị kẹp `min(actual, hold)` = nền tảng **nuốt phần vượt hold**. Hold = est × 1,5 là đệm; nếu provider tăng giá > 50%, đệm vỡ → lỗ. **→ Theo dõi `actual_cost_usd / est_cost_usd`; nếu thường > 1,2 phải tăng đơn giá config.**
- REFUND 100% khi lỗi hệ thống: provider chập chờn → render fail → hoàn toàn bộ + đã tốn tiền gọi provider một phần. **Tỉ lệ fail cao = lỗ thầm.** Đo qua admin: % job REFUND.

---

## 6. CÁCH ĐO CHI PHÍ THẬT (làm trước khi khoá giá)

Đây là phần quan trọng nhất. **Đừng định giá bằng ước lượng config.**

### 6.1 Đo qua estimator (báo giá trước — đã hoạt động) ✅

Gọi trực tiếp `estimate_job_cost` để xem báo giá hiện hệ thống tính:

```bash
cd /c/Users/NTD/Desktop/vietvid
PYTHONUTF8=1 /c/Python314/python -c "from video_engine.providers.routing import estimate_job_cost as e; import json; print(json.dumps(e('premium','final',15,'720p'), indent=2, ensure_ascii=False))"
```

→ in `video_usd`, `image_usd`, `other_usd`, `total_usd`, `total_vnd`. Đây là **số hệ thống đang báo cho user**, dựa trên config — vẫn là ước lượng cho tới khi config khớp giá thật.

### 6.2 Đo chi phí THẬT sau render (`actual_cost_usd`) — nguồn vàng 🔜

Khi đã điền key provider (GEMINI/PIAPI/fal — xem [HANDOFF.md §7](../HANDOFF.md)) và render thật, mỗi job ghi **chi phí thật** vào DB:

- Cộng dồn trong [`render_service.py`](../../video_engine/render_service.py): `actual_cost` += clean-plate + ảnh + **video (`seconds × usd_per_second`)** + finishing.
- Lưu vào `Job.actual_cost_usd` ([`jobs.py:132`](../../app_api/jobs.py) `job.actual_cost_usd = result.cost_usd`).

Query COGS thật trung bình theo loại (cần `VIETVID_DATABASE_URL`, xem [HANDOFF.md §6](../HANDOFF.md)):

```sql
SELECT kind, resolution, seconds,
       count(*)                              AS n_jobs,
       round(avg(actual_cost_usd)::numeric,4) AS avg_cost_usd,
       round(avg(actual_cost_usd)*25400)      AS avg_cost_vnd,
       round(avg(actual_cost_usd / nullif(est_cost_usd,0))::numeric,3) AS actual_over_est
FROM jobs
WHERE status IN ('READY','QA_FAIL') AND actual_cost_usd IS NOT NULL
GROUP BY kind, resolution, seconds
ORDER BY n_jobs DESC;
```

- `avg_cost_vnd` = **giá vốn thật/video** → thay vào §3, §4, §5.
- `actual_over_est` > 1,2 đều đặn → **báo giá thấp, tăng đơn giá config** (`video_seedance_prices_json`).
- Lấy ≥30 job/loại trước khi tin số. Lặp lại định kỳ (hàng tuần) — provider đổi giá thì số đổi.

### 6.3 Đo Vbee riêng (vì estimator đang gộp thô) 🔜

`other_usd` đang là hằng 0,01 USD, KHÔNG tách Vbee. Để biết giọng thật bao nhiêu:
1. Render thật một loạt video, xem hoá đơn Vbee (theo ký tự / số request) cho đúng khoảng thời gian.
2. Chia tổng tiền Vbee cho số video → **đ/video thật cho giọng**.
3. Nếu muốn estimator chính xác hơn: set `tts_estimated_cost_per_call_usd` ([`registry.py:562`](../../config/registry.py)) và tách khỏi `other_usd` (cần sửa `routing.py` — hiện chưa làm).

> Đọc ToS gói thương mại Vbee trước khi bán lại (markup credit hợp lệ với điều kiện mua đúng gói — xem quyết định vận hành & [06-providers.md](06-providers.md)).

### 6.4 Đối chiếu hoá đơn provider (sự thật cuối cùng) 🔜

`actual_cost_usd` vẫn tính từ **config đơn giá**, không phải hoá đơn. Mỗi tháng:
1. Lấy tổng tiền THẬT từ dashboard PiAPI/fal/Vbee.
2. So với `SUM(actual_cost_usd)` cùng kỳ trong DB.
3. Lệch > 10% → sửa đơn giá trong `config/registry.py` cho khớp hoá đơn. **Hoá đơn thắng.**

---

## 7. Việc cần làm (checklist)

- [ ] Điền key provider (GEMINI/PIAPI/fal) để render THẬT thay vì mock — [HANDOFF.md §7](../HANDOFF.md).
- [ ] Render ≥30 job thật mỗi loại (product_ad/kol_full 480p, premium 720p) để có mẫu `actual_cost_usd`.
- [ ] Chạy query §6.2 → ghi **giá vốn THẬT/video (VND)** vào §3/§4/§5 thay số ước lượng.
- [ ] Kiểm `actual_over_est`: nếu > 1,2 thường xuyên → tăng `video_seedance_prices_json` cho khớp.
- [ ] Đo Vbee riêng (§6.3) → xác nhận giọng thật ~vài trăm đồng; cân nhắc tách khỏi `other_usd`.
- [ ] Đối chiếu hoá đơn PiAPI/fal/Vbee hàng tháng với `SUM(actual_cost_usd)` (§6.4); lệch >10% thì sửa config.
- [ ] Xác minh con số "3.000-12.000đ/video" của quyết định vận hành: đúng/sai sau khi có số thật? Nếu COGS thật cao hơn → định lại giá ([08](08-pricing-plans-credits.md)) hoặc rút ngắn clip free ([09](09-free-tier-abuse.md)).
- [ ] Sau khi có COGS thật, kiểm lại `FREE_GRANT_CREDITS=300` còn hợp lý không (memory `free-grant-min-hold`).
- [ ] Khoá biên gộp mục tiêu (40-60%) cho từng gói → đẩy vào [08-pricing-plans-credits.md](08-pricing-plans-credits.md) & [21-financial-model.md](21-financial-model.md).
- [ ] Theo dõi % job REFUND trong admin ([11-admin-panel.md](11-admin-panel.md)) — fail cao = lỗ thầm.
