# 06 — Tích hợp nhà cung cấp AI

Cách cắm key cho 3 lớp tốn tiền của Vyra: **video** (PiAPI/fal: Seedance/Kling/Hailuo), **ảnh** (Gemini/fal Flux), **giọng** (Vbee/Gemini TTS). Gồm: router chọn model, fallback, config-gate fail-closed, ghi nhận chi phí thật/job, lưu ý ToS gói thương mại, bảng so giá/chất lượng (ước lượng, cần đo).

**Trạng thái:** ⚙️ một phần — code provider + router + sổ ngân sách ĐÃ CÓ và fail-closed; còn THIẾU KEY thật nên render trong app đang mock. fal key đã có (dùng cho ảnh/hover web).

**Liên quan:** [05-queue-worker-rendering.md](05-queue-worker-rendering.md) (worker gọi provider) · [07-economics.md](07-economics.md) (chi phí/video) · [08-pricing-plans-credits.md](08-pricing-plans-credits.md) (markup credit) · [09-free-tier-abuse.md](09-free-tier-abuse.md) (siết provider rẻ cho free) · [15-security.md](15-security.md) (lưu key) · [02-infrastructure.md](02-infrastructure.md) (set env trên Railway).

---

## 1. Bức tranh tổng: 3 lớp provider

| Lớp | Provider code | Dịch vụ thật | Env gate | Trạng thái |
|---|---|---|---|---|
| **Video (i2v/t2v)** | `fal` (`video_stage/fal_video.py`), `seedance_piapi` (`video_stage/seedance_piapi.py`), `mock` (`video_stage/mock.py`) | fal.ai (Seedance/Kling/Hailuo/Luma...) · PiAPI (Seedance) | `FAL_API_KEY` / `PIAPI_API_KEY` | ⚙️ fal key ✅, PiAPI ❌ |
| **Ảnh** | `gemini` (`image_stage/gemini.py`), `local`/`mock` | Gemini 2.5 Flash Image · fal Flux (qua script) | `GEMINI_API_KEY` | 🔜 GEMINI ❌ (ảnh web dùng fal qua `scripts/gen_*.py`) |
| **Giọng** | `vbee`, `gemini_tts`, `edge` (free fallback) (`voice/tts_providers.py`) | Vbee · Gemini TTS · edge-tts (miễn phí) | `VBEE_*` / `GEMINI_API_KEY` | 🔜 chưa cắm; edge-tts free là last-resort |

**Nguyên tắc bất biến (đã code):** thiếu key → `ProviderNotConfiguredError` → job vào `WAITING_CONFIG`, **TUYỆT ĐỐI không chạy giả** rồi tính tiền. Đây là fail-closed, đừng nới.

> ⚠️ Config đọc thẳng `os.environ` (không có `.env` commit). Tên env var = TÊN FIELD VIẾT HOA. Ví dụ field `fal_api_key` → đặt biến `FAL_API_KEY`. Field định nghĩa ở `config/registry.py`, KHÔNG sửa `config/settings.py` tay.

---

## 2. Video — cách cắm key & chọn provider

### 2.1 Hai đường vào: fal vs PiAPI

Cả hai đều là **aggregator** bán lại model của ByteDance (Seedance), Kuaishou (Kling), v.v. Khác nhau ở API + giá + giới hạn gói:

- **fal.ai** (`FalVideoProvider`, `video_stage/fal_video.py`): 1 key mở khoá nhiều model. Submit → poll → tải mp4. Ảnh khung (i2v) gửi thẳng **data-URI base64**, không cần upload trước. Đây là đường **khuyến nghị bật trước** vì key đã có sẵn (`_fal_key.txt`).
- **PiAPI** (`SeedancePiapiProvider`, `video_stage/seedance_piapi.py`): chuyên Seedance, có cơ chế upload ảnh tạm 24h + fallback data-URI khi gói chặn upload, có `resume_task_id` (poll lại task cũ khi mạng đứt → không đốt tiền 2 lần). Phức tạp hơn nhưng **resume tốt** cho job dài.

### 2.2 Set env (ví dụ thật)

```bash
# fal.ai (khuyến nghị bật đầu tiên — key đã có)
export FAL_API_KEY="$(cat _fal_key.txt)"            # local đọc từ file gitignored
export VIDEO_PROVIDER=fal                            # provider đơn
export FAL_VIDEO_MODEL="fal-ai/bytedance/seedance/v1/pro/image-to-video"   # default trong registry

# HOẶC PiAPI
export PIAPI_API_KEY="<key-piapi-thật>"
export VIDEO_PROVIDER=seedance_piapi
# (PIAPI_BASE_URL default https://api.piapi.ai — không cần set)
```

Trên prod (Railway): vào **Variables** của service worker, thêm `FAL_API_KEY` (và `VIDEO_PROVIDER`). Xem cách set + nơi lưu an toàn ở [02-infrastructure.md](02-infrastructure.md) + [15-security.md](15-security.md).

### 2.3 Chuỗi fallback (chain) — bền hơn provider đơn

`build_video_provider()` (`video_stage/__init__.py:28`) hỗ trợ chuỗi: thử lần lượt, **bỏ qua provider thiếu key**, gói các provider còn lại vào `RoutedVideoProvider`.

```bash
export VIDEO_PROVIDER_CHAIN="fal,seedance_piapi,mock"
```

Luật fallback (`video_stage/router.py`):
- **`ProviderRejectedError` (moderation/từ chối nội dung) → KHÔNG fallback**, ném ngay. Đổi provider cho cùng nội dung bị-cấm là vô ích.
- **Lỗi hạ tầng / không-cấu-hình → sang provider kế.**
- Hết provider → ném lỗi cuối cùng.

> Gợi ý prod: `VIDEO_PROVIDER_CHAIN="fal,seedance_piapi"` (bỏ `mock` ở prod để tránh trả clip placeholder cho khách). `mock` chỉ dùng dev/test (`USE_FAKE_CLIENTS=1` cũng ép về mock).

### 2.4 Router CHỌN MODEL theo mode/purpose

`route_video(mode, purpose, resolution)` ở `providers/routing.py:50` quyết định model + độ phân giải + giá:

| mode / purpose | model_id | resolution (default) | speed | ghi chú |
|---|---|---|---|---|
| `purpose=draft` | `seedance-2-fast` | `VIDEO_DRAFT_RESOLUTION` (480p) | fast | chỉ xem trước, không đăng |
| `mode=premium` | `seedance-2` (pro) | `VIDEO_PREMIUM_RESOLUTION` (720p) | pro | upsell chất lượng cao |
| còn lại (`product_only`, `kol_full`) | `seedance-2-fast` | `VIDEO_RESOLUTION` (480p) | fast | text persona, ảnh SP làm khung đầu, KHÔNG gửi mặt → né tường deepfake |

Lưu ý: `routing.py` (model_id seedance-2/seedance-2-fast) là cho **đường PiAPI**. Đường **fal** dùng tên model riêng kiểu `fal-ai/...` set qua `FAL_VIDEO_MODEL` / `FAL_VIDEO_MODEL_DRAFT`. Hai hệ tên model là độc lập — đây là điểm dễ nhầm.

### 2.5 Nâng model cho NÉT hơn (KOL hover, premium)

HANDOFF §10.A.3: LTX-Video (hover) bị móp/mờ. Hướng nâng (ước lượng, cần đo thật chất lượng):

| Mục đích | Model gợi ý | Đặt ở đâu |
|---|---|---|
| Hover live-portrait nét | `fal-ai/kling-video/v1.6/standard/image-to-video` | `scripts/gen_kol_videos.py` (asset offline) hoặc `FAL_VIDEO_MODEL` |
| Premium trong app | `seedance-2` 720p (PiAPI) hoặc Kling pro (fal) | `VIDEO_PREMIUM_RESOLUTION=720p` / `FAL_VIDEO_MODEL` |
| Veo (cần GEMINI key) | Gemini Veo | cần `GEMINI_API_KEY`, chưa wire vào video_stage |

> Kling đắt hơn Seedance nhiều (~$0.25/clip ước lượng, **cần đo thật**). Chỉ bật cho premium/asset, không cho free tier ([09-free-tier-abuse.md](09-free-tier-abuse.md)).

---

## 3. Ảnh — Gemini & fal Flux

- **Trong engine:** `GeminiImageProvider` (`image_stage/gemini.py`) — Gemini 2.5 Flash Image, sinh ảnh KOL cầm/mặc/dùng SP hoặc ảnh hero. Gate `GEMINI_API_KEY`. Model qua `VIDEO_GEMINI_IMAGE_MODEL` (default `gemini-2.5-flash-image`). Có timeout 60s + retry 2 lần (tenacity).
- **Ảnh marketing web** (mặt KOL casting, nền cinematic) hiện sinh **offline bằng fal Flux** qua `scripts/gen_*.py` (Flux 1.1 Pro ultra+raw), đọc `_fal_key.txt`. Đây là asset tĩnh, không phải render runtime.

```bash
export GEMINI_API_KEY="<key-gemini-thật>"
export IMAGE_PROVIDER=gemini          # default đang là 'local'
# export VIDEO_GEMINI_IMAGE_MODEL=gemini-2.5-flash-image   # đã là default
```

Thiếu `GEMINI_API_KEY` → image stage `WAITING_CONFIG`. Chi phí ảnh ước tính qua `VIDEO_IMAGE_COST_USD` (default **$0.039/ảnh** — số trong registry, **cần đo thật theo hoá đơn Gemini**).

---

## 4. Giọng — Vbee (chính), Gemini TTS, edge-tts (free)

`build_tts_provider(gender)` ở `voice/tts_providers.py:294` chọn theo `TTS_PROVIDER`:

| `TTS_PROVIDER` | Provider | Gate | Ghi chú |
|---|---|---|---|
| `edge` / `none` / rỗng (default) | edge-tts (do TTSEngine xử lý) | không | **miễn phí**, giọng máy — last-resort |
| `vbee` | `VbeeProvider` | `VBEE_APP_ID` + `VBEE_API_TOKEN` + giọng + `VBEE_CALLBACK_URL` HTTPS thật + budget | giọng Việt thật, **rẻ (~vài trăm đồng/job, cần đo)** |
| `gemini_tts` | `GeminiTTSProvider` | `GEMINI_API_KEY` + budget | prosody tự nhiên, chọn giọng theo gender |

### 4.1 Cắm Vbee (giọng chính của Vyra)

```bash
export TTS_PROVIDER=vbee
export VBEE_APP_ID="<app-id>"
export VBEE_API_TOKEN="<token>"
# Giọng: hoặc VBEE_VOICE_CODE (nhiều mã ngăn dấu phẩy), hoặc tách male/female:
export VBEE_VOICE_CODE_MALE="<mã-giọng-nam>"
export VBEE_VOICE_CODE_FEMALE="<mã-giọng-nữ>"
export VBEE_CALLBACK_URL="https://<domain-prod>/vbee-callback"   # PHẢI HTTPS thật, KHÔNG example.com
# Bắt buộc bật sổ ngân sách TTS, nếu không provider trả phí raise lỗi:
export TTS_DAILY_BUDGET_USD=2.0
export TTS_ESTIMATED_COST_PER_CALL_USD=0.01      # ước lượng, cần đo thật theo hoá đơn Vbee
```

Fail-closed: bật `vbee` mà thiếu bất kỳ thứ trên → `NotConfiguredTTSProvider` raise `RenderError` ("không giả lập giọng khi đã bật"). Đây là CHỦ Ý — không để Vbee fail rồi tụt edge monotone âm thầm.

> ⚠️ ToS Vbee: phải mua **gói API thương mại** đúng quy mô (đọc ToS Vbee về bán-lại giọng tổng hợp). User nhận VIDEO có giọng, không nhận quyền API → markup hợp lệ (xem §6).

### 4.2 Gemini TTS (thay thế)

```bash
export TTS_PROVIDER=gemini_tts
export GEMINI_API_KEY="<key>"
export TTS_DAILY_BUDGET_USD=2.0
export TTS_ESTIMATED_COST_PER_CALL_USD=0.01    # ước lượng, cần đo thật
```

---

## 5. Ghi nhận CHI PHÍ THẬT mỗi job (sổ ngân sách)

Hai sổ độc lập, đều fail-closed:

### 5.1 Sổ video/ảnh — `provider_ledger` (DB, nguồn sự thật)

`providers/ledger.py`. Mọi job **reserve trước** ước tính USD, **settle sau** bằng chi phí thật:

- `reserve_video_budget(est_usd)` (`ledger.py:66`) — row-lock `SELECT … FOR UPDATE` theo `(date, provider="video_engine")`. Vượt `VIDEO_DAILY_BUDGET_USD` → `VideoBudgetError` → job xếp hàng mai (KHÔNG gọi API). Trần phụ `VIDEO_MAX_PER_DAY` chống spam.
- `settle_video_budget(reserved, actual, day=...)` (`ledger.py:111`) — hoàn phần reserve thừa/thiếu. **Phải truyền `day` mà reserve trả về** (job vắt qua nửa đêm sẽ ghi nhầm ngày khác).
- Ngày tính theo **múi giờ vận hành** `DISPATCH_TIMEZONE` (không phải UTC) — tránh "Chi phí hôm nay" hiện $0 lúc 7h sáng VN.
- `ledger_snapshot()` — trạng thái hôm nay cho admin/cost screen ([11-admin-panel.md](11-admin-panel.md)).

```bash
export VIDEO_DAILY_BUDGET_USD=5.0     # default; PHẢI > 0 nếu không reserve raise lỗi (chống đốt tiền)
export VIDEO_MAX_PER_DAY=10           # trần phụ chống spam
export DISPATCH_TIMEZONE="Asia/Ho_Chi_Minh"
```

> Lưu ý 2 lớp tiền KHÁC NHAU: sổ này là **trần chi tiêu API của Vyra/ngày** (bảo vệ founder khỏi đốt tiền). Còn **ví credit của user** (HOLD→SETTLE/REFUND) ở `app_api/wallet.py` là tiền user trả. Hai cái độc lập — xem [07-economics.md](07-economics.md).

### 5.2 Sổ TTS — file JSON

`voice/tts_providers.py:_reserve_tts_budget`. Sổ theo ngày (UTC) ghi vào `TTS_BUDGET_LEDGER_PATH`. Mỗi call reserve `TTS_ESTIMATED_COST_PER_CALL_USD`, vượt `TTS_DAILY_BUDGET_USD` → `RenderError`.

### 5.3 Ước tính TRƯỚC khi chạy (hiện ở nút "Tạo")

`estimate_job_cost(mode, purpose, seconds)` (`routing.py:72`) trả breakdown:
```
image_usd (n_images × VIDEO_IMAGE_COST_USD) + video_usd (seconds × usd_per_second) + other_usd (0.01 voice+compose)
→ total_usd, total_vnd (× FX_VND_PER_USD)
```
Đơn giá video/giây lấy từ `VIDEO_SEEDANCE_PRICES_JSON`. **Đây là đường để đo chi phí thật**: so `estimate` với hoá đơn fal/PiAPI thực tế rồi chỉnh JSON.

---

## 6. ToS & tính hợp lệ của markup (mua sỉ API → bán qua credit)

Mô hình: Vyra mua **gói API thương mại** của fal/PiAPI/Vbee → render video → bán cho user qua **credit** (~150đ/credit). User nhận **VIDEO/giọng**, KHÔNG nhận quyền truy cập API → đây là markup SaaS hợp lệ.

**Điều kiện bắt buộc (đọc ToS từng provider):**
- [ ] Mua đúng **gói thương mại / commercial tier** (không dùng free/personal tier để bán lại).
- [ ] Vbee: kiểm tra điều khoản về **bán-lại giọng tổng hợp** + quy mô gói.
- [ ] fal/PiAPI: kiểm tra điều khoản **resell / sublicense output**. Phần lớn cho phép thương mại hoá output, nhưng PHẢI xác nhận bằng văn bản ToS, không suy đoán.
- [ ] Không quảng cáo "dùng model X của hãng Y" theo cách vi phạm trademark.

Số tiền/biên lợi nhuận: xem [07-economics.md](07-economics.md) và [21-financial-model.md](21-financial-model.md).

---

## 7. Bảng so giá / chất lượng (ƯỚC LƯỢNG — CẦN ĐO THẬT)

> ⚠️ **CẢNH BÁO TRUNG THỰC:** các số dưới đây một phần lấy từ `VIDEO_SEEDANCE_PRICES_JSON` mặc định trong code (`registry.py:669`) — đây là số CẤU HÌNH, không phải hoá đơn thật. Kling/Veo là **ước lượng**. PHẢI đo thật trước khi định giá: chạy 5-10 job mỗi model, đối chiếu hoá đơn provider, cập nhật lại JSON.

| Model (đường) | Đơn giá ước lượng | Độ phân giải | Chất lượng (ước lượng) | Dùng cho |
|---|---|---|---|---|
| seedance-2-fast (PiAPI) | $0.08/s (480p), $0.16/s (720p) | 480/720p | khá, nhanh, rẻ | free/draft/product/kol |
| seedance-2 pro (PiAPI) | $0.10/s (480p), $0.20/s (720p), $0.50/s (1080p) | tới 1080p | cao | premium |
| Seedance v1 (fal) | cần đo thật | 720/1080p | cao | default fal |
| Kling v1.6 (fal) | ~$0.25/clip (ước lượng) | 720p+ | nét hơn, đẹp chuyển động | hover/premium |
| Gemini Veo | cần đo thật + cần key | cao | rất cao | premium tương lai |
| **Giọng Vbee** | ~vài trăm đồng/job (ước lượng) | — | giọng Việt thật | giọng chính |
| edge-tts | $0 (free) | — | giọng máy | last-resort |
| Ảnh Gemini Flash Image | $0.039/ảnh (config) | — | tốt | khung đầu / hero |

**Cách đo thật (cầm tay chỉ việc):**
1. Cắm key thật, set `VIDEO_DAILY_BUDGET_USD` đủ cho mẫu thử.
2. Chạy 5-10 job thật mỗi model (qua `POST /jobs` hoặc `runner_cli.py`).
3. Mở dashboard hoá đơn fal/PiAPI/Vbee → ghi USD thật/job.
4. Chia ra USD/giây → cập nhật `VIDEO_SEEDANCE_PRICES_JSON` (đường PiAPI) và ghi chú giá fal model vào [07-economics.md](07-economics.md).
5. So `estimate_job_cost` với hoá đơn → chênh > 20% thì chỉnh lại đơn giá + hệ số HOLD 1.5x (`wallet.py`).
6. Đối chiếu mẫu ASR/xem khung hình để chấm chất lượng (skill `real-qa`).

---

## 8. Quy trình bật render thật trên prod (checklist nhanh)

1. Set `FAL_API_KEY` (+ tuỳ chọn `PIAPI_API_KEY`) trên service worker Railway.
2. `VIDEO_PROVIDER_CHAIN="fal,seedance_piapi"` (bỏ mock).
3. `GEMINI_API_KEY` nếu cần ảnh runtime trong app.
4. Vbee: `TTS_PROVIDER=vbee` + đủ `VBEE_*` + `TTS_DAILY_BUDGET_USD` + `TTS_ESTIMATED_COST_PER_CALL_USD`.
5. `VIDEO_DAILY_BUDGET_USD` đặt theo ngân sách thật/ngày (chống đốt tiền).
6. Tắt `USE_FAKE_CLIENTS` (đảm bảo không còn mock).
7. Chạy 1 job thật e2e → kiểm video output bằng `real-qa` (mắt thấy, không tin log).

---

## Việc cần làm (checklist)

- [ ] Lấy & set `FAL_API_KEY` trên prod (key đã có local) → bật render video thật.
- [ ] Quyết định mua `PIAPI_API_KEY` gói thương mại (cho resume + Seedance) hay chỉ dùng fal.
- [ ] Set `GEMINI_API_KEY` nếu cần ảnh runtime trong app (hiện ảnh web là asset offline).
- [ ] Mua gói Vbee thương mại + cắm `VBEE_*` + `VBEE_CALLBACK_URL` HTTPS thật.
- [ ] Đọc & lưu lại điều khoản ToS resell của fal / PiAPI / Vbee (mục §6) — xác nhận bằng văn bản.
- [ ] Đo CHI PHÍ THẬT mỗi model (mục §7 bước 1-6) → cập nhật `VIDEO_SEEDANCE_PRICES_JSON` + ghi giá fal/Kling/Veo.
- [ ] Đo CHẤT LƯỢNG Kling vs Seedance cho hover/premium → quyết model nâng (HANDOFF §10.A.3).
- [ ] Cấu hình `VIDEO_DAILY_BUDGET_USD` + `DISPATCH_TIMEZONE=Asia/Ho_Chi_Minh` đúng prod.
- [ ] Set `VIDEO_PROVIDER_CHAIN="fal,seedance_piapi"` (bỏ mock) trên prod.
- [ ] Verify e2e 1 job render thật bằng `real-qa` trước khi mở cho user.
