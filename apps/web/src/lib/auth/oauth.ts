"use client";

import { getSupabase } from "./supabase";

export type OAuthProvider = "google" | "facebook";

/**
 * Bắt đầu đăng nhập mạng xã hội qua Supabase OAuth (PKCE). Trình duyệt sẽ chuyển
 * tới Google/Facebook rồi quay về /auth/callback. Yêu cầu: Supabase đã cấu hình
 * (NEXT_PUBLIC_SUPABASE_*) + provider tương ứng đã bật trong dashboard Supabase.
 */
export async function signInWithProvider(provider: OAuthProvider, next = "/app"): Promise<void> {
  const supabase = getSupabase();
  if (!supabase) throw new Error("Chưa cấu hình Supabase OAuth — đặt NEXT_PUBLIC_SUPABASE_URL/ANON_KEY.");
  const safeNext = next.startsWith("/") && !next.startsWith("//") ? next : "/app";
  const redirectTo = `${window.location.origin}/auth/callback?next=${encodeURIComponent(safeNext)}`;
  const { error } = await supabase.auth.signInWithOAuth({ provider, options: { redirectTo } });
  if (error) throw new Error(error.message);
}
