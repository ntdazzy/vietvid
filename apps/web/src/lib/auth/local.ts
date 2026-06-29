"use client";

import { API_BASE_URL, DEV_TOKEN_KEY, REFRESH_TOKEN_KEY } from "@/lib/config";
import { setAuthCookie } from "./cookie";

type AuthTokens = { access_token: string; refresh_token?: string };

async function post(path: string, body: unknown): Promise<unknown> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = await res
      .json()
      .then((j) => j.detail as string)
      .catch(() => "");
    throw new Error(detail || (res.status === 409 ? "Email đã tồn tại" : "Có lỗi xảy ra"));
  }
  return res.json().catch(() => ({}));
}

function storeTokens(j: AuthTokens) {
  localStorage.setItem(DEV_TOKEN_KEY, j.access_token);
  if (j.refresh_token) localStorage.setItem(REFRESH_TOKEN_KEY, j.refresh_token);
  setAuthCookie();
}

async function authCall(path: string, body: unknown): Promise<AuthTokens> {
  const j = (await post(path, body)) as AuthTokens;
  storeTokens(j);
  return j;
}

export const registerLocal = (email: string, password: string, full_name = "") =>
  authCall("/v1/auth/register", { email, password, full_name });

export const loginLocal = (email: string, password: string) =>
  authCall("/v1/auth/login", { email, password });

export const forgotPassword = (email: string) => post("/v1/auth/forgot", { email });

export const resetPassword = (token: string, new_password: string) =>
  post("/v1/auth/reset", { token, new_password });

export const verifyEmail = (token: string) => post("/v1/auth/verify", { token });

/** Đổi access token còn hạn lấy cặp mới (rotate). Trả false nếu refresh hết hạn. */
export async function refreshSession(): Promise<boolean> {
  const rt = typeof window !== "undefined" ? localStorage.getItem(REFRESH_TOKEN_KEY) : null;
  if (!rt) return false;
  try {
    await authCall("/v1/auth/refresh", { refresh_token: rt });
    return true;
  } catch {
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    return false;
  }
}

/** Thu hồi refresh token phía server (đăng xuất thật). */
export async function logoutLocal(): Promise<void> {
  const rt = typeof window !== "undefined" ? localStorage.getItem(REFRESH_TOKEN_KEY) : null;
  if (rt) await post("/v1/auth/logout", { refresh_token: rt }).catch(() => {});
}
