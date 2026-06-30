import {
  Shirt,
  Film,
  Megaphone,
  Flame,
  Music2,
  BookOpen,
  Copy,
  Type,
  Image as ImageIcon,
  Video,
  Layers,
  Clapperboard,
  CalendarClock,
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

// Cấu trúc đúng theo menu autovis: 3 cột trong "Tạo nội dung".
export const CONTENT_GROUPS: FeatureGroup[] = [
  {
    title: "Công cụ chủ lực",
    items: [
      { key: "lookbook", label: "Lookbook Thời trang", desc: "KOL mặc SP bối cảnh editorial", icon: Shirt, available: true, href: "/features/lookbook" },
      { key: "review", label: "Tạo Video Review", desc: "KOL review SP theo kịch bản", icon: Film, badge: "Viral", available: true, href: "/features/review" },
      { key: "product_ad", label: "Quảng cáo sản phẩm", desc: "Biến SP thành video quảng cáo", icon: Megaphone, badge: "Mới", available: true, href: "/features/product_ad" },
      { key: "trends_image", label: "Tạo Ảnh Trends", desc: "Bắt trend thịnh hành, ảnh viral", icon: Flame, badge: "Sắp có", available: false, href: "#" },
      { key: "motion_copy", label: "Sao chép chuyển động", desc: "KOL nhảy theo trend dance", icon: Music2, badge: "Sắp có", available: false, href: "#" },
      { key: "story", label: "Video dạng câu chuyện", desc: "Video storyboard dài", icon: BookOpen, badge: "Sắp có", available: false, href: "#" },
      { key: "bulk", label: "Sao chép hàng ngàn video", desc: "Nhân video viral lên KOL AI", icon: Copy, badge: "Sắp có", available: false, href: "#" },
    ],
  },
  {
    title: "Xây kênh ẩn danh",
    items: [
      { key: "text_to_video", label: "Văn bản → Video", desc: "Text-to-video (AI tạo khung)", icon: Type, available: true, href: "/features/text_to_video" },
      { key: "image_to_video", label: "Video từ hình ảnh", desc: "Image-to-video", icon: ImageIcon, available: true, href: "/features/product_ad" },
      { key: "video_remix", label: "Video từ video mẫu", desc: "Video-to-video remix", icon: Video, badge: "Sắp có", available: false, href: "#" },
      { key: "composite", label: "Ghép Video & Hình ảnh", desc: "Ghép nhiều ảnh thành video", icon: Layers, available: true, href: "/features/composite" },
      { key: "pexels", label: "Video từ kho Pexels", desc: "Stock footage AI", icon: Clapperboard, badge: "Sắp có", available: false, href: "#" },
      { key: "autopost", label: "Đăng bài tự động", desc: "Lên lịch đăng bài", icon: CalendarClock, badge: "Sắp có", available: false, href: "#" },
    ],
  },
  {
    title: "Ảnh & Âm thanh",
    items: [
      { key: "seedance", label: "Seedance 2.0", desc: "Video cinematic AI cao cấp", icon: Sparkles, badge: "Nâng cao", available: true, href: "/features/product_ad" },
      { key: "ai_image", label: "Tạo ảnh nghệ thuật AI", desc: "Generate ảnh art AI", icon: Palette, available: true, href: "/features/ai_image" },
      { key: "ai_audio", label: "Tạo âm thanh AI", desc: "Văn bản → giọng Việt", icon: AudioLines, available: true, href: "/features/ai_audio" },
      { key: "voice_clone", label: "Nhân bản giọng nói", desc: "Voice clone (VieNeu)", icon: Mic2, badge: "Sắp có", available: false, href: "#" },
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
      { key: "m_seedance", label: "Seedance 2.0", desc: "Video điện ảnh AI cao cấp", icon: Sparkles, badge: "Nâng cao", available: true, href: "/app/create" },
      { key: "m_kling", label: "Kling", desc: "Chuyển động mượt, dài hơi", icon: Video, badge: "Sắp có", available: false, href: "#" },
      { key: "m_hailuo", label: "Hailuo · MiniMax", desc: "Nhanh, hợp clip ngắn", icon: Clapperboard, badge: "Sắp có", available: false, href: "#" },
      { key: "m_veo", label: "Runway · Veo", desc: "Chất điện ảnh cao cấp", icon: Film, badge: "Sắp có", available: false, href: "#" },
    ],
  },
  {
    title: "Model Ảnh",
    items: [
      { key: "m_gemini", label: "Gemini · Imagen", desc: "Ảnh sắc nét, bám mô tả", icon: ImageIcon, available: true, href: "/app/image-gen" },
      { key: "m_flux", label: "Flux", desc: "Ảnh thực, chữ trong ảnh chuẩn", icon: Wand2, badge: "Sắp có", available: false, href: "#" },
      { key: "m_sdxl", label: "Stable Diffusion XL", desc: "Tùy biến mạnh + LoRA", icon: Boxes, badge: "Sắp có", available: false, href: "#" },
      { key: "m_dalle", label: "DALL·E", desc: "Phác ý tưởng nhanh", icon: Palette, badge: "Sắp có", available: false, href: "#" },
    ],
  },
  {
    title: "Giọng & Nhân vật",
    items: [
      { key: "m_voice", label: "Giọng Việt thật", desc: "7 giọng cá tính, nghe thử ngay", icon: AudioLines, available: true, href: "/app/audio" },
      { key: "m_character", label: "Nhân vật AI", desc: "Diễn viên nhất quán, tái dùng", icon: Drama, available: true, href: "/app/character" },
      { key: "m_instantid", label: "Giữ gương mặt", desc: "Khóa danh tính khi sinh lại (InstantID)", icon: ScanFace, badge: "Sắp có", available: false, href: "#" },
    ],
  },
];

// Tính năng (use-case / feature page) — mega-panel "Tính năng". 2 nhóm → cols=2.
export const FEATURES_GROUPS: FeatureGroup[] = [
  {
    title: "Bán hàng & KOL",
    items: [
      { key: "f_kol", label: "KOL AI", desc: "Gương mặt ảo review nhất quán", icon: Flame, available: true, href: "/app/kol" },
      { key: "f_review", label: "Video review", desc: "KOL review theo kịch bản", icon: Film, available: true, href: "/features/review" },
      { key: "f_lookbook", label: "Lookbook thời trang", desc: "Trình diễn SP bối cảnh editorial", icon: Shirt, available: true, href: "/features/lookbook" },
      { key: "f_ad", label: "Quảng cáo sản phẩm", desc: "1 ảnh → video chốt đơn", icon: Megaphone, available: true, href: "/features/product_ad" },
    ],
  },
  {
    title: "Sáng tạo & câu chuyện",
    items: [
      { key: "f_t2v", label: "Văn bản → Video", desc: "Ý tưởng → khung AI", icon: Type, available: true, href: "/features/text_to_video" },
      { key: "f_image", label: "Tạo ảnh AI", desc: "Mô tả một câu, AI vẽ ảnh", icon: Palette, available: true, href: "/features/ai_image" },
      { key: "f_composite", label: "Ghép video & ảnh", desc: "Nhiều ảnh thành video", icon: Layers, available: true, href: "/features/composite" },
      { key: "f_story", label: "Kể chuyện / phim ngắn", desc: "Storyboard theo timecode", icon: BookOpen, badge: "Sắp có", available: false, href: "#" },
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
