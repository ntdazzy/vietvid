import { cn } from "@/lib/utils/cn";

export function MiniMoney({ label, value, sub, tone }: { label: string; value: string; sub?: string; tone?: "hold" }) {
  return (
    <div>
      <div className="text-[11px] uppercase tracking-wider text-ink-low">{label}</div>
      <div className={cn("mt-0.5 font-numeric text-sm font-semibold tabular", tone === "hold" ? "text-hold" : "text-ink-high")}>
        {value}
      </div>
      {sub && <div className="text-[10px] text-ink-low">{sub}</div>}
    </div>
  );
}
