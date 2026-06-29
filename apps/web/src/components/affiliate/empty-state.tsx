"use client";

import { useTranslations } from "next-intl";
import { Link2 } from "lucide-react";

/** Empty state — vẫn glass, có gợi ý hành động, không vô hồn. */
export function EmptyState() {
  const t = useTranslations("affiliate");
  return (
    <div className="flex flex-col items-center gap-3 rounded-2xl glass-bordered px-6 py-14 text-center">
      <span className="grid h-12 w-12 place-items-center rounded-xl bg-amber-500/10 ring-1 ring-amber-400/20">
        <Link2 className="h-6 w-6 text-amber-200" />
      </span>
      <div>
        <p className="font-display font-semibold text-ink-high">{t("emptyTitle")}</p>
        <p className="mt-1 text-sm text-ink-low">
          {t("emptyDesc")}
        </p>
      </div>
    </div>
  );
}
