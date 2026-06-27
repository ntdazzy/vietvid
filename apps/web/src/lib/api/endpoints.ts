import { API_BASE_URL } from "@/lib/config";
import { getToken } from "@/lib/auth/session";
import { apiDelete, apiGet, apiPatch, apiPost } from "./client";
import type {
  AdminStats,
  AdminUser,
  AffiliateLink,
  BootstrapResponse,
  BrandKit,
  NotifList,
  CreditPack,
  EstimateRequest,
  EstimateResponse,
  JobCreateRequest,
  JobCreateResponse,
  JobDetail,
  JobList,
  KolPersona,
  LedgerEntry,
  MeResponse,
  ModItem,
  OrgInvite,
  OrgMember,
  ProfileResponse,
  SeriesResponse,
  Template,
  TopupResponse,
  VariantPerf,
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
  createSeries: (body: Record<string, unknown>) => apiPost<SeriesResponse>("/v1/series", body),
  seriesPerformance: (group: string) =>
    apiGet<VariantPerf[]>(`/v1/series/${group}/performance`),
  // URL authed thô (cần Bearer — render-timeline fetch kèm header rồi tạo blob).
  videoUrl: (id: string) => `${API_BASE_URL}/v1/jobs/${id}/video`,
  // URL CÓ CHỮ KÝ: phát/tải/chia sẻ KHÔNG cần Bearer (token query, hết hạn).
  getVideoSignedUrl: async (id: string): Promise<string> => {
    const { url } = await apiGet<{ url: string }>(`/v1/jobs/${id}/video-url`);
    return `${API_BASE_URL}${url}`;
  },
  getShareUrl: (id: string) => apiGet<{ share_url: string; video_url: string }>(`/v1/jobs/${id}/share-url`),

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

  // content: templates / KOL / brand kits
  templates: () => apiGet<Template[]>("/v1/templates"),
  createTemplate: (body: Partial<Template>) => apiPost<Template>("/v1/templates", body),
  deleteTemplate: (id: string) => apiDelete<void>(`/v1/templates/${id}`),
  kolPersonas: () => apiGet<KolPersona[]>("/v1/kol-personas"),
  createKol: (body: Partial<KolPersona> & { consent_confirmed?: boolean }) =>
    apiPost<KolPersona>("/v1/kol-personas", body),
  deleteKol: (id: string) => apiDelete<void>(`/v1/kol-personas/${id}`),
  brandKits: () => apiGet<BrandKit[]>("/v1/brand-kits"),
  createBrandKit: (body: Partial<BrandKit>) => apiPost<BrandKit>("/v1/brand-kits", body),
  updateBrandKit: (id: string, body: Partial<BrandKit>) =>
    apiPatch<BrandKit>(`/v1/brand-kits/${id}`, body),
  deleteBrandKit: (id: string) => apiDelete<void>(`/v1/brand-kits/${id}`),

  // admin
  adminStats: () => apiGet<AdminStats>("/v1/admin/stats"),
  adminUsers: (q = "") => apiGet<AdminUser[]>(`/v1/admin/users?q=${encodeURIComponent(q)}`),
  adminSetUserStatus: (userId: string, status: string) =>
    apiPost(`/v1/admin/users/${userId}/status`, { status }),
  adminCreditAdjust: (orgId: string, amount: number, note = "") =>
    apiPost(`/v1/admin/orgs/${orgId}/credit-adjust`, { amount, note }),
  adminModeration: () => apiGet<ModItem[]>("/v1/admin/moderation"),
  adminModerate: (kolId: string, orgId: string, approve: boolean) =>
    apiPost(`/v1/admin/moderation/${kolId}/decision`, { org_id: orgId, approve }),

  // affiliate
  affiliateLinks: () => apiGet<AffiliateLink[]>("/v1/affiliate/links"),
  createAffiliateLink: (body: { target_url: string; label?: string; network?: string; job_id?: string }) =>
    apiPost<AffiliateLink>("/v1/affiliate/links", body),
  deleteAffiliateLink: (id: string) => apiDelete<void>(`/v1/affiliate/links/${id}`),
  affiliateStats: () => apiGet<{ links: number; clicks: number }>("/v1/affiliate/stats"),

  // notifications
  notifications: () => apiGet<NotifList>("/v1/notifications"),
  markNotificationsRead: (ids?: string[]) => apiPost("/v1/notifications/read", { ids: ids ?? null }),

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
