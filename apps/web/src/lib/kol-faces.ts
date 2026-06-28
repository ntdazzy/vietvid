// Gương mặt AI mẫu cho persona hệ thống (avatar_url rỗng). User tự tải sẽ đè lên.
export const SYSTEM_KOL_FACES: Record<string, string> = {
  Linh: "/kol/linh.jpg",
  Minh: "/kol/an.jpg",
  Hà: "/kol/mai.jpg",
};

/** Trả về ảnh gương mặt cho 1 KOL: ưu tiên avatar thật, fallback ảnh mẫu hệ thống. */
export function kolFace(name: string, avatarUrl?: string): string {
  return avatarUrl || SYSTEM_KOL_FACES[name] || "";
}
