// Cấu hình trang showcase từng tính năng. Mỗi feature có BẢN SẮC riêng: accent + heroVariant
// + bộ section riêng → nhìn lướt là phân biệt, không còn "y chang nhau". Dữ liệu thật, không bịa số.
import type { Accent } from "@/lib/accents";

export type HeroVariant = "kol" | "transform" | "tool";
export type SectionId = "highlights" | "beforeAfter" | "results" | "useCases" | "voiceBar" | "comparison" | "proof";

export type FeaturePage = {
  key: string;
  badge?: string;
  eyebrow: string;
  title: string; // "Trước|Sau" → dòng 2 đổ gradient
  sub: string;
  ctaHref: string;
  ctaLabel: string;
  heroSample: string; // file trong /samples (không đuôi) — dùng cho teaser marquee
  gallery: string[];
  bullets: string[];
  steps: { t: string; d: string }[];
  // ── bản sắc + nội dung giàu ──
  accent: Accent;
  heroVariant: HeroVariant;
  sections: SectionId[];
  kols?: { name: string; img: string; industry: string }[];
  beforeAfter?: { before: string; beforeLabel: string; after: string; afterVideo?: string; afterLabel: string; note: string };
  io?: {
    inLabel: string;
    inKind: "text" | "thumbs" | "ratios";
    inText?: string;
    thumbs?: string[];
    ratios?: string[];
    outKind: "video" | "image" | "audio";
    outImg?: string;
    outVideo?: string;
    outLabel: string;
  };
  highlights?: { icon: string; t: string; d: string }[];
  useCases?: { tag: string; t: string; d: string }[];
  voices?: { name: string; vibe: string }[];
  comparison?: { oldWay: string[]; vyraWay: string[] };
  results?: { img: string; video?: string; ratio: "9:16" | "1:1" | "16:9"; caption: string }[];
  proof?: { stat: string; label: string }[];
};

const VOICES = [
  { name: "Mai", vibe: "Trẻ trung, năng động" },
  { name: "Linh", vibe: "Nhẹ nhàng, tâm tình" },
  { name: "Trang", vibe: "Rõ ràng, chuyên nghiệp" },
  { name: "Bống", vibe: "Láu lỉnh, dí dỏm" },
  { name: "Khoa", vibe: "Năng động, cuốn hút" },
  { name: "Hùng", vibe: "Trầm ấm, tin cậy" },
  { name: "Tú", vibe: "Trẻ trung, vui vẻ" },
];

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
    accent: "rose",
    heroVariant: "kol",
    sections: ["highlights", "beforeAfter", "results", "useCases", "proof"],
    kols: [
      { name: "Linh", img: "/kol/linh.jpg", industry: "Thời trang" },
      { name: "Hà", img: "/kol/mai.jpg", industry: "Mỹ phẩm" },
      { name: "Thu", img: "/kol/thu.jpg", industry: "Phụ kiện" },
    ],
    beforeAfter: {
      before: "/bg/studio.jpg", beforeLabel: "Chỉ có ảnh sản phẩm",
      after: "/samples/lookbook.png", afterLabel: "Lookbook editorial (minh hoạ)",
      note: "Vyra dựng trong ~60 giây, không cần buổi chụp.",
    },
    highlights: [
      { icon: "Shirt", t: "Mặc SP lên KOL AI", d: "Một tấm áo thành nhiều look trên cùng gương mặt." },
      { icon: "UserCheck", t: "Giữ gương mặt nhất quán", d: "Một KOL xuyên suốt mọi khung, không lệch." },
      { icon: "Crop", t: "Đủ tỉ lệ xuất", d: "9:16 cho Reels, 1:1 cho feed, 16:9 cho web." },
      { icon: "Images", t: "Nhiều bối cảnh", d: "Đường phố, studio, editorial — một buổi 'chụp'." },
    ],
    results: [
      { img: "/samples/lookbook.png", ratio: "9:16", caption: "Street style mùa thu" },
      { img: "/samples/fashion.png", video: "/samples/fashion.mp4", ratio: "9:16", caption: "Clip lookbook chạy" },
      { img: "/samples/beauty.png", ratio: "9:16", caption: "Phối phụ kiện" },
    ],
    useCases: [
      { tag: "Shop quần áo", t: "Lên đồ cho SP mới", d: "Không cần thuê mẫu cho mỗi mẫu áo." },
      { tag: "Phụ kiện", t: "Khoe chi tiết", d: "Túi, kính, trang sức trên người thật." },
      { tag: "Local brand", t: "Đồng bộ hình ảnh", d: "Một gương mặt đại diện xuyên suốt." },
    ],
    proof: [
      { stat: "~60s", label: "mỗi lookbook" },
      { stat: "1 ảnh", label: "đầu vào" },
      { stat: "3 tỉ lệ", label: "xuất sẵn" },
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
    accent: "violet",
    heroVariant: "kol",
    sections: ["highlights", "voiceBar", "results", "comparison", "proof"],
    kols: [
      { name: "Mai", img: "/kol/mai.jpg", industry: "Mỹ phẩm" },
      { name: "An", img: "/kol/an.jpg", industry: "Công nghệ" },
      { name: "Hoa", img: "/kol/hoa.jpg", industry: "Gia dụng" },
    ],
    voices: VOICES,
    highlights: [
      { icon: "Captions", t: "Kịch bản 6 góc chốt đơn", d: "Vấn đề→giải pháp, trước→sau, so sánh..." },
      { icon: "Mic", t: "Giọng Việt thật", d: "7 giọng cá tính, nghe thử rồi mới tạo." },
      { icon: "UserCheck", t: "Một KOL nhất quán", d: "Gương mặt giữ nguyên qua mọi review." },
      { icon: "Captions", t: "Phụ đề khớp khung", d: "Timing lấy từ kịch bản, không sai chữ." },
    ],
    results: [
      { img: "/samples/kol_review.png", ratio: "9:16", caption: "Review trên sofa" },
      { img: "/samples/beauty.png", video: "/samples/beauty.mp4", ratio: "9:16", caption: "Review mỹ phẩm" },
      { img: "/samples/tech.png", video: "/samples/tech.mp4", ratio: "9:16", caption: "Review công nghệ" },
    ],
    comparison: {
      oldWay: ["Thuê KOL + ekip quay", "Chờ 3-5 ngày mỗi clip", "Mỗi SP một buổi quay", "Chi phí cao, khó nhân bản"],
      vyraWay: ["KOL AI sẵn, không ekip", "~60 giây mỗi video", "Đổi SP, giữ nguyên gương mặt", "Nhân hàng loạt biến thể"],
    },
    proof: [
      { stat: "6 góc", label: "kịch bản chốt đơn" },
      { stat: "7 giọng", label: "Việt thật" },
      { stat: "~60s", label: "mỗi video" },
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
    accent: "amber",
    heroVariant: "transform",
    sections: ["beforeAfter", "highlights", "comparison", "results", "proof"],
    beforeAfter: {
      before: "/samples/tech.png", beforeLabel: "Ảnh sản phẩm phẳng",
      after: "/samples/tech.png", afterVideo: "/samples/tech.mp4", afterLabel: "Video chốt đơn 60s (minh hoạ)",
      note: "Có hook, có nhịp, có CTA — sẵn chạy ads.",
    },
    highlights: [
      { icon: "Zap", t: "Hook 0-2 giây", d: "Giữ chân ngay khung đầu, giảm lướt." },
      { icon: "Megaphone", t: "CTA dụ chốt đơn", d: "Kết bằng lời kêu gọi mua rõ ràng." },
      { icon: "Coins", t: "Minh bạch credit", d: "Thấy giá trước khi tạo, hoàn nếu lỗi." },
      { icon: "GitBranch", t: "Auto-series A/B", d: "Nhiều biến thể, đo click, giữ bản thắng." },
    ],
    comparison: {
      oldWay: ["Thuê dựng phim quảng cáo", "Brief đi brief lại", "1 bản, khó test", "Watermark gói rẻ"],
      vyraWay: ["Engine dựng tự động", "Sửa trực tiếp, thấy giá", "Tạo nhiều biến thể đo click", "0 watermark gói trả phí"],
    },
    results: [
      { img: "/samples/tech.png", video: "/samples/tech.mp4", ratio: "9:16", caption: "Ad công nghệ" },
      { img: "/samples/food.png", video: "/samples/food.mp4", ratio: "9:16", caption: "Ad ẩm thực" },
      { img: "/samples/fashion.png", video: "/samples/fashion.mp4", ratio: "9:16", caption: "Ad thời trang" },
    ],
    proof: [
      { stat: "~60s", label: "mỗi video" },
      { stat: "A/B", label: "đo click thật" },
      { stat: "0", label: "watermark trả phí" },
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
    accent: "sky",
    heroVariant: "tool",
    sections: ["highlights", "results", "useCases", "proof"],
    io: {
      inLabel: "Mô tả của bạn", inKind: "text",
      inText: "Ly trà sữa trân châu trên bàn gỗ, ánh sáng ấm, nền bokeh — giới thiệu món mới.",
      outKind: "video", outImg: "/samples/home.png", outVideo: "/samples/home.mp4", outLabel: "Video AI dựng",
    },
    highlights: [
      { icon: "Type", t: "Bắt đầu từ chữ", d: "Không cần ảnh — chỉ một đoạn mô tả." },
      { icon: "Wand2", t: "AI tạo khung", d: "Sinh ảnh nền theo đúng ý tưởng." },
      { icon: "Mic", t: "Giọng Việt + phụ đề", d: "Lồng tiếng tự nhiên, phụ đề tự động." },
      { icon: "Timer", t: "~60 giây", d: "Từ ý tưởng tới clip sẵn đăng." },
    ],
    results: [
      { img: "/samples/home.png", video: "/samples/home.mp4", ratio: "9:16", caption: "Giới thiệu dịch vụ" },
      { img: "/samples/food_review.png", ratio: "9:16", caption: "Nội dung kênh" },
      { img: "/samples/trend.png", ratio: "9:16", caption: "Bắt ý tưởng nhanh" },
    ],
    useCases: [
      { tag: "Kênh ẩn danh", t: "Nội dung đều tay", d: "Không cần lộ mặt, không cần quay." },
      { tag: "Dịch vụ", t: "Clip giới thiệu", d: "Spa, quán, khoá học — từ mô tả." },
      { tag: "Ý tưởng", t: "Test nhanh", d: "Dựng thử concept trong 1 phút." },
    ],
    proof: [
      { stat: "0 ảnh", label: "vẫn tạo được" },
      { stat: "~60s", label: "mỗi clip" },
      { stat: "Tự động", label: "giọng + phụ đề" },
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
    accent: "cyan",
    heroVariant: "tool",
    sections: ["highlights", "results", "useCases", "proof"],
    io: {
      inLabel: "Ảnh của bạn (2–8 tấm)", inKind: "thumbs",
      thumbs: ["/samples/food.png", "/samples/home.png", "/samples/beauty.png"],
      outKind: "video", outImg: "/samples/food.png", outVideo: "/samples/food.mp4", outLabel: "Slideshow dọc",
    },
    highlights: [
      { icon: "Layers", t: "Ghép 2–8 ảnh", d: "Thành một video dọc liền mạch." },
      { icon: "Film", t: "Chuyển cảnh mượt", d: "Hiệu ứng tự động giữa các ảnh." },
      { icon: "Timer", t: "Tuỳ chỉnh nhịp", d: "Mỗi ảnh 2–4 giây theo ý bạn." },
      { icon: "Download", t: "Xuất MP4 ngay", d: "Tải về đăng được liền." },
    ],
    results: [
      { img: "/samples/food.png", video: "/samples/food.mp4", ratio: "9:16", caption: "Album món ăn" },
      { img: "/samples/home.png", video: "/samples/home.mp4", ratio: "9:16", caption: "Bộ ảnh gia dụng" },
      { img: "/samples/beauty.png", ratio: "9:16", caption: "Trước → sau" },
    ],
    useCases: [
      { tag: "Shop", t: "Album sản phẩm", d: "Nhiều góc một SP thành 1 clip." },
      { tag: "Sự kiện", t: "Tổng hợp ảnh", d: "Ghép nhanh thành video kỷ niệm." },
      { tag: "Feed", t: "Đổi gió", d: "Biến ảnh tĩnh thành nội dung động." },
    ],
    proof: [
      { stat: "2–8", label: "ảnh mỗi video" },
      { stat: "Dọc", label: "9:16 sẵn đăng" },
      { stat: "MP4", label: "tải ngay" },
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
    accent: "emerald",
    heroVariant: "tool",
    sections: ["highlights", "results", "useCases", "proof"],
    io: {
      inLabel: "Mô tả ảnh", inKind: "ratios",
      inText: "Ly trà sữa trân châu trên bàn gỗ, ánh sáng ấm, nền bokeh.",
      ratios: ["9:16", "1:1", "16:9"],
      outKind: "image", outImg: "/samples/beauty.png", outLabel: "Ảnh AI",
    },
    highlights: [
      { icon: "Type", t: "Text → ảnh", d: "Mô tả một câu, AI dựng khung." },
      { icon: "Crop", t: "Đủ 3 tỉ lệ", d: "Dọc, vuông, ngang theo nhu cầu." },
      { icon: "Image", t: "Khung cho video", d: "Dùng ngay làm ảnh đầu cho clip." },
      { icon: "Palette", t: "Ảnh bài đăng", d: "Hoặc ảnh nghệ thuật riêng để post." },
    ],
    results: [
      { img: "/samples/beauty.png", ratio: "9:16", caption: "Khung dọc 9:16" },
      { img: "/samples/fashion.png", ratio: "1:1", caption: "Vuông 1:1 cho feed" },
      { img: "/samples/home.png", ratio: "16:9", caption: "Ngang 16:9 cho web" },
    ],
    useCases: [
      { tag: "Video", t: "Khung đầu", d: "Tạo ảnh nền rồi dựng thành clip." },
      { tag: "Feed", t: "Ảnh bài đăng", d: "Nội dung hình bắt mắt mỗi ngày." },
      { tag: "Concept", t: "Thử ý tưởng", d: "Phác hình nhanh trước khi sản xuất." },
    ],
    proof: [
      { stat: "3 tỉ lệ", label: "dọc·vuông·ngang" },
      { stat: "1 câu", label: "thành ảnh" },
      { stat: "Tải", label: "hoặc dựng tiếp" },
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
    accent: "slate",
    heroVariant: "tool",
    sections: ["voiceBar", "highlights", "useCases", "proof"],
    io: {
      inLabel: "Lời cần đọc", inKind: "text",
      inText: "Da bạn sẽ căng mướt và rạng rỡ chỉ sau bảy ngày sử dụng.",
      outKind: "audio", outLabel: "Giọng Việt",
    },
    voices: VOICES,
    highlights: [
      { icon: "Mic", t: "7 giọng Việt thật", d: "Mỗi giọng một cá tính riêng." },
      { icon: "Volume2", t: "Nghe thử ngay", d: "Chọn đúng giọng trước khi tải." },
      { icon: "AudioLines", t: "Tự nhiên", d: "Không máy móc, hợp lồng tiếng." },
      { icon: "Download", t: "Tải MP3", d: "Chất lượng cao, dùng được ngay." },
    ],
    useCases: [
      { tag: "Video", t: "Lồng tiếng", d: "Giọng đọc cho clip review/quảng cáo." },
      { tag: "Podcast", t: "Đọc bài", d: "Biến văn bản thành audio ngắn." },
      { tag: "Thông báo", t: "Voice nội bộ", d: "Đọc thông báo, hướng dẫn nhanh." },
    ],
    proof: [
      { stat: "7", label: "giọng Việt" },
      { stat: "Nghe thử", label: "trước khi tải" },
      { stat: "MP3", label: "chất lượng cao" },
    ],
  },
};

export const FEATURE_PAGE_KEYS = Object.keys(FEATURE_PAGES);
