import { Activity } from "lucide-react";
import { useTranslations } from "next-intl";
import { cn } from "@/lib/utils/cn";

export const DOW_KEYS = ["dowSun", "dowMon", "dowTue", "dowWed", "dowThu", "dowFri", "dowSat"] as const;

export function ActivityChart({
  days,
  maxDay,
  t,
}: {
  days: { d: Date; count: number }[];
  maxDay: number;
  t: ReturnType<typeof useTranslations>;
}) {
  return (
    <>
      <div className="mb-5 flex items-center justify-between">
        <span className="flex items-center gap-2 text-sm font-medium text-ink-medium">
          <Activity className="h-4 w-4 text-emerald-300" /> {t("rhythm14d")}
        </span>
        <span className="font-numeric text-xs text-ink-low">{t("peakPerDay", { max: maxDay })}</span>
      </div>
      <div className="flex h-40 items-end gap-1.5 sm:gap-2">
        {days.map((b, i) => {
          const isToday = i === days.length - 1;
          return (
            <div key={i} className="group flex flex-1 flex-col items-center gap-1.5" title={t("barTitle", { count: b.count })}>
              <span className="font-numeric text-[10px] text-ink-disabled opacity-0 transition group-hover:opacity-100">
                {b.count}
              </span>
              <div className="flex w-full flex-1 items-end">
                <div
                  className={cn(
                    "w-full rounded-t-md transition-all duration-300",
                    isToday
                      ? "bg-gradient-to-t from-emerald-400/60 to-emerald-300 shadow-[0_0_12px_rgba(16,185,129,0.35)]"
                      : "bg-gradient-to-t from-emerald-500/25 to-emerald-400/70 group-hover:from-emerald-500/45 group-hover:to-emerald-300",
                  )}
                  style={{ height: `${Math.max(4, (b.count / maxDay) * 100)}%` }}
                />
              </div>
              <span className={cn("text-[9px]", isToday ? "text-emerald-300" : "text-ink-disabled")}>
                {t(DOW_KEYS[b.d.getDay()])}
              </span>
            </div>
          );
        })}
      </div>
    </>
  );
}
