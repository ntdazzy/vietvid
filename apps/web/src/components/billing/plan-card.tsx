"use client";

import { useTranslations } from "next-intl";
import { Check, Loader2, Sparkles } from "lucide-react";
import type { Plan } from "@/lib/api/types";
import { cn } from "@/lib/utils/cn";

const vnd = (n: number) => n.toLocaleString("vi-VN") + "đ";

/** Một gói tháng (subscription). Gói khuyên dùng = hero gradient nổi bật; còn lại = glass.
 * Pricing table KHÔNG 4-tháp-giống-hệt: nhấn bằng MÀU + ribbon + checklist, không bằng chiều cao. */
export function PlanCard({
  plan,
  isRecommended,
  pending,
  disabled,
  onBuy,
}: {
  plan: Plan;
  isRecommended: boolean;
  pending: boolean;
  disabled: boolean;
  onBuy: () => void;
}) {
  const t = useTranslations("billing");
  const hero = isRecommended;
  const perCredit = Math.round(plan.monthly_price_vnd / Math.max(1, plan.credits));
  const features = [
    t("planResUpTo", { res: plan.max_resolution }),
    t("planLenUpTo", { sec: plan.max_seconds }),
    ...(plan.watermark_free ? [t("planNoWatermark")] : []),
  ];

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

      <div className="relative mb-3 flex min-h-[26px] items-start">
        {hero && (
          <span className="inline-flex items-center gap-1 rounded-full bg-white/20 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wider text-white">
            <Sparkles className="h-3 w-3" /> {t("popular")}
          </span>
        )}
      </div>

      <h3 className={cn("relative font-display text-xs font-semibold uppercase tracking-wider", hero ? "text-white/75" : "text-ink-low")}>
        {plan.name_vi || plan.name}
      </h3>

      <div className="relative mt-1.5 flex items-baseline gap-1.5">
        <span className={cn("font-numeric text-[34px] font-extrabold leading-none tabular", hero ? "text-white" : "text-gradient")}>
          {plan.credits.toLocaleString("vi-VN")}
        </span>
        <span className={cn("text-xs font-medium", hero ? "text-white/70" : "text-ink-low")}>{t("planCreditsUnit")}</span>
      </div>

      <div className={cn("relative mt-2 flex items-baseline gap-1", hero ? "text-white" : "text-ink-high")}>
        <span className="font-numeric text-lg font-bold">{vnd(plan.monthly_price_vnd)}</span>
        <span className={cn("text-xs", hero ? "text-white/60" : "text-ink-low")}>{t("planPerMonth")}</span>
      </div>
      <div className={cn("relative mt-0.5 text-xs", hero ? "text-white/70" : "text-ink-low")}>
        {t("planValuePerCredit", { v: perCredit })}
      </div>

      <ul className="relative mt-4 flex flex-col gap-2">
        {features.map((f) => (
          <li key={f} className={cn("flex items-center gap-2 text-xs", hero ? "text-white/90" : "text-ink-medium")}>
            <Check className={cn("h-3.5 w-3.5 shrink-0", hero ? "text-white" : "text-emerald-400")} />
            {f}
          </li>
        ))}
      </ul>

      <button
        type="button"
        disabled={disabled}
        onClick={onBuy}
        className={cn(
          "relative mt-5 inline-flex w-full items-center justify-center gap-2 rounded-xl py-2.5 text-sm font-semibold transition-all duration-200 active:scale-[0.98] disabled:opacity-50",
          hero
            ? "bg-white text-violet-700 hover:bg-white/90 hover:shadow-glow-sm"
            : "border border-white/12 text-ink-high hover:border-violet-400/50 hover:bg-violet-500/10",
        )}
      >
        {pending && <Loader2 className="h-4 w-4 animate-spin" />} {t("planSubscribe")}
      </button>

      <p className={cn("relative mt-2.5 text-center text-[11px]", hero ? "text-white/55" : "text-ink-disabled")}>
        {t("planExpiryNote")}
      </p>
    </div>
  );
}
