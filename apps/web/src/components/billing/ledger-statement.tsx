"use client";

import { useTranslations } from "next-intl";
import {
  Plus, Gift, Lock, Check, RotateCcw, ArrowDownToLine, Loader2, Receipt, type LucideIcon,
} from "lucide-react";
import type { LedgerEntry, LedgerKind } from "@/lib/api/types";
import { GlassCard } from "@/components/ui/glass-card";
import { formatDate } from "@/lib/job-status";
import { cn } from "@/lib/utils/cn";

const META: Record<LedgerKind, { labelKey: string; icon: LucideIcon; color: string }> = {
  TOPUP: { labelKey: "kindTopup", icon: ArrowDownToLine, color: "text-success" },
  BONUS: { labelKey: "kindBonus", icon: Gift, color: "text-violet-300" },
  HOLD: { labelKey: "kindHold", icon: Lock, color: "text-hold" },
  SETTLE: { labelKey: "kindSettle", icon: Check, color: "text-ink-medium" },
  REFUND: { labelKey: "kindRefund", icon: RotateCcw, color: "text-refund" },
  ADJUST: { labelKey: "kindAdjust", icon: Plus, color: "text-ink-medium" },
  EXPIRE: { labelKey: "kindExpire", icon: RotateCcw, color: "text-ink-low" },
};

function deltaColor(e: LedgerEntry): string {
  if (e.delta_credits > 0) return "text-success";
  if (e.entry_type === "HOLD") return "text-hold";
  if (e.entry_type === "REFUND") return "text-refund";
  return "text-ink-medium";
}

type Filter = LedgerKind | "ALL";

/** Sổ cái như sao kê ngân hàng: lọc theo loại, gom theo job, số dư chạy — bằng chứng minh bạch. */
export function LedgerStatement({
  entries,
  isLoading,
  filter,
  setFilter,
}: {
  entries: LedgerEntry[] | undefined;
  isLoading: boolean;
  filter: Filter;
  setFilter: (f: Filter) => void;
}) {
  const t = useTranslations("billing");
  const all = entries ?? [];
  const kinds = Array.from(new Set(all.map((e) => e.entry_type)));
  const rows = filter === "ALL" ? all : all.filter((e) => e.entry_type === filter);

  return (
    <div className="flex flex-col gap-3">
      {all.length > 0 && (
        <div className="flex items-center justify-end">
          <span className="text-xs text-ink-low">{t("recentTransactions", { count: all.length })}</span>
        </div>
      )}

      {/* lọc — chỉ hiện loại thực sự có trong dữ liệu */}
      {all.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {(["ALL", ...kinds] as Filter[]).map((k) => {
            const active = filter === k;
            return (
              <button
                key={k}
                type="button"
                onClick={() => setFilter(k)}
                aria-pressed={active}
                className={cn(
                  "rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400/40",
                  active
                    ? "border-emerald-400/40 bg-emerald-500/15 text-ink-high"
                    : "border-white/10 text-ink-low hover:text-ink-medium",
                )}
              >
                {k === "ALL" ? t("filterAll") : t(META[k].labelKey)}
              </button>
            );
          })}
        </div>
      )}

      <GlassCard className="divide-y divide-white/[0.05] p-0">
        {isLoading ? (
          <div className="flex items-center gap-2 p-5 text-ink-low">
            <Loader2 className="h-4 w-4 animate-spin" /> {t("loading")}
          </div>
        ) : all.length === 0 ? (
          <div className="flex flex-col items-center gap-3 py-14 text-center">
            <div className="grid h-12 w-12 place-items-center rounded-2xl bg-white/[0.04]">
              <Receipt className="h-5 w-5 text-ink-low" />
            </div>
            <p className="max-w-xs text-sm text-ink-low">
              {t("emptyAll")}
            </p>
          </div>
        ) : rows.length === 0 ? (
          <p className="p-6 text-center text-sm text-ink-low">{t("emptyFiltered")}</p>
        ) : (
          rows.map((e) => {
            const m = META[e.entry_type] ?? META.ADJUST;
            return (
              <div
                key={e.id}
                className={cn(
                  "flex items-center gap-3 px-4 py-3",
                  e.job_id && "border-l-2 border-white/[0.06] pl-3",
                )}
              >
                <span className={cn("grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-white/[0.05]", m.color)}>
                  <m.icon className="h-4 w-4" />
                </span>
                <div className="min-w-0 flex-1">
                  <div className="text-sm text-ink-high">{t(m.labelKey)}</div>
                  <div className="truncate text-xs text-ink-low">
                    {e.note ? e.note : e.created_at ? formatDate(e.created_at) : "—"}
                  </div>
                </div>
                <div className="whitespace-nowrap text-right">
                  <div className={cn("font-numeric text-xs font-semibold tabular sm:text-sm", deltaColor(e))}>
                    {e.delta_credits > 0 ? "+" : ""}
                    {e.delta_credits.toLocaleString("vi-VN")}
                  </div>
                  <div className="text-[11px] text-ink-disabled">
                    {t("balancePrefix")} <span className="font-numeric">{e.balance_after.toLocaleString("vi-VN")}</span>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </GlassCard>

      <p className="text-center text-xs text-ink-low">
        {t("ledgerFooter")}
      </p>
    </div>
  );
}
