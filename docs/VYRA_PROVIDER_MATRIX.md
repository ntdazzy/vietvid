# VYRA — Ma trận năng lực Provider API (CometAPI vs Runware) — 2026-07-01

> Câu hỏi: 2 provider này có đủ API cho mọi việc Vyra cần không (không cần tự-host GPU)?
> Trả lời ngắn: **CÓ, gần như đủ 100%.** Chỉ thiếu 1 thứ: giọng Việt chuẩn (tự-host VieNeu-TTS).

## Ma trận: việc Vyra cần × provider nào làm được

| Việc Vyra cần | CometAPI | Runware | Vyra đã nối? |
|---|---|---|---|
| **Tạo video** (chữ/ảnh → clip) | ✅ Seedance 1.5-pro/2.0/2.0-fast, Kling v3, Veo 3.1, Sora 2, Wan, Hailuo, Vidu | ✅ Seedance 2.0, Kling 3.0, Veo 3.1, Wan 2.6, Hailuo, PixVerse, LTX-2 | ✅ (Seedance) |
| **Mặt nói bán hàng** (ảnh + giọng → đầu nói) | ✅ **Kling AI Avatar** (std/pro) — ❌ KHÔNG có OmniHuman | ✅ **OmniHuman 1.5** + Kling Avatar 2.0 + HeyGen | ❌ chưa |
| **Lip-sync** (khớp môi video sẵn) | ✅ Kling Lip-Sync / Advanced | ✅ sync-3 (95 ngữ), lipsync-2-pro | ❌ |
| **Nhập-vai / thay người** (đưa mặt/chuyển động vào clip) | ✅ **Runway Act-Two**, Kling multimodal edit | ✅ **P-Video-Replace**, Wan 2.7 Animate | ❌ |
| **Tạo ảnh KOL + ảnh sản phẩm** | ✅ FLUX, GPT-Image 2, Seedream 4/5, Midjourney, Nano-Banana | ✅ FLUX.2, Seedream, Nano-Banana — **RẺ NHẤT** ($0.0006-0.24/ảnh) | ⚠️ đang local/Gemini |
| **Khoá mặt nhất quán** (1 KOL nhiều ảnh) | ✅ Seedream 14-ref, Kling multi-image, Identify-Face | ✅ **PuLID, InstantID, IP-Adapter, ACE++, PhotoMaker** | ❌ |
| **Thử đồ / thay đồ KOL** | ✅ Kling Kolors Virtual Try-On | ✅ FLUX Virtual Try-On | ❌ |
| **Giọng Việt** | ⚠️ gpt-4o-mini-tts (đa ngữ, chưa chuẩn VN) | ⚠️ Fish Audio S2.1 (đa ngữ) | ✅ edge/vbee/gemini |
| **Upscale / xóa nền / mở rộng ảnh** | ✅ Bria, Runway Upscale, Kling Expansion | ✅ đầy đủ (10 upscale, 12 bg-removal, ControlNet) | ❌ |
| **Làm mượt frame (interpolation)** | ❓ không rõ | ✅ (Seedance 1.0 Pro) | ❌ |

## Khác nhau giữa 2 provider

| | CometAPI | Runware |
|---|---|---|
| Bản chất | **Reseller/proxy** (bán lại API bên khác) | **Chạy GPU riêng** (Sonic engine) |
| Kết nối | 1 key **OpenAI-compatible** (dễ nối) | API riêng (AIR model-id, vd `bytedance:seedance@2.0`) |
| Số model | ~500+ | ~400K (191 ảnh, 107 video, 32 audio) |
| Tính tiền | credits nạp trước, rẻ hơn official 20-40% | pay-per-request, free $2 dùng thử |
| Mạnh nhất | Video + avatar Kling, 1 key gọn | **Ảnh rẻ nhất** + có OmniHuman + FLUX Try-On + identity adapter |
| Thiếu | ❌ OmniHuman, ❓ interpolation | Giá video/avatar/TTS chưa niêm yết (phải gọi API mới biết) |
| Vyra đã có key? | ✅ có | ⚠️ chưa (registry để sẵn slot) |

## Kết luận cho Vyra

1. **KHÔNG cần tự-host GPU (Wan2.2) cho prod.** Mọi việc — video, mặt-nói, nhập-vai, thử-đồ, tạo-ảnh-KOL, khoá-mặt, upscale — đều gọi được qua API. 1 card của bạn chỉ để test.
2. **Chiến lược provider (giữ chain hiện tại `cometapi → runware → piapi`):**
   - **CometAPI = xương sống** (đã có key, 1 key OpenAI-compatible): video Seedance/Kling, mặt-nói Kling Avatar, nhập-vai Runway Act-Two, thử-đồ Kolors.
   - **Runware = chuyên gia ảnh + avatar cao cấp** (nối thêm khi cần): ảnh KOL rẻ nhất, **OmniHuman** (cái CometAPI thiếu), FLUX Try-On, khoá-mặt PuLID/InstantID.
3. **Khoảng trống DUY NHẤT = giọng Việt chuẩn.** Cả 2 chỉ có TTS đa ngữ (đọc tên nước ngoài/cảm xúc chưa chuẩn). → **tự-host `VieNeu-TTS` + `vietnormalizer`** (đã clone) cho giọng Việt xịn. TTS chạy nhẹ, 12GB thừa sức.
4. **Việc cần làm (chỉ là NỐI THÊM API, không cần GPU):** Vyra mới nối video-gen. Cần thêm endpoint cho: **mặt-nói** (Kling Avatar/OmniHuman), **thử-đồ** (Kolors/FLUX Try-On), **tạo-ảnh-KOL** (FLUX/Seedream), **khoá-mặt** (identity). Mỗi cái = 1 hàm gọi API.

## Giá tham khảo (per-clip/giây)
- Seedance 2.0: CometAPI **$0.063/s** · Runware **$0.16/clip**
- Veo 3.1-fast: CometAPI **$0.08/s**
- Kling AI Avatar (mặt nói): CometAPI **$0.0448/clip**
- Kling Virtual Try-on: CometAPI **$0.056/req**
- Ảnh (FLUX/Seedream): Runware **$0.0006-0.24/ảnh** (rẻ nhất)
