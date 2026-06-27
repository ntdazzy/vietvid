"use client";

import { motion } from "framer-motion";
import { CreditValue } from "@/components/ui/credit-value";
import { cn } from "@/lib/utils/cn";

/**
 * "Đồng hồ nhiên liệu credit" (mục F #2) — hiển thị 3 khoảnh khắc minh bạch:
 * Ước tính → Giữ tối đa → (sau khi tạo) Dùng / Hoàn. Số liệu thật từ API.
 */
export function HoldMeter({
  balance,
  estCredits,
  holdCredits,
  usedCredits,
  refundedCredits,
  phase,
}: {
  balance: number;
  estCredits: number;
  holdCredits: number;
  usedCredits?: number;
  refundedCredits?: number;
  phase: "estimate" | "settled";
}) {
  const remaining = Math.max(0, balance - holdCredits);
  // tỉ lệ phần "giữ" trên tổng (balance + hold đã trừ) để vẽ thanh
  const total = Math.max(balance, holdCredits, 1);
  const holdPct = Math.min(100, (holdCredits / total) * 100);

  return (
    <div className="glass-bordered p-5">
      <div className="flex items-baseline justify-between">
        <span className="text-sm text-ink-low">
          {phase === "estimate" ? "Ước tính cho video này" : "Quyết toán"}
        </span>
        <span className="font-numeric text-2xl font-bold text-ink-high">
          ~<CreditValue value={estCredits} suffix="credit" className="text-2xl" />
        </span>
      </div>

      {/* meter bar */}
      <div className="mt-4 h-3 w-full overflow-hidden rounded-full bg-white/[0.06]">
        <motion.div
          className={cn(
            "h-full rounded-full",
            phase === "estimate" ? "bg-hold" : "bg-grad-brand",
          )}
          initial={{ width: 0 }}
          animate={{ width: `${holdPct}%` }}
          transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
        />
      </div>

      <div className="mt-4 grid grid-cols-3 gap-3 text-center">
        <Cell label="Giữ tối đa" tone="hold" value={holdCredits} />
        {phase === "estimate" ? (
          <Cell label="Còn lại sau khi giữ" tone="neutral" value={remaining} />
        ) : (
          <Cell label="Đã dùng" tone="neutral" value={usedCredits ?? 0} />
        )}
        {phase === "estimate" ? (
          <Cell label="Số dư hiện tại" tone="neutral" value={balance} />
        ) : (
          <Cell label="Hoàn lại" tone="refund" value={refundedCredits ?? 0} />
        )}
      </div>

      <p className="mt-4 text-center text-xs text-ink-low">
        Tạm giữ tối đa, dùng bao nhiêu tính bấy nhiêu. Hoàn 100% nếu lỗi hệ thống.
      </p>
    </div>
  );
}

function Cell({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: "hold" | "refund" | "neutral";
}) {
  const color =
    tone === "hold" ? "text-hold" : tone === "refund" ? "text-refund" : "text-ink-high";
  return (
    <div>
      <div className={cn("font-numeric text-lg font-semibold tabular", color)}>
        {value.toLocaleString("vi-VN")}
      </div>
      <div className="mt-0.5 text-[11px] leading-tight text-ink-low">{label}</div>
    </div>
  );
}
