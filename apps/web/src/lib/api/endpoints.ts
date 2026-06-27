import { API_BASE_URL } from "@/lib/config";
import { getToken } from "@/lib/auth/session";
import { apiDelete, apiGet, apiPatch, apiPost } from "./client";
import type {
  BootstrapResponse,
  CreditPack,
  EstimateRequest,
  EstimateResponse,
  JobCreateRequest,
  JobCreateResponse,
  JobDetail,
  JobList,
  LedgerEntry,
  MeResponse,
  OrgInvite,
  OrgMember,
  ProfileResponse,
  TopupResponse,
  WalletResponse,
} from "./types";

export const api = {
  health: () => apiGet<{ status: string; auth_mode: string; exec_mode: string }>("/health"),
  bootstrap: () => apiPost<BootstrapResponse>("/v1/tenants/bootstrap"),
  me: () => apiGet<MeResponse>("/v1/auth/me"),
  wallet: () => apiGet<WalletResponse>("/v1/wallet"),
  ledger: (limit = 50) => apiGet<LedgerEntry[]>(`/v1/wallet/ledger?limit=${limit}`),
  billingPacks: () => apiGet<CreditPack[]>("/v1/billing/packs"),
  topup: (packId: string, provider = "dev") =>
    apiPost<TopupResponse>("/v1/billing/topup", { pack_id: packId, provider }),
  estimate: (body: EstimateRequest) => apiPost<EstimateResponse>("/v1/jobs/estimate", body),
  createJob: (body: JobCreateRequest) => apiPost<JobCreateResponse>("/v1/jobs", body),
  listJobs: (limit = 30) => apiGet<JobList>(`/v1/jobs?limit=${limit}`),
  getJob: (id: string) => apiGet<JobDetail>(`/v1/jobs/${id}`),
  cancelJob: (id: string) => apiPost(`/v1/jobs/${id}/cancel`),
  deleteJob: (id: string) => apiDelete<void>(`/v1/jobs/${id}`),
  // URL authed thô (cần Bearer — render-timeline fetch kèm header rồi tạo blob).
  videoUrl: (id: string) => `${API_BASE_URL}/v1/jobs/${id}/video`,
  // URL CÓ CHỮ KÝ: phát/tải/chia sẻ KHÔNG cần Bearer (token query, hết hạn).
  getVideoSignedUrl: async (id: string): Promise<string> => {
    const { url } = await apiGet<{ url: string }>(`/v1/jobs/${id}/video-url`);
    return `${API_BASE_URL}${url}`;
  },

  // hồ sơ + đổi mật khẩu
  updateProfile: (body: { full_name?: string; avatar_url?: string; locale?: string }) =>
    apiPatch<ProfileResponse>("/v1/auth/me", body),
  changePassword: (current_password: string, new_password: string) =>
    apiPost<{ ok: boolean; detail: string }>("/v1/auth/change-password", {
      current_password,
      new_password,
    }),

  // org / team
  orgMembers: () => apiGet<OrgMember[]>("/v1/orgs/members"),
  orgInvites: () => apiGet<OrgInvite[]>("/v1/orgs/invites"),
  inviteMember: (email: string, role = "member") =>
    apiPost<OrgInvite>("/v1/orgs/invite", { email, role }),
  removeMember: (userId: string) => apiDelete<{ ok: boolean }>(`/v1/orgs/members/${userId}`),
  revokeInvite: (id: string) => apiDelete<{ ok: boolean }>(`/v1/orgs/invites/${id}`),
  acceptInvite: (token: string) =>
    apiPost<{ ok: boolean; detail: string }>("/v1/orgs/accept-invite", { token }),

  async uploadImage(file: File): Promise<{ image_path: string; filename: string; bytes: number }> {
    const fd = new FormData();
    fd.append("file", file);
    const token = await getToken();
    const res = await fetch(`${API_BASE_URL}/v1/uploads`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: fd,
    });
    if (!res.ok) {
      const t = await res.text();
      throw new Error(res.status === 415 ? "Chỉ nhận ảnh JPEG/PNG/WebP" : `Upload lỗi: ${t}`);
    }
    return res.json();
  },

  async voicePreview(text: string, gender: string): Promise<string> {
    const token = await getToken();
    const res = await fetch(`${API_BASE_URL}/v1/voice/preview`, {
      method: "POST",
      headers: { "content-type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      body: JSON.stringify({ text, gender }),
    });
    if (!res.ok) throw new Error("Tạo giọng lỗi");
    return URL.createObjectURL(await res.blob());
  },

  async generateImage(prompt: string, aspect?: string): Promise<{ url: string; path: string }> {
    const token = await getToken();
    const res = await fetch(`${API_BASE_URL}/v1/images/generate`, {
      method: "POST",
      headers: { "content-type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      body: JSON.stringify({ prompt, aspect }),
    });
    if (!res.ok) {
      const t = await res.text();
      throw new Error(t.includes("GEMINI") ? "Cần cấu hình IMAGE_PROVIDER=gemini" : "Tạo ảnh lỗi");
    }
    const path = res.headers.get("X-Image-Path") ?? "";
    return { url: URL.createObjectURL(await res.blob()), path };
  },

  async compose(imagePaths: string[], secondsPer = 3): Promise<string> {
    const token = await getToken();
    const res = await fetch(`${API_BASE_URL}/v1/compose`, {
      method: "POST",
      headers: { "content-type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      body: JSON.stringify({ image_paths: imagePaths, seconds_per: secondsPer }),
    });
    if (!res.ok) throw new Error("Ghép video lỗi");
    return URL.createObjectURL(await res.blob());
  },
};
