// Để rỗng ("") → dùng đường dẫn tương đối (same-origin), request /v1/* đi qua
// rewrite trong next.config về backend. Hữu ích khi chạy sau 1 tunnel/proxy duy nhất.
// undefined (không set) → mặc định gọi thẳng backend local.
export const API_BASE_URL =
  (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8099").replace(/\/$/, "");

export const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL || "";
export const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";

/** true = có Supabase thật; false = dev-mode (đăng nhập bằng dev token qua backend). */
export const supabaseConfigured = () => Boolean(SUPABASE_URL && SUPABASE_ANON_KEY);

export const DEV_TOKEN_KEY = "vietvid_dev_token";
export const REFRESH_TOKEN_KEY = "vietvid_refresh_token";
/** Cookie cờ "có phiên" (chỉ "1", không chứa token) — middleware đọc để guard /app. */
export const AUTH_COOKIE = "vyra_auth";
