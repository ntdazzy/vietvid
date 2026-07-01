# Vyra Studio — Chiến lược (nghiên cứu sâu 2026-07-01)

> Nguồn: workflow điều tra 20 agent (repo nội bộ + mổ xẻ đối thủ + săn GitHub + đánh giá tính năng lớn).
> Tổng: 328 lượt gọi công cụ, ~1.36M token. 19/20 agent xong (1 lỗi retry: "nhập vai + gói thể loại").

## Kết luận sống-còn (Viability)

**KHẢ THI — nhưng chỉ khi thắng "mũi nhọn người bán affiliate/TikTok-Shop" TRƯỚC, coi tham vọng "studio kiểu OpenArt" là giai đoạn 2.**

Thị trường có khe hở thật, chưa ai chiếm:
- Topview + mọi tool ngoại (OpenArt, InVideo, Kling, Pika, Higgsfield) **bắt người bán VN trả thẻ USD**, coi tiếng Việt là "ngôn ngữ #80", avatar Tây generic, bẫy credit (trừ tiền render lỗi, xu hết hạn).
- Autovis giữ ngách affiliate nội địa nhưng **bị kẹt trong "video review"**, giọng Việt yếu, mang tiếng bán tài khoản chợ đen, tùy biến kém.

**2 thứ Vyra có mà ĐỐI THỦ KHÓ COPY:**
1. Thanh toán MoMo + bank-QR thật (poller nhận tiền thật).
2. Ví HOLD-rồi-mới-trừ: **render lỗi KHÔNG bao giờ trừ tiền** + xu mua không hết hạn.

**Nguy cơ lớn nhất = chính cú pivot.** Đuổi theo "mọi model, mọi loại video" như OpenArt = lao vào đánh nhau tay đôi với global player ở nơi biên lợi nhuận ≈ 0 (Seedance từng bán đúng giá vốn), nơi Vyra không có lợi thế phân phối. **Thắng chiến hào người bán trước, lấy dòng tiền đó nuôi bề rộng studio — đừng dẫn đầu bằng studio.**

## 8 cách để THẮNG (howToWin)

1. **Dẫn đầu bằng mũi nhọn affiliate, không phải studio.** Hero trang chủ = 1 ô "dán link Shopee/TikTok Shop → video chốt đơn" (đúng cửa thắng của Topview), nhưng output THẬT hơn: mặt Việt/Á "trắng hồng" + giọng persona, vs avatar UGC generic bị TikTok bóp reach. Headline: "video thật, không lộ hàng AI". Studio là scroll thứ 2.
2. **Vũ khí hóa moat thanh toán + công bằng trong CÂU CHỮ, không chỉ trong code.** Trang giá ghi rõ tiếng Việt: "Nạp MoMo/chuyển khoản · Render lỗi KHÔNG trừ tiền · Xu mua không hết hạn". Đã làm cả 3 trong code — đối thủ về cấu trúc không match rẻ được.
3. **Dưới giá Autovis ở tầng vào, trên chất ở tầng cao.** Khởi đầu 179k đã dưới 199k của họ + nhiều credit hơn. Neo vào ROI: máy tính "số SP/tháng → chi phí video vs thuê KOC + hoa hồng". Người bán mua kết quả, không mua phép tính credit.
4. **Khóa độ-trung-thực-sản-phẩm trước mọi thứ hào nhoáng.** image-to-image để "sản phẩm không bị méo" (học ClipForge) — nếu SP thật bị méo, video vô dụng, khách bỏ. Ưu tiên hơn thêm tên model.
5. **Biến vv_characters + /suite/character thành "dàn KOL ảo cố định".** Dựng 1 spokesperson Việt, tái dùng free cả chiến dịch. OpenArt vừa làm khách giận vì tính tiền lại khi tái dùng nhân vật — Vyra để FREE + trung thực gương mặt, và nói to điều đó.
6. **Đóng vòng lặp đối thủ bỏ ngỏ, KHÔNG ôm rủi ro auto-post.** Họ dừng ở "tạo video". Vyra ship "bộ đăng liền" (9:16 + caption + hook 3 giây + hashtag + đúng tỉ lệ từng nền) + "Nhân bản chiến dịch" (1 SP → biến thể nam/nữ/hook 1 click A/B). Cảm giác nhanh-lên-sóng như Autovis, không dính ToS/ban.
7. **Cho người bán "công thức" sẵn để không đối mặt prompt trống:** "Review SP TikTok Shop", "Quảng cáo shop online", "Unbox mỹ phẩm", "Video bất động sản". Ẩn hoàn toàn chuỗi provider — "Vyra tự chọn engine tốt nhất", picker nâng cao chỉ cho pro.
8. **Free trial phải ra được 1 video chia sẻ được, ít watermark, qua render thật.** Autovis/Topview đều watermark-shame + ma sát xác minh. Trial cho 1 kết quả thật = xây lại niềm tin họ đã bào mòn.

## Lộ trình xây (4 giai đoạn)

### Giai đoạn 1 — Chiếm chiến hào người bán (nền tảng dòng tiền)
- Ship "dán link → video" làm luồng chính trang chủ: URL → cào ảnh+giá+tiêu đề → pipeline studio. API-first (pattern Shopee JSON của paulodarosa/warifp), patchright làm fallback chống bot, upload ảnh/text là lối thoát thủ công. **(rủi ro hạ tầng #1)**
- Khóa độ-trung-thực-SP (image-to-image không méo) — học ClipForge; đây là thứ diệt-churn.
- Nối template kịch bản hook-3-giây + AIDA (5 nhóm × 4 phong cách từ ClipForge/vibevid) qua instructor/BAML để script.json không bao giờ làm hỏng renderer.
- Làm lại trang giá: MoMo/bank-QR + "render lỗi không trừ tiền" + "xu không hết hạn" + máy tính ROI. **Bật công tắc reseller CometAPI/Runware (sau khi verify thẻ VN thanh toán được) — đây là đòn bẩy biên 0%→~65%.**
- Hoàn tất test-live /v1/batch (dán 20 link → job_id → báo xong qua Zalo/Telegram/Web-Push bằng arq + apprise). **(rủi ro hạ tầng #3)**

*Vì sao đầu tiên: đây là nơi DUY NHẤT Vyra có lợi thế bất công (thanh toán + công bằng + mặt bản địa) chống đối thủ đánh bại được. Dòng tiền người bán nuôi studio. Fix margin = lãi thuần, người dùng không thấy đổi gì.*

### Giai đoạn 2 — Giữ chân (biến 1-video-tool thành thói quen tháng)
- Nâng vv_characters thành "dàn KOL ảo cố định" hạng nhất: dựng 1 lần (InstantID/PuLID cho ảnh tĩnh, EchoMimic/Sonic/LivePortrait cho talking-head), tái dùng FREE. Trung thực gương mặt, không pay-to-reuse.
- VieNeu-TTS + vietnormalizer làm lớp giọng (tự host — thứ DUY NHẤT nên tự xây, không mua): sửa "đọc sai số/tên nước ngoài" + "nghe như AI" — điểm yếu uy tín của Autovis/OpenArt.
- "Nhân bản chiến dịch": 1 SP → biến thể nam/nữ/hook 1 click, A/B đa nền.
- Xuất "bộ đăng liền" (tỉ lệ + caption + hashtag + hook).
- Dashboard theo dõi view/đơn trong studio — đối thủ chỉ chứng minh bằng case-study tự khai; dashboard thật = wedge giữ chân + niềm tin.

### Giai đoạn 3 — Mở bề rộng "mọi loại video" (chỉ khi GĐ1 nuôi được)
- Mega-menu theo ý định (STORY/VIDEO/IMAGE/CHARACTER/AUDIO đóng khung theo việc VN: Video bán hàng / KOL ảo / Lồng tiếng / Chỉnh sửa) — copy taxonomy OpenArt, KHÔNG copy "soup model".
- Tổng quát RoutedVideoProvider thành model-registry chung (video+ảnh+nhân vật) với selector chi phí/chất/độ trễ — vô hình với user.
- Thêm công thức ngoài affiliate: kể chuyện dân gian, explainer, phim ngắn AI nguyên gốc, trend/dance (Wan2.2-Animate qua Replicate — **CHỈ chèn danh tính ảnh có đồng ý, KHÔNG face-swap; cấm roop/Deep-Live-Cam**).
- Cache ngữ nghĩa + tri giác (GPTCache cho kịch bản/copy, videohash/imagededup để "không render lại video gần trùng") — phòng thủ biên lợi nhuận khi volume tăng.
- Thư viện video trang chủ / feed user đăng (tái dùng video user tốt làm nội dung trang chủ).

### Giai đoạn 4 — Đánh bóng & hiệu năng (chạy song song GĐ2-3, không đi trước lõi)
- Làm lại trang chủ: gộp 3 section giống nhau, thêm "solutions delivered" + thư viện video, trang category kiểu autovis (art nguyên gốc tránh vi phạm).
- Tile auto-xoay + hover-phát-đúng-video + zoom (react-hover-video-player), lazy-load asset (masonic + hls.js), tối ưu mobile (embla-carousel vuốt kiểu TikTok), cài PWA (serwist).
- Tách menu công cụ theo taxonomy (âm thanh/ảnh/phim ngắn + affiliate/dịch vụ).
- Tải không logo (cobalt self-host / yt-dlp) + review phim tự động (keithhb33/AI-Movie-Shorts + VieNeu-TTS) làm thể loại trả phí sau.

## Quick wins (làm nhanh, giá trị cao)
1. Copy niềm tin trang giá: "Nạp MoMo · Render lỗi KHÔNG trừ tiền · Xu không hết hạn" — đã làm cả 3 trong code, chỉ là câu chữ, chạm đúng vết đau mọi đối thủ. **~1 giờ.**
2. Widget máy tính ROI trên trang giá.
3. Hero → 1 ô "dán link SP → video" làm CTA đỉnh (cửa thắng Topview), studio là section 2. Chỉ đổi IA, không cần engine mới.
4. Thẻ công thức đặt-tên-theo-kết-quả trên màn create (pre-fill scene+duration+voice) — diệt vấn đề prompt trống.
5. Hiện "chi phí trước khi tạo" trên nút render — đối thủ giấu rồi charge bất ngờ; Vyra có sẵn số HOLD, chỉ cần hiện. Tín hiệu niềm tin lớn, đổi nhỏ.
6. Free-trial đảm bảo 1 video chia sẻ được từ render thật (FREE_GRANT đã chỉnh sẵn).
7. **Bật công tắc reseller/CometAPI (sau khi verify thẻ VN): lật margin 0%→~65%, người dùng không thấy đổi gì. Hành động đơn lẻ giá trị cao nhất nếu cổng tài khoản/thanh toán thông tuần này.**
8. Tile hover-phát-đúng-video + zoom (react-hover-video-player) — cảm giác đánh bóng cao, 1 component.

## 5 con hào (moats)
1. **Đường ray thanh toán bản địa đã sống:** MoMo + bank-QR thật nhận tiền thật. Mọi tool ngoại bắt thẻ USD. Hào sâu nhất, khó copy nhất — incumbent sẽ không ưu tiên thị trường VN để lấp.
2. **Kiến trúc công bằng mang tính CẤU TRÚC, không phải marketing:** HOLD-rồi-trừ (không bao giờ tính render lỗi) + 2-ví (credit mua không hết hạn). Cả thị trường bị ghét vì "bẫy credit". Không fake bằng copy được — Vyra xây thật nên hứa thật được.
3. **Chất mặt + giọng Việt-first:** t2v mặt Việt/Á "trắng hồng" thật, qua moderation (đúng use-case OpenArt chặn gắt, Autovis làm "uncanny") + VieNeu-TTS + vietnormalizer tự host cho số/tên-nước-ngoài/giọng đúng. Win side-by-side demo được.
4. **Dàn KOL/nhân vật Việt tái-dùng-FREE** (vv_characters + /suite/character đã xây) — primitive "dựng 1 lần, dùng cả chiến dịch" mà InVideo/Higgsfield tính tiền và OpenArt vừa làm khách giận vì tính-tiền-2-lần.
5. **Tính chính danh trong thị trường xám:** giá VND minh bạch, thanh toán thật, không chợ đen tài khoản (Autovis có vụ "cảnh báo mua tài khoản"). Với người bán VN bị billing ngoại + tài khoản xám làm bỏng tay, là lựa chọn hợp pháp-bản địa-minh bạch = lợi thế niềm tin cộng dồn theo mỗi scandal đối thủ.

## Đánh giá tính năng lớn (feasibility)
| Tính năng | Kết luận | Ghi chú |
|---|---|---|
| Review phim tự động | **Một phần** | Engine recap/script/TTS ~70% đã có trong Vyra; khó = pháp lý bản quyền phim nguồn + độ tin cậy đọc tên. |
| Dashboard phân tích đơn | **Một phần** | Lõi "xếp SP thắng + gen script + hook" ~80% tái dùng; nghẽn = nhập đơn (không có API đơn công khai → nhập thủ công/upload). |
| Deep studio customizer | **Một phần** | Mọi sub-capability xây được, model hỗ trợ đủ; nghẽn thật = phạm vi UX + compiler prompt deterministic bền, không phải năng lực model. |
| Chia sẻ video cộng đồng | **Một phần** | Plumbing publish/serve/schema ~70% đã xây; thiếu moderation tự động; "tái dùng để tiết kiệm cost gen" phần lớn là *ảo tưởng kinh tế* (cost đã tiêu rồi). |
| Tile trang chủ động | **CÓ** | 3/4 hành vi đã ship; chỉ auto-xoay từng tile là mới, đổi nhỏ phía client, 0 cost inference. |
| Nhập vai + gói thể loại | *(agent lỗi)* | Cần chạy lại; hướng: Wan2.2-Animate chèn danh tính có đồng ý, cấm face-swap. |

## Repo GitHub đáng học (săn được)
- **Cào SP:** paulodarosa/shopee-scraper (gọi JSON API Shopee công khai), warifp.
- **Tải không logo:** imputnet/cobalt (~41k sao, chuẩn tham chiếu), yt-dlp.
- **Giọng Việt:** pnnbao97/VieNeu-TTS (~2k sao, clone giọng 3-5s, chạy CPU real-time), vietnormalizer.
- **Recap phim:** keithhb33/AI-Movie-Shorts (~58 sao, phim → recap dọc/ngang).
- **Face/nhân vật:** instantX-research/InstantID (~12k), PuLID, LivePortrait, EchoMimic, Sonic.
- **Prompt:** jnMetaCode/ai-shortfilm-prompts (~224 sao, có Claude Skill sau phim ngắn nổi tiếng).
- **Cache/dedup:** zilliztech/GPTCache (~8.1k), videohash, imagededup.
- **E-com short-video:** xixihhhh/clipforge (~186 sao, pipeline UGC bán hàng — nguồn học độ-trung-thực-SP + template hook).

## Repo nội bộ (làm rõ 3 câu hỏi user)
- **AI-auto-generate-video** = `D:/vyra-research/repos/09-video-gen-pipelines/AI-auto-generate-video` (huytranvan2010, MIT, TS, `aicoding-template-video` v2.0.0): bài/URL Việt vào → short 9:16 ra, 1 lệnh, 0 chỉnh tay. Insight lõi = đòn bẩy chi phí (item #1 roadmap).
- **D:/vyra-research/repos** = kho ~13 nhóm repo tham khảo đã tải để học/tái dùng (video-gen-pipelines, scraping, TTS, face...).
