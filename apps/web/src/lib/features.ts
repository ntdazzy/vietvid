import {
  Shirt,
  Film,
  Megaphone,
  Flame,
  Music2,
  BookOpen,
  Type,
  Image as ImageIcon,
  Video,
  Layers,
  Clapperboard,
  Sparkles,
  Palette,
  AudioLines,
  Mic2,
  Wand2,
  Boxes,
  Drama,
  ScanFace,
  Library,
  LayoutTemplate,
  BarChart3,
  Link2,
  Webhook,
  HelpCircle,
  Download,
  type LucideIcon,
} from "lucide-react";

export type FeatureBadge = "Mới" | "Viral" | "Nâng cao" | "Sắp có";

export interface Feature {
  key: string;
  label: string;
  desc: string;
  icon: LucideIcon;
  badge?: FeatureBadge;
  available: boolean; // true = nối engine thật; false = cần tích hợp ngoài (Sắp có)
  href: string; // /app/create?feature=<key> nếu available
}

export interface FeatureGroup {
  title: string;
  items: Feature[];
}

// Menu "Công cụ AI" — gom theo LOẠI OUTPUT (kiểu OpenArt): Video / Ảnh / Âm thanh / Nhân vật.
// Dễ tìm theo thứ mình muốn tạo, thay vì gom theo use-case như cũ.
export const CONTENT_GROUPS: FeatureGroup[] = [
  {
    title: "Video",
    items: [
      { key: "product_ad", label: "Quảng cáo sản phẩm", desc: "1 ảnh → video chốt đơn", icon: Megaphone, badge: "Mới", available: true, href: "/features/product_ad" },
      { key: "review", label: "Video review", desc: "KOL review SP theo kịch bản", icon: Film, badge: "Viral", available: true, href: "/features/review" },
      { key: "lookbook", label: "Lookbook thời trang", desc: "KOL mặc SP, bối cảnh editorial", icon: Shirt, available: true, href: "/features/lookbook" },
      { key: "text_to_video", label: "Văn bản → Video", desc: "Ý tưởng → khung AI dựng clip", icon: Type, available: true, href: "/features/text_to_video" },
      { key: "image_to_video", label: "Ảnh → Video", desc: "Biến ảnh tĩnh thành clip động", icon: ImageIcon, available: true, href: "/features/product_ad" },
      { key: "composite", label: "Ghép video & ảnh", desc: "Nhiều ảnh thành 1 video", icon: Layers, available: true, href: "/features/composite" },
      { key: "video_remix", label: "Video từ video mẫu", desc: "Remix theo clip có sẵn", icon: Video, badge: "Sắp có", available: false, href: "#" },
      { key: "story", label: "Phim ngắn / kể chuyện", desc: "Storyboard theo timecode", icon: BookOpen, badge: "Sắp có", available: false, href: "#" },
    ],
  },
  {
    title: "Ảnh",
    items: [
      { key: "ai_image", label: "Tạo ảnh AI", desc: "Mô tả một câu, AI vẽ ảnh", icon: Palette, available: true, href: "/features/ai_image" },
      { key: "trends_image", label: "Ảnh bắt trend", desc: "Bắt trend thịnh hành, ảnh viral", icon: Sparkles, badge: "Sắp có", available: false, href: "#" },
    ],
  },
  {
    title: "Âm thanh",
    items: [
      { key: "ai_audio", label: "Giọng đọc AI", desc: "Văn bản → giọng Việt tự nhiên", icon: AudioLines, available: true, href: "/features/ai_audio" },
      { key: "voice_clone", label: "Nhân bản giọng nói", desc: "Voice clone (VieNeu)", icon: Mic2, badge: "Sắp có", available: false, href: "#" },
    ],
  },
  {
    title: "Nhân vật & KOL",
    items: [
      { key: "kol_ai", label: "KOL AI", desc: "Gương mặt ảo review nhất quán", icon: Flame, available: true, href: "/app/kol" },
      { key: "character_ai", label: "Nhân vật AI", desc: "Diễn viên nhất quán, tái dùng", icon: Drama, available: true, href: "/app/character" },
      { key: "motion_copy", label: "Sao chép chuyển động", desc: "KOL nhảy theo trend dance", icon: Music2, badge: "Sắp có", available: false, href: "#" },
      { key: "keep_face", label: "Giữ gương mặt", desc: "Khoá danh tính khi sinh lại", icon: ScanFace, badge: "Sắp có", available: false, href: "#" },
    ],
  },
];

// Model AI — định vị aggregator: Vyra route tới NHIỀU model tốt nhất cho từng việc.
// available=true CHỈ khi đã nối engine thật (Seedance video, Gemini ảnh, giọng Việt, nhân vật);
// còn lại "Sắp có" — KHÔNG hứa cái chưa cắm (anti-slop).
export const MODELS_GROUPS: FeatureGroup[] = [
  {
    title: "Model Video",
    items: [
      { key: "m_seedance", label: "Seedance 2.0", desc: "Video điện ảnh AI, đang chạy thật", icon: Sparkles, badge: "Nâng cao", available: true, href: "/app/create" },
      { key: "m_seedance25", label: "Seedance 2.5", desc: "Thế hệ mới, người thật hơn", icon: Sparkles, badge: "Sắp có", available: false, href: "#" },
      { key: "m_kling", label: "Kling 3.0", desc: "Chuyển động mượt, dài hơi", icon: Video, badge: "Sắp có", available: false, href: "#" },
      { key: "m_veo", label: "Veo 3.1", desc: "Chất điện ảnh cao cấp", icon: Film, badge: "Sắp có", available: false, href: "#" },
      { key: "m_wan", label: "Wan 2.6", desc: "Bám prompt sát, ổn định", icon: Clapperboard, badge: "Sắp có", available: false, href: "#" },
      { key: "m_hailuo", label: "Hailuo · MiniMax", desc: "Nhanh, hợp clip ngắn", icon: Video, badge: "Sắp có", available: false, href: "#" },
    ],
  },
  {
    title: "Model Ảnh",
    items: [
      { key: "m_gemini", label: "Gemini · Imagen", desc: "Ảnh sắc nét, đang chạy thật", icon: ImageIcon, available: true, href: "/app/image-gen" },
      { key: "m_grok", label: "Grok Img 1.5", desc: "Ảnh người siêu thực, bắt sáng", icon: Wand2, badge: "Sắp có", available: false, href: "#" },
      { key: "m_flux", label: "FLUX.2", desc: "Ảnh thực, chữ trong ảnh chuẩn", icon: Boxes, badge: "Sắp có", available: false, href: "#" },
      { key: "m_seedream", label: "Seedream 5", desc: "Ảnh sản phẩm nét, đủ sáng", icon: Sparkles, badge: "Sắp có", available: false, href: "#" },
      { key: "m_nanobanana", label: "Nano-Banana", desc: "Sửa ảnh bằng câu lệnh", icon: Palette, badge: "Sắp có", available: false, href: "#" },
      { key: "m_ideogram", label: "Ideogram", desc: "Chữ & poster trong ảnh", icon: Type, badge: "Sắp có", available: false, href: "#" },
    ],
  },
  {
    title: "Mặt nói & khoá mặt",
    items: [
      { key: "m_omnihuman", label: "OmniHuman 1.5", desc: "Ảnh + giọng → mặt nói bán hàng", icon: Drama, badge: "Sắp có", available: false, href: "#" },
      { key: "m_klingavatar", label: "Kling Avatar 2.0", desc: "Avatar nói chuyện tự nhiên", icon: Drama, badge: "Sắp có", available: false, href: "#" },
      { key: "m_instantid", label: "InstantID", desc: "Khoá gương mặt khi sinh lại", icon: ScanFace, badge: "Sắp có", available: false, href: "#" },
      { key: "m_pulid", label: "PuLID", desc: "Giữ danh tính, đổi bối cảnh", icon: ScanFace, badge: "Sắp có", available: false, href: "#" },
      { key: "m_dreamo", label: "DreamO", desc: "1 gương mặt nhất quán mọi cảnh", icon: ScanFace, badge: "Sắp có", available: false, href: "#" },
    ],
  },
  {
    title: "Giọng & Nhân vật",
    items: [
      { key: "m_voice", label: "Giọng Việt thật", desc: "7 giọng cá tính, đang chạy thật", icon: AudioLines, available: true, href: "/app/audio" },
      { key: "m_character", label: "Nhân vật AI", desc: "Diễn viên nhất quán, tái dùng", icon: Drama, available: true, href: "/app/character" },
      { key: "m_vieneu", label: "VieNeu-TTS", desc: "Giọng Việt neural, cảm xúc", icon: Mic2, badge: "Sắp có", available: false, href: "#" },
      { key: "m_fishaudio", label: "Fish Audio", desc: "Nhân bản giọng, đa ngôn ngữ", icon: AudioLines, badge: "Sắp có", available: false, href: "#" },
    ],
  },
];

// Tính năng (use-case / feature page) — mega-panel "Tính năng". 2 nhóm → cols=2.
export const FEATURES_GROUPS: FeatureGroup[] = [
  {
    title: "Bán hàng & KOL",
    items: [
      { key: "f_ad", label: "Quảng cáo sản phẩm", desc: "1 ảnh → video chốt đơn", icon: Megaphone, available: true, href: "/features/product_ad" },
      { key: "f_review", label: "Video review", desc: "KOL review theo kịch bản", icon: Film, available: true, href: "/features/review" },
      { key: "f_lookbook", label: "Lookbook thời trang", desc: "Trình diễn SP bối cảnh editorial", icon: Shirt, available: true, href: "/features/lookbook" },
      { key: "f_kol", label: "KOL AI", desc: "Gương mặt ảo review nhất quán", icon: Flame, available: true, href: "/app/kol" },
      { key: "f_tryon", label: "Thử đồ KOL", desc: "Mặc thử sản phẩm lên người mẫu AI", icon: Shirt, badge: "Sắp có", available: false, href: "#" },
      { key: "f_faceswap", label: "Nhập vai (đưa mặt vào video)", desc: "Đưa gương mặt bạn vào clip AI", icon: ScanFace, badge: "Sắp có", available: false, href: "#" },
    ],
  },
  {
    title: "Sáng tạo & thể loại",
    items: [
      { key: "f_t2v", label: "Văn bản → Video", desc: "Ý tưởng → khung AI dựng clip", icon: Type, available: true, href: "/features/text_to_video" },
      { key: "f_image", label: "Tạo ảnh AI", desc: "Mô tả một câu, AI vẽ ảnh", icon: Palette, available: true, href: "/features/ai_image" },
      { key: "f_composite", label: "Ghép video & ảnh", desc: "Nhiều ảnh thành 1 video", icon: Layers, available: true, href: "/features/composite" },
      { key: "f_story", label: "Phim ngắn / kể chuyện", desc: "Storyboard theo timecode", icon: BookOpen, badge: "Sắp có", available: false, href: "#" },
      { key: "f_anime", label: "Hoạt hình / anime", desc: "Dựng clip phong cách hoạt hình", icon: Sparkles, badge: "Sắp có", available: false, href: "#" },
      { key: "f_trend", label: "Đu trend / biến hình", desc: "Douyin transform, nhảy trend", icon: Music2, badge: "Sắp có", available: false, href: "#" },
    ],
  },
  {
    title: "Phân tích & Kênh",
    items: [
      { key: "f_order", label: "Phân tích đơn Shopee/TikTok", desc: "Tìm SP thắng + gợi ý kịch bản", icon: Boxes, badge: "Mới", available: true, href: "/app/order-analysis" },
      { key: "f_moviereview", label: "Review phim tự động", desc: "Kịch bản + giọng đọc AI bám phim", icon: Film, badge: "Mới", available: true, href: "/app/movie-review" },
      { key: "f_download", label: "Tải video không logo", desc: "TikTok / Facebook / YouTube", icon: Download, badge: "Sắp có", available: false, href: "#" },
      { key: "f_affiliate", label: "Affiliate", desc: "Gắn link, đo hoa hồng", icon: Link2, available: true, href: "/app/affiliate" },
      { key: "f_reports", label: "Báo cáo hiệu quả", desc: "Đo click, view, bản thắng", icon: BarChart3, available: true, href: "/app/reports" },
    ],
  },
];

// Tài nguyên — mega-panel "Tài nguyên". 2 nhóm → cols=2.
export const RESOURCES_GROUPS: FeatureGroup[] = [
  {
    title: "Không gian làm việc",
    items: [
      { key: "r_library", label: "Thư viện video", desc: "Xem, tải, chia sẻ", icon: Library, available: true, href: "/app/library" },
      { key: "r_templates", label: "Mẫu dựng sẵn", desc: "Khoá thể loại + brief", icon: LayoutTemplate, available: true, href: "/app/templates" },
      { key: "r_brand", label: "Bộ nhận diện", desc: "Logo, màu, watermark", icon: Palette, available: true, href: "/app/brand-kits" },
      { key: "r_reports", label: "Báo cáo", desc: "Đo click, bản thắng", icon: BarChart3, available: true, href: "/app/reports" },
    ],
  },
  {
    title: "Mở rộng & hỗ trợ",
    items: [
      { key: "r_affiliate", label: "Affiliate", desc: "Gắn link, hoa hồng", icon: Link2, available: true, href: "/app/affiliate" },
      { key: "r_api", label: "API & Webhook", desc: "Tích hợp B2B", icon: Webhook, available: true, href: "/app/api" },
      { key: "r_faq", label: "Câu hỏi thường gặp", desc: "Giải đáp nhanh", icon: HelpCircle, available: true, href: "/#faq" },
    ],
  },
];

// Preset cho wizard khi mở /app/create?feature=<key>: đặt loại video + gợi ý brief + cách lấy khung.
export const FEATURE_PRESETS: Record<
  string,
  { videoType: "product_ad" | "kol_full"; brief: string; frameMode?: "upload" | "ai" }
> = {
  product_ad: { videoType: "product_ad", brief: "" },
  image_to_video: { videoType: "product_ad", brief: "" },
  seedance: { videoType: "product_ad", brief: "" },
  text_to_video: { videoType: "product_ad", brief: "", frameMode: "ai" },
  review: { videoType: "kol_full", brief: "Làm video review sản phẩm theo kịch bản, KOL nói tự nhiên, nêu ưu điểm chính." },
  lookbook: { videoType: "kol_full", brief: "Lookbook thời trang: KOL trình diễn/giới thiệu sản phẩm trong bối cảnh editorial sang." },
};
