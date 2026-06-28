"use client";

import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";
import { ACCENTS, type Accent } from "@/lib/accents";
import { cn } from "@/lib/utils/cn";

export { ACCENTS };
export type { Accent };

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
