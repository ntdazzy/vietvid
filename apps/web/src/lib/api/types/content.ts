// Khớp 1-1 với app_api/schemas.py (M1). Đừng đổi tên field.

export interface Template {
  id: string;
  name: string;
  description: string;
  category: string;
  preset: Record<string, unknown>;
  thumbnail_url: string;
  is_system: boolean;
}

export interface BrandKit {
  id: string;
  name: string;
  logo_url: string;
  primary_color: string;
  secondary_color: string;
  font: string;
  watermark_text: string;
  disclosure_text: string;
  is_default: boolean;
}
