# VYRA — ROADMAP đầy đủ (23 ý gốc từ user + trạng thái)

> Chép lại TOÀN BỘ ý user giao (office-hours 2026-06-28→07-01) để không sót ý nào qua các session.
> Trạng thái: ✅ xong · 🟡 làm 1 phần · ⏳ chưa làm · 💡 ý tưởng lớn (sau). Chi tiết chiến lược ở VYRA_CHIENLUOC_NHOM1.md.

## Đã trả lời (câu hỏi điều tra)
- **#1** Repo `AI-auto-generate-video` (huytranvan2010) = tool VN "bài viết → short 9:16", dùng **HTML/CSS frames** (đòn bẩy cắt chi phí). ✅
- **#3** 191 repo ở `D:/vyra-research/repos` (17 thư mục) = kho học/mượn pattern. ✅ (VYRA_REPOS_INVENTORY + _V2)

## Nhóm A — Mũi nhọn affiliate (kiếm tiền, làm TRƯỚC)
- **#17 💡 Phân tích đơn Shopee/TikTok → giải pháp + kịch bản + cách viral** (nhập nhiều đơn). CHƯA làm. Repo: bcat95/shopee-aff, duyet/pricetrack, nexscope-ai/eCommerce-Skills.
- **#23 🟡 Studio tùy chỉnh sâu** (số người/mặt/da/dáng/quần áo/upload ảnh thật+đồ/bối cảnh/kịch bản/hành động-theo-giây/intro-outro; bấm-chọn không gõ lệnh). Mới làm bản nhẹ (Style cards). Repo: flowboard, jaaz, react-video-editor.
- **#11(nhập vai) 💡 Đưa mặt user vào video / nhập vai** (consent, ảnh-của-chính-mình). API: Runway Act-Two / Wan-Animate (Replicate). Local test: UniAnimate/DreamO. KHÔNG dùng face-swap deepfake.
- **#7,#16 ✅/🟡 Làm nổi Seedance 2.5 + tường model AI**. ModelWall redesign ✅, menu Seedance 2.5 ✅. Còn: liệt kê chi tiết hơn model CometAPI/Runware + Grok img.
- **#9 💡 Chia sẻ video** (user tạo hay → share lên web như MXH → homepage lấy làm nội dung, tiết kiệm tiền tạo video mẫu). CHƯA làm.
- **Việc #1 lõi ✅** "dán link → video bán hàng chốt đơn": reveal SP ✅, 6 góc chốt đơn ✅, **làm hàng loạt /v1/batch ✅ (cần test-live)**.

## Nhóm B — Đánh bóng + UX (làm xen kẽ)
- **#4 🟡 Trang chủ**: gộp 3 mục na ná ("Một nền tảng/Mẫu output thật/Một studio"), thêm **thư viện video show trang chủ** (như autovis.ai/home), phần "giải pháp mang lại" (mạnh hơn autovis), tối ưu độ dài trang, **thêm trang danh mục mới** (giống autovis, biến thành nét riêng, tránh bản quyền). CHƯA làm phần lớn.
- **#5 ⏳ Menu công cụ chia rõ** (âm thanh/hình ảnh/phim ngắn... như OpenArt + affiliate/dịch vụ). CHƯA (cần chốt taxonomy).
- **#6 ✅ Ảnh hover menu con đúng mục** (hết "toàn KOL").
- **#8 ⏳ Liệt kê chi tiết tính năng + ý tưởng**. CHƯA.
- **#10 ⏳ Tile tự đổi ảnh/video** (không cố định) + hover phát đúng video đó + ảnh thì zoom to. CHƯA. Repo: masonic, react-hover-video-player.
- **#12 ✅ Sửa chữ đọc-giống-AI** (hero/s1/useCases). Còn chỗ khác rà tiếp.
- **#13 ✅ Hero "Vyra biến nó thành hiện thực"**.
- **#14 ✅ Login: logo bấm được + nút trở về**.
- **#15 ✅ Stat "10+ công cụ"** (không phải 7).
- **#21 ⏳ Tối ưu load nhiều asset mượt** (ảo hóa/lazy). Repo: masonic, intersection-observer, next-video, hls.js.
- **#22 ⏳ Tối ưu mobile** (đang tệ). Repo: embla-carousel (vuốt như TikTok).
- **#19 ⏳ PWA** (cài web thành app). Repo: serwist.

## Nhóm C — Bom tấn (làm sau khi mũi nhọn có khách)
- **#11(thể loại) 💡 Thêm thể loại**: hoạt hình, phim, hành động, ma, siêu anh hùng, trend Douyin biến hình, nhảy đu trend, thay đồ KOL, bán hàng, quảng cáo, đu trend bóng đá. Repo: Wan2.2-Animate (gộp nhiều), VToonify (anime), CatVTON/ViVID (thử đồ), MimicMotion (nhảy), ai-cinema-studio-engine (LUT genre), awesome-ai-video-prompts.
- **#18 💡 Tải video no-logo** TikTok/FB/YouTube. Repo: cobalt (self-host), yt-dlp.
- **#20 💡 Review phim tự động**: AI xem phim → kịch bản → giọng Việt cảm xúc (đọc đúng tên nước ngoài, không nuốt chữ, học phong cách từ file voice user upload). Tính phí, dùng API bên thứ 3 chất lượng. Repo: AI-Movie-Shorts + VieNeu-TTS v3 + vietnormalizer.

## Hạ tầng bắt buộc (4 rủi ro — xem VYRA_CHIENLUOC_NHOM1.md §4b)
1. Chặn-bot Shopee → ingest 3 tầng (API chính thức → Firecrawl → Scrapling+Camoufox + fallback upload ảnh/text).
2. Credit minh bạch theo loại (1 credit HTML / ~5 credit mặt-AI) + lịch sử trừ credit. Repo: lago, openmeter.
3. Hàng-đợi batch (20 link = 15-30 phút) → queue backend + báo Zalo/Telegram/Web Push. Repo: arq (FastAPI), apprise, zalo-sdk.
4. Bản quyền/kiểm duyệt mặt → ToS + ưu tiên kho KOL AI có sẵn + chỉ ảnh-của-chính-mình có consent.

## Quyết định lớn đã chốt
- Mũi nhọn = **affiliate/TikTok Shop** trước; các nhóm khác sau.
- **KHÔNG tự-host GPU cho prod** (RTX 3060 12GB chỉ test) → dùng **API CometAPI + Runware**; giọng Việt tự-host VieNeu-TTS.
- Batch nhân khuôn /v1/series (atomic credit). mp4 gitignore. Model chưa-nối để "Sắp có" (anti-slop).
