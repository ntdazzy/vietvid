// Khớp 1-1 với app_api/schemas.py (M1). Đừng đổi tên field.

export interface OrgMember {
  user_id: string;
  email: string;
  full_name: string;
  role: string;
  status: string;
  is_owner: boolean;
}

export interface OrgInvite {
  id: string;
  email: string;
  role: string;
  status: string;
  expires_at: string;
}

export interface ApiKey {
  id: string;
  name: string;
  prefix: string;
  last_used_at: string | null;
  created_at: string | null;
}

export interface Webhook {
  id: string;
  url: string;
  active: boolean;
  created_at: string | null;
}

export interface AffiliateLink {
  id: string;
  code: string;
  short_url: string;
  target_url: string;
  label: string;
  network: string;
  clicks: number;
}

export interface AppNotification {
  id: string;
  type: string;
  title: string;
  body: string;
  ref_type: string;
  ref_id: string;
  read: boolean;
  created_at: string | null;
}

export interface NotifList {
  items: AppNotification[];
  unread: number;
}
