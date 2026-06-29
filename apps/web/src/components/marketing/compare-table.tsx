"use client";

import { Check } from "lucide-react";
import { useTranslations } from "next-intl";
import { Reveal } from "@/components/marketing/reveal";
import { SectionHeading } from "@/components/marketing/section-heading";
import { cn } from "@/lib/utils/cn";

// So sánh ĐỊNH TÍNH (không bịa số). Cột Vyra sáng.
const ROW_KEYS = ["voice", "captions", "winner", "time", "link"] as const;

export function CompareTable() {
  const t = useTranslations("home");
  const ROWS: [string, string, string, string][] = ROW_KEYS.map((k) => [
    t(`compareRow_${k}_crit`),
    t(`compareRow_${k}_a`),
    t(`compareRow_${k}_b`),
    t(`compareRow_${k}_vyra`),
  ]);
  return (
    <div className="mx-auto max-w-5xl px-4">
      <SectionHeading
        align="center"
        eyebrow={t("compareEyebrow")}
        title={t.rich("compareTitle", { grad: (c) => <span className="text-gradient">{c}</span> })}
      />
      <Reveal className="mt-10 overflow-x-auto">
        <table className="w-full min-w-[640px] border-separate border-spacing-0 text-sm">
          <thead>
            <tr className="text-left">
              <th className="p-3 font-medium text-ink-low">{t("compareColCrit")}</th>
              <th className="p-3 font-medium text-ink-low">{t("compareColAgency")}</th>
              <th className="p-3 font-medium text-ink-low">{t("compareColForeign")}</th>
              <th className="rounded-t-xl bg-violet-500/[0.08] p-3 font-bold text-ink-high ring-1 ring-violet-400/20">
                Vyra
              </th>
            </tr>
          </thead>
          <tbody>
            {ROWS.map(([crit, a, b, v], i) => (
              <tr key={crit}>
                <td className="border-t border-white/[0.06] p-3 font-medium text-ink-medium">{crit}</td>
                <td className="border-t border-white/[0.06] p-3 text-ink-low">{a}</td>
                <td className="border-t border-white/[0.06] p-3 text-ink-low">{b}</td>
                <td className={cn(
                  "border-t border-violet-400/20 bg-violet-500/[0.06] p-3 font-semibold text-ink-high",
                  i === ROWS.length - 1 && "rounded-b-xl",
                )}>
                  <span className="inline-flex items-center gap-1.5">
                    <Check className="h-4 w-4 text-success" /> {v}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Reveal>
    </div>
  );
}
