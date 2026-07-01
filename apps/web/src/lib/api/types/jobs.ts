// Khớp 1-1 với app_api/schemas.py (M1). Đừng đổi tên field.

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

export interface VoicePersona {
  id: string;
  name: string;
  gender: string;
  vibe: string;
  blurb: string;
  rate: number;
  pitch: number;
}

export interface ScriptBeat {
  label: string;
  t_start: number;
  t_end: number;
  narration: string;
  scene: string;
}

export interface CaptionCue {
  index: number;
  start: number;
  end: number;
  text: string;
}

export interface ClaimWarning {
  match: string;
  label: string;
  severity: "block" | "warn";
  beat_index?: number;
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
  cues?: CaptionCue[];
  claim_warnings?: ClaimWarning[];
  narration_full: string;
  word_count: number;
  target_words: number;
  source: string;
}

export interface ScriptAngle {
  value: string;
  label: string;
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

// Làm hàng loạt: N sản phẩm KHÁC nhau → N video (gom bằng batch_group = series_group backend).
export interface BatchResponse {
  batch_group: string;
  job_ids: string[];
  count: number;
  total_hold_credits: number;
  balance_credits: number;
  held_credits: number;
}

export interface VariantPerf {
  job_id: string;
  label: string;
  status: string;
  clicks: number;
  has_video: boolean;
  is_winner: boolean;
}
