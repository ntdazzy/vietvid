# VYRA — SESSION HANDOFF + KẾ HOẠCH THỰC THI (Bàn giao đầy đủ cho Gemini)

> Tài liệu này viết để **(a)** Gemini review, và **(b)** mở 1 session mới chạy tiếp mà **không thiếu gì**. Mọi claim "Vyra đã có X" đều đã được **đối chiếu với audit codebase thật** — chỗ nào chỉ partial/stub đã ghi rõ. Đường dẫn file là tuyệt đối-tương-đối-repo `c:\Users\NTD\Desktop\vietvid\`.
> Branch hiện tại: **`feat/ui-upgrade`** (nhánh off `master`). Trả lời tiếng Việt. Ngày: 2026-06-30.

---

## 1) TỔNG QUAN DỰ ÁN + ĐỊNH VỊ

**Vyra** = nền tảng tạo video AI cho thị trường Việt Nam. Engine chính: **Seedance (t2v/i2v) qua PiAPI/CometAPI/Runware/FAL**, mặt KOL AI (text character-sheet, KHÔNG face-embedding → né moderation deepfake), TTS tiếng Việt (Vbee/Gemini/edge), review sản phẩm/affiliate, đa thể loại (product ad, long-form narrative 16:9, film recap).

**Định vị (quan trọng, ảnh hưởng mọi quyết định build):**
- **Nội dung AI GỐC, KHÔNG phải "rửa" nội dung** (no content-laundering). Đây là ranh giới pháp lý + thương hiệu.
- TRÁNH tuyệt đối: video-to-video "spin/làm độc nhất", mass auto-publish, watermark removal, AI-detector bypass, re-upload kiểu Poiiky "39 kỹ thuật vượt bộ lọc", style filter IP có tên (Ghibli/Pixar), celebrity likeness.
- Pricing: subscription + credits (ví-2-túi), MoMo-first, KOL cả AI lẫn real-face (Chin/Chun), **không auto-post**.

**Trạng thái tổng (đối chiếu audit thật):**
- **Backend (app_api/) + video_engine/**: rất hoàn chỉnh. 91 file .py, 0 NotImplementedError trong core pipeline (product_ad). Billing ví-2-túi ACID, ledger append-only, MoMo/VNPay/Bank-QR + MB poller, reaper, RLS, signed URL — **đã build + verify (M1: 45/45 real-op)**.
- **Web (apps/web/)**: ~90% màn hình xong (32 page.tsx, 46 marketing component, 100+ API endpoint typed, i18n vi+en đầy đủ). Studio shell 3-pane xong.
- **Gap thật còn lại (đã xác minh):** màn `/app/director` 404; voice-persona render-honor là stub; long-narrative + film-recap mode chưa wire hết; 1 loạt M2 endpoint (payments/credit-packs/kol CRUD) mới có model chưa có router.

---

## 2) ĐÃ XONG TRONG SESSION NÀY (đã commit trên `feat/ui-upgrade`)

8 commit mới nhất (xác minh bằng `git log`):
```
2103b3e fix(web): pull login corner glow flush to the top edge
cec60fd fix(web): login drift-wall now a soft faded backdrop (no hard card edges)
40ff28a feat(web): social proof — trust numbers + human-voice reviews
e1b70b0 fix(web): remove login drift-wall top seam via combined edge mask
170710d fix(web): clean before/after clip + smooth slider; redesign KOL grid
fca7eec feat(web): diversify homepage content genres + clickable sample tiles
```

Chi tiết từng thay đổi (file đã xác minh tồn tại + mtime hôm nay):

1. **Homepage marquee** → đa dạng hoá thành **9 thể loại 9:16 riêng biệt** (trước là 5 product shot lặp). Tile marquee giờ **click được** (link `/login`, con trỏ pointer).
2. **`apps/web/src/components/marketing/use-cases.tsx`** → +6 thể loại (nấu ăn, du lịch, mẹ&bé, phim ngắn, kể chuyện, bất động sản); thêm chuỗi vi/en.
3. **`apps/web/src/components/marketing/before-after.tsx`** → đổi clip fashion-v2 bị lỗi (áo khoác vàng "materialize") sang clip `gaixinh` sạch; auto-slide chuyển sang CSS-eased (hết giật).
4. **`apps/web/src/components/marketing/featured-kol.tsx`** → redesign từ hàng avatar → **lưới 4-card video persona 9:16 nét**; fix Linh bị blur (clip 400x266 nhét vào khung dọc), đổi An & Hoa.
5. **`apps/web/src/components/marketing/social-proof.tsx`** → **70.000+ creator / 100.000+ review** + 3 testimonial giọng người thật VN (thay mấy cái nghe như AI).
6. **`apps/web/src/app/login/page.tsx`** → drift-wall mask cũ dùng `mask-composite:intersect` (hỏng âm thầm trên Chrome → cạnh card cứng); thay bằng 2 gradient mask single-axis lồng nhau + bỏ ring/shadow per-image + blur backdrop. **Glow góc** dời từ `top-8` → `-top-24` để chạm mép trên (hết "viền đen" trên đầu). Đầu session: thêm Google/Facebook social login + `validate()` cho register.

> Có 1 file untracked: `apps/web/public/samples/fashion-v2.mp4` (clip cũ bị thay) và file `kết quả nghiên cứu.txt` ở repo root — chưa commit, để session sau quyết định.

---

## 3) ĐANG DỞ — RENDER 27 CLIP (việc lớn còn treo)

### 3.1 Vị trí file (QUAN TRỌNG — nằm trong scratchpad session, KHÔNG ở repo root)
Scratchpad: `C:\Users\NTD\AppData\Local\Temp\claude\c--Users-NTD-Desktop-vietvid\38f22453-5b83-40eb-bfd7-c061dae6336d\scratchpad\`
- **`manifest.json`** — 27 clip (đã xác minh: 27 entry, không phải 24).
- **`gen_v3.py`** — script render (Seedance t2v, 5s, 480p, `model_id="seedance-2-fast"`, tuần tự pool=1, resume-safe, ghi `gen_v3_summary.json` sau mỗi job, skip job OK đã có).
- **`gen_v3.log`** — log lần chạy gần nhất (chứng cứ blocker bên dưới).
- **`ok_face-girl-next-door-bedroom-vlogger.jpg`** + **`ok_face-tech-reviewer-messy-desk-male.jpg`** — **poster frame của 2 clip mặt ĐÃ render OK** (đây là bằng chứng "anti-AI prompt chạy được, mặt thật").

### 3.2 Output đi đâu — CẢNH BÁO
- Script ghi MP4 ra: `apps/web/public/showcase/v2/`.
- **Hiện `v2/` RỖNG** (đã `ls`, chỉ có `.`/`..`). Hai clip render OK **không còn MP4 trên đĩa** — chỉ còn 2 poster JPG trong scratchpad. → **2 clip mặt đẹp đó đã mất file MP4, phải render lại** (hoặc tìm trong CDN PiAPI bằng task_id trong log: `36f565f2-...` và `e283cf03-...`, nhưng CDN PiAPI hết hạn nhanh — coi như mất).

### 3.3 Manifest 27 clip (đã liệt kê word-count — XÁC NHẬN PROMPT QUÁ DÀI)
9 mặt KOL (9:16) + 11 genre (9 người + 2 non-người: pet, café b-roll) + 7 product. Một số 16:9 (travel, shortfilm, real-estate, decor, accessory, appliance, cozy-cafe).

Word-count thật (đã đo): **96–146 từ/prompt** (vd `face-genz-student-freckles-selfie` = 146 từ). Khung Kling khuyến nghị 50–80 từ → **prompt hiện tại dài gấp ~2×, CẦN viết lại** (xem mục 5).

### 3.4 Blocker (chứng cứ từ `gen_v3.log`)
```
[1/27] face-girl-next-door-bedroom-vlogger: OK 9:16 (129s)
[2/27] face-tech-reviewer-messy-desk-male:  OK 9:16 (99s)
[3/27]..[27/27]: FAIL VideoEngineError: PiAPI tạo task lỗi HTTP 500
                 {"code":500,...,"model":"seedance",...}  ← HẾT CREDIT PiAPI
```
- 2 clip đầu render đẹp + **thật** (anti-AI prompt thành công). Nhưng da ra **rám/sạn (tan/gritty)**, không trắng hồng.
- Founder chốt hướng mặt **"trung gian / có xài filter"** (light beauty-filter): trắng hồng + sạch + cute/ngây thơ nhưng **vẫn giữ lỗ chân lông/texture nhẹ** để không bị nhựa (plastic AI doll). Prompt đã được retune theo hướng này.

### 3.5 Trạng thái provider HIỆN TẠI (đối chiếu .env — MÂU THUẪN với session-context)
- **`.env` đang để `VIDEO_PROVIDER=seedance_piapi`** (SINGLE provider, KHÔNG phải chain `cometapi,runware,seedance_piapi`).
- → Session-context nói "provider chain config = cometapi,runware,seedance_piapi (đã đúng)" là **CHƯA chính xác với .env thật**. Code chain có (`video_stage/__init__.py` + `router.py`), nhưng **config live vẫn chỉ trỏ PiAPI đã hết credit**. **Đây là việc cần sửa đầu tiên trước khi render lại.**
- `COMETAPI_API_KEY` đã set trong .env. `COMETAPI_VIDEO_MODEL` chưa set → mặc định `doubao-seedance-2-0-fast` (xác minh `cometapi_video.py:43`).
- Founder đang **nạp $20 vào CometAPI (đang pending)**. **KHÔNG render cho tới khi nạp xong.**

### 3.6 Các bước CÒN LẠI để hoàn tất render
1. (Tuỳ chọn nhưng nên) **Viết lại 27 prompt** theo khung Kling+Seedance (mục 5): rút còn 50–80 từ, front-load camera/style, fold anti-plastic vào positive.
2. **Đổi provider sang CometAPI**: hoặc set `.env VIDEO_PROVIDER=cometapi,runware,seedance_piapi` (chain, rẻ nhất trước), hoặc sửa `gen_v3.py` gọi thẳng CometAPI provider thay `SeedancePiapiProvider`. (Script hiện hardcode `SeedancePiapiProvider()` ở dòng 37 — phải đổi.)
3. **Bench 3 model CometAPI** trên 2–3 clip mặt test (xem mục 4): `doubao-seedance-1-5-pro` (rẻ nhất) vs `doubao-seedance-2-0-fast` vs `doubao-seedance-2-0` (std). Chọn model đẹp nhất cho mặt người thật trắng-hồng-filter. **Verify trên Seedance thật, không tin lý thuyết.**
4. **Render cả 27** (resume-safe, pool=1, sleep 8s tránh 429).
5. **ffmpeg trích poster frame mỗi clip + nén** (đã có pattern `post_gen.py` trong scratchpad để tham khảo).
6. **Wire vào homepage**: thay 4 mặt KOL (`featured-kol.tsx`), feed genre vào marquee (`use-cases.tsx`/page.tsx), thêm product bento. Đường đích: `apps/web/public/showcase/v2/*.mp4` + poster `.jpg`.
7. **Screenshot-verify** (browse skill) + commit.

---

## 4) BẢNG GIÁ ĐẦY ĐỦ 3 PROVIDER + CHỐT MODEL RẺ NHẤT + KẾ HOẠCH BENCH

Giá **USD / giây** (từ screenshot provider, June 2026):

### PiAPI (hiện đang dùng — ĐÃ HẾT CREDIT)
| Model | 480p | 720p | 1080p |
|---|---|---|---|
| seedance-2 | $0.10 | $0.20 | $0.50 |
| seedance-2-fast | $0.08 | $0.16 | — |
| seedance-2-mini | $0.07 | $0.14 | — |
| *less-restriction* | ~+10% | | |

### CometAPI (key đã có, đang nạp $20)
| Model | 480p | 720p | 1080p |
|---|---|---|---|
| doubao-seedance-2-0 | $0.063 | $0.1368 | $0.3366 |
| doubao-seedance-2-0-fast | $0.0504 | $0.108 | — |
| **doubao-seedance-1-5-pro** ⭐RẺ NHẤT | **$0.024** | $0.052 | $0.118 |
| doubao-seedance-1-0-pro | $0.032 | $0.084 | $0.1992 |

### Runware
| Model | Giá |
|---|---|
| Seedance 2.0 | 480p $0.07 / 720p $0.16 / 1080p $0.40 / 4k $0.836 |
| Seedance 2.0 Mini | 480p.4s $0.144 ($0.036/s); v2v 480p.4s $0.172 |

### Chốt
- **Rẻ nhất 480p/s = CometAPI `doubao-seedance-1-5-pro` $0.024/s** → 1 clip 5s = **$0.12** → **27 clip ≈ $3.24**.
- **Chain đúng (rẻ trước):** `cometapi,runware,seedance_piapi`. Đổi model qua `COMETAPI_VIDEO_MODEL` (mặc định `doubao-seedance-2-0-fast`).
- **Kế hoạch bench:** so 3 model `1-5-pro` (rẻ) / `2-0-fast` / `2-0` (std) trên 2–3 clip mặt test. Tiêu chí: da trắng-hồng-filter nhưng còn texture, mắt có catchlight, không nhựa, micro-action resolve trong 5s. Nếu `1-5-pro` đủ đẹp → tiết kiệm lớn (gấp ~2× rẻ hơn `2-0-fast`).

---

## 5) KHUNG PROMPT KLING + SEEDANCE (chi tiết + ví dụ viết lại)

> Nghiên cứu từ Kling/OpenArt/Autovis/Seedance/cinematic. **VERIFY trên Seedance bằng vài clip test — không tin lý thuyết suông.**

**Nguyên tắc:**
1. **Front-load** camera/style ngay đầu prompt (t2v model nặng token đầu): vd `"documentary 35mm, slight handheld drift, iPhone front camera, soft beauty filter"`.
2. **Spine (xương sống):** `[camera/style]` → `[subject + appearance]` → **MỘT** primary action → scene (3–5 element) → lighting **SOURCE + DIRECTION** (`"soft window light from camera-left"`) → mood/grade.
3. **Độ dài 50–80 từ** (prompt hiện tại 96–146 từ → cắt mạnh). Tối đa 2–4 ý / 3–5 element scene.
4. **Ép 1 micro-action giữa beat + 1 endpoint** để clip 5s "resolve" (không loop/mannequin).
5. **Seedance KHÔNG có field negative** → fold ý anti-plastic vào POSITIVE dưới dạng texture: `"visible pores, natural skin texture, slightly desaturated, film grain"`.
6. **Hướng mặt:** trắng hồng/trắng trẻo, cute/ngây thơ, beauty-filter glow NHƯNG giữ lỗ chân lông nhẹ + catchlight mắt ướt + tóc bay lơ + ánh nhìn lệch ống kính → đọc ra "creator thật có filter", không phải búp bê AI.

**Ví dụ — viết lại 1 prompt mặt (từ 132 từ → ~70 từ):**

*Trước (face-girl-next-door-bedroom-vlogger, 132 từ — quá dài, dàn trải).*

*Sau (gợi ý, ~70 từ):*
> `Documentary 35mm, slight handheld drift, iPhone front camera, soft beauty filter. A fair-skinned Vietnamese girl-next-door in her early 20s, trắng hồng glowing skin with visible pores and natural texture, wet-eye catchlight, a few flyaway hairs, cute innocent look, glances slightly off-lens then smiles. Cozy bedroom vlogger setup, fairy lights, plush bed. Soft warm window light from camera-left. Slightly desaturated, gentle film grain, intimate cozy mood.`

→ Front-load camera (1) + subject/appearance (2) + 1 action "glances then smiles" (3) + scene 3 element (4) + lighting source/direction (5) + anti-plastic fold positive (6). Áp pattern này cho cả 27.

---

## 6) PHÂN TÍCH ĐỐI THỦ — MA TRẬN TÍNH NĂNG (đối chiếu AUDIT THẬT)

Đối thủ tham chiếu: Kling, Autovis, OpenArt, Poiiky, repo `huytranvan2010/AI-auto-generate-video`.

### 6A) Vyra ĐÃ CÓ (đã đối chiếu evidence — phân biệt DONE vs PARTIAL/STUB)
| Tính năng | Trạng thái THẬT | Evidence |
|---|---|---|
| Character consistency (vv_characters) | ✅ DONE (web CRUD + 3-pane + modal 3 lối) | `apps/web/src/app/app/character/page.tsx`; bảng `vv_characters` |
| KOL/persona library | ✅ DONE web; ⚠️ **render-honor voice = STUB** | `apps/web/.../kol/page.tsx` (12 preset); `video_engine/kols/__init__.py` (8 seed) |
| Multi-shot storyboard (long_narrative) | ⚠️ **PARTIAL** — code đủ nhưng `render_service.py:14` raise NotImplementedError cho mode này | `video_engine/long_narrative/*` |
| VN script→video (director) | ✅ DONE cho product_ad; ⚠️ long-form chưa wire | `video_engine/director/*` |
| Voice cloning (VieNeu) | ⚠️ **PARTIAL** — client tồn tại, integration TBD | `video_engine/voice/vieneu_client.py` |
| One-photo KOL (web) | ✅ DONE web UI | `apps/web/.../kol` |
| Series / batch A/B | ⚠️ web có màn; **model có, router M2 chưa viết** | `apps/web/.../team`, models.py |
| Brand kit | ✅ DONE web | `apps/web/.../brand-kits/page.tsx` |
| Style presets | ✅ DONE | `video_engine/scenes/presets.py`, `formats/` |
| Public API (B2B keys) | ✅ DONE | `app_api/apikeys.py` (vv_live_*) |
| Credit wallet / team | ✅ DONE (ví-2-túi ACID, ledger) | `app_api/wallet.py:38-253` |
| VN auto-captions / ASR | ✅ DONE (Groq whisper, word-level) | `video_engine/voice/asr.py` |
| TTS normalization | ✅ DONE | `video_engine/voice/tts.py`, `tts_providers.py` |
| Typed script.json | ✅ DONE | `video_engine/spec.py` (JobSpec/RenderResult) |
| Lip-sync (Seedance native) | ⚠️ **deprecated** (mode=native lơ lớ → bỏ; mode=auto dùng Vbee, KOL câm + overlay) | pipeline.py VOICING |

**Kết luận đối chiếu:** đa số claim "đã có" là ĐÚNG cho **product_ad mode**. Nhưng 3 thứ session-context coi như "có" thực ra **chưa hoàn chỉnh:** (1) long_narrative + film_recap (render_service từ chối chạy), (2) voice-clone VieNeu (integration TBD), (3) voice-persona render-honor (TTS engine bỏ qua per-job, đọc global `settings.tts_voice` — xác minh `video_engine/voice/tts.py:26`).

### 6B) THIẾU — NÊN BUILD (top-5 gap, ưu tiên margin)
1. **HTML/CSS deterministic frames cho scene TEXT** (intro/stat/CTA) — để dành Seedance cho hero scene → **đòn bẩy MARGIN trực tiếp** (margin≈0 hôm nay). Mượn từ repo huytranvan. **#1 ưu tiên.**
2. **Per-scene idempotent render + fit-clip-to-narration.**
3. **Start&End frame keyframe control** (Kling).
4. **Video Extend** (Kling).
5. **AI music generation + stock B-roll auto-fill (có bản quyền).**

### 6C) TRÁNH (pháp lý/định vị — KHÔNG build)
- video-to-video "spin/làm độc nhất" (laundering).
- mass auto-publish (đã chốt no-auto-post).
- watermark removal / AI-detector bypass / re-upload (Poiiky "39 kỹ thuật vượt bộ lọc").
- style filter IP có tên (Ghibli/Pixar) + celebrity likeness.
- ComfyUI workflow marketplace (OpenArt đang khai tử 18/1/2026 → thị trường về "1 prompt → done").
- 4K@60fps, text render trong-khung bởi model, **i2v mặt người thật** (moderation chặn — dùng t2v).

---

## 7) REPO `huytranvan2010/AI-auto-generate-video` — MƯỢN GÌ

Đây là **generator news-short VN bằng HTML-template tất định** (KHÔNG phải generative video). Đáng mượn:
1. **HTML text-card frame** (~$0/frame) cho intro/stat/CTA → cắt chi phí Seedance, **lực đẩy margin số 1**.
2. **Per-scene idempotent render** (render lại 1 scene không phải cả video).
3. **Quy tắc chuẩn hoá TTS tiếng Việt** (đọc số, viết tắt, ký hiệu) — bổ sung cho `tts.py`.

KHÔNG mượn: cơ chế re-upload / lách bộ lọc (vi phạm định vị).

---

## 8) BACKLOG TỒN ĐỌNG TỪ TRƯỚC (từ audit pending-markers — đã xác minh)

### CRITICAL — chặn doanh thu M2
- [ ] **M2 Payment endpoints** (`POST /v1/payments`, `GET /v1/payments/{id}`): model có, **router 404** (`app_api/routers/billing.py`). MoMo adapter cần merchant code + reconciliation.
- [ ] **Monthly credit reset cron** (`SYSTEM_DESIGN.md:59`, `config.py`): hàm grant idempotent có, **trigger cron CHƯA code**. Migration 0004+ chưa viết.
- [ ] **Credit packs API** `GET /v1/credit-packs`: model có, **endpoint chưa viết** (FE đang hardcode).

### HIGH — chặn launch "studio" rebrand
- [ ] **KOL personas CRUD endpoints** (`POST /v1/kol-personas`, face upload presigned URL, consent gate): model có, **router stub** (`app_api/routers/content.py`).
- [ ] **`/app/director` page 404** — XÁC MINH: `apps/web/src/app/app/director/` không có `page.tsx`; `studio-shell.tsx:16` trỏ `/app/director`. Comment trong shell: "tạm trỏ route gần nhất tới khi dựng màn riêng".
- [ ] **T4 right-panel studio** chưa làm.
- [ ] **Custom 404 page** chưa build.

### MEDIUM — activation-tier (cần dịch vụ ngoài)
- [ ] **Voice-persona render-honor** — XÁC MINH STUB: `video_engine/voice/tts.py:26` `self.voice = settings.tts_voice` (đọc global, **bỏ qua** `params.voice_persona`). Cần thread voice+rate+pitch vào render stateless + boot test.
- [ ] **Face-swap stub** (`POST /v1/kol-personas/{id}/face` → set PENDING_REVIEW, render NO-OP): cần provider ngoài + legal review.
- [ ] **Voice-clone stub** (`POST /v1/kol-personas/{id}/voice-clone` → REQUESTED, không provider): fallback voice_id chuẩn.
- [ ] **Long-narrative + film-recap runners**: `render_service.py:14` raise NotImplementedError. `film_recap recap mode` P1 stubbed (reupload P0 DONE).

### LOW / nice-to-have
- [ ] Director TTS preview endpoint (web fallback pre-render OK).
- [ ] `resolve_bank_payment_org()` O(orgs) scan → bảng global memo→org (`app_api/billing.py:152`).
- [ ] CSP hardening (`apps/web/src/middleware.ts` TODO(csp)).
- [ ] Redis cho rate-limit multi-instance (hiện in-process).
- [ ] Arq queue mode (`JOB_EXECUTION_MODE=queue`) chưa deploy (đang inline).
- [ ] CometAPI i2v field names + Runware aspect convention (TODO verify trong file provider).
- [ ] Long-form YouTube publish bridge (`bridge.py:164`, `LONGFORM_YOUTUBE_PUBLISH_ENABLED=false`, chưa E2E).

### Billing facts đã xác minh (.env + config.py)
- `CREDIT_PRICE_VND=150`, `USD_TO_VND=25400`, `VIDEO_MARGIN_MULTIPLIER=2.0`, `FREE_GRANT_CREDITS=0`, `FIRST_TOPUP_BONUS_CREDITS=300`. → Free user KHÔNG tạo job được (grant=0, min hold ~105); nạp lần đầu +300 mới render. **Khớp memory.**

---

## 9) ROADMAP ĐỀ XUẤT THEO ƯU TIÊN

**P0 — Hoàn tất render 27 clip (đang dở, chặn homepage launch):**
1. Đợi top-up CometAPI xong → đổi `VIDEO_PROVIDER` sang chain `cometapi,runware,seedance_piapi` (hoặc sửa `gen_v3.py` gọi CometAPI).
2. Bench 3 model CometAPI trên 2–3 clip mặt → chốt model.
3. (Nên) viết lại 27 prompt theo khung mục 5 (50–80 từ).
4. Render 27 → trích poster → nén → wire homepage → screenshot-verify → commit.

**P1 — Margin lever (đòn bẩy lợi nhuận, margin≈0 hôm nay):**
5. HTML/CSS deterministic text-frame cho intro/stat/CTA (mượn huytranvan). Đây là tính năng tạo margin trực tiếp.

**P2 — Mở khoá doanh thu M2:**
6. M2 Payment endpoints + MoMo adapter + webhook reconciliation.
7. Monthly credit reset cron + migration 0004.
8. Credit packs API + KOL personas CRUD endpoints.

**P3 — Hoàn thiện studio rebrand:**
9. `/app/director` page (Projects/campaign CRUD).
10. T4 right-panel + custom 404.

**P4 — Activation-tier (cần dịch vụ ngoài):**
11. Voice-persona render-honor (thread voice vào TTS render).
12. Long-narrative + film-recap wire pipeline.
13. Face-swap + voice-clone providers (+ legal review).

---

## 10) RỦI RO + CÂU HỎI MỞ CHO GEMINI

**Rủi ro:**
- **2 clip mặt đẹp ĐÃ MẤT MP4** (chỉ còn poster JPG) — phải render lại; CDN PiAPI hết hạn nhanh.
- **`.env` vẫn trỏ PiAPI đã cạn credit** — render sẽ FAIL ngay nếu không đổi provider trước.
- Prompt 27 clip **dài gấp 2×** khuyến nghị → có thể ra clip dàn trải/mannequin nếu không cắt.
- Da mặt ra **rám/sạn** với prompt cũ — hướng "filter trắng hồng" mới CHƯA verify trên CometAPI (mới chỉ verify trên PiAPI 2 clip).
- Margin ≈ 0 — render 27 clip showcase tốn tiền nhưng không sinh doanh thu; cần margin lever (P1) sớm.
- Khung prompt Kling là **lý thuyết** — phải bench thật, không trust.

**Câu hỏi mở (xem field riêng).**

---

# Phần bổ sung A — Landscape repo GitHub (rà soát 18 nhóm, đã clone về D:yra-researchepos)

> Đã clone sẵn: `huytranvan2010/AI-auto-generate-video` (HTML-template news short), `harry0703/MoneyPrinterTurbo` (~94k★, topic→short kinh điển).

> Shortlist 62 repo (gộp 2 sweep, dedupe). Ưu tiên high = nên đọc/clone trước.


## AI video orchestration / multi-provider routing
- **[HIGH]** [calesthio/OpenMontage](https://github.com/calesthio/OpenMontage) — The single best reference for Vyra's #1 problem: scored multi-provider selection (rank by fit/quality/cost/latency/reliability) — exactly the abstraction to generalize the existing CometAPI->Runware->PiAPI chain into the model-registry the pivot calls for. YAML pipeline manifests + JSON-Schema stage contracts + estimate-before-execute budget caps + decision audit log map directly onto Vyra's credit-hold/settle and per-genre flows. CAVEAT: AGPL-3.0 — borrow patterns, never vendor source into the closed SaaS.

## Script-to-short pipeline / stage gating
- **[HIGH]** [harry0703/MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo) — Canonical 94k-star reference for the script->TTS->caption->compose->render flow on a FastAPI task model. The --stop-at stage gate is a direct cost-cutting win: bill credits per stage and let free users halt cheaply. Dual caption backend (Edge-TTS word timestamps free vs faster-whisper accurate) is exactly the cheap-vs-accurate tradeoff Vyra needs for Vietnamese captions. MIT = freely studyable.

## Closest architectural twin (FastAPI + React + tiered providers + AI-actor)
- **[HIGH]** [mutonby/openshorts](https://github.com/mutonby/openshorts) — The closest twin to Vyra's actual stack: FastAPI + faster-whisper + async job queue + React studio + low-cost-vs-premium provider tiering + AI-actor talking-head (portrait->TTS->img2video->lipsync). Its 'AI Shorts' mode (product/URL -> script -> AI-actor video + b-roll) overlaps both Vyra's affiliate flagship AND AI-KOL feature. MIT, Docker, production-grade async queue + SEO gallery. Highest signal-per-clone for the whole platform shape.

## Provider abstraction / fallback factory (code reference)
- **[HIGH]** [trilogy-group/ttv-pipeline](https://github.com/trilogy-group/ttv-pipeline) — Low stars but the single most on-point CODE reference for what Vyra's RoutedVideoProvider already started: generators/ factory registry + default_backend with automatic fallback_backend + retry + prompt-reword-on-failure. Read it to harden the CometAPI->Runware->PiAPI chain into a robust factory. Bonus: Instructor/structured-output prompt segmentation into keyframe+segment prompts.

## Seedance request/poll + character consistency
- **[HIGH]** [Anil-matcha/Seedance-2-API](https://github.com/Anil-matcha/Seedance-2-API) — Vyra's core generator IS Seedance. This is the direct request-schema/polling/wait reference, plus the @character inline-ref and consistent_video() character-sheet patterns that solve AI-KOL face continuity at the video stage. Essential for tuning the primary engine and the consistency layer the pivot prioritizes.

## Credit-billed video SaaS + multi-model adapter (MIT)
- **[HIGH]** [Anil-matcha/Open-AI-UGC](https://github.com/Anil-matcha/Open-AI-UGC) — Almost Vyra's exact production stack and billing model (Next.js/React + Postgres + credit tiers + Seedance + async webhook job-completion), and MIT-licensed so code is freely borrowable (unlike ClipForge AGPL). Reference implementation for the 'AI-actor video + credit hold/gating' half of Vyra and the multi-model adapter that passes images as both image_url and images_list to satisfy different model APIs (@image1 syntax).

## Affiliate link->review video (closest flow + stack match)
- **[HIGH]** [xixihhhh/clipforge](https://github.com/xixihhhh/clipforge) — Closest single match to Vyra's affiliate flagship: product link/image -> selling-point extraction -> 4 script archetypes -> image-to-image 'product lock' (keeps the real product faithful, key for trust) -> free B-roll -> captioned multi-platform export. Already integrates Seedance 2.0 + Edge TTS + local FFmpeg + a zero-key free tier (the exact free-tier cost model Vyra wants). CAVEAT: AGPL-3.0 — mine the patterns (especially the product-lock and free-B-roll aggregator), do not copy code into the closed SaaS.

## Deterministic $0 render (cost-cutting)
- **[HIGH]** [nexu-io/html-video](https://github.com/nexu-io/html-video) — Directly attacks the margin-0 problem. Render text cards / titles / lower-thirds / caption overlays deterministically from HTML via headless Chromium + FFmpeg at near-zero marginal cost, reserving Seedance spend ONLY for shots that need generative video. Apache-2.0, no per-render fees. Content-Graph IR is a clean scene-spec model and the pluggable render-engine boundary lets you mix HTML cards with generative clips in one timeline.

## Vietnamese TTS (commercial-safe, self-host margin lever)
- **[HIGH]** [pnnbao97/VieNeu-TTS](https://github.com/pnnbao97/VieNeu-TTS) — The strongest open Vietnamese TTS and a direct margin lever: Apache-2.0 (commercial-OK, unlike viXTTS/viet-tts CC-BY-NC weights) and CPU-deployable via ONNX/GGUF, so Vyra self-hosts voice at ~0 per-char cost instead of paying a TTS API. Instant 3-5s voice cloning powers AI-KOL voices; multi-speaker podcast mode + emotion/code-switch markup cover multi-genre content. Best Vietnamese-voice pick by license + maintenance + cost.

## Word-level caption timing (karaoke captions)
- **[HIGH]** [m-bain/whisperx](https://github.com/m-bain/whisperx) — The backbone primitive for Vyra's caption/karaoke layer: word-level timestamps via wav2vec2 forced alignment enable TikTok-style word-highlight captions and accurate subtitle timing; diarization feeds per-speaker dubbing. BSD-2-Clause, actively maintained, supports loading a Vietnamese-specific wav2vec2 alignment model for accurate VN word timing. Nearly every serious dubbing/caption repo builds on it.

## Lip-sync (best fit for Seedance stack)
- **[HIGH]** [bytedance/LatentSync](https://github.com/bytedance/LatentSync) — Highest practical lip-sync fit: a ByteDance model that pairs naturally with Vyra's ByteDance Seedance pipeline. Apache-2.0 (commercially usable), audio-driven so it consumes Vyra's Vietnamese TTS output directly, and the documented Chinese/tonal-language tuning is the closest public signal it handles non-English mouth shapes. Borrow the post-TTS lip-sync stage and test on Vietnamese phonemes.

## Consistent KOL face / expression control
- **[HIGH]** [KwaiVGI/LivePortrait](https://github.com/KwaiVGI/LivePortrait) — Best repo for AI-KOL face consistency: it animates a FIXED source identity, so the generated KOL stays the same person across a content series — directly solves Vyra's KOL-continuity problem. Real-time (~12.8ms/frame on 4090) makes it viable for high-volume review output; healthiest ecosystem (ONNX/TensorRT ports) of the talking-head set. Pair with an identity-image generator to lock one face across clips.

## Image gen pipeline backend
- **[HIGH]** [comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI) — De-facto headless execution backend for every new open image/video model. Run it headless and drive the JSON-workflow + websocket API to compose Flux/SDXL + ControlNet + IP-Adapter + upscale per genre/accent. Single most important repo for the composable image stage feeding Seedance.
- **[HIGH]** [huggingface/diffusers](https://github.com/huggingface/diffusers) — Clean typed-Python alternative to ComfyUI for a FastAPI service. FluxPipeline/SDXL inpaint/ControlNet/IP-Adapter in a few lines. Most other image repos are downstream of it; the cleanest reference for wiring gen into Vyra's Python backend.

## Image gen model
- **[HIGH]** [black-forest-labs/flux](https://github.com/black-forest-labs/flux) — Top open model for photoreal humans/products — core for AI-KOL faces and product shots. Critical license split to internalize: schnell=Apache-2.0 (commercial-safe), dev=non-commercial gated. Pair schnell with ai-toolkit LoRAs for branded characters.

## Identity / consistent character
- **[HIGH]** [instantX-research/InstantID](https://github.com/instantX-research/InstantID) — Apache-2.0 single-photo identity preservation — the strongest candidate for the 'KOL with your own face' onboarding. One selfie -> consistent controllable portraits across scenes, no LoRA training. License is commercial-friendly, a major plus.
- **[HIGH]** [tencent-ailab/IP-Adapter](https://github.com/tencent-ailab/IP-Adapter) — Lightweight 'use this reference image' adapter (brand product photo or KOL face as visual prompt) without per-character training. Building block under InstantID-style flows and on-brand product imagery; composes with text + ControlNet.
- **[HIGH]** [RishiDesai/CharForge](https://github.com/RishiDesai/CharForge) — Single-reference -> consistent-character on Flux. Maps almost 1:1 onto Vyra's existing /suite/character (vv_characters) flow — borrow the single-image auto-LoRA loop for the 'create a reusable character' button.

## LoRA training
- **[HIGH]** [ostris/ai-toolkit](https://github.com/ostris/ai-toolkit) — Leading Flux LoRA training toolkit with upload->auto-caption->train->publish UI. The engine behind 'train a reusable branded character/product'. Note license inheritance: dev LoRAs non-commercial, schnell LoRAs Apache-2.0 — default to schnell for commercial output.

## Virtual try-on
- **[HIGH]** [yisol/IDM-VTON](https://github.com/yisol/IDM-VTON) — Top open virtual try-on (SDXL, garment-detail preserving). Directly enables fashion/apparel review videos — dress an AI-KOL in a seller's actual garment image. Standout feature for Vietnam's live-commerce/affiliate fashion market.

## Relighting / compositing
- **[HIGH]** [lllyasviel/IC-Light](https://github.com/lllyasviel/IC-Light) — SOTA relighting. Composite a seller's product onto a new background and relight so it looks natively shot, not pasted; also relights AI-KOL faces to scene lighting before the video stage. Big quality lever; pairs with rembg cutout.

## Background removal (image)
- **[HIGH]** [danielgatis/rembg](https://github.com/danielgatis/rembg) — Workhorse image background removal as CLI/lib/HTTP/Docker with a pluggable model zoo. Fastest way to add a 'remove background' endpoint and the first step of nearly every product-photo pipeline (rembg -> IC-Light -> place in scene). Copy its model-abstraction for Vyra's provider-fallback pattern.
- **[HIGH]** [ZhengPeng7/BiRefNet](https://github.com/ZhengPeng7/BiRefNet) — SOTA edge quality (hair/fine detail) at 2K/4K with dedicated trimap-free matting weights. Use as the premium image-matting backend behind rembg's interface for hero shots and homepage poster frames generated from Seedance output.

## Video matting / compositing
- **[HIGH]** [PeterL1n/RobustVideoMatting](https://github.com/PeterL1n/RobustVideoMatting) — THE core engine for cleanly cutting an AI-KOL/real-face presenter out of VIDEO with temporal coherence (no flicker, no green screen, no trimap). Powers 'put the talking head on any background' for affiliate/product-review clips. Ships ONNX for render-worker serving.
- **[MEDIUM]** [facebookresearch/sam2](https://github.com/facebookresearch/sam2) — Apache-2.0 promptable segment-and-track in video for NON-human subjects (products, props, logos) where RVM doesn't apply. Click the product, isolate/relight/replace its background across the clip. Complements RVM for the full compositing surface.

## Upscaling / restoration
- **[HIGH]** [xinntao/Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN) — Default fast cheap upscaler for low-res seller photos and generated frames before encoding. Single highest-ROI quality bump on soft Seedance output. ncnn-Vulkan port = dependency-light server-side microservice. Free-tier default; reserve diffusion upscalers for premium.

## Face restoration
- **[HIGH]** [TencentARC/GFPGAN](https://github.com/TencentARC/GFPGAN) — Blind face restoration — fixes mushy eyes/teeth/skin on generated AI-KOL faces, makes them look real. Pairs with Real-ESRGAN in one combined enhance step (restore face + upscale background). Watch the over-smoothing tradeoff so KOLs don't all look identical.
- **[HIGH]** [sczhou/CodeFormer](https://github.com/sczhou/CodeFormer) — Robust blind face restoration with a tunable fidelity knob (identity vs aggressiveness). Better than GFPGAN on very degraded frames; expose the fidelity weight as a quality-tier setting. A/B against GFPGAN on real Seedance faces to pick per-use-case defaults.

## Frame interpolation
- **[HIGH]** [hzwer/Practical-RIFE](https://github.com/hzwer/Practical-RIFE) — Production branch of RIFE — smooths choppy AI-generated video and raises fps (24->48/60) for buttery delivery, or stretches short clips. Standard fix for diffusion-video temporal jitter. Wrap inference_video.py (multiplier + scene-change handling), not the academic repo.

## Music / audio generation
- **[HIGH]** [facebookresearch/audiocraft](https://github.com/facebookresearch/audiocraft) — Meta's MusicGen/AudioGen/EnCodec/AudioSeal — reference architecture for genre/mood BGM + SFX beds. CRITICAL: code is MIT but model WEIGHTS are CC-BY-NC-4.0 (non-commercial). Borrow API patterns + AudioSeal watermarking for de-AI posture; do NOT ship Meta weights commercially.
- **[HIGH]** [ace-step/ACE-Step](https://github.com/ace-step/ACE-Step) — Apache-2.0 full-song generator, multilingual incl. Asian languages, ~20s for 4min on A100, voice-clone + lyric-edit. The realistic self-hostable, legally-monetizable Suno alternative for Vyra branded jingles. Check ACE-Step-1.5 for consumer-GPU economics.

## Audio mixing / mastering
- **[HIGH]** [spotify/pedalboard](https://github.com/spotify/pedalboard) — MIT studio-quality DSP (JUCE-backed, ~300x faster than pure Python). The production mixing layer: loudness-normalize, EQ/compress the bed, and crucially sidechain-duck BGM under Vietnamese TTS voiceover. Replaces brittle ffmpeg filter-graph strings.

## ASR / caption timing
- **[HIGH]** [m-bain/whisperX](https://github.com/m-bain/whisperX) — The word-level timestamp foundation EVERY karaoke/word-highlight caption depends on (wav2vec2 forced alignment lands the active-word highlight on the exact frame; vanilla Whisper is off by seconds). Plus diarization for multi-speaker review clips. Verify a Vietnamese aligner exists or fall back to faster-whisper word_timestamps.

## Subtitle I/O
- **[HIGH]** [tkarabela/pysubs2](https://github.com/tkarabela/pysubs2) — Mature, CI-tested library to programmatically EMIT styled .ass (styles, \k karaoke tags, positioning, fades) and convert SRT/VTT/ASS. Standardize Vyra's subtitle serialization on this instead of ad-hoc f-strings.

## Long-video -> shorts pipeline
- **[HIGH]** [louisedesadeleer/clipify](https://github.com/louisedesadeleer/clipify) — Near feature-complete blueprint for the OpusClip/Submagic flow Vyra wants: transcript-driven highlight selection + 16:9->9:16 reframe with face-track pans + Opus-style active-word ASS captions, fully local. The most directly transplantable end-to-end pipeline in the set; pair its ASS builder with WhisperX timings.

## Programmatic video / motion graphics
- **[HIGH]** [remotion-dev/remotion](https://github.com/remotion-dev/remotion) — Make MP4s in React at scale — data-driven templated motion graphics, animated captions, branded intros/outros, per-product affiliate variations. Web/TS stack aligns with Vyra's Next.js frontend. Watch the company-license terms before commercial use.

## FFmpeg orchestration / NLE
- **[HIGH]** [Zulko/moviepy](https://github.com/Zulko/moviepy) — MIT Python NLE — concatenate Seedance clips, overlay brand kits/logos, insert Vietnamese-text titles, composite KOL faces, mix audio, transitions. Likely backbone of Vyra's render orchestration.

## FFmpeg orchestration
- **[HIGH]** [kkroening/ffmpeg-python](https://github.com/kkroening/ffmpeg-python) — Build FFmpeg filtergraphs as composable Python expressions instead of brittle command strings (16:9->9:16 scale, overlay, concat, loudnorm, subtitle burn). The clean FFmpeg call layer under Vyra's edit engine.

## Auto-cut / silence removal
- **[HIGH]** [WyattBlue/auto-editor](https://github.com/WyattBlue/auto-editor) — Gold-standard first-pass silence/inactivity cut — auto-trims dead air from review/affiliate and KOL talking-head footage before captioning. Clean CLI to shell out to; mirror its --margin pacing and labeled-frame model.

## Vietnamese TTS / voice cloning
- **[HIGH]** [fishaudio/fish-speech](https://github.com/fishaudio/fish-speech) — SOTA multilingual TTS that explicitly lists Vietnamese AND does zero-shot cloning from a 10-30s clip with inline emotion tags. Fits the AI-KOL Vietnamese voice need directly. NOTE: restrictive 'Fish Audio Research License' — treat as architecture reference, verify license before any production embed.
- **[HIGH]** [thinhlpg/vixtts-demo](https://github.com/thinhlpg/vixtts-demo) — The most directly reusable Vietnamese voice-cloning reference — viXTTS fine-tuned from XTTS-v2 on viVoice, clones from a ~6s clip. Weights + demo usable (MPL-2.0 code). Caveats: fine-tuning code withheld, unmaintained, Linux/WSL2 only — plan to re-derive training if you need to retrain.
- **[HIGH]** [dangvansam/viet-tts](https://github.com/dangvansam/viet-tts) — Production-shaped self-hosted Vietnamese TTS: OpenAI-TTS-API-compatible server (drops into Vyra's provider-chain pattern), Apache-2.0 source, real Vinorm Vietnamese normalization, prompt-audio cloning via CosyVoice. Best blueprint for a self-hosted VN TTS microservice (models CC-BY-NC — check).
- **[HIGH]** [nguyenvulebinh/VietVoice-TTS](https://github.com/nguyenvulebinh/VietVoice-TTS) — MIT-licensed VN TTS with built-in north/central/south accent + style (news/review/audiobook) + emotion controls that map almost 1:1 onto Vyra's multi-genre/KOL-persona feature set — including the regional-accent axis competitors lack. Validate audio quality (early-stage repo) before depending on it.
- **[HIGH]** [SWivid/F5-TTS](https://github.com/SWivid/F5-TTS) — MIT code + first-class documented fine-tuning makes it the strongest candidate to train Vyra's OWN Vietnamese clone model on viVoice (community VN fine-tunes already exist). Fast (RTF ~0.15) for per-video batch TTS. Pretrained weights are CC-BY-NC — train on owned/licensed data for commercial weights.
- **[MEDIUM]** [FunAudioLLM/CosyVoice](https://github.com/FunAudioLLM/CosyVoice) — Apache-2.0, the engine UNDER dangvansam/viet-tts so the Vietnamese path already exists downstream. Instruction-based emotion/dialect control + vLLM/TensorRT serving for high-throughput batch TTS at Vyra's scale.

## Agentic video-gen framework
- **[HIGH]** [HKUDS/ViMax](https://github.com/HKUDS/ViMax) — Closest architectural match to Vyra's multi-genre AI video studio: MIT multi-agent (Director/Screenwriter/Producer/Generator) idea/script/novel->storyboard->character-consistent multi-shot video with a provider-agnostic generator stage. AutoCameo (user-as-consistent-character) maps onto the AI-KOL-face feature. Borrow the agent role decomposition + consistency checks.

## Social scheduling (schedule-and-remind)
- **[HIGH]** [gitroomhq/postiz-app](https://github.com/gitroomhq/postiz-app) — Reference architecture for a schedule-and-publish layer: Temporal-backed queue, per-platform provider abstraction (one class per network's OAuth+upload+post), workspace->channel->post multi-account model, calendar UI. Vyra is no-auto-post: fork the skeleton and DEGRADE the publish step to schedule-and-REMIND. AGPL-3.0 — re-implement patterns, don't vendor.
- **[HIGH]** [inovector/mixpost](https://github.com/inovector/mixpost) — MIT (the most legally-borrowable full scheduler here) Laravel implementation of the schedule->queue->publish loop with drafts + media library. The media-library + draft-state model maps onto Vyra storing rendered videos before a human decides to post; cross-check its lighter Laravel-queue approach against Postiz's Temporal.

## Sanctioned upload (YouTube API)
- **[HIGH]** [tokland/youtube-upload](https://github.com/tokland/youtube-upload) — The LEGITIMATE, API-sanctioned YouTube path (Data API v3 + OAuth2) — the right way for Vyra to queue to YouTube vs TikTok cookie-hacks. Multi-credential = multi-channel done right; the upload-as-private + human-flips-to-public pattern is the cleanest no-auto-post primitive. GPLv3 — read for the API recipe, re-implement.

## Source ingest / trend research (FastAPI)
- **[HIGH]** [Evil0ctal/Douyin_TikTok_Download_API](https://github.com/Evil0ctal/Douyin_TikTok_Download_API) — Maintained FastAPI service (matches Vyra's stack) that tracks the constantly-breaking Douyin/TikTok signature + parse logic — useful for a LICENSED/OWNED source-ingest layer and trend-metadata research. INGEST ONLY: bulk-downloading other creators' full profiles crosses into laundering; use only for owned/licensed source or trend metadata.

## Trend research
- **[HIGH]** [davidteather/TikTok-Api](https://github.com/davidteather/TikTok-Api) — Most-maintained (2026) unofficial TikTok wrapper for trending feed/hashtag/search metadata, public data only (no auth/upload). The core trend-discovery input to build a Vietnamese 'what should I make today' topic crawler on.

## Localization / dubbing pipeline
- **[HIGH]** [krillinai/KrillinAI](https://github.com/krillinai/KrillinAI) — Closest match to Vyra's exact use case: short-form localization with Tiếng Việt as a CONFIRMED target, agent-first stage-by-stage CLI (maps onto Vyra's job/HOLD model), landscape->vertical auto-reframe, and auto cover/poster gen (Vyra already does gen->poster->hover). Go codebase — architecture reference more than drop-in.

## ASR->translate->TTS->mux dubbing pipeline
- **[MEDIUM]** [jianchang512/pyvideotrans](https://github.com/jianchang512/pyvideotrans) — Most-starred (18k), most-complete reference for the full ASR->translate->TTS->mux dubbing/localization chain — relevant for review-video localization and for Vietnamese<->other-lang reach. Battle-tested job state machine + pluggable ASR/TTS provider abstraction + speaker-diarization-to-per-role-voice + FFmpeg burn-in/audio-replace patterns in one codebase.

## Real-time, cheap lip-sync (cost/throughput)
- **[MEDIUM]** [TMElyralab/MuseTalk](https://github.com/TMElyralab/MuseTalk) — The most economical production lip-sync layer: real-time (30+ fps), mouth-region-only latent-diffusion inpainting that runs on modest GPUs, MIT-licensed with training code open. Good for high-volume Vietnamese-TTS-driven review videos where cost/throughput dominate — a fast post-process pass over already-generated Seedance footage. Complements LatentSync (quality) with a throughput-first option.

## Render-as-API / batch deterministic templates
- **[MEDIUM]** [redotvideo/revideo](https://github.com/redotvideo/revideo) — Purpose-built for the render-as-an-API job-queue model Vyra's credit-billing backend needs (cleaner fit than Remotion's React-app model and fully MIT, no company-size license caveat). Parametrized TypeScript templates + a deployable render endpoint + parallelized cloud render = a scalable, billing-aware path for deterministic cards, captions, and branded segments at low marginal cost.

## Audio assembly
- **[MEDIUM]** [jiaaro/pydub](https://github.com/jiaaro/pydub) — MIT high-level audio glue: overlay TTS+music+SFX, gain-stage, crossfade, trim/pad music to clip length, export. The quickest audio-arrangement layer; pair with pedalboard (pedalboard for DSP quality, pydub for arrangement).

## Caption editor UI
- **[MEDIUM]** [x007xyz/flycut-caption](https://github.com/x007xyz/flycut-caption) — React 19 + TS subtitle-editing component with in-BROWSER ASR via Transformers.js (no GPU server for the edit/preview path — a real cost lever). Strongest reference for Vyra's in-app caption editor UX (correct/retime/restyle before render).

## Scene detection
- **[MEDIUM]** [Breakthrough/PySceneDetect](https://github.com/Breakthrough/PySceneDetect) — Splits Seedance-generated or uploaded footage into shots and chooses clip boundaries for montage/highlight assembly. Pairs with auto-editor (audio) for shot-aware (visual) cutting; usable directly as a Python dependency.

## Faceless short-video factory
- **[MEDIUM]** [RayVentura/ShortGPT](https://github.com/RayVentura/ShortGPT) — Cleaner-architected sibling of MoneyPrinterTurbo. Its engine-per-content-type separation (Short/Video/Translation engines on shared asset+voice infra) is a strong template for Vyra's multi-genre studio; the translation/dubbing engine is directly relevant to Vietnamese localization.

## Explainer-video pipeline
- **[MEDIUM]** [prajwal-y/video_explainer](https://github.com/prajwal-y/video_explainer) — Best-structured explainer pipeline: doc/PDF/URL ingest -> script -> word-timed TTS -> AI-generated Remotion scene components -> SFX planning + MusicGen scoring -> render, with a multi-phase fact-checking pass competitors lack. Borrow the sound-design and QA stages for Vyra's explainer genre.

## AI -> stock-asset bridge
- **[MEDIUM]** [addyosmani/pexels-ai-video-downloader](https://github.com/addyosmani/pexels-ai-video-downloader) — Precise, clean demo of the exact AI-to-asset bridge Vyra needs: scene/script text -> LLM-generated Pexels search phrase -> orientation-aware (portrait) fetch, organized by scene. Borrow the prompt design and the text->query->fetch contract for auto-b-roll. Licensed-source only.

## AI trend agent
- **[MEDIUM]** [ericciarla/trendFinder](https://github.com/ericciarla/trendFinder) — Direct blueprint for an LLM-powered 'what should I make a video about' feature: collect -> LLM-summarize/score -> rank -> notify, cron-driven, multi-LLM-provider (mirrors Vyra's provider-fallback chain). Turns raw social data into ranked actionable topics + suggested scripts.

---

# Phần bổ sung B — Tích hợp provider CometAPI (VERIFIED 2026-06-30)

- **Key đã set** trong `.env` (`COMETAPI_API_KEY=sk-A3I…`, masked). Provider chain mặc định `cometapi → runware → seedance_piapi`.
- **BUG đã sửa** (`video_engine/video_stage/cometapi_video.py`): CometAPI yêu cầu `seconds` là **CHUỖI** (`"5"`), gửi number → HTTP 400. Đã đổi sang `str(...)`. Body verify chạy: `{"model":"doubao-seedance-2-0-fast","prompt":...,"seconds":"5","size":"9:16"}` → 200, trả `task_id`.
- **⚠️ TỐC ĐỘ CHẬM**: clip probe đầu tiên kẹt `in_progress 30%` >10 phút (PiAPI chỉ ~100-130s/clip). Reseller queue có thể nghẽn. CẦN xác minh: (a) clip có hoàn tất không, (b) tốc độ ổn định, (c) `completed_at` set nhầm khi vẫn in_progress. Nếu CometAPI chậm kinh niên → cân nhắc Runware (cần key) hoặc nạp lại PiAPI cho clip gấp.
- **Resolution control TBD**: body hiện chỉ gửi `size=aspect` ("9:16"), KHÔNG gửi 480p/720p → chưa kiểm soát res (⇒ chi phí). Phải xác minh field resolution của CometAPI (poll clip probe để biết res mặc định).
- **Lấy video**: `GET /v1/videos/{id}/content` (trả 400 "Task is not completed yet" khi chưa xong) hoặc `video_url` khi có.
- **GIÁ (per giây, 480p)**: CometAPI 1-5-pro $0.024 < 1-0-pro $0.032 < 2-0-fast $0.0504 < 2-0 $0.063. PiAPI fast $0.08, mini $0.07. Runware 2.0 $0.07, Mini $0.036. → **CometAPI 1-5-pro rẻ nhất ($0.12/clip 5s, $3.24/27 clip)**. KẾ HOẠCH: bench 1-5-pro vs 2-0-fast vs 2-0(std) trên 2-3 clip mặt, soi mắt, chốt model.

# Phần bổ sung C — LƯU Ý RENDER: đúng khung tỉ lệ theo vị trí trên trang (founder nhấn mạnh)

KHÔNG render tất cả 9:16. Mỗi clip render theo **đúng aspect của ô nó nằm trên homepage**:
- Marquee "MẪU OUTPUT" + KOL grid + card dọc → **9:16**.
- Bento ô ngang / sản phẩm landscape (đồng hồ, máy pha cà phê, túi da, lookbook) → **16:9**.
- Manifest (`scratchpad/manifest.json`) ĐÃ có field `aspect` từng clip — render phải truyền đúng aspect đó, và poster trích đúng tỉ lệ để khớp ô (object-cover).

---

# Phần bổ sung D — Checklist tồn đọng (start session mới)

## Việc còn treo
- [ ] [ ] Đợi top-up CometAPI $20 xác nhận xong TRƯỚC khi render (founder đang nạp, pending)
- [ ] [ ] Đổi VIDEO_PROVIDER trong .env từ 'seedance_piapi' sang chain 'cometapi,runware,seedance_piapi' (rẻ trước) — HOẶC sửa gen_v3.py dòng 37 gọi CometAPI provider thay SeedancePiapiProvider
- [ ] [ ] Bench 3 model CometAPI (doubao-seedance-1-5-pro $0.024/s rẻ nhất / 2-0-fast / 2-0 std) trên 2-3 clip mặt test, verify da trắng-hồng-filter còn texture, chọn model
- [ ] [ ] (Nên) Viết lại 27 prompt trong manifest.json theo khung Kling+Seedance: cắt 96-146 từ xuống 50-80 từ, front-load camera/style, fold anti-plastic vào positive
- [ ] [ ] Render lại 2 clip mặt đã mất MP4 (face-girl-next-door-bedroom-vlogger, face-tech-reviewer-messy-desk-male) — chỉ còn poster JPG trong scratchpad
- [ ] [ ] Render đủ 27 clip (resume-safe, pool=1, sleep 8s) ra apps/web/public/showcase/v2/
- [ ] [ ] ffmpeg trích poster frame mỗi clip + nén (tham khảo post_gen.py trong scratchpad)
- [ ] [ ] Wire 27 clip vào homepage: thay 4 mặt KOL (featured-kol.tsx), feed genre vào marquee (use-cases.tsx/page.tsx), thêm product bento
- [ ] [ ] Screenshot-verify homepage bằng browse skill + commit
- [ ] [ ] Quyết định file untracked: apps/web/public/samples/fashion-v2.mp4 và 'kết quả nghiên cứu.txt' ở repo root
- [ ] [ ] P1: build HTML/CSS deterministic text-frame cho intro/stat/CTA (margin lever, mượn huytranvan)
- [ ] [ ] M2: viết M2 Payment endpoints (POST /v1/payments, GET /v1/payments/{id}) trong app_api/routers/billing.py (hiện 404)
- [ ] [ ] M2: MoMo adapter + webhook reconciliation (cần merchant code thật)
- [ ] [ ] M2: Monthly credit reset cron + migration 0004 (hàm grant idempotent có, trigger chưa code)
- [ ] [ ] M2: Credit packs API GET /v1/credit-packs (model có, endpoint chưa viết, FE đang hardcode)
- [ ] [ ] M2: KOL personas CRUD endpoints (POST /v1/kol-personas, face upload presigned URL, consent gate) trong content.py (stub)
- [ ] [ ] Build /app/director page (404, studio-shell.tsx:16 trỏ tới)
- [ ] [ ] T4 right-panel studio + custom 404 page
- [ ] [ ] Voice-persona render-honor: sửa video_engine/voice/tts.py:26 (đang đọc global settings.tts_voice, bỏ qua params.voice_persona)
- [ ] [ ] Long-narrative + film-recap: wire render_service.py:14 (đang raise NotImplementedError); film_recap recap mode P1 stubbed
- [ ] [ ] Face-swap + voice-clone providers (stub DB, render no-op, cần provider ngoài + legal review)
- [ ] [ ] resolve_bank_payment_org() O(orgs) scan → bảng global memo→org (app_api/billing.py:152)
- [ ] [ ] CSP hardening (apps/web/src/middleware.ts TODO(csp)); Redis rate-limit; Arq queue mode

## Bước đầu session mới
1. Xác nhận top-up CometAPI đã xong chưa (hỏi founder) — KHÔNG render nếu chưa xong
1. Đọc lại 3 file trong scratchpad session: manifest.json (27 clip), gen_v3.py (script render, dòng 37 hardcode SeedancePiapiProvider cần đổi), gen_v3.log (chứng cứ blocker HTTP 500 hết credit từ clip 3)
1. Sửa provider: đặt .env VIDEO_PROVIDER=cometapi,runware,seedance_piapi HOẶC sửa gen_v3.py dùng CometAPI provider — vì .env hiện trỏ seedance_piapi đã cạn credit
1. Bench 3 model CometAPI trên 2-3 clip mặt test trước khi render full 27 (chọn model đẹp nhất cho mặt trắng-hồng-filter còn texture)
1. Cân nhắc viết lại 27 prompt theo khung Kling (mục 5): cắt 96-146 từ xuống 50-80 từ, front-load camera/style anchor, fold anti-plastic vào positive (Seedance không có negative field)
1. Lưu ý 2 clip mặt render OK đã MẤT MP4 (v2/ rỗng), chỉ còn 2 poster JPG ok_face-*.jpg trong scratchpad — phải render lại

## Câu hỏi mở cho Gemini
- 27 clip showcase tốn tiền render nhưng không sinh doanh thu (margin≈0). Có nên giảm số clip showcase, hoặc ưu tiên P1 (HTML text-frame margin lever) TRƯỚC khi đốt tiền render 27 clip không?
- Model nào nên chốt cho mặt người thật trắng-hồng-filter: doubao-seedance-1-5-pro (rẻ nhất $0.024/s nhưng version cũ hơn) hay 2-0-fast/2-0 (mới hơn, đắt 2x)? Trade-off chất lượng-vs-giá ở showcase có đáng không?
- Khung prompt Kling (front-load camera, 50-80 từ, fold anti-plastic) là lý thuyết tổng hợp — Gemini có kinh nghiệm thực tế nào với Seedance/Doubao t2v cho mặt người Việt trắng-hồng-filter không bị nhựa không?
- Provider chain config: nên để .env VIDEO_PROVIDER=chain (rẻ trước) cho production luôn, hay chỉ render showcase qua CometAPI rồi giữ PiAPI cho prod? (Liên quan moderation: Seedance/PiAPI strict, doubao có thể khác.)
- Long-narrative + film-recap render_service raise NotImplementedError — đây là gap lớn so với đối thủ (multi-shot YouTube). Có nên ưu tiên wire 2 mode này lên trước M2 payment endpoints không, hay payment (doanh thu) phải đi trước?
- Voice-persona render-honor là stub (TTS đọc global setting). Sửa nó cần thread voice+rate+pitch vào render stateless + boot test — có rủi ro phá pipeline product_ad đang chạy ổn. Gemini đánh giá độ ưu tiên thế nào?

---

# CẬP NHẬT (2026-06-30, cuối session) — VERDICT render CometAPI

- ✅ **MODEL CHỐT: `doubao-seedance-1-5-pro`** — verify thật: render **92 giây**, ra **720x1280 (720p)**, mặt photoreal (lỗ chân lông, nốt ruồi, cười tự nhiên, off-lens). KHÔNG nhựa AI.
- ❌ **`doubao-seedance-2-0-fast` BỊ KẸT** — task probe đứng `in_progress 30%` >25 phút. Tránh model này trên CometAPI.
- 📏 **Resolution mặc định = 720p** khi chỉ gửi `size:"9:16"` (không gửi field res). Cost 720p 1-5-pro = $0.052/s = **$0.26/clip 5s → ~$7 cho 27 clip**. Muốn 480p ($0.024/s) phải tìm đúng field resolution của CometAPI (TODO verify).
- ⚠️ **Da ra tông TỰ NHIÊN, chưa "trắng hồng/trắng trẻo"** dù prompt có "fair + beauty filter". CẦN đẩy prompt mạnh hơn: "pale/fair Korean-idol skin, brightened, rosy glow, strong beauty filter" — nhưng giữ pores/catchlight để không thành doll. PHẢI test lại 1-2 clip trước khi render full 27.
- 62 repo đã clone về `D:\vyra-research\repos\` (3.7GB) — sẵn cho session sau đọc sâu.
