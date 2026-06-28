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
