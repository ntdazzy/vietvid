"use client";

import { Plus, Loader2, Sparkles } from "lucide-react";
import type { CreditPack } from "@/lib/api/types";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { CreditValue } from "@/components/ui/credit-value";
import { cn } from "@/lib/utils/cn";

const vnd = (n: number) => n.toLocaleString("vi-VN") + "đ";

/** Một gói credit. Nhấn mạnh được tính từ giá thật (đ/credit), KHÔNG theo index. */
export function PackCard({
  pack,
  isBest,
  isRecommended,
  perCredit,
  savePct,
  pending,
  disabled,
  onBuy,
}: {
  pack: CreditPack;
  isBest: boolean;
  isRecommended: boolean;
  perCredit: number;
  savePct: number;
  pending: boolean;
  disabled: boolean;
  onBuy: () => void;
}) {
  return (
    <GlassCard
      bordered={isBest || isRecommended}
      className={cn("flex h-full flex-col p-5", isBest && "lg:scale-[1.02]")}
    >
      {/* hàng badge — chừa chiều cao để 3 thẻ thẳng hàng */}
      <div className="mb-2 flex min-h-[28px] items-start">
        {isBest ? (
          <Badge tone="success">
            <Sparkles className="h-3 w-3" /> Giá tốt nhất
          </Badge>
        ) : isRecommended ? (
          <Badge tone="brand">Phổ biến</Badge>
        ) : null}
      </div>

      <h3 className="font-display text-base font-semibold text-ink-high">{pack.name}</h3>
      <div className="mt-2">
        <CreditValue value={pack.credits} className="text-3xl font-bold text-ink-high" />
      </div>
      <div className="mt-1 text-ink-medium">{vnd(pack.amount_vnd)}</div>

      {/* giá trị thật — chừa chiều cao; để TRỐNG nơi lẽ ra là "giảm giá" giả */}
      <div className="mt-2 min-h-[34px]">
        <div className={cn("text-xs", isBest ? "text-success" : "text-ink-low")}>
          <span className="font-numeric">{perCredit}</span>đ/credit
        </div>
        {savePct > 0 && <div className="text-xs text-success">Tiết kiệm {savePct}%</div>}
      </div>

      <Button
        className="mt-auto w-full gap-2"
        variant={isBest ? "primary" : "glass"}
        disabled={disabled}
        onClick={onBuy}
        aria-label={`Nạp gói ${pack.name} — ${pack.credits.toLocaleString("vi-VN")} credit`}
      >
        {pending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />} Nạp
      </Button>
    </GlassCard>
  );
}
