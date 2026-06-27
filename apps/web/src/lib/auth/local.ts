"use client";

import { API_BASE_URL, DEV_TOKEN_KEY } from "@/lib/config";

async function call(path: string, body: unknown) {
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
  const j = (await res.json()) as { access_token: string };
  localStorage.setItem(DEV_TOKEN_KEY, j.access_token);
  return j;
}

export const registerLocal = (email: string, password: string, full_name = "") =>
  call("/v1/auth/register", { email, password, full_name });

export const loginLocal = (email: string, password: string) =>
  call("/v1/auth/login", { email, password });
