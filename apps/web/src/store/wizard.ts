"use client";

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

// State cho Create Wizard 5 bước. Persist sessionStorage để rời tab không mất.
export type WizardStep = 1 | 2 | 3 | 4 | 5;

interface Product {
  name: string;
  category: string;
  price: string;
  description: string;
  image_path: string; // server path từ /v1/uploads (rỗng nếu chỉ mô tả)
}

export type VideoType = "product_ad" | "kol_full";

export interface WizardState {
  step: WizardStep;
  // B1
  videoType: VideoType; // "product_ad" = video sản phẩm | "kol_full" = KOL AI
  frameMode: "upload" | "ai"; // lấy ảnh khung: tải lên hay tạo bằng AI (text→video)
  product: Product;
  imagePreviewUrl: string; // objectURL client-side để xem trước
  // B2
  purpose: "final" | "draft";
  seconds: number;
  resolution: string;
  videoEngine: string;
  brief: string;
  // B3
  voiceGender: "" | "female" | "male";
  kolName: string; // chỉ dùng khi videoType=kol_full
  kolStyle: string;
  consent: boolean; // KOL bắt buộc đồng ý
  // FK chọn từ gallery (Sóng 4)
  templateId: string;
  kolPersonaId: string;
  brandKitId: string;
  // B5
  idempotencyKey: string;
  jobId: string;

  setStep: (s: WizardStep) => void;
  patch: (p: Partial<WizardState>) => void;
  patchProduct: (p: Partial<Product>) => void;
  reset: () => void;
}

const freshKey = () =>
  typeof crypto !== "undefined" && crypto.randomUUID ? crypto.randomUUID() : `k-${Date.now()}`;

const initial = {
  step: 1 as WizardStep,
  videoType: "product_ad" as VideoType,
  frameMode: "upload" as "upload" | "ai",
  purpose: "final" as const,
  seconds: 8,
  resolution: "720p",
  videoEngine: "seedance",
  brief: "",
  product: { name: "", category: "", price: "", description: "", image_path: "" },
  imagePreviewUrl: "",
  voiceGender: "" as const,
  kolName: "",
  kolStyle: "",
  consent: false,
  templateId: "",
  kolPersonaId: "",
  brandKitId: "",
  idempotencyKey: "",
  jobId: "",
};

export const useWizard = create<WizardState>()(
  persist(
    (set) => ({
      ...initial,
      setStep: (step) => set({ step }),
      patch: (p) => set(p),
      patchProduct: (p) => set((s) => ({ product: { ...s.product, ...p } })),
      reset: () => set({ ...initial, idempotencyKey: freshKey() }),
    }),
    { name: "vietvid-wizard", storage: createJSONStorage(() => sessionStorage) },
  ),
);

export { freshKey };
