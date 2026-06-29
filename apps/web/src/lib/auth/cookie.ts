"use client";

// Cookie CỜ "có phiên" cho middleware auth-guard. CHỈ là cờ "1" — KHÔNG chứa token
// (token thật vẫn ở localStorage; API mới là cổng bảo mật thật). Middleware đọc cookie
// này để redirect /app -> /login với khách chưa đăng nhập (chỉ điều hướng UX).
import { AUTH_COOKIE } from "@/lib/config";

export function setAuthCookie() {
  if (typeof document === "undefined") return;
  document.cookie = `${AUTH_COOKIE}=1; path=/; max-age=${60 * 60 * 24 * 30}; samesite=lax`;
}

export function clearAuthCookie() {
  if (typeof document === "undefined") return;
  document.cookie = `${AUTH_COOKIE}=; path=/; max-age=0; samesite=lax`;
}
