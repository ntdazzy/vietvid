"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
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
  const t = useTranslations("billing");
  const [amount, setAmount] = useState(100_000);
  const credits = Math.max(1, Math.round(amount / PRICE));
  const valid = amount >= MIN && amount <= MAX;

  return (
    <GlassCard className="flex flex-col gap-3 p-5">
      <div className="flex items-center justify-between">
        <h3 className="flex items-center gap-1.5 font-display text-base font-semibold text-ink-high">
          <Coins className="h-4 w-4 text-emerald-300" /> {t("customAmountTitle")}
        </h3>
        <span className="text-xs text-ink-low">{t("priceHint")}</span>
      </div>

      {/* quy đổi LIVE — tâm điểm: KH thấy ngay nhận được bao nhiêu credit */}
      <div className="flex items-baseline gap-2 rounded-xl bg-emerald-500/[0.07] px-4 py-3 ring-1 ring-emerald-400/15">
        <span className={cn("font-numeric text-3xl font-extrabold tabular leading-none", valid ? "text-emerald-300" : "text-ink-low")}>
          {credits.toLocaleString("vi-VN")}
        </span>
        <span className="text-sm font-medium text-ink-low">credit</span>
        <span className="ml-auto text-xs text-ink-low">≈ {vnd(amount || 0)}</span>
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
                ? "border-emerald-400/40 bg-emerald-500/15 text-ink-high"
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
            placeholder={t("amountPlaceholder")}
            aria-label={t("amountAria")}
            className={cn(inputCls, "font-numeric pr-8")}
          />
          <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-sm text-ink-low">đ</span>
        </div>
        <Button onClick={() => onBuy(amount)} disabled={disabled || !valid} className="shrink-0 gap-2">
          {pending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
          {valid ? t("topupCredits", { credits: credits.toLocaleString("vi-VN") }) : t("topup")}
        </Button>
      </div>

      {amount > 0 && !valid && (
        <p className="text-xs text-hold">{t("amountRange", { min: vnd(MIN), max: vnd(MAX) })}</p>
      )}
    </GlassCard>
  );
}
