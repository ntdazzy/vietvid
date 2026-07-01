# VYRA — Kho repo tham khảo V2 (đợt quét 2026-07-01)

> ~54 repo MỚI (chưa có trong 62 repo cũ ở `VYRA_REPOS_INVENTORY.md`), quét 8 mảng.
> Clone vào **thư mục phân loại**: `D:/vyra-research/repos/<mã-mảng>/<repo>`.
> Mục đích: đọc **logic + thuật toán** của họ để nâng cấp Vyra. Ngôn ngữ: Việt, dễ hiểu.

**8 mảng (thư mục):**
`01-affiliate-scraping` · `02-batch-queue-credit` · `03-prompt-script` · `04-avatar-tts-film` · `05-downloader-trend` · `06-reuse-pwa-studio` · `07-webperf-gallery` · `08-genre-trend-roleplay`

---

## 01 — Affiliate + quét Shopee/TikTok + né chặn-bot  → giải RỦI RO #1

| Repo | ⭐ | Học gì |
|---|---|---|
| firecrawl/firecrawl | 142k | URL bất kỳ → JSON có cấu trúc; tự lo proxy + né bot + render JS. Lớp "nuốt link" mặc định |
| D4Vinci/Scrapling | 67k | Vũ khí chống anti-bot: giả fingerprint, vượt Cloudflare, xoay proxy sẵn |
| daijro/camoufox | 9.7k | Firefox tàng hình (giả navigator/WebGL ở tầng C++) cho trang chặn gắt nhất |
| prizmad/Prizmad-MCP-server | mới | **Blueprint gần y hệt Vyra**: URL sản phẩm → video ad 9:16, presets caption/nhạc/CTA |
| HasData/auto-ecommerce-scraper | — | Tự nhận nền tảng (Shopify/Woo) rồi chọn cách bóc title/giá/ảnh/review |
| mishushakov/llm-scraper | 6.8k | Dùng LLM + schema đọc trang → data (chịu được layout đổi, không giòn như CSS) |
| congminh1254/shopee-sdk | 154 | **Shopee Open API v2** chính thức — đường HỢP PHÁP khi user là chủ shop, không bao giờ bị chặn |

**Kiến trúc chốt (rủi ro #1):** ingest 3 tầng có dự phòng → (1) **API chính thức** Shopee/Lazada khi user là chủ shop → (2) **Firecrawl** (managed, tự né bot) → (3) **Scrapling + Camoufox** + LLM-parse khi Firecrawl fail. Luôn cho user **upload ảnh + dán text** làm chốt chặn cuối.

---

## 02 — Hàng đợi + thông báo + credit (tính năng "làm hàng loạt")  → giải RỦI RO #2, #3

| Repo | ⭐ | Học gì |
|---|---|---|
| getlago/lago | 7.9k | **Engine credit** đầy đủ: ví trả trước, "1 credit HTML / 5 credit mặt-AI", top-up, breakage |
| openmeterio/openmeter | 2.7k | Đo dùng real-time cho AI: credit ưu-tiên-hết-hạn-trước (đốt credit KM trước). Nhẹ hơn Lago |
| caronc/apprise | 13k | **1 thư viện = 80+ kênh báo "job xong"** (Telegram/email/push). Bỏ qua viết từng cái |
| taskforcesh/bullmq-video-transcoder | 150 | **Mẫu batch chuẩn**: 1 job to chẻ thành job con (20 link = 1 cha, mỗi video = 1 con) |
| taskforcesh/bullmq | 7k | Hàng đợi Redis cho Node: retry + backoff + ưu tiên + cha/con |
| python-arq/arq | 2.5k | **Hàng đợi async cho FastAPI** (đúng backend Vyra): chạy trăm job gọi API AI chậm không đơ |
| tungnguyentien/zalo-node-sdk · ttpro1995/zalo-python-sdk | — | Bắn tin **Zalo OA** khi render xong (Apprise chưa có Zalo) |

**Kiến trúc chốt (rủi ro #2, #3):** hàng đợi **ARQ** (hợp FastAPI) → dán 20 link, enqueue ngay, trả job_id để theo dõi. Báo xong qua **Apprise** (Zalo wire riêng). Credit đặt trên **Lago/OpenMeter** (ví 2-túi, lịch sử minh bạch), giữ-rồi-trừ (HOLD) để credit không mất khi lỗi.

---

## 03 — Prompt + viết kịch bản bán hàng  → nâng chất "chốt đơn"

| Repo | ⭐ | Học gì |
|---|---|---|
| coreyhaines31/marketingskills | 35.6k | 50+ khung marketing (ad-creative, tâm lý mua) làm sườn cho prompt viết kịch bản Việt |
| f/awesome-chatgpt-prompts | 165k | Thư viện persona (copywriter, đạo diễn) làm mồi vai cho AI |
| WynterJones/CoppieGPT | 160 | **232 công thức copywriting** (AIDA/PAS/FAB) → chọn ~15 làm "bộ chọn công thức" tiếng Việt |
| YouMind-OpenLab/awesome-seedance-2-prompts | 1.5k | 2000+ prompt Seedance (ads/UGC) + mẹo giữ nhân vật nhất quán — đúng model Vyra dùng |
| shijincai/veo3-prompt-generator | 27 | **Khung JSON "cảnh nào quay gì"** (góc máy/ống kính/ánh sáng/màu) làm hợp đồng script→render |
| 567-labs/instructor | 13.3k | **Ép AI ra đúng JSON + tự sửa nếu sai** (Claude-native). Xương sống chất lượng đầu ra |
| dontriskit/awesome-ai-system-prompts | 6k | 8 mẫu VÌ SAO prompt hoạt động — sách thiết kế system prompt của Vyra |
| shixinzhang/tiktok-viral-hooks | 6 | 126+ mẫu "hook 3 giây đầu" — chỗ quyết định video chốt đơn |
| realkimbarrett/advertising-skills | mới | Chuỗi: bóc chân dung KH → bóc offer → chọn góc → viết — đúng luồng Vyra |

**Kiến trúc chốt:** 3 lớp — (1) system-prompt lấy sườn từ `marketingskills` + 8 mẫu `awesome-ai-system-prompts` + ~15 công thức `CoppieGPT`; (2) ép JSON bằng `instructor` theo schema `veo3-prompt-generator`; (3) prompt video few-shot từ `awesome-seedance-2-prompts` + hook từ `tiktok-viral-hooks`.

---

## 04 — Mặt AI nói chuyện + giọng Việt + review phim

| Repo | ⭐ | Học gì | API/Tự host |
|---|---|---|---|
| Tencent-Hunyuan/HunyuanVideo-Avatar | 2.1k | Mặt nói có **cảm xúc + nhiều người** (10GB VRAM). Bản tự-host dự phòng | Tự host / PiAPI |
| Omni-Avatar/OmniAvatar | 1.8k | Mặt+thân audio-driven, Apache-2.0 (dự phòng khi API OmniHuman đắt) | Tự host |
| MeiGen-AI/InfiniteTalk | mới | **Lồng tiếng dài vô hạn** khớp môi — hợp review phim | Tự host / Replicate |
| bytedance/InfiniteYou | ICCV'25 | **Khoá mặt nhất quán từ 1 ảnh** (FLUX) — hơn InstantID/PuLID cũ | Tự host / Replicate |
| PKU-YuanGroup/ConsisID | CVPR'25 | Giữ mặt ổn định **suốt cả clip** (không chỉ 1 khung) | Tự host |
| OpenBMB/VoxCPM | mới | TTS 30 ngôn ngữ (có Việt), voice-design + nhái giọng — tier cao cấp | Tự host |
| keithhb33/AI-Movie-Shorts | 57 | **Bộ khung review phim**: phim → phụ đề → kịch bản → giọng đọc → cắt ghép 9:16 | Tự host |

*(Giọng Việt `VieNeu-TTS v3` — đã có trong 62 repo cũ — giải đúng: đọc tên nước ngoài + cảm xúc + nhái giọng 3-5s.)*

**Kiến trúc chốt:** mặt nói = **MUA API** OmniHuman/Kling (fal.ai/CometAPI) trước, `HunyuanVideo-Avatar` tự-host để dành. Mặt nhất quán = `InfiniteYou`. Review phim = `AI-Movie-Shorts` + giọng `VieNeu-TTS`.

---

## 05 — Tải video no-logo + quét trend

| Repo | ⭐ | Học gì | Rủi ro |
|---|---|---|---|
| imputnet/cobalt | 41k | **Tool "tải video không logo"** TikTok/IG/YT/FB — tự host làm sidecar | Thấp (AGPL, chỉ content công khai) |
| yt-dlp/yt-dlp | 100k+ | Engine tải dưới mọi wrapper, 1800+ site | Thấp |
| sansan0/TrendRadar | 60k | **Quét hot-search Douyin** + 10 sàn CN, có MCP để agent hỏi "đang hot gì" | Thấp (GPL, chỉ bảng xếp hạng công khai) |

**⚠️ TRÁNH:** các repo reverse-engineer API TikTok lậu (zetreex/notemrovsky/armxe) — vi phạm điều khoản. Trend biến-hình/nhảy/bóng đá: KHÔNG có repo riêng → dùng TrendRadar + lọc từ khoá (`biếnhình`, `bóngđá`, sound-id nhảy).

---

## 06 — Tái dùng asset (tiết kiệm tiền) + PWA + studio kéo-thả

| Repo | ⭐ | Học gì |
|---|---|---|
| zilliztech/GPTCache | 8.1k | **Nhớ video/ảnh/giọng đã tạo → không trả tiền tạo lại** (cache theo nghĩa). Engine "đừng trả 2 lần" |
| directus/directus | 34.5k | **Kho asset có API** (tag, biến đổi ảnh, phân quyền) — biến clip đã tạo thành thư viện tra cứu |
| 11cafe/jaaz | 6.4k | Studio canvas vô hạn (Canva/Manus local) — mẫu UX "chọn cảnh/hành động, app tự dựng" |
| designcombo/react-video-editor | 1.7k | **Editor web kiểu CapCut** (timeline kéo/cắt/snap) — lấy mô hình timeline → render-spec |
| serwist/serwist | 1.4k | **Biến web thành app cài được (PWA)** cho Next.js — cách chuẩn hiện nay |
| tryvinci/vinci-clips | 127 | 1 video dài → nhiều short (cắt thông minh + caption) — làm giàu trang chủ rẻ |

**Kiến trúc chốt (tái dùng):** `GPTCache` (cache theo nghĩa, không trả tiền tạo lại) đứng trước `Directus` (kho asset có API) → clip cũ thành thư viện tái dùng + đắp lên trang chủ. Studio kéo-thả: `jaaz` (UX) + `react-video-editor` (code timeline). PWA: `serwist`.

---

## 07 — Web tải nhiều video mượt + tường video/gallery + mobile  → giải RỦI RO lag + mobile tệ

| Repo | ⭐ | Học gì |
|---|---|---|
| jaredLunde/masonic | 1.4k | **Tường masonry ảo hóa** — 500 ô chỉ mount vài ô đang hiện → không lag |
| thebuilder/react-intersection-observer | 5.5k | "Chỉ phát video khi lọt màn hình, cuộn qua thì dừng" — đòn bẩy số 1 chống giật |
| Gyanreyer/react-hover-video-player | 99 | Ô video: **rê mới phát** (trễ N ms mới tải), có poster/loading sẵn |
| muxinc/next-video | 1.2k | Video kiểu Next.js: `loading="viewport"`, poster mờ trước, phát sau khi tương tác |
| davidjerleke/embla-carousel | 8.3k | **Vuốt-snap mobile** — mỗi video 1 màn như TikTok (bản sửa mobile) |
| video-dev/hls.js | 16.8k | Streaming đổi độ nét theo mạng — mobile/mạng yếu tải bản nhẹ trước |

**Kiến trúc chốt:** desktop = tường masonry ảo hóa, mỗi ô là `react-hover-video-player` bật/tắt qua `intersection-observer` → dù bao nhiêu clip chỉ vài cái chạy thật. Serve qua `next-video` + HLS (poster rẻ trước, streaming theo mạng). Mobile = bỏ lưới, chuyển `embla` vuốt full màn.

---

## 08 — Thể loại (hoạt hình/phim) + trend + nhập-vai (đưa mặt vào video)

| Repo | ⭐ | Học gì | API/Tự host |
|---|---|---|---|
| **Wan-Video/Wan2.2** | **16.5k** | **ÁT CHỦ BÀI**: Wan2.2-Animate = nhập-vai (đưa mặt mình vào) + nhảy trend + thay đồ + biến hình Douyin, GỘP 1 model. Apache-2.0 | Tự host / Replicate/fal |
| Tencent/MimicMotion | 2.8k | "Cho ảnh này nhảy" (pose-driven) — engine nhảy/đu-trend, ít méo tay chân | Tự host |
| Zheng-Chong/CatVTON | 1.4k | **Thử đồ / thay đồ** (try-on) — lõi thay-đồ-KOL | Tự host |
| poptechstudio/ai-cinema-studio-engine | mới (MIT) | 21 LUT màu phim + 1645 preset quay phim → **look điện ảnh/ma/hành động** đắp lên clip | Tự host |
| geekjourneyx/awesome-ai-video-prompts | — | Bộ prompt genre (điện ảnh/ma/hành động/siêu anh hùng) → ship "nút style" ngay tuần này | Data |
| williamyang1991/VToonify | 3.6k | Video chân dung → **hoạt hình/anime/pixar** | Tự host |
| TheDenk/ControledAnimateDiff | — | AnimateDiff+ControlNet+RAVE = hiệu ứng **biến hình Douyin** thật (morph anime) | Tự host (ComfyUI) |

**⚠️ Nhập-vai = CHÈN danh tính, KHÔNG face-swap.** Tránh cụm face-swap (ghost/roop/Deep-Live-Cam) — chuyên deepfake người nổi tiếng trái phép. Vyra chỉ cho **user đưa ẢNH CỦA CHÍNH MÌNH** (có consent) → animate thành nhân vật (Wan2.2-Animate). Đây cũng là giải rủi ro #4.

**Kiến trúc chốt:** genre look = rẻ, làm ngay (prompt pack + LUT + VToonify). Nhập-vai/nhảy/thay-đồ/biến-hình = gom về **Wan2.2-Animate** (mua API trước, tự host sau). Sports/try-on-video = giai đoạn 2.

---

## Tổng kết — thứ tự đập vào Vyra

1. **Ngay (Nhóm 1 mũi nhọn):** ingest 3-tầng (01), hàng đợi + credit (02), prompt chốt đơn (03) → hoàn thiện "dán link → video bán hàng + làm hàng loạt".
2. **Kế:** mặt nói API (04) + Wan2.2-Animate nhập-vai (08) → gói cao.
3. **Song song (đánh bóng):** tường video mượt + mobile (07), tái dùng asset + PWA (06).
4. **Sau:** review phim (04), genre đầy đủ (08), sports/try-on (08 phase 2).

---

# ĐỢT 3 — Bản thay thế Wan2.2 (chạy 12GB) + hidden gems ít-sao

## A. Thay thế Wan2.2-Animate cho RTX 3060 12GB

Không 1 model nào làm cả 2 việc trên 12GB → tách:

| Việc | LOCAL trên 12GB (miễn phí) | API (làm cho khách) |
|---|---|---|
| **Mặt nói bán hàng** | `LivePortrait` (đã có, gần real-time) + `MuseTalk` (đã có) · **`JoyVASA`** (MIT, 8GB) · **`ditto-talkinghead`** (real-time, thương mại OK) · **`echomimic_v2`** (nửa người, 6-8GB) | **OmniHuman** $0.14/s hoặc **Kling Avatar** $0.115/s |
| **Nhập-vai / đưa mặt vào clip** | **`UniAnimate`** (repo duy nhất ghi rõ ~12GB, Apache) · `StableAnimator`/`MimicMotion` (một phần) | **Runway Act-Two** $0.05/s (rẻ+nét) · Wan-Animate qua **Replicate/WaveSpeed** (chính model đó, khỏi GPU) |
| **Khoá mặt KOL + thử đồ + style** | **`DreamO`** (bytedance, Apache, đường **8GB**) — 1 model gộp identity+try-on+style | — |
| **Thay đồ trên người đang chuyển động** | **`ViViD`** (Apache, cần offload) | — |

**Wan2.2-Animate 14B trên 12GB:** chỉ chạy bản nén **GGUF Q4 (~11.5GB)** qua ComfyUI + offload RAM → RẤT CHẬM (phút/giây video). Chỉ để test. Bản **5B** chạy tốt 12GB nhưng KHÔNG có tính năng Animate.
→ **Chốt: máy để test (LivePortrait/UniAnimate/DreamO); làm cho khách dùng API.**

## B. Hidden gems ít-sao nhưng chất (quét sâu)

| Repo | ⭐ | Vàng ở chỗ | Mảng |
|---|---|---|---|
| **nghimestudio/vietnormalizer** | 92 | Biến số/tiền VND-USD/%/tên nước ngoài → chữ đọc tiếng Việt TRƯỚC khi TTS. Giải đúng lỗi đọc sai. MIT, ~0.6ms | 13 |
| **bcat95/shopee-aff** | 43 | API Shopee Affiliate VN chính thức: tạo short-link + lấy data SP + hoa hồng. Đường HỢP PHÁP | 01 |
| **LCSantos-cmt/vibevid** | 0 | Pipeline gần y hệt Vyra: ảnh SP→persona→kịch bản AIDA→video + **chấm điểm chất lượng tự lọc**. Bê kiến trúc | 09 |
| **crisng95/flowboard** | 369 | Studio canvas kéo-node (Model/Product/Scene→nối→Generate) — UX studio Vyra 1:1 | 06 |
| **moshehbenavraham/vidapi** | 4 | Blueprint FastAPI "JSON template → render video" đúng kiến trúc Vyra cần | 09 |
| **messkan/prompt-cache** | 238 | Proxy cache LLM (hợp Claude) cắt ~80% tiền viết kịch bản | 06 |
| **BoundaryML/baml** | 8.5k | Ép LLM ra đúng cấu trúc, mạnh hơn instructor (đáng thử head-to-head) | 03 |
| **nexscope-ai/eCommerce-Skills** | 304 | 157 skill AI e-commerce, có khối TikTok Shop — làm kho tri thức kịch bản | 03 |
| **DreamO / ViViD / JoyVASA / ditto / UniAnimate** | — | Engine 12GB (xem bảng A) | 04/08 |

**⚠️ TRÁNH:** cụm face-swap roop/Deep-Live-Cam/ghost (deepfake trái phép). Nhập-vai của Vyra = animate ẢNH CỦA CHÍNH USER (có consent), không dán mặt lên người khác.
**⚠️ License:** `FLOAT`, `Sonic`, `valtec-tts`, `opentryon`, `AnimeGANv3` = **non-commercial** → chỉ tham khảo/API, đừng ship weights.
