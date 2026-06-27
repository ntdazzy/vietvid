"use client";

import { API_BASE_URL, DEV_TOKEN_KEY } from "@/lib/config";
import { api } from "@/lib/api/endpoints";
import type { DevTokenResponse } from "@/lib/api/types";

/**
 * Đăng nhập DEV (khi chưa cấu hình Supabase): xin token HS256 từ backend /v1/dev/token,
 * lưu localStorage, rồi bootstrap tenant (tạo ví + tặng credit free). Idempotent.
 */
export async function devLogin(email?: string): Promise<DevTokenResponse> {
  const res = await fetch(`${API_BASE_URL}/v1/dev/token`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(email ? { email } : {}),
  });
  if (!res.ok) {
    throw new Error(
      res.status === 404
        ? "Dev login đã tắt (backend đang ở chế độ Supabase). Cấu hình Supabase env."
        : `Dev token lỗi: ${res.status}`,
    );
  }
  const token = (await res.json()) as DevTokenResponse;
  localStorage.setItem(DEV_TOKEN_KEY, token.access_token);
  await api.bootstrap(); // tạo workspace + ví + free credit (idempotent)
  return token;
}
