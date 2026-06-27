// Khớp 1-1 với app_api/schemas.py (M1). Đừng đổi tên field.

export type LedgerKind = "TOPUP" | "HOLD" | "SETTLE" | "REFUND" | "BONUS" | "ADJUST" | "EXPIRE";

export type JobStatus =
  | "WAITING_CONFIG"
  | "QUEUED"
  | "HELD"
  | "RUNNING"
  | "DIRECTING"
  | "IMAGING"
  | "RENDERING_VIDEO"
  | "VOICING"
  | "COMPOSING"
  | "QA"
  | "QA_FAIL"
  | "READY"
  | "FAILED"
  | "REFUNDED"
  | "CANCELLED";

/** Pipeline stage (cho timeline render trực tiếp — mục F #3). */
export const RENDER_STAGES = [
  "QUEUED",
  "DIRECTING",
  "IMAGING",
  "RENDERING_VIDEO",
  "VOICING",
  "COMPOSING",
  "QA",
  "READY",
] as const;
export type RenderStage = (typeof RENDER_STAGES)[number];

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

export interface WalletResponse {
  org_id: string;
  balance_credits: number;
  held_credits: number;
}

export interface LedgerEntry {
  id: number;
  entry_type: LedgerKind;
  delta_credits: number;
  balance_after: number;
  job_id?: string | null;
  payment_id?: string | null;
  note: string;
  created_at?: string | null;
}

export interface EstimateRequest {
  mode: string;
  purpose: string;
  seconds: number;
  resolution: string;
}

export interface EstimateResponse {
  est_usd: number;
  est_credits: number;
  hold_credits: number;
  model_id: string;
  resolution: string;
  seconds: number;
  breakdown: Record<string, unknown>;
  clamp_notes: string[];
}

export interface ProductInput {
  name?: string;
  category?: string;
  price?: string;
  description?: string;
  image_path?: string;
  image_url?: string;
  image_paths_json?: string;
}

export interface JobCreateRequest {
  idempotency_key: string;
  mode?: string;
  purpose?: string;
  seconds?: number;
  resolution?: string;
  format_key?: string;
  product?: ProductInput;
  kol?: Record<string, unknown> | null;
  params?: Record<string, unknown>;
  scene_prompt?: string;
  structure_reference?: string;
  template_id?: string;
  kol_persona_id?: string;
  brand_kit_id?: string;
}

export interface JobCreateResponse {
  job_id: string;
  status: JobStatus;
  hold_credits: number;
  est_credits: number;
  est_usd: number;
  duplicated: boolean;
  balance_credits: number;
  held_credits: number;
  clamp_notes: string[];
}

export interface JobEvent {
  stage: string;
  event_type: string;
  provider: string;
  cost_usd: number;
  asset_url: string;
  detail: Record<string, unknown>;
  created_at?: string | null;
}

export interface Job {
  id: string;
  status: JobStatus;
  kind: string;
  seconds: number;
  resolution: string;
  aspect: string;
  est_credits: number;
  est_cost_usd: number;
  actual_cost_usd: number;
  error: string;
  stage_timings: Record<string, number>;
  has_video: boolean;
  created_at?: string | null;
  finished_at?: string | null;
}

export interface JobDetail extends Job {
  events: JobEvent[];
}

export interface JobList {
  items: Job[];
  count: number;
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

export interface Template {
  id: string;
  name: string;
  description: string;
  category: string;
  preset: Record<string, unknown>;
  thumbnail_url: string;
  is_system: boolean;
}

export interface KolPersona {
  id: string;
  name: string;
  description: string;
  gender: string;
  voice_gender: string;
  avatar_url: string;
  source: string; // ai | upload
  moderation_status: string;
  is_system: boolean;
}

export interface BrandKit {
  id: string;
  name: string;
  logo_url: string;
  primary_color: string;
  secondary_color: string;
  font: string;
  watermark_text: string;
  disclosure_text: string;
  is_default: boolean;
}

export interface AdminStats {
  users: number;
  orgs: number;
  jobs: number;
  videos: number;
  credits_issued: number;
}

export interface ScriptBeat {
  label: string;
  t_start: number;
  t_end: number;
  narration: string;
  scene: string;
}

export interface Script {
  angle: string;
  angle_label: string;
  duration_seconds: number;
  voice_gender: string;
  hook_line: string;
  beats: ScriptBeat[];
  cta: string;
  captions: string[];
  narration_full: string;
  word_count: number;
  target_words: number;
  source: string;
}

export interface ScriptAngle {
  value: string;
  label: string;
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

export interface SeriesResponse {
  series_group: string;
  job_ids: string[];
  count: number;
  total_hold_credits: number;
  balance_credits: number;
  held_credits: number;
  tracked: boolean;
}

export interface VariantPerf {
  job_id: string;
  label: string;
  status: string;
  clicks: number;
  has_video: boolean;
  is_winner: boolean;
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

export interface CreditPack {
  id: string;
  name: string;
  amount_vnd: number;
  credits: number;
}

export interface TopupResponse {
  payment_id: string;
  provider: string;
  status: string;
  credits: number;
  amount_vnd: number;
  balance_credits?: number;
  pay_url?: string;
}
