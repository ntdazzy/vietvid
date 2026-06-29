"use client";

import { Coins, Lock } from "lucide-react";
import { useTranslations } from "next-intl";
import { useWallet } from "@/lib/query/hooks";
import { CreditValue } from "@/components/ui/credit-value";
import { Skeleton } from "@/components/ui/skeleton";

/** Số dư + "đang giữ" cạnh nhau (wedge minh bạch — mục F #2). */
export function CreditBadge() {
  const t = useTranslations("credit");
  const { data, isLoading, isError } = useWallet();

  if (isLoading) return <Skeleton className="h-9 w-32" />;
  if (isError || !data)
    return <span className="text-sm text-ink-low">{t("balance")}: …</span>;

  return (
    <div className="flex items-center gap-2">
      <div className="glass flex items-center gap-2 rounded-full px-3 py-1.5">
        <Coins className="h-4 w-4 text-violet-300" />
        <CreditValue value={data.balance_credits} suffix={null} className="text-sm text-ink-high" />
      </div>
      {data.held_credits > 0 && (
        <div className="flex items-center gap-1.5 rounded-full border border-hold/30 bg-hold/[0.12] px-3 py-1.5 text-hold">
          <Lock className="h-3.5 w-3.5" />
          <span className="text-xs">
            {t("held")}{" "}
            <CreditValue value={data.held_credits} suffix={null} className="text-xs" />
          </span>
        </div>
      )}
    </div>
  );
}
