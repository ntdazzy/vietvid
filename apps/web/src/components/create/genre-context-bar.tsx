"use client";

import { RefreshCw } from "lucide-react";
import { ACCENTS, type Accent } from "@/lib/accents";
import { FilmLabel } from "@/components/ui/cinematic";
import { cn } from "@/lib/utils/cn";

/** Banner ngữ cảnh thể loại ở đầu configurator — ảnh + accent riêng → flow "có gốc", không
 *  còn là form generic. Mọi chuỗi hiển thị truyền từ ngoài (i18n-agnostic). */
export function GenreContextBar({
  image,
  label,
  title,
  sub,
  accent,
  changeLabel,
  onChange,
}: {
  image: string;
  label: string;
  title: string;
  sub: string;
  accent: Accent;
  changeLabel: string;
  onChange: () => void;
}) {
  const a = ACCENTS[accent];
  return (
    <div className="relative overflow-hidden rounded-2xl glass-bordered">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={image} alt="" className="absolute inset-0 h-full w-full object-cover opacity-[0.16]" />
      <div className="absolute inset-0 bg-gradient-to-r from-bg-surface via-bg-surface/85 to-bg-surface/45" />
      <div className="pointer-events-none absolute -left-10 -top-14 h-44 w-44 rounded-full blur-3xl" style={{ background: a.glow }} />
      <div className="relative flex items-center gap-4 p-3.5 sm:p-4">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={image} alt="" className={cn("h-14 w-14 shrink-0 rounded-xl object-cover ring-2", a.ring)} />
        <div className="min-w-0">
          <FilmLabel dot={false} className={a.text}>{label}</FilmLabel>
          <div className="mt-0.5 truncate font-display text-base font-semibold text-ink-high">{title}</div>
          <div className="truncate text-xs text-ink-low">{sub}</div>
        </div>
        <button
          type="button"
          onClick={onChange}
          className="ml-auto inline-flex shrink-0 items-center gap-1.5 rounded-full border border-white/12 px-3 py-1.5 text-xs text-ink-medium transition-colors hover:border-white/25 hover:text-ink-high"
        >
          <RefreshCw className="h-3 w-3" /> {changeLabel}
        </button>
      </div>
    </div>
  );
}
