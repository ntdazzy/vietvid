"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api/endpoints";
import type { JobCreateRequest, TopupRequestBody } from "@/lib/api/types";

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
    mutationFn: (body: TopupRequestBody) => api.topup({ provider: "dev", ...body }),
    onSuccess: (res) => {
      // vnpay/momo: redirect sang cổng. bank_qr: trang tự mở panel QR (poll riêng).
      if ((res.provider === "vnpay" || res.provider === "momo") && res.pay_url) {
        window.location.href = res.pay_url;
        return;
      }
      if (res.provider === "bank_qr") return; // page mở QrPayPanel + poll trạng thái
      // dev: cộng ngay → refresh ví + sổ cái.
      qc.invalidateQueries({ queryKey: ["wallet"] });
      qc.invalidateQueries({ queryKey: ["ledger"] });
    },
  });
}
