"use client";

import { useTranslations } from "next-intl";
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
  const t = useTranslations("create");
  const remaining = Math.max(0, balance - holdCredits);
  // tỉ lệ phần "giữ" trên tổng (balance + hold đã trừ) để vẽ thanh
  const total = Math.max(balance, holdCredits, 1);
  const holdPct = Math.min(100, (holdCredits / total) * 100);

  return (
    <div className="glass-bordered p-5">
      <div className="flex items-baseline justify-between">
        <span className="text-sm text-ink-low">
          {phase === "estimate" ? t("estimateForThisVideo") : t("settlement")}
        </span>
        <span className="font-numeric text-2xl font-bold text-ink-high">
          ~<CreditValue value={estCredits} suffix="credit" className="text-2xl" />
        </span>
      </div>

      {/* meter bar */}
      <div
        role="progressbar"
        aria-valuenow={Math.round(holdPct)}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={t("holdRatioLabel")}
        className="mt-4 h-3 w-full overflow-hidden rounded-full bg-white/[0.06]"
      >
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
        <Cell label={t("cellMaxHold")} tone="hold" value={holdCredits} />
        {phase === "estimate" ? (
          <Cell label={t("cellRemainingAfterHold")} tone="neutral" value={remaining} />
        ) : (
          <Cell label={t("cellUsed")} tone="neutral" value={usedCredits ?? 0} />
        )}
        {phase === "estimate" ? (
          <Cell label={t("cellCurrentBalance")} tone="neutral" value={balance} />
        ) : (
          <Cell label={t("cellRefunded")} tone="refund" value={refundedCredits ?? 0} />
        )}
      </div>

      <p className="mt-4 text-center text-xs text-ink-low">
        {t("holdExplainer")}
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
