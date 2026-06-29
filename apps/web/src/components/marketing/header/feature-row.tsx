"use client";

import Link from "next/link";
import { type Feature } from "@/lib/features";
import { cn } from "@/lib/utils/cn";

export function FeatureRow({ f, onNav }: { f: Feature; onNav?: () => void }) {
  const inner = (
    <div
      className={cn(
        "group relative flex items-start gap-3 rounded-xl p-2.5 transition-all duration-200",
        f.available
          ? "hover:translate-x-0.5 hover:bg-violet-500/[0.07]"
          : "cursor-default opacity-55",
      )}
    >
      {/* thanh accent trái trượt vào khi hover (available) */}
      {f.available && (
        <span className="absolute left-0 top-1/2 h-0 w-[3px] -translate-y-1/2 rounded-full bg-violet-400 transition-all duration-200 group-hover:h-7" />
      )}
      <span
        className={cn(
          "mt-0.5 grid h-9 w-9 shrink-0 place-items-center rounded-xl transition-colors",
          f.available
            ? "bg-violet-500/[0.12] text-violet-300 group-hover:bg-violet-500/20"
            : "bg-white/[0.04] text-ink-low",
        )}
      >
        <f.icon className="h-[18px] w-[18px]" />
      </span>
      <div className="min-w-0 py-0.5">
        <div className="flex items-center gap-1.5">
          <span className="text-sm font-medium text-ink-high">{f.label}</span>
          {f.badge && (
            <span
              className={cn(
                "rounded px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wide",
                f.badge === "Sắp có"
                  ? "bg-white/[0.06] text-ink-low"
                  : "bg-violet-500/20 text-violet-200",
              )}
            >
              {f.badge}
            </span>
          )}
        </div>
        <div className="mt-0.5 text-xs leading-snug text-ink-low">{f.desc}</div>
      </div>
    </div>
  );
  if (!f.available) return inner;
  return (
    <Link href={f.href} onClick={onNav} className="rounded-xl outline-none focus-visible:ring-2 focus-visible:ring-violet-400/60">
      {inner}
    </Link>
  );
}
