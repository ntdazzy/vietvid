export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") || "http://127.0.0.1:8099";

export const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL || "";
export const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";

/** true = có Supabase thật; false = dev-mode (đăng nhập bằng dev token qua backend). */
export const supabaseConfigured = () => Boolean(SUPABASE_URL && SUPABASE_ANON_KEY);

export const DEV_TOKEN_KEY = "vietvid_dev_token";
export const REFRESH_TOKEN_KEY = "vietvid_refresh_token";
