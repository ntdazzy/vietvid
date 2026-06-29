// Khớp 1-1 với app_api/schemas.py (M1). Đừng đổi tên field.

export interface AdminStats {
  users: number;
  orgs: number;
  jobs: number;
  videos: number;
  credits_issued: number;
}

export interface AdminConfig {
  video_provider_chain: string;
  max_api_jobs_per_day: number;
  feature_flags: Record<string, Record<string, boolean>>;
}

export interface AdminEconomics {
  credits_issued: number;
  credits_consumed: number;
  provider_cost_usd: number;
  provider_cost_vnd: number;
  revenue_vnd: number;
  margin_vnd: number;
  jobs_total: number;
  jobs_by_status: Record<string, number>;
  success_rate: number;
}

export interface AdminUser {
  id: string;
  email: string;
  full_name: string;
  status: string;
  org_id: string | null;
  plan_code: string | null;
  created_at: string | null;
}

export interface ModItem {
  id: string;
  org_id: string;
  name: string;
  avatar_url: string;
  description: string;
}
