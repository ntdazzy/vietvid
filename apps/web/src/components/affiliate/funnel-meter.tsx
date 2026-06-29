"use client";

import { useTranslations } from "next-intl";
import { MousePointerClick, ArrowDown, ShoppingBag } from "lucide-react";

/** Phễu 2 tầng: tổng click ở miệng phễu → số link đang đổ về sàn. Số THẬT từ stats. */
export function FunnelMeter({
  clicks,
  links,
  loading,
}: {
  clicks: number;
  links: number;
  loading: boolean;
}) {
  const t = useTranslations("affiliate");
  return (
    <div className="rounded-2xl border border-white/[0.07] bg-bg-base/40 p-5 backdrop-blur-sm">
      {/* tầng 1 — click vào video */}
      <div className="flex items-center gap-3 rounded-xl border border-amber-400/20 bg-gradient-to-br from-amber-500/[0.12] to-orange-500/[0.04] p-4">
        <span className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-amber-500/15 ring-1 ring-amber-400/25">
          <MousePointerClick className="h-5 w-5 text-amber-200" />
        </span>
        <div className="min-w-0">
          <div className="text-xs uppercase tracking-wide text-ink-low">{t("funnelClicks")}</div>
          <div className="font-numeric text-3xl font-bold tabular leading-tight text-ink-high">
            {loading ? (
              <span className="inline-block h-8 w-20 animate-pulse rounded bg-white/[0.08]" />
            ) : (
              clicks.toLocaleString("vi-VN")
            )}
          </div>
        </div>
      </div>

      {/* mũi tên phễu */}
      <div className="flex justify-center py-1.5" aria-hidden>
        <ArrowDown className="h-4 w-4 text-amber-300/70" />
      </div>

      {/* tầng 2 — link đổ về sàn */}
      <div className="flex items-center gap-3 rounded-xl border border-white/[0.07] bg-white/[0.02] p-4">
        <span className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-white/[0.04] ring-1 ring-white/10">
          <ShoppingBag className="h-5 w-5 text-ink-medium" />
        </span>
        <div className="min-w-0">
          <div className="text-xs uppercase tracking-wide text-ink-low">{t("funnelLinks")}</div>
          <div className="font-numeric text-3xl font-bold tabular leading-tight text-ink-high">
            {loading ? (
              <span className="inline-block h-8 w-16 animate-pulse rounded bg-white/[0.08]" />
            ) : (
              links.toLocaleString("vi-VN")
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
