# ⭐ VYRA — TRẠNG THÁI MỚI NHẤT (2026-07-01) — ĐỌC FILE NÀY TRƯỚC

> Handoff sang session mới. File này = state HIỆN TẠI + việc cần làm. Trả lời user bằng **TIẾNG VIỆT**.
> Phân tích sâu (đối thủ, repo, prompt framework, pricing) ở: **docs/VYRA_SESSION_HANDOFF.md** + **docs/VYRA_REPOS_INVENTORY.md**.
> Branch: **feat/ui-upgrade**. Repo: `c:/Users/NTD/Desktop/vietvid`. Web dev: localhost:3000.

---

## ✅ ĐÃ XONG (đêm 2026-07-01): 25 clip v2 nhúng homepage + trang con — KHÔNG cần render nữa

**Việc chính HOÀN TẤT bằng RECOVERY (không cần CometAPI).** 6 mặt "thiếu" được khôi phục từ `D:/vyra-research`
(các clip `div_`/`idol3_` 2.0 mới nhất + `clip-library/round3-faces-1.5`), nén web + trích poster, nhúng vào trang chủ.

**25 clip v2 đang LIVE** (`apps/web/public/showcase/v2/<key>.mp4` + `.jpg`, đã nén 95KB–1MB):
| Loại | Số | Nguồn | Vị trí trên trang |
|---|---|---|---|
| Mặt KOL | **9/9** | 3 sẵn (2.0) + 3 recover 2.0 (skincare/bookshop→1.5/genz) + 3 từ 1.5 (streetwear/young-mom/yoga) | `FeaturedKol` — lưới 9 mặt (featured Linh 2×2 + 8 ô dọc) |
| Genre | **10** | v2 (1 clip `genre-fitness-stretch-girl` = TRẺ EM → đã GỠ khỏi site, master còn ở `v2-masters/`) | `GenreWall` — bento trộn dọc/ngang |
| Sản phẩm | **6** | v2 (thiếu `prod-beauty-lipstick-vanity`, chưa render — không bắt buộc) | `ProductReel` — bento 3 dọc + 3 ngang |

**Components mới:** `genre-wall.tsx`, `product-reel.tsx` (hardcode nhãn Việt, dùng `HoverVideo`, tỉ lệ-aware).
`featured-kol.tsx` viết lại 4→9 mặt. Chèn vào `page.tsx` sau `<FeaturedKol/>`. **Trang con:** `/features/review|product_ad|lookbook`
results đổi sang clip v2; vá bug ảnh vỡ teaser marquee (`/<key>.jpg` → `/samples/<key>.jpg` trong `feature-showcase.tsx`).

**QA THẬT (Playwright + soi từng frame) ĐÃ PASS:** 9 mặt đều người lớn 24-28 photoreal; rê chuột chạy clip OK
(currentTime>0); **0 lỗi 404** asset (home + feature); `tsc --noEmit` xanh. Ảnh QA ở scratchpad/qa/.

**Masters gốc** (4–8MB) archive ở `D:/vyra-research/clip-library/v2-masters/` (luật "đừng xóa video" — đã giữ).

### Còn lại của "việc 1" (render) — KHÔNG bắt buộc, credit đã nạp còn nguyên
`scratchpad/gen_comet.py` + `manifest.json` đã MẤT (scratchpad rỗng) → không resume được. Nhưng goal (đủ 9 mặt trang chủ) đã đạt bằng recovery.
Nếu muốn bản 2.0 tươi cho 3 mặt đang dùng 1.5 (streetwear-male, young-mom, yoga) + 1 SP lipstick:
render bằng CometAPI (`doubao-seedance-2-0-fast`, seconds="5"), rồi **chỉ cần bỏ file vào** `apps/web/public/showcase/v2/<key>.mp4`,
nén `ffmpeg -i src -vf scale=-2:960 -crf 30 -an -movflags +faststart out.mp4` + poster `ffmpeg -ss 2.6 -i src -frames:v 1 -q:v 3 <key>.jpg` → trang tự nhận (key giữ nguyên).

---

## 🎨 CÔNG THỨC MẶT — ĐÃ CHỐT (đừng đổi nữa, user đã duyệt qua nhiều vòng)

**Model:** `doubao-seedance-2-0-fast` (user xác nhận **2.0 photoreal hơn 1.5 nhiều** — 1.5 hơi lộ AI). Ra 720p.

**9 mặt = đa dạng, KHÁC NHAU rõ, đều TRẮNG + ĐẸP + DÁNG:**
- 6 gái: **bob-cute** / **elegant-sexy tóc đen** / **sassy tóc nâu** / **soft curtain-bangs** / **sporty ponytail** / **glam tóc xoăn bồng**.
- 2 trai handsome fair, 1 mẹ bỉm.
- Yêu cầu user (đã thoả): **da trắng porcelain**, **mặt láng mịn KHÔNG mụn**, **tóc bồng glossy KHÔNG bết**, **dáng đầy đặn đường cong/ngực** (tinh tế, SFW — Seedance chặn hở), **RÕ LÀ NGƯỜI LỚN 24-26** (KHÔNG teen/trẻ con — đã sửa 2 cô bị nhìn trẻ), beauty-filter nhưng vẫn photographic.
- Prompt cuối đã nằm trong `manifest.json`. KHÔNG tái tạo người thật (user nhắc "Trần Hà Linh" → chỉ bắt PHONG CÁCH).

---

## 🚫 LUẬT: ĐỪNG XÓA VIDEO (user yêu cầu)
- KHÔNG bao giờ `rm` clip. **Archive** vào `D:/vyra-research/clip-library/` (đã có: `round1-faces`, `round2-tooyoung`, `round3-faces-1.5`).
- Clip gốc homepage `apps/web/public/showcase/*.mp4` (18) + `samples/*.mp4` (6) NGUYÊN VẸN. Clip test ở `D:/vyra-research/*.mp4`.

---

## ✅ VIỆC CẦN LÀM (TODO) — phần nhúng homepage ĐÃ XONG
- [x] Recover 6 mặt thiếu từ D: → đủ 9 mặt (đã soi frame, đều người lớn 24-28).
- [x] Nén web + poster 25 clip v2 (95KB–1MB) — archive master 4-8MB ở `v2-masters/`.
- [x] `FeaturedKol` 9 mặt + `GenreWall` 10 genre + `ProductReel` 6 SP, nhúng `page.tsx`.
- [x] Gỡ clip trẻ em `genre-fitness-stretch-girl` khỏi site.
- [x] Trang con `/features/review|product_ad|lookbook` dùng clip v2 + vá bug ảnh-vỡ teaser.
- [x] QA Playwright desktop+mobile, hover-play OK, 0 lỗi 404, tsc xanh.
- [ ] (tuỳ chọn) render 2.0 tươi cho 3 mặt 1.5 (streetwear/young-mom/yoga) + 1 SP lipstick — xem mục trên.
- [ ] (tuỳ chọn) nâng REEL/SAMPLES marquee cũ trên `page.tsx` sang clip v2 (hiện vẫn dùng clip showcase cũ, BỔ TRỢ chứ không trùng).
- [ ] (lâu dài, từ phân tích đối thủ — xem VYRA_SESSION_HANDOFF.md §roadmap): HTML-frame cảnh chữ (đòn bẩy margin), link→review trọn gói, Start&End frame, Video Extend, đọc sâu 62 repo ở D.

---

## 🔑 KIẾN THỨC PROVIDER (quan trọng)
- **CometAPI**: key trong `.env`. API `POST base/v1/videos` body `{model, prompt, seconds:"5" (STRING!), size:aspect}` → task_id; poll `GET /v1/videos/{id}`; tải `GET /v1/videos/{id}/content` (retry, đôi khi trả rác <50KB). Ra 720p.
  - Model: **`2-0-fast` đẹp nhất + chạy được** (lúc trước kẹt 30p là transient outage). **`2-0` (std) vẫn kẹt**. `1-5-pro` ổn định nhưng hơi AI.
  - Giá/giây: 1-5-pro 480p $0.024/720p $0.052; 2-0-fast 480p $0.05/720p $0.108. → 2.0-fast 720p ≈ $0.54/clip.
  - Registry default hiện = `1-5-pro` (ổn định). Nếu chốt dùng 2.0 cho web → đổi default + thêm fallback (2.0 intermittent).
- **PiAPI**: HẾT credit. **Runware**: chưa có key. Chain `cometapi→runware→seedance_piapi`.

---

## 📦 ĐÃ COMMIT session này (feat/ui-upgrade, mới→cũ)
- `f5e10df` CometAPI default 1-5-pro + download retry · `aebf291` seconds=string + handoff doc · `8a2dfbe` handoff + 180-repo inventory
- UI: `2103b3e`/`cec60fd`/`e1b70b0` login (glow + drift-wall) · `40ff28a` social proof · `170710d` before-after + KOL grid · `fca7eec` marquee đa thể loại
- **CHƯA commit:** thay đổi `config/registry.py` (default model — nếu có), `cometapi_video.py` (seconds/retry — đã commit). Mặt/clip chưa nhúng vào code (đang ở v2/).

---

## 📚 PHÂN TÍCH ĐÃ LÀM (đầy đủ ở 2 doc kia — đừng làm lại, tốn token)
- **Đối thủ** (Kling/Autovis/OpenArt/Poiiky/repo huytranvan): ma trận tính năng Vyra ĐÃ-CÓ / NÊN-BUILD / TRÁNH (laundering/né-detection). Top build: HTML-frame margin, link→review. → VYRA_SESSION_HANDOFF.md.
- **180 repo GitHub** rà soát, **62 clone** ở `D:/vyra-research/repos/`. → VYRA_REPOS_INVENTORY.md.
- **Prompt framework Kling+Seedance** + **bảng giá 3 provider** + **audit codebase** (video_engine rất đầy đủ: director, long_narrative, KOL, voice clone, captions, compose, QA, provider chain). → VYRA_SESSION_HANDOFF.md.
