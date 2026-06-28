"use client";

import { useRef } from "react";
import type { FeaturePage } from "@/lib/feature-pages";
import { ACCENTS } from "@/lib/accents";
import { SectionHeading } from "@/components/marketing/section-heading";
import { Reveal } from "@/components/marketing/reveal";
import { cn } from "@/lib/utils/cn";

const RATIO_CLS: Record<string, string> = { "9:16": "aspect-[9/16]", "1:1": "aspect-square", "16:9": "aspect-video" };

function ResultTile({ r, accent }: { r: NonNullable<FeaturePage["results"]>[number]; accent: keyof typeof ACCENTS }) {
  const a = ACCENTS[accent];
  const vref = useRef<HTMLVideoElement>(null);
  return (
    <div
      className={cn("group relative overflow-hidden rounded-2xl glass-bordered", RATIO_CLS[r.ratio] ?? RATIO_CLS["9:16"])}
      onMouseEnter={() => vref.current?.play().catch(() => {})}
      onMouseLeave={() => { if (vref.current) { vref.current.pause(); vref.current.currentTime = 0; } }}
    >
      {r.video ? (
        <video ref={vref} poster={r.img} src={r.video} muted loop playsInline preload="none" className="h-full w-full object-cover" />
      ) : (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={r.img} alt={r.caption} className="h-full w-full object-cover transition-transform duration-700 group-hover:scale-105" />
      )}
      <div className="absolute inset-0 bg-gradient-to-t from-black/75 via-transparent to-transparent" />
      <span className={cn("absolute right-2 top-2 rounded-md border bg-black/40 px-1.5 py-0.5 font-numeric text-[10px]", a.chip)}>{r.ratio}</span>
      <span className="absolute inset-x-3 bottom-2 text-xs font-medium text-white/95">{r.caption}</span>
    </div>
  );
}

export function ResultsShowcase({ page }: { page: FeaturePage }) {
  const a = ACCENTS[page.accent];
  const results = page.results ?? [];
  const isKol = page.heroVariant === "kol";
  if (!results.length && !isKol) return null;

  return (
    <section className="mx-auto max-w-6xl px-4 py-16">
      <SectionHeading align="center" eyebrow="Mẫu output thật" title={<>Kết quả từ engine Vyra</>} sub="Bản dựng minh hoạ, chưa qua chỉnh sửa. Di chuột để xem clip chạy." />

      <div className="mt-10 grid gap-4 sm:grid-cols-3">
        {results.map((r, i) => (
          <Reveal key={r.caption} delay={0.06 * i}>
            <ResultTile r={r} accent={page.accent} />
          </Reveal>
        ))}
      </div>

      {/* dải gương mặt KOL — bằng chứng "một gương mặt, nhiều cảnh" */}
      {isKol && (page.kols?.length ?? 0) > 0 && (
        <Reveal delay={0.2}>
          <div className="mt-6 flex flex-col gap-3 rounded-2xl glass p-4 sm:flex-row sm:items-center">
            <div className="flex -space-x-3">
              {(page.kols ?? []).map((k) => (
                <span key={k.name} className={cn("h-12 w-12 overflow-hidden rounded-full ring-2", a.ring)}>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={k.img} alt={k.name} className="h-full w-full object-cover" />
                </span>
              ))}
            </div>
            <div>
              <div className="font-display text-sm font-semibold text-ink-high">Một gương mặt — giữ nhất quán qua mọi clip</div>
              <div className="text-xs text-ink-low">Không lệch mặt, không lệch outfit giữa các cảnh.</div>
            </div>
          </div>
        </Reveal>
      )}
    </section>
  );
}
