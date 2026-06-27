"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api/endpoints";
import type { JobCreateRequest } from "@/lib/api/types";

export function useUploadImage() {
  return useMutation({ mutationFn: (file: File) => api.uploadImage(file) });
}

export function useCreateJob() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: JobCreateRequest) => api.createJob(body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["wallet"] });
      qc.invalidateQueries({ queryKey: ["jobs"] });
    },
  });
}

export function useTopup() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ packId, provider = "dev" }: { packId: string; provider?: string }) =>
      api.topup(packId, provider),
    onSuccess: (res) => {
      // dev: cộng ngay → refresh ví + sổ cái; vnpay: redirect sang cổng.
      if (res.provider === "vnpay" && res.pay_url) {
        window.location.href = res.pay_url;
        return;
      }
      qc.invalidateQueries({ queryKey: ["wallet"] });
      qc.invalidateQueries({ queryKey: ["ledger"] });
    },
  });
}
