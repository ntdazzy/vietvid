"use client";

import {
  Plus, Gift, Lock, Check, RotateCcw, ArrowDownToLine, Loader2, Receipt, type LucideIcon,
} from "lucide-react";
import type { LedgerEntry, LedgerKind } from "@/lib/api/types";
import { GlassCard } from "@/components/ui/glass-card";
import { formatDate } from "@/lib/job-status";
import { cn } from "@/lib/utils/cn";

const META: Record<LedgerKind, { label: string; icon: LucideIcon; color: string }> = {
  TOPUP: { label: "Nạp credit", icon: ArrowDownToLine, color: "text-success" },
  BONUS: { label: "Tặng", icon: Gift, color: "text-violet-300" },
  HOLD: { label: "Tạm giữ", icon: Lock, color: "text-hold" },
  SETTLE: { label: "Quyết toán", icon: Check, color: "text-ink-medium" },
  REFUND: { label: "Hoàn lại", icon: RotateCcw, color: "text-refund" },
  ADJUST: { label: "Điều chỉnh", icon: Plus, color: "text-ink-medium" },
  EXPIRE: { label: "Hết hạn", icon: RotateCcw, color: "text-ink-low" },
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
  const all = entries ?? [];
  const kinds = Array.from(new Set(all.map((e) => e.entry_type)));
  const rows = filter === "ALL" ? all : all.filter((e) => e.entry_type === filter);

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-baseline justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-ink-low">Sổ cái minh bạch</h2>
        {all.length > 0 && (
          <span className="text-xs text-ink-low">{all.length} giao dịch gần đây</span>
        )}
      </div>

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
                  "rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors",
                  active
                    ? "border-violet-400/40 bg-violet-500/20 text-ink-high"
                    : "border-white/10 text-ink-low hover:text-ink-medium",
                )}
              >
                {k === "ALL" ? "Tất cả" : META[k].label}
              </button>
            );
          })}
        </div>
      )}

      <GlassCard className="divide-y divide-white/[0.05] p-0">
        {isLoading ? (
          <div className="flex items-center gap-2 p-5 text-ink-low">
            <Loader2 className="h-4 w-4 animate-spin" /> Đang tải…
          </div>
        ) : all.length === 0 ? (
          <div className="flex flex-col items-center gap-3 py-14 text-center">
            <div className="grid h-12 w-12 place-items-center rounded-2xl bg-white/[0.04]">
              <Receipt className="h-5 w-5 text-ink-low" />
            </div>
            <p className="max-w-xs text-sm text-ink-low">
              Chưa có giao dịch nào. Mọi lần nạp, giữ, dùng, hoàn sẽ xuất hiện ở đây.
            </p>
          </div>
        ) : rows.length === 0 ? (
          <p className="p-6 text-center text-sm text-ink-low">Không có giao dịch loại này.</p>
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
                  <div className="text-sm text-ink-high">{m.label}</div>
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
                    dư <span className="font-numeric">{e.balance_after.toLocaleString("vi-VN")}</span>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </GlassCard>

      <p className="text-center text-xs text-ink-low">
        Mọi lần giữ, dùng, hoàn đều ghi lại. Không bao giờ trừ tiền âm thầm.
      </p>
    </div>
  );
}
