"use client";

import { useState } from "react";
import { Plus, Loader2, Coins } from "lucide-react";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { inputCls } from "@/components/ui/field";
import { cn } from "@/lib/utils/cn";

const PRICE = 150; // 1 credit = 150đ
const MIN = 20_000;
const MAX = 50_000_000;
const QUICK = [50_000, 100_000, 200_000, 500_000];
const vnd = (n: number) => n.toLocaleString("vi-VN") + "đ";

/** Nạp số tiền tuỳ ý (ngoài gói) — quy đổi credit theo giá gốc. */
export function CustomAmount({
  pending,
  disabled,
  onBuy,
}: {
  pending: boolean;
  disabled: boolean;
  onBuy: (amountVnd: number) => void;
}) {
  const [amount, setAmount] = useState(100_000);
  const credits = Math.max(1, Math.round(amount / PRICE));
  const valid = amount >= MIN && amount <= MAX;

  return (
    <GlassCard className="flex flex-col gap-3 p-5">
      <div className="flex items-center justify-between">
        <h3 className="flex items-center gap-1.5 font-display text-base font-semibold text-ink-high">
          <Coins className="h-4 w-4 text-violet-300" /> Số tiền khác
        </h3>
        <span className="text-xs text-ink-low">1 credit = 150đ</span>
      </div>

      <div className="flex flex-wrap gap-2">
        {QUICK.map((q) => (
          <button
            key={q}
            type="button"
            onClick={() => setAmount(q)}
            className={cn(
              "rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors",
              amount === q
                ? "border-violet-400/40 bg-violet-500/20 text-ink-high"
                : "border-white/10 text-ink-low hover:text-ink-medium",
            )}
          >
            {vnd(q)}
          </button>
        ))}
      </div>

      <div className="flex items-stretch gap-3">
        <div className="relative flex-1">
          <input
            type="number"
            inputMode="numeric"
            value={amount || ""}
            onChange={(e) => setAmount(Number(e.target.value) || 0)}
            placeholder="Nhập số tiền"
            aria-label="Số tiền nạp (đồng)"
            className={cn(inputCls, "font-numeric pr-8")}
          />
          <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-sm text-ink-low">đ</span>
        </div>
        <Button onClick={() => onBuy(amount)} disabled={disabled || !valid} className="shrink-0 gap-2">
          {pending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
          {valid ? `Nạp ${credits.toLocaleString("vi-VN")} credit` : "Nạp"}
        </Button>
      </div>

      {amount > 0 && !valid && (
        <p className="text-xs text-hold">Nạp từ {vnd(MIN)} đến {vnd(MAX)}.</p>
      )}
    </GlassCard>
  );
}
