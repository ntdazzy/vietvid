"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api/endpoints";
import type { EstimateRequest } from "@/lib/api/types";
import { isTerminal } from "@/lib/job-status";

/** Ước tính credit realtime theo lựa chọn wizard (B2/B4). KHÔNG ghi DB, KHÔNG HOLD. */
export function useEstimate(p: EstimateRequest, enabled = true) {
  return useQuery({
    queryKey: ["estimate", p.mode, p.purpose, p.seconds, p.resolution],
    queryFn: () => api.estimate(p),
    enabled,
    staleTime: 60_000,
  });
}

export function useMe() {
  return useQuery({ queryKey: ["me"], queryFn: api.me });
}

export function useWallet() {
  return useQuery({ queryKey: ["wallet"], queryFn: api.wallet, refetchInterval: 20_000 });
}

export function useLedger(limit = 50) {
  return useQuery({ queryKey: ["ledger", limit], queryFn: () => api.ledger(limit) });
}

export function useJobs(limit = 30) {
  return useQuery({ queryKey: ["jobs", limit], queryFn: () => api.listJobs(limit) });
}

/** Poll chi tiết job 2.5s tới khi terminal (mục C — live render timeline). */
export function useJob(id: string | null) {
  return useQuery({
    queryKey: ["job", id],
    queryFn: () => api.getJob(id as string),
    enabled: Boolean(id),
    refetchInterval: (q) => (q.state.data && isTerminal(q.state.data.status) ? false : 2500),
  });
}
