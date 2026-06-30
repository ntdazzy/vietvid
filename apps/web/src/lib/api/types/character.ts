// Khớp 1-1 với app_api/routers/characters.py. Đừng đổi tên field.
// Nhân vật AI tái dùng (clone openart /suite/character) — "bring into future images & videos".

export interface Character {
  id: string;
  name: string;
  description: string;
  avatar_url: string;
  images: string[];
  source: string; // image | describe | build
  gender: string;
  ethnicity: string;
  age_range: string;
  vibe: string;
  voice_gender: string;
  is_system: boolean;
}

export interface CharacterCreate {
  name: string;
  description?: string;
  avatar_url?: string;
  images?: string[];
  source?: string;
  gender?: string;
  ethnicity?: string;
  age_range?: string;
  vibe?: string;
  voice_gender?: string;
}
