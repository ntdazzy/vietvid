"use client";

import { motion } from "framer-motion";
import { ArrowRight, Volume2 } from "lucide-react";
import { ACCENTS, type Accent } from "@/lib/accents";
import { MiniReel } from "@/components/marketing/mini-reel";
import { cn } from "@/lib/utils/cn";
import type { FeaturePage } from "@/lib/feature-pages";

export function IoPanel({ io, accent }: { io: NonNullable<FeaturePage["io"]>; accent: Accent }) {
  const a = ACCENTS[accent];
  return (
    <div className="grid items-stretch gap-3 sm:grid-cols-[1fr_auto_1fr]">
      {/* INPUT */}
      <div className="flex flex-col gap-2.5 rounded-2xl glass-bordered p-4">
        <span className="text-xs text-ink-low">{io.inLabel}</span>
        {io.inKind === "thumbs" ? (
          <div className="flex gap-2">
            {(io.thumbs ?? []).map((t, i) => (
              <span key={i} className="aspect-[3/4] flex-1 overflow-hidden rounded-lg ring-1 ring-white/10">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={t} alt="" className="h-full w-full object-cover" />
              </span>
            ))}
          </div>
        ) : (
          <div className="min-h-[84px] rounded-lg bg-bg-base/40 p-3 text-sm leading-relaxed text-ink-medium">{io.inText}</div>
        )}
        {io.inKind === "ratios" && (
          <div className="flex gap-2">
            {(io.ratios ?? []).map((r) => (
              <span key={r} className={cn("rounded-md border px-2 py-1 font-numeric text-[11px]", a.chip)}>{r}</span>
            ))}
          </div>
        )}
      </div>

      {/* ARROW */}
      <div className="flex items-center justify-center">
        <span className={cn("grid h-10 w-10 rotate-90 place-items-center rounded-full bg-gradient-to-br ring-1 sm:rotate-0", a.tile, a.ring)}>
          <ArrowRight className={cn("h-5 w-5", a.icon)} />
        </span>
      </div>

      {/* OUTPUT */}
      <div className="flex flex-col gap-2.5 rounded-2xl glass-bordered p-4">
        <span className="text-xs text-ink-low">{io.outLabel}</span>
        {io.outKind === "video" && io.outVideo ? (
          <MiniReel poster={io.outImg ?? ""} video={io.outVideo} captions={[io.outLabel]} className="mx-auto w-full max-w-[170px] rounded-xl" />
        ) : io.outKind === "image" ? (
          <span className="mx-auto aspect-[9/16] w-full max-w-[170px] overflow-hidden rounded-xl ring-1 ring-white/10">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={io.outImg ?? ""} alt="" className="h-full w-full object-cover" />
          </span>
        ) : (
          <div className="flex flex-1 flex-col items-center justify-center gap-3 py-6">
            <div className="flex h-16 items-center gap-1">
              {Array.from({ length: 28 }).map((_, i) => (
                <motion.span
                  key={i}
                  className={cn("w-1 rounded-full", a.bar)}
                  animate={{ height: [6, 10 + (i % 7) * 5, 6] }}
                  transition={{ duration: 0.9 + (i % 5) * 0.15, repeat: Infinity, ease: "easeInOut", delay: i * 0.04 }}
                />
              ))}
            </div>
            <span className="flex items-center gap-1.5 text-xs text-ink-low">
              <Volume2 className={cn("h-3.5 w-3.5", a.icon)} /> Giọng Việt thật
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
