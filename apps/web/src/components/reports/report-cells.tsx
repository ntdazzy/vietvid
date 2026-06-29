import { Film } from "lucide-react";
import { cn } from "@/lib/utils/cn";

export function FlowLegend({ color, label, value, sub }: { color: string; label: string; value: number; sub: string }) {
  return (
    <div>
      <div className="flex items-center gap-1.5 text-xs text-ink-low">
        <span className={cn("h-2.5 w-2.5 rounded-sm", color)} /> {label}
      </div>
      <div className="mt-1 font-numeric text-lg font-semibold tabular text-ink-high">{value.toLocaleString("vi-VN")}</div>
      <div className="font-numeric text-[11px] text-ink-disabled">{sub}</div>
    </div>
  );
}

export function MetricCell({
  icon: Icon,
  accent,
  label,
  value,
  hint,
}: {
  icon: typeof Film;
  accent: string;
  label: string;
  value: number;
  hint?: string;
}) {
  return (
    <div className="px-4 first:pl-0 last:pr-0">
      <div className="flex items-center gap-1.5 text-xs text-ink-low">
        <Icon className={cn("h-3.5 w-3.5", accent)} /> {label}
      </div>
      <div className="mt-1.5 font-numeric text-2xl font-bold tabular text-ink-high">{value.toLocaleString("vi-VN")}</div>
      {hint && <div className="mt-0.5 text-xs text-ink-low">{hint}</div>}
    </div>
  );
}

export function AffiliateRow({ icon: Icon, label, value }: { icon: typeof Film; label: string; value: number }) {
  return (
    <div className="flex items-center justify-between rounded-xl border border-white/[0.05] bg-white/[0.02] px-4 py-3">
      <span className="flex items-center gap-2 text-sm text-ink-medium">
        <Icon className="h-4 w-4 text-amber-300" /> {label}
      </span>
      <span className="font-numeric text-lg font-semibold tabular text-ink-high">{value.toLocaleString("vi-VN")}</span>
    </div>
  );
}
