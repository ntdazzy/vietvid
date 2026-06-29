// Khớp 1-1 với app_api/schemas.py (M1). Đừng đổi tên field.

export interface BootstrapResponse {
  org_id: string;
  user_id: string;
  created: boolean;
  granted_credits: number;
  balance_credits: number;
}

export interface MeResponse {
  user_id: string;
  email: string;
  org_id: string;
  role: string;
  auth_mode: string;
  balance_credits: number;
  held_credits: number;
  is_admin?: boolean;
}

export interface DevTokenResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  email: string;
  expires_in: number;
}

export interface ProfileResponse {
  user_id: string;
  email: string;
  full_name: string;
  avatar_url: string;
  locale: string;
  email_verified: boolean;
}
