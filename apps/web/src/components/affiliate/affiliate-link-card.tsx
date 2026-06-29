"use client";

import { useTranslations } from "next-intl";
import { Copy, Check, Trash2, ExternalLink } from "lucide-react";
import { ACCENTS } from "@/lib/accents";
import { cn } from "@/lib/utils/cn";
import type { AffiliateLink } from "@/lib/api/types";

const a = ACCENTS.amber;

export function AffiliateLinkCard({
  link,
  maxClicks,
  top,
  copied,
  onCopy,
  onDelete,
}: {
  link: AffiliateLink;
  maxClicks: number;
  top: boolean;
  copied: string | null;
  onCopy: (url: string) => void;
  onDelete: () => void;
}) {
  const t = useTranslations("affiliate");
  const l = link;
  return (
    <article
      className={cn(
        "group relative overflow-hidden rounded-2xl glass-bordered p-4 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-glow-sm hover:ring-1",
        a.ring,
      )}
    >
      {/* vạch số click theo tỉ lệ so với link top — nền mờ phía sau */}
      <div
        className="pointer-events-none absolute inset-y-0 left-0 bg-gradient-to-r from-amber-500/[0.07] to-transparent transition-all"
        style={{
          width:
            maxClicks > 0
              ? `${Math.max(8, (l.clicks / maxClicks) * 100)}%`
              : "0%",
        }}
      />
      <div className="relative flex items-center gap-4">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="truncate font-display text-sm font-semibold text-ink-high">
              {l.label || l.target_url}
            </span>
            {l.network && (
              <span className="rounded-md border border-white/10 bg-white/[0.04] px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-ink-low">
                {l.network}
              </span>
            )}
            {top && (
              <span
                className={cn(
                  "rounded-md border px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wide",
                  a.chip,
                )}
              >
                {t("topBadge")}
              </span>
            )}
          </div>

          <button
            onClick={() => onCopy(l.short_url)}
            className="mt-1.5 inline-flex max-w-full items-center gap-1.5 text-xs text-amber-200/90 transition hover:text-amber-100"
            aria-label={t("copyAria", { url: l.short_url })}
          >
            {copied === l.short_url ? (
              <Check className="h-3 w-3 shrink-0 text-success" />
            ) : (
              <Copy className="h-3 w-3 shrink-0" />
            )}
            <span className="truncate">{l.short_url}</span>
          </button>

          <div className="mt-1 flex items-center gap-1 text-[11px] text-ink-low">
            <ExternalLink className="h-3 w-3 shrink-0" />
            <span className="truncate">{l.target_url}</span>
          </div>
        </div>

        {/* số click — đậm, là tâm điểm thẻ */}
        <div className="shrink-0 text-right">
          <div className="font-numeric text-2xl font-bold tabular text-ink-high">
            {l.clicks.toLocaleString("vi-VN")}
          </div>
          <div className="text-[10px] uppercase tracking-wide text-ink-low">{t("clickLabel")}</div>
        </div>

        <button
          onClick={onDelete}
          className="grid h-8 w-8 shrink-0 place-items-center rounded-lg text-ink-low opacity-60 transition hover:bg-danger/10 hover:text-danger group-hover:opacity-100"
          aria-label={t("deleteAria")}
        >
          <Trash2 className="h-4 w-4" />
        </button>
      </div>
    </article>
  );
}
