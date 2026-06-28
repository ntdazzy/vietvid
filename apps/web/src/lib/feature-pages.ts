// Cấu hình trang showcase từng tính năng (giống autovis: mỗi tính năng 1 trang chi tiết).
// Dùng asset mẫu thật trong /samples. ctaHref = nơi "Tạo ngay" dẫn tới (wizard preset / tool page).

export type FeaturePage = {
  key: string;
  badge?: string;
  eyebrow: string;
  title: string; // có thể chứa "|" để tách dòng gradient: "Trước|Sau"
  sub: string;
  ctaHref: string;
  ctaLabel: string;
  heroSample: string; // file trong /samples (không đuôi)
  gallery: string[]; // các sample 9:16
  bullets: string[];
  steps: { t: string; d: string }[];
};

export const FEATURE_PAGES: Record<string, FeaturePage> = {
  lookbook: {
    key: "lookbook",
    badge: "Thời trang",
    eyebrow: "KOL AI · Lookbook",
    title: "Lookbook thời trang|từ một tấm ảnh.",
    sub: "Mặc sản phẩm lên KOL AI, phối nhiều outfit và bối cảnh editorial, giữ gương mặt nhất quán qua mọi khung — không cần người mẫu, không cần buổi chụp.",
    ctaHref: "/app/create?feature=lookbook",
    ctaLabel: "Tạo lookbook",
    heroSample: "fashion",
    gallery: ["fashion", "beauty", "home", "tech"],
    bullets: [
      "Phối nhiều outfit + bối cảnh từ một sản phẩm",
      "Giữ gương mặt & phong cách KOL nhất quán",
      "Xuất dọc 9:16 cho TikTok/Reels, vuông 1:1 cho feed",
    ],
    steps: [
      { t: "Tải ảnh sản phẩm", d: "Một tấm áo/váy/phụ kiện là đủ." },
      { t: "Chọn KOL & phong cách", d: "Gương mặt AI + tông editorial." },
      { t: "Nhận lookbook 60 giây", d: "Nhiều look, một outfit nhất quán." },
    ],
  },
  review: {
    key: "review",
    badge: "Viral",
    eyebrow: "KOL AI · Review",
    title: "Video review sản phẩm|nói tiếng Việt thật.",
    sub: "KOL AI cầm sản phẩm, review theo kịch bản chốt đơn với giọng Việt tự nhiên và phụ đề khớp khung — như clip tự quay, không lộ AI.",
    ctaHref: "/app/create?feature=review",
    ctaLabel: "Tạo video review",
    heroSample: "beauty",
    gallery: ["beauty", "tech", "food", "home"],
    bullets: [
      "Kịch bản review theo 6 góc chốt đơn",
      "7 giọng Việt thật, nghe thử trước khi tạo",
      "Phụ đề lấy timing từ kịch bản, 0 lỗi nhận dạng",
    ],
    steps: [
      { t: "Tải ảnh + thông tin SP", d: "Hoặc dán link Shopee/TikTok-Shop." },
      { t: "Chọn góc & giọng", d: "Engine viết hook + beat timecode." },
      { t: "Nhận video review", d: "Sửa từng câu rồi dựng 60 giây." },
    ],
  },
  product_ad: {
    key: "product_ad",
    badge: "Mới",
    eyebrow: "Quảng cáo · Bán hàng",
    title: "Một ảnh sản phẩm.|Một video chốt đơn.",
    sub: "Biến ảnh sản phẩm thành video quảng cáo 60 giây có nhịp, có hook, có CTA — giọng Việt thật, sẵn sàng đăng và chạy ads.",
    ctaHref: "/app/create?feature=product_ad",
    ctaLabel: "Tạo video quảng cáo",
    heroSample: "tech",
    gallery: ["tech", "fashion", "food", "beauty"],
    bullets: [
      "Hook 0-2s giữ chân, CTA dụ chốt đơn",
      "Minh bạch credit: thấy giá trước khi tạo",
      "Tạo nhiều biến thể, đo click, giữ bản thắng",
    ],
    steps: [
      { t: "Tải/dán link sản phẩm", d: "Tự bóc tên, giá, ảnh." },
      { t: "Chọn phong cách & giọng", d: "Thấy ước tính credit ngay." },
      { t: "Nhận video bán hàng", d: "Đủ tỉ lệ, không watermark gói trả phí." },
    ],
  },
  text_to_video: {
    key: "text_to_video",
    eyebrow: "Công cụ · Text → Video",
    title: "Gõ ý tưởng.|AI dựng khung và video.",
    sub: "Từ một đoạn mô tả, Vyra sinh khung hình bằng AI rồi dựng thành video có giọng Việt — không cần ảnh sẵn.",
    ctaHref: "/app/create?feature=text_to_video",
    ctaLabel: "Thử text → video",
    heroSample: "home",
    gallery: ["home", "food", "tech", "fashion"],
    bullets: [
      "Không cần ảnh đầu vào — AI tạo khung",
      "Lồng giọng Việt + phụ đề tự động",
      "Hợp giới thiệu dịch vụ, ý tưởng, nội dung kênh",
    ],
    steps: [
      { t: "Mô tả nội dung", d: "Vài câu ý tưởng là đủ." },
      { t: "AI tạo khung", d: "Sinh ảnh nền theo mô tả." },
      { t: "Dựng video", d: "Ghép giọng + phụ đề + nhịp." },
    ],
  },
  composite: {
    key: "composite",
    eyebrow: "Công cụ · Ghép video",
    title: "Nhiều ảnh.|Một video mượt.",
    sub: "Chọn nhiều ảnh, Vyra ghép thành video slideshow dọc có chuyển cảnh — nhanh, gọn, sẵn đăng.",
    ctaHref: "/app/compose",
    ctaLabel: "Ghép video ngay",
    heroSample: "food",
    gallery: ["food", "home", "beauty", "fashion"],
    bullets: [
      "Ghép nhiều ảnh thành 1 video dọc",
      "Chuyển cảnh mượt, thời lượng tuỳ chỉnh",
      "Xuất MP4 đăng được ngay",
    ],
    steps: [
      { t: "Chọn ảnh", d: "Tải lên các ảnh muốn ghép." },
      { t: "Đặt thời lượng", d: "Mỗi ảnh hiện bao lâu." },
      { t: "Tải video", d: "Nhận MP4 slideshow dọc." },
    ],
  },
  ai_image: {
    key: "ai_image",
    eyebrow: "Ảnh & Âm thanh · Tạo ảnh AI",
    title: "Mô tả một câu.|AI vẽ ảnh nghệ thuật.",
    sub: "Tạo ảnh khung cho video hoặc ảnh bài đăng từ mô tả văn bản — đủ tỉ lệ dọc, vuông, ngang.",
    ctaHref: "/app/image-gen",
    ctaLabel: "Tạo ảnh AI",
    heroSample: "beauty",
    gallery: ["beauty", "fashion", "home", "tech"],
    bullets: [
      "Text → ảnh, đủ 3 tỉ lệ",
      "Dùng làm khung đầu cho video",
      "Hoặc ảnh bài đăng riêng",
    ],
    steps: [
      { t: "Mô tả ảnh", d: "Vd: ly trà sữa trên bàn gỗ, ánh ấm." },
      { t: "Chọn tỉ lệ", d: "Dọc 9:16 · vuông 1:1 · ngang 16:9." },
      { t: "Nhận ảnh", d: "Tải về hoặc dựng tiếp thành video." },
    ],
  },
  ai_audio: {
    key: "ai_audio",
    eyebrow: "Ảnh & Âm thanh · Giọng Việt",
    title: "Văn bản thành|giọng Việt thật.",
    sub: "Nhập đoạn lời, chọn 1 trong 7 giọng Việt có cá tính, nghe thử và tải về — tự nhiên, không máy móc.",
    ctaHref: "/app/audio",
    ctaLabel: "Tạo âm thanh",
    heroSample: "tech",
    gallery: ["tech", "food", "beauty", "home"],
    bullets: [
      "7 giọng Việt: trẻ trung, nhẹ nhàng, trầm ấm, dí dỏm",
      "Nghe thử ngay trước khi tải",
      "Dùng lồng tiếng video hoặc podcast ngắn",
    ],
    steps: [
      { t: "Nhập lời", d: "Đoạn văn bản muốn đọc." },
      { t: "Chọn giọng", d: "7 giọng Việt thật, nghe thử." },
      { t: "Tải audio", d: "Nhận MP3 chất lượng cao." },
    ],
  },
};

export const FEATURE_PAGE_KEYS = Object.keys(FEATURE_PAGES);
