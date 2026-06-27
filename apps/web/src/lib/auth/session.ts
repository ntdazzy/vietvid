"use client";

import { DEV_TOKEN_KEY, supabaseConfigured } from "@/lib/config";
import { getSupabase } from "./supabase";

/**
 * Lấy Bearer token cho API.
 * - Có Supabase → access_token của session.
 * - Dev-mode → token lưu localStorage (phát qua backend /v1/dev/token, xem dev.ts).
 */
export async function getToken(): Promise<string | null> {
  if (supabaseConfigured()) {
    const sb = getSupabase();
    const { data } = (await sb?.auth.getSession()) ?? { data: { session: null } };
    return data.session?.access_token ?? null;
  }
  if (typeof window !== "undefined") return localStorage.getItem(DEV_TOKEN_KEY);
  return null;
}

export function clearSession() {
  if (typeof window !== "undefined") localStorage.removeItem(DEV_TOKEN_KEY);
  if (supabaseConfigured()) void getSupabase()?.auth.signOut();
}

export async function isAuthed(): Promise<boolean> {
  return Boolean(await getToken());
}
