# ⭐ VYRA — TRẠNG THÁI MỚI NHẤT (2026-07-01) — ĐỌC FILE NÀY TRƯỚC

> Handoff sang session mới. File này = state HIỆN TẠI + việc cần làm. Trả lời user bằng **TIẾNG VIỆT**.
> Phân tích sâu (đối thủ, repo, prompt framework, pricing) ở: **docs/VYRA_SESSION_HANDOFF.md** + **docs/VYRA_REPOS_INVENTORY.md**.
> Branch: **feat/ui-upgrade**. Repo: `c:/Users/NTD/Desktop/vietvid`. Web dev: localhost:3000.

---

## 🎬 ĐANG DỞ: render 27 clip nội dung homepage (việc chính)

**Mục tiêu:** render 27 clip (9 mặt KOL + 11 genre + 7 sản phẩm) → nhúng vào homepage thay clip cũ.

**Trạng thái render (20/27 xong):**
| Loại | Xong | Thiếu | Model | Output |
|---|---|---|---|---|
| Mặt KOL | 3/9 (vlogger, café, tech-male) | **6** (streetwear-male, young-mom, genz-student, bookshop, yoga, skincare) | **2.0-fast** | `apps/web/public/showcase/v2/<key>.mp4` |
| Genre | 11/11 ✓ | 0 | 1.5-pro | nt |
| Sản phẩm | 6/7 | **1** (prod-beauty-lipstick-vanity) | 1.5-pro | nt |

**⛔ BLOCKER: CometAPI HẾT CREDIT** (`HTTP 403 insufficient_user_quota, remaining $-0`). $20 đã cạn (do nhiều vòng tinh chỉnh mặt). Render lỗi KHÔNG bị trừ tiền. **Cần user nạp thêm ~$10 CometAPI** rồi render nốt 7 clip.

**Cách render tiếp (sau khi nạp):**
1. `python scratchpad/gen_comet.py` — resume-safe, chỉ render clip còn FAIL/thiếu trong `scratchpad/gen_comet_summary.json`. Manifest: `scratchpad/manifest.json` (đã có prompt cuối). MODEL trong gen_comet.py = `doubao-seedance-2-0-fast`.
2. Resume-safe + timeout 600s/clip (bỏ clip kẹt) + download retry.

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

## ✅ VIỆC CẦN LÀM (TODO, ưu tiên trên xuống)
1. **(chờ user nạp CometAPI)** render nốt 6 mặt + 1 sản phẩm (2.0-fast): `python scratchpad/gen_comet.py`.
2. (tuỳ chọn) nâng vài genre có người lên 2.0 cho đồng bộ realism.
3. Soi poster cả 27 — lệch thì sửa prompt manifest → archive clip cũ → render lại clip đó.
4. Trích poster (`ffmpeg -ss 2.2 -frames:v 1 -q:v 3`) + nén mp4 (`scale=-2:864 -crf 28`) + nén jpg.
5. **Nhúng homepage ĐÚNG TỈ LỆ**: `featured-kol.tsx` (9 mặt → card 9:16), `page.tsx` SAMPLES marquee (genre), bento REEL (sản phẩm 16:9 → ô ngang). Đổi `/showcase/<x>` → `/showcase/v2/<key>`.
6. Chụp Playwright kiểm chứng → commit (**CHỈ .jpg poster, KHÔNG .mp4** — gitignored).
7. (lâu dài, từ phân tích đối thủ — xem VYRA_SESSION_HANDOFF.md §roadmap): HTML-frame cảnh chữ (đòn bẩy margin), link→review trọn gói, Start&End frame, Video Extend, đọc sâu 62 repo ở D.

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
