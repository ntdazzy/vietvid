import { API_BASE_URL, supabaseConfigured } from "@/lib/config";
import { getToken } from "@/lib/auth/session";
import { refreshSession } from "@/lib/auth/local";

export class ApiError extends Error {
  status: number;
  detail: string;
  constructor(status: number, detail: string) {
    super(`API ${status}: ${detail}`);
    this.status = status;
    this.detail = detail;
  }
}

async function authHeaders(): Promise<Record<string, string>> {
  const t = await getToken();
  return t ? { Authorization: `Bearer ${t}` } : {};
}

async function parse<T>(res: Response): Promise<T> {
  const text = await res.text();
  if (!res.ok) {
    let detail = text;
    try {
      detail = JSON.parse(text).detail ?? text;
    } catch {
      /* giữ text thô */
    }
    throw new ApiError(res.status, detail);
  }
  return (text ? JSON.parse(text) : null) as T;
}

/** Tự refresh access token 1 lần khi gặp 401 (dev-mode), rồi thử lại. */
async function withRefresh<T>(run: () => Promise<Response>): Promise<T> {
  let res = await run();
  if (res.status === 401 && !supabaseConfigured() && (await refreshSession())) {
    res = await run();
  }
  return parse<T>(res);
}

export async function apiGet<T>(path: string): Promise<T> {
  return withRefresh<T>(async () =>
    fetch(`${API_BASE_URL}${path}`, { headers: { ...(await authHeaders()) }, cache: "no-store" }),
  );
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  return withRefresh<T>(async () =>
    fetch(`${API_BASE_URL}${path}`, {
      method: "POST",
      headers: { "content-type": "application/json", ...(await authHeaders()) },
      body: JSON.stringify(body ?? {}),
      cache: "no-store",
    }),
  );
}

export async function apiPatch<T>(path: string, body?: unknown): Promise<T> {
  return withRefresh<T>(async () =>
    fetch(`${API_BASE_URL}${path}`, {
      method: "PATCH",
      headers: { "content-type": "application/json", ...(await authHeaders()) },
      body: JSON.stringify(body ?? {}),
      cache: "no-store",
    }),
  );
}

export async function apiDelete<T>(path: string): Promise<T> {
  return withRefresh<T>(async () =>
    fetch(`${API_BASE_URL}${path}`, {
      method: "DELETE",
      headers: { ...(await authHeaders()) },
      cache: "no-store",
    }),
  );
}
