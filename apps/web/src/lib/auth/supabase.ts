"use client";

import { createBrowserClient } from "@supabase/ssr";
import { SUPABASE_ANON_KEY, SUPABASE_URL, supabaseConfigured } from "@/lib/config";

let _client: ReturnType<typeof createBrowserClient> | null = null;

/** Trả Supabase browser client nếu đã cấu hình env, ngược lại null (dev-mode). */
export function getSupabase() {
  if (!supabaseConfigured()) return null;
  if (!_client) _client = createBrowserClient(SUPABASE_URL, SUPABASE_ANON_KEY);
  return _client;
}
