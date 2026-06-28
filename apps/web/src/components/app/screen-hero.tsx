"use client";

import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils/cn";

// Mỗi màn 1 accent riêng → nhìn lướt là biết màn nào, không "y chang nhau".
// Giữ nền dark + glass chung (đồng bộ brand); accent chỉ tô icon-tile + glow + chi tiết.
export type Accent = "violet" | "emerald" | "amber" | "sky" | "rose" | "cyan" | "slate";

export const ACCENTS: Record<Accent, { tile: string; icon: string; glow: string; ring: string; line: string; chip: string }> = {
  violet: { tile: "from-violet-500/30 to-indigo-500/10", icon: "text-violet-200", glow: "rgba(124,77,255,0.20)", ring: "ring-violet-400/25", line: "via-violet-500/60", chip: "bg-violet-500/15 text-violet-200 border-violet-400/30" },
  emerald: { tile: "from-emerald-500/30 to-teal-500/10", icon: "text-emerald-200", glow: "rgba(16,185,129,0.18)", ring: "ring-emerald-400/25", line: "via-emerald-500/60", chip: "bg-emerald-500/15 text-emerald-200 border-emerald-400/30" },
  amber: { tile: "from-amber-500/30 to-orange-500/10", icon: "text-amber-200", glow: "rgba(245,158,11,0.18)", ring: "ring-amber-400/25", line: "via-amber-500/60", chip: "bg-amber-500/15 text-amber-200 border-amber-400/30" },
  sky: { tile: "from-sky-500/30 to-blue-500/10", icon: "text-sky-200", glow: "rgba(56,189,248,0.18)", ring: "ring-sky-400/25", line: "via-sky-500/60", chip: "bg-sky-500/15 text-sky-200 border-sky-400/30" },
  rose: { tile: "from-rose-500/30 to-pink-500/10", icon: "text-rose-200", glow: "rgba(244,63,94,0.18)", ring: "ring-rose-400/25", line: "via-rose-500/60", chip: "bg-rose-500/15 text-rose-200 border-rose-400/30" },
  cyan: { tile: "from-cyan-500/30 to-teal-500/10", icon: "text-cyan-200", glow: "rgba(34,211,238,0.18)", ring: "ring-cyan-400/25", line: "via-cyan-500/60", chip: "bg-cyan-500/15 text-cyan-200 border-cyan-400/30" },
  slate: { tile: "from-slate-400/25 to-slate-500/10", icon: "text-slate-200", glow: "rgba(148,163,184,0.16)", ring: "ring-slate-300/20", line: "via-slate-400/60", chip: "bg-slate-400/15 text-slate-200 border-slate-300/25" },
};

/** Hero đầu màn — icon-tile accent + tiêu đề + (tuỳ chọn) hành động + slot số liệu. */
export function ScreenHero({
  icon: Icon,
  title,
  sub,
  accent = "violet",
  action,
  children,
}: {
  icon: LucideIcon;
  title: string;
  sub?: string;
  accent?: Accent;
  action?: ReactNode;
  children?: ReactNode;
}) {
  const a = ACCENTS[accent];
  return (
    <div className="relative overflow-hidden rounded-2xl glass-bordered p-5 sm:p-6">
      <div
        className="pointer-events-none absolute inset-x-0 -top-16 h-36"
        style={{ background: `radial-gradient(55% 100% at 35% 0%, ${a.glow}, transparent 72%)` }}
      />
      <div className="relative flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <span className={cn("grid h-12 w-12 shrink-0 place-items-center rounded-xl bg-gradient-to-br ring-1", a.tile, a.ring)}>
            <Icon className={cn("h-6 w-6", a.icon)} />
          </span>
          <div className="min-w-0">
            <h1 className="font-display text-2xl font-bold text-ink-high lg:text-[30px]">{title}</h1>
            {sub && <p className="mt-0.5 text-sm text-ink-low">{sub}</p>}
          </div>
        </div>
        {action && <div className="shrink-0">{action}</div>}
      </div>
      {children && <div className="relative mt-5">{children}</div>}
    </div>
  );
}

/** Ô số liệu dùng trong hero hoặc lưới — số dùng font-numeric. */
export function StatTile({
  icon: Icon,
  label,
  value,
  hint,
  accent,
  loading,
}: {
  icon?: LucideIcon;
  label: string;
  value: ReactNode;
  hint?: string;
  accent?: Accent;
  loading?: boolean;
}) {
  const a = accent ? ACCENTS[accent] : null;
  return (
    <div className="rounded-xl border border-white/[0.05] bg-white/[0.02] p-4">
      <div className="flex items-center gap-1.5 text-xs text-ink-low">
        {Icon && <Icon className={cn("h-3.5 w-3.5", a?.icon ?? "text-ink-low")} />} {label}
      </div>
      <div className="mt-1.5 font-numeric text-2xl font-bold tabular text-ink-high">
        {loading ? <span className="inline-block h-7 w-16 animate-pulse rounded bg-white/[0.06]" /> : value}
      </div>
      {hint && <div className="mt-0.5 text-xs text-ink-low">{hint}</div>}
    </div>
  );
}
