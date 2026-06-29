// Khớp 1-1 với app_api/schemas.py (M1). Đừng đổi tên field.

export interface KolPersona {
  id: string;
  name: string;
  description: string;
  gender: string;
  voice_gender: string;
  avatar_url: string;
  source: string; // ai | upload
  moderation_status: string;
  is_system: boolean;
}
