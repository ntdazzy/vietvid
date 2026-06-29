"use client";

import { useTranslations } from "next-intl";
import { Plus, Loader2, Sparkles } from "lucide-react";
import type { CreditPack } from "@/lib/api/types";
import { cn } from "@/lib/utils/cn";

const vnd = (n: number) => n.toLocaleString("vi-VN") + "đ";

/** Một gói credit. Gói "giá tốt nhất" = hero gradient nổi bật; còn lại = glass.
 * Nhấn mạnh tính từ giá thật (đ/credit), KHÔNG theo index. */
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
  const t = useTranslations("billing");
  const hero = isBest; // gói rẻ-nhất/credit = thẻ chủ đạo
  const tag = isBest ? t("bestPrice") : isRecommended ? t("popular") : "";

  return (
    <div
      className={cn(
        "group relative flex h-full flex-col overflow-hidden rounded-2xl p-5 transition-all duration-300",
        hero
          ? "bg-gradient-to-br from-violet-600 via-violet-600 to-indigo-600 shadow-[0_22px_60px_-16px_rgba(124,58,237,.6)] lg:-translate-y-2"
          : "glass-bordered hover:-translate-y-1 hover:shadow-glow-sm",
      )}
    >
      {hero && (
        <div aria-hidden className="pointer-events-none absolute -right-12 -top-12 h-36 w-36 rounded-full bg-white/15 blur-3xl" />
      )}

      {/* nhãn — chừa chiều cao cố định để 3 thẻ thẳng hàng */}
      <div className="relative mb-3 flex min-h-[26px] items-start">
        {tag && (
          <span
            className={cn(
              "inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wider",
              hero ? "bg-white/20 text-white" : "bg-violet-500/15 text-violet-200 ring-1 ring-violet-400/25",
            )}
          >
            {isBest && <Sparkles className="h-3 w-3" />} {tag}
          </span>
        )}
      </div>

      <h3 className={cn("relative font-display text-xs font-semibold uppercase tracking-wider", hero ? "text-white/75" : "text-ink-low")}>
        {pack.name}
      </h3>
      <div className="relative mt-1.5 flex items-baseline gap-1.5">
        <span className={cn("font-numeric text-[40px] font-extrabold leading-none tabular", hero ? "text-white" : "text-gradient")}>
          {pack.credits.toLocaleString("vi-VN")}
        </span>
        <span className={cn("text-sm font-medium", hero ? "text-white/70" : "text-ink-low")}>credit</span>
      </div>
      <div className={cn("relative mt-1.5 font-numeric text-lg font-bold", hero ? "text-white" : "text-ink-high")}>
        {vnd(pack.amount_vnd)}
      </div>

      {/* giá trị thật: đ/credit + thanh tiết kiệm (data-viz, không phải badge giả) */}
      <div className="relative mt-3 space-y-1.5">
        <div className={cn("flex items-center justify-between text-xs", hero ? "text-white/85" : "text-ink-low")}>
          <span>
            <span className="font-numeric">{perCredit}</span>
            {t("perCreditSuffix")}
          </span>
          {savePct > 0 && (
            <span className={cn("font-semibold", hero ? "text-white" : "text-success")}>{t("save", { pct: savePct })}</span>
          )}
        </div>
        <div className={cn("h-1 overflow-hidden rounded-full", hero ? "bg-white/20" : "bg-white/[0.06]")}>
          <div
            className={cn("h-full rounded-full", hero ? "bg-white" : "bg-grad-brand")}
            style={{ width: `${Math.min(100, 28 + savePct * 5)}%` }}
          />
        </div>
      </div>

      <button
        type="button"
        disabled={disabled}
        onClick={onBuy}
        aria-label={t("buyPackAria", { name: pack.name, credits: pack.credits.toLocaleString("vi-VN") })}
        className={cn(
          "relative mt-5 inline-flex w-full items-center justify-center gap-2 rounded-xl py-2.5 text-sm font-semibold transition-all duration-200 active:scale-[0.98] disabled:opacity-50",
          hero
            ? "bg-white text-violet-700 hover:bg-white/90 hover:shadow-glow-sm"
            : "border border-white/12 text-ink-high hover:border-violet-400/50 hover:bg-violet-500/10",
        )}
      >
        {pending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />} {t("topup")}
      </button>
    </div>
  );
}
