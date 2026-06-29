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

export interface PaymentConfig {
  bank_bin: string;
  bank_account: string;
  bank_account_name: string;
  bank_name: string;
  webhook_token: string;
  momo_partner: string;
  momo_access: string;
  momo_secret: string;
  vnpay_tmn: string;
  vnpay_hash: string;
  enabled: { bank_qr: boolean; momo: boolean; vnpay: boolean };
  secrets_storage: "encrypted" | "env-only";
}
