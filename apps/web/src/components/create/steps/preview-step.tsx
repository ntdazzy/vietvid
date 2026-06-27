"use client";

import { Loader2 } from "lucide-react";
import { useWizard } from "@/store/wizard";
import { useEstimate, useWallet } from "@/lib/query/hooks";
import { HoldMeter } from "@/components/create/hold-meter";

export function PreviewStep() {
  const w = useWizard();
  const wallet = useWallet();
  const est = useEstimate({
    mode: w.videoType,
    purpose: w.purpose,
    seconds: w.seconds,
    resolution: w.resolution,
  });

  const rows: [string, string][] = [
    ["Loại video", w.videoType === "kol_full" ? "KOL AI" : "Video sản phẩm"],
    ["Sản phẩm", w.product.name || "(chưa đặt tên)"],
    ...(w.videoType === "kol_full" ? ([["KOL", w.kolName || "(chưa đặt tên)"]] as [string, string][]) : []),
    ["Thời lượng", `${w.seconds}s · ${w.resolution}`],
    ["Engine", w.videoEngine],
    [
      "Giọng",
      `${w.voiceGender === "male" ? "Nam" : "Nữ"}${
        w.voicePersona ? ` · ${w.voicePersona.charAt(0).toUpperCase()}${w.voicePersona.slice(1)}` : ""
      }`,
    ],
    ["Bản", w.purpose === "draft" ? "Nháp" : "Hoàn chỉnh"],
  ];

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-xl font-bold text-ink-high">Xem trước & chi phí</h2>
        <p className="mt-1 text-sm text-ink-low">
          Đây là khoảnh khắc minh bạch: thấy rõ chi phí trước khi tạo.
        </p>
      </div>

      <div className="glass rounded-xl divide-y divide-white/[0.06]">
        {rows.map(([k, v]) => (
          <div key={k} className="flex items-center justify-between px-4 py-3 text-sm">
            <span className="text-ink-low">{k}</span>
            <span className="text-ink-high">{v}</span>
          </div>
        ))}
      </div>

      {est.isLoading || wallet.isLoading ? (
        <div className="glass-bordered grid place-items-center p-10">
          <Loader2 className="h-5 w-5 animate-spin text-ink-low" />
        </div>
      ) : (
        <HoldMeter
          phase="estimate"
          balance={wallet.data?.balance_credits ?? 0}
          estCredits={est.data?.est_credits ?? 0}
          holdCredits={est.data?.hold_credits ?? 0}
        />
      )}
    </div>
  );
}
