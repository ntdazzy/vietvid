// Khớp 1-1 với app_api/schemas.py (M1). Đừng đổi tên field.

import type { LedgerKind } from "./common";

export interface WalletResponse {
  org_id: string;
  balance_credits: number; // xu mua/thưởng — không hết hạn
  held_credits: number;
  plan_credits?: number; // xu gói tháng — hết hạn
  plan_expires_at?: string | null;
  available_credits?: number; // balance + plan
}

export interface Plan {
  code: string;
  name: string;
  name_vi: string;
  monthly_price_vnd: number;
  credits: number;
  max_resolution: string;
  max_seconds: number;
  watermark_free: boolean;
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

export interface CreditPack {
  id: string;
  name: string;
  amount_vnd: number;
  credits: number;
}

export interface BankInfo {
  name: string;
  bin: string;
  account_number: string;
  account_name: string;
}

export interface TopupResponse {
  payment_id: string;
  provider: string;
  status: string;
  credits: number;
  amount_vnd: number;
  balance_credits?: number;
  pay_url?: string;
  // bank_qr
  qr_image_url?: string;
  memo?: string;
  bank?: BankInfo;
}

export interface PaymentStatusResponse {
  id: string;
  status: string;
  provider: string;
  credits: number;
  amount_vnd: number;
}

export interface TopupRequestBody {
  pack_id?: string;
  plan_code?: string;
  amount_vnd?: number;
  provider?: string;
}
