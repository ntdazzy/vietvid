# Free tier & chống lạm dụng

Mục đích: giải thích vì sao gói FREE của Vyra **đốt tiền thật** (mỗi render gọi API trả phí), và cách siết cứng để free vừa đủ "nếm thử" mà không thành lỗ hổng đốt ví founder. Bao gồm: trần kỹ thuật free, mối quan hệ `FREE_GRANT_CREDITS` ↔ HOLD tối thiểu, chống đa tài khoản, rate limit, và trần chi phí free toàn hệ thống.

Trạng thái: ⚙️ một phần — rate limit + clamp theo gói + free-grant **đã có**; watermark/giới-hạn-số-video-tháng/chống-multi-account/trần-chi-phí-toàn-hệ-thống **chưa làm**.

Liên quan: [07-economics.md](07-economics.md) (chi phí 1 video), [08-pricing-plans-credits.md](08-pricing-plans-credits.md) (gói & credit), [06-providers.md](06-providers.md) (provider rẻ cho free), [10-payments.md](10-payments.md) (nạp tiền lên gói trả phí), [11-admin-panel.md](11-admin-panel.md) (theo dõi/khoá lạm dụng), [12-logging-observability.md](12-logging-observability.md) (đo chi phí thật).

---

## 1. Vì sao FREE đốt tiền thật (khác SaaS thường)

SaaS phần mềm thuần: thêm 1 user free ≈ 0đ (chỉ tốn DB/băng thông cỏn con). **Vyra thì KHÁC** — mỗi video free render là một lệnh gọi API trả phí ra ngoài (PiAPI/fal cho video, Vbee cho giọng, Flux cho ảnh). User không trả gì, nhưng founder vẫn **phải trả nhà cung cấp bằng tiền thật**.

Đường tiền khi 1 user free bấm "Tạo":

```
User free bấm Tạo (0đ)
   → POST /v1/jobs → HOLD credit (credit FREE tặng sẵn)
   → worker render → gọi PiAPI/fal (video) + Vbee (giọng)  ← TIỀN THẬT RA
   → SETTLE/REFUND ví credit (chỉ là sổ cái nội bộ, KHÔNG hoàn tiền API)
```

Điểm mấu chốt: **credit là tiền ảo nội bộ; hoá đơn provider là tiền thật.** Khi user free hết credit tặng, ta ngừng cho render — nhưng các render đã chạy thì **đã trả phí rồi, không lấy lại được**. Nên free tier không phải "miễn phí với ta", mà là **chi phí marketing/acquisition** có trần.

> Số chi phí thật mỗi video: **chưa đo** (Vyra mới ra mắt, render trong app đang mock — xem [HANDOFF.md §7](../HANDOFF.md)). Ước lượng định hướng ~3.000–12.000đ/video tuỳ provider/độ dài/độ phân giải, **cần đo thật** sau khi cắm key. Cách đo ở [07-economics.md](07-economics.md).

---

## 2. Trần kỹ thuật cho FREE — siết cứng từng tầng

Nguyên tắc: free phải đủ để user **thấy chất lượng Vyra**, nhưng mỗi video free phải là cấu hình **rẻ nhất + không-dùng-thương-mại-được** (có watermark) để không ăn mòn doanh thu.

| Tầng siết | Free | Trả phí (Pro/Business) | Trạng thái | File / chốt chặn |
|---|---|---|---|---|
| Độ phân giải tối đa | **480p** | 720p–1080p | ✅ đã clamp | `app_api/validate.py:17` `_PLAN_LIMITS` |
| Thời lượng tối đa | **≤20s** | 60s (pro) / 120s (business) | ✅ đã clamp | `app_api/validate.py:18` |
| Provider video | rẻ nhất (`seedance-2-fast` 480p) | chọn được model xịn | ✅ route mặc định rẻ | `video_engine/providers/routing.py:50` `route_video` |
| Watermark logo Vyra | **BẮT BUỘC có** | KHÔNG | 🔜 chưa làm | xem §6 |
| Số video / tháng | có trần (đề xuất ~5–10) | theo gói credit | 🔜 chưa làm | xem §5 |
| Credit tặng | `FREE_GRANT_CREDITS` (mặc định 300) | mua thêm | ✅ có | `app_api/config.py:74` |

### 2.1 Cách clamp đang chạy (✅ đã có)

`validate_and_clamp(spec_input, plan_code)` chạy **trước khi HOLD/enqueue** (`app_api/routers/jobs.py:69`). Nó **không từ chối** user vượt trần — nó **kẹp (clamp) về trần gói + ghi note**, nên free request 1080p/60s vẫn chạy nhưng bị hạ xuống 480p/20s:

```python
# app_api/validate.py:17
_PLAN_LIMITS = {
    "free":     {"max_seconds": 20,  "max_resolution": "480p"},
    "pro":      {"max_seconds": 60,  "max_resolution": "1080p"},
    "business": {"max_seconds": 120, "max_resolution": "1080p"},
}
```

`plan_code` lấy từ `tenancy.org_plan_code(org_id)` (`app_api/tenancy.py:135`); org mới bootstrap luôn `plan_code="free"` (`tenancy.py:76`). → **Free bị giam ở 480p/20s ở tầng server, không bypass được từ client.** Đây là chốt chặn tốt: dù UI gửi gì, server vẫn kẹp.

> Cách kiểm chứng: tạo token dev → bootstrap (org free) → `POST /v1/jobs` với `resolution:"1080p", seconds:60` → response `notes` phải có "độ phân giải 1080p → trần gói 480p" và "thời lượng 60s → trần gói 20s". HOLD tính trên giá trị đã kẹp.

---

## 3. `FREE_GRANT_CREDITS` vs HOLD tối thiểu — bất biến phải giữ

**Đây là cái bẫy đã từng cắn** (memory `free-grant-min-hold`, [HANDOFF.md §13](../HANDOFF.md)).

Khi tạo job, ví **HOLD** trước `hold = ceil(est_credits × 1.5)` (`app_api/wallet.py`, [HANDOFF.md §5](../HANDOFF.md)). Job rẻ nhất (draft 5s/480p, `seedance-2-fast`) có `est ≈ 70` → **HOLD ≈ 105 credit**.

→ Nếu `FREE_GRANT_CREDITS ≤ 105`, user free vừa tạo workspace bấm Tạo sẽ **dính 402 ngay** (không đủ credit để HOLD) — coi như free tier chết. Mặc định cũ 100 đã gây đúng lỗi này.

**Bất biến (BẮT BUỘC giữ):**

```
FREE_GRANT_CREDITS  >  HOLD của job rẻ nhất (~105)
```

Mặc định hiện tại = **300** (`app_api/config.py:74`) ≈ vài draft thử. Chỉnh qua env `FREE_GRANT_CREDITS`.

### 3.1 Khi đổi giá → PHẢI check lại bất biến này

Mọi lần đổi `CREDIT_PRICE_VND`, `USD_TO_VND`, hoặc đổi provider/giá → HOLD tối thiểu đổi theo → **phải tính lại `FREE_GRANT_CREDITS`**. Công thức:

```
est_credits = usd_to_credits( estimate_job_cost("product_ad", "draft", 5, "480p")["total"] )
hold_min    = ceil(est_credits × 1.5)
FREE_GRANT_CREDITS  nên  ≥  hold_min × (số draft muốn cho free thử, đề xuất 2–3)
```

`estimate_job_cost` ở `video_engine/providers/routing.py:72`; quy đổi `usd_to_credits` ở `app_api/pricing.py`. → chi tiết quy đổi ở [08-pricing-plans-credits.md](08-pricing-plans-credits.md).

> ⚠️ Đừng đặt `FREE_GRANT_CREDITS` quá cao: mỗi credit free = chi phí provider thật khi user tiêu. 300 cho phép ~2 draft; cao hơn = mời gọi farm account (xem §4). Cân giữa "đủ nếm thử" và "không thành mỏ vàng cho kẻ lạm dụng".

---

## 4. Chống đa tài khoản (multi-account farming) 🔜 chưa làm

**Lỗ hổng:** `FREE_GRANT_CREDITS` tặng **mỗi org** lúc bootstrap. Một người tạo N email → N org → N×300 credit free → render N×vài video bằng tiền của founder. Đây là rủi ro chi phí **lớn nhất** của free tier.

Hiện trạng chốt chặn:
- ✅ `grant_once` chỉ tặng **đúng 1 lần / org** (idempotent, khoá ví FOR UPDATE — `app_api/tenancy.py:101`). → Chặn farm-bằng-cách-bootstrap-lại-cùng-org, **không** chặn farm-bằng-email-mới.
- ⚙️ Rate limit auth 10/60s/IP (`app_api/config.py:141`) cản đăng ký hàng loạt **cùng IP** trong thời gian ngắn — nhưng kẻ farm dùng proxy/đăng ký rải rác vẫn lọt.
- 🔜 **Chưa có:** email-verify bắt buộc trước khi cấp free credit, chặn email tạm (disposable), fingerprint thiết bị, giới hạn free-grant theo IP/ngày.

### 4.1 Hàng rào đề xuất (làm dần, rẻ → đắt)

| Biện pháp | Chặn được gì | Chi phí làm | Trạng thái |
|---|---|---|---|
| **Bắt verify email TRƯỚC khi cấp free credit** | email rác dùng-một-lần | thấp (đã có flow verify, `config.py:154` `VERIFY_TOKEN_TTL`) | 🔜 |
| **Chặn domain email tạm** (mailinator, 10minutemail…) | farm email tạm | thấp (1 blocklist) | 🔜 |
| **Giới hạn free-grant theo IP / ngày** (vd ≤3 org free mới/IP/ngày) | farm rải rác cùng IP | trung (cần đếm cross-org → admin/global table) | 🔜 |
| **Bắt OTP SĐT VN trước khi cấp free** (Sóng sau) | farm quy mô lớn | cao (tốn phí SMS) | 🔜 |
| **Giảm free-grant + tăng giá trị "free preview"** (cho xem nhưng watermark nặng, không tải) | làm farm vô nghĩa về kinh tế | trung | 🔜 |

> Nguyên tắc kinh tế: không cần chặn 100% — chỉ cần làm **chi phí farm > giá trị credit free** thì kẻ lạm dụng tự bỏ. Watermark + free-grant vừa-đủ + verify email đã loại 90% trường hợp.

### 4.2 Việc cụ thể khi làm verify-gate

Free-grant đang cấp **vô điều kiện** trong `bootstrap_tenant` (`app_api/tenancy.py:101`). Để gate theo verify:
1. Kiểm `user.email_verified` trước khi gọi `wallet.grant_once(...)`.
2. Nếu chưa verify → tạo org + ví nhưng **chưa tặng credit**; tặng khi user verify xong (endpoint `/v1/auth/verify`).
3. Lưu ý: dev-token tự đặt `email_verified=True` (`tenancy.py:39`) → chỉ áp gate khi `auth_mode()=="supabase"` (prod thật), tránh chặn QA dev.

---

## 5. Giới hạn số video / tháng cho free 🔜 chưa làm

Hiện free chỉ bị giới hạn **gián tiếp** qua hết credit (300 credit ≈ 2 draft). Khi reset credit hàng tháng (M2 — `config.py:71` ghi rõ "Reset hàng tháng = M2") được bật, cần thêm **trần cứng số video free/tháng** để credit-reset không thành vòi nước vô hạn.

Đề xuất (cần chốt theo kinh tế thật):
- Free: **≤5–10 video/tháng**, đều 480p/≤20s/có-watermark, provider rẻ nhất.
- Đếm ở tầng `POST /v1/jobs`: query số job READY của org trong tháng → nếu ≥ trần → 402/429 với thông điệp "Hết lượt free tháng này, nâng cấp để tạo tiếp".
- Trần này là **knob env** (vd `FREE_MONTHLY_VIDEO_CAP`) để chỉnh không cần deploy.

> Chưa quyết con số. Cần đo: chi phí thật/video (§1) × trần/tháng × số user free dự kiến = **trần chi phí free/tháng** ta chịu được (§7).

---

## 6. Watermark cho free 🔜 chưa làm

Hiện `routers/jobs.py:295` chỉ ghi chú "serve MP4 không watermark — gói trả phí", **chưa có nhánh thêm watermark cho free**. Watermark là đòn bẩy kinh tế quan trọng: video free **vẫn đẹp để khoe**, nhưng **không dùng thương mại được** → user nghiêm túc phải nâng cấp.

Việc cần làm:
1. Trong engine render (hoặc bước compose ffmpeg), nếu `plan_code=="free"` → overlay logo Vyra góc dưới (ffmpeg `drawtext`/`overlay`, ffmpeg đã có trên máy — [HANDOFF.md §6](../HANDOFF.md)).
2. Truyền `plan_code` (hoặc cờ `watermark:bool`) từ `POST /jobs` xuống spec render. Engine stateless → cờ phải đi qua `spec`, KHÔNG query DB trong engine.
3. Đảm bảo watermark **không** áp khi gói trả phí (kiểm bằng QA thật: render 1 free + 1 pro, trích khung hình so sánh).

> Watermark nhẹ-mà-rõ: đủ để không xài thương mại, không phá trải nghiệm xem thử. Đừng làm watermark che nửa màn (phản tác dụng marketing).

---

## 7. Trần chi phí free toàn hệ thống 🔜 chưa làm

Đây là **van an toàn cuối cùng** cho founder: kể cả mọi hàng rào trên thủng, tổng tiền free đốt mỗi ngày/tháng **không được vượt ngân sách**.

Cơ chế đề xuất:
- **Đếm tổng `cost_usd` thật của các job free** (engine trả `cost_usd` trong `RenderResult` — [HANDOFF.md §5](../HANDOFF.md)) trong cửa sổ ngày/tháng.
- Knob env: `FREE_DAILY_BUDGET_USD` (vd 5–10$/ngày khởi đầu).
- Khi tổng chi free chạm trần → **tạm dừng cấp render free toàn hệ thống** (free user thấy "Lượt tạo miễn phí tạm đầy, thử lại sau hoặc nâng cấp"), trả phí vẫn chạy bình thường.
- Hiển thị số này ở admin ([11-admin-panel.md](11-admin-panel.md)) để founder thấy free đang đốt bao nhiêu.

> Vì sao cần: render là tiền-thật-ra-ngoài. Một bug hay đợt farm có thể đốt sạch ngân sách trong vài giờ. Trần toàn-hệ-thống biến "có thể mất không-giới-hạn" thành "mất tối đa $X/ngày" — ngủ ngon hơn. Số $X cần đặt sau khi đo chi phí thật/video (§1).

---

## 8. Rate limit — đang chạy ✅

`app_api/ratelimit.py` (middleware, cửa sổ cố định trong-tiến-trình). Đủ cho MVP 1-box; prod đa-instance phải đổi backend sang Redis (knob giữ nguyên — `ratelimit.py:3`).

| Bucket | Mặc định | Áp cho | Chống |
|---|---|---|---|
| `auth` | **10 / 60s / IP** | login/register/reset/verify/dev-token (`ratelimit.py:30`) | brute-force + farm đăng ký lấy 300 credit |
| `expensive` | **30 / 60s / IP** | POST `/v1/jobs`, `/images/generate`, `/voice/preview`, `/compose` (`ratelimit.py:33`) | đốt tiền provider + ffmpeg |
| `default` | **120 / 60s / IP** | mọi route còn lại | spam chung |

Knob env (`app_api/config.py:139`): `VIETVID_RATE_LIMIT` (bật/tắt), `VIETVID_RL_AUTH`, `VIETVID_RL_EXPENSIVE`, `VIETVID_RL_DEFAULT` — định dạng `"N/giây"`.

Vượt trần → HTTP **429** + header `Retry-After` (`ratelimit.py:81`). IP lấy từ `X-Forwarded-For` (sau proxy Railway/Vercel/Cloudflare) rồi tới client trực tiếp (`ratelimit.py:52`).

> ⚠️ **Prod multi-instance:** rate limit hiện đếm **trong từng tiến trình**. Chạy 2+ worker/instance trên Railway → mỗi instance có bộ đếm riêng → trần thực tế = N×limit. Khi scale ngang, **bắt buộc** chuyển sang Redis INCR+EXPIRE (Upstash/Redis Railway). Liên quan [05-queue-worker-rendering.md](05-queue-worker-rendering.md) (đã cần Redis cho queue → dùng chung).

> ⚠️ IP từ `X-Forwarded-For` chỉ tin được khi đứng sau proxy mình kiểm soát. Trên Railway/Vercel header này do platform đặt — OK. Nếu app từng nhận request trực tiếp (không proxy), kẻ tấn công giả `X-Forwarded-For` để né rate limit → đảm bảo prod LUÔN sau proxy.

---

## 9. Tóm tắt: free tier an toàn cần đủ 3 lớp

1. **Trần mỗi video** (480p/≤20s/provider rẻ/watermark) → mỗi video free rẻ nhất + không xài thương mại.
2. **Trần mỗi user** (free-grant vừa đủ + verify email + số-video/tháng) → 1 người không đốt nhiều.
3. **Trần toàn hệ thống** (rate limit + budget $/ngày) → kể cả thủng 2 lớp trên, tổng thiệt hại có nắp.

Đã có lớp 1 (một phần: thiếu watermark) + một phần lớp 3 (rate limit). Thiếu: watermark, verify-gate, chống multi-account, số-video/tháng, budget toàn-hệ-thống.

---

## Việc cần làm (checklist)

- [ ] **Đo chi phí thật/video** mỗi cấu hình free (480p/draft, 480p/final) sau khi cắm key provider — điền vào [07-economics.md](07-economics.md). (chặn việc đặt mọi con số trần bên dưới)
- [ ] **Watermark free**: thêm overlay logo Vyra trong render/compose khi `plan_code=="free"`; truyền cờ qua `spec` (engine stateless); QA thật so sánh free vs pro.
- [ ] **Verify-gate free-grant**: chỉ `grant_once` sau khi `email_verified` (chỉ áp ở `auth_mode()=="supabase"`); sửa `app_api/tenancy.py:101`.
- [ ] **Blocklist email tạm** trong flow đăng ký/verify.
- [ ] **Giới hạn free-grant theo IP/ngày** (chống multi-account farm rải rác) — cần bảng đếm cross-org (global, ngoài RLS).
- [ ] **Số video free/tháng**: knob `FREE_MONTHLY_VIDEO_CAP`, kiểm ở `POST /v1/jobs`; chốt con số sau khi đo chi phí.
- [ ] **Trần chi phí free toàn hệ thống**: knob `FREE_DAILY_BUDGET_USD`, đếm `cost_usd` job free, tạm dừng free khi chạm trần; hiện ở admin.
- [ ] **Rate limit → Redis** khi scale ngang prod (Upstash/Redis Railway); giữ nguyên knob env.
- [ ] **Đảm bảo prod luôn sau proxy** (Railway/Vercel/Cloudflare) để `X-Forwarded-For` đáng tin.
- [ ] Mỗi lần đổi `CREDIT_PRICE_VND`/`USD_TO_VND`/provider → **tính lại** `FREE_GRANT_CREDITS > HOLD min` (§3.1).
