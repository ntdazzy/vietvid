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

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-xl font-bold text-ink-high">Xem trước & chi phí</h2>
        <p className="mt-1 text-sm text-ink-low">
          Đây là khoảnh khắc minh bạch: thấy rõ cấu hình bên phải và chi phí trước khi tạo.
        </p>
      </div>

      {/* tóm tắt cấu hình + meter ở pane phải (desktop); mobile vẫn thấy HoldMeter ngay đây */}
      <div className="lg:hidden">
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

      <p className="hidden text-sm text-ink-low lg:block">
        Tạm giữ tối đa, dùng bao nhiêu tính bấy nhiêu. Hoàn 100% nếu lỗi hệ thống. Bấm
        <span className="text-ink-medium"> Tạo video </span> khi đã ưng cấu hình bên phải.
      </p>
    </div>
  );
}
