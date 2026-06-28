"use client";

import Link from "next/link";
import { ArrowRight, Check } from "lucide-react";
import type { FeaturePage } from "@/lib/feature-pages";
import { ACCENTS } from "@/lib/accents";
import { Button } from "@/components/ui/button";
import { MiniReel } from "@/components/marketing/mini-reel";
import { Reveal } from "@/components/marketing/reveal";
import { IoPanel } from "./io-panel";
import { cn } from "@/lib/utils/cn";

export function FeatureHero({ page }: { page: FeaturePage }) {
  const a = ACCENTS[page.accent];
  const [titleA, titleB] = page.title.split("|");
  const reelCaptions = ["Mẫu dựng từ engine Vyra", "Giọng Việt thật, phụ đề khớp", "Sẵn đăng trong ~60 giây"];

  return (
    <section className="relative isolate overflow-hidden pt-32 pb-16">
      <div
        className="pointer-events-none absolute right-[6%] top-[2%] h-[440px] w-[540px]"
        style={{ background: `radial-gradient(50% 50% at 50% 50%, ${a.glow}, transparent 70%)` }}
      />
      <div className="mx-auto grid max-w-6xl items-center gap-10 px-4 lg:grid-cols-[1.05fr_0.95fr]">
        {/* LEFT */}
        <Reveal>
          {page.badge && (
            <span className={cn("inline-flex items-center rounded-full border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide", a.chip)}>
              {page.badge}
            </span>
          )}
          <p className={cn("mt-3 text-xs font-semibold uppercase tracking-[0.18em]", a.text)}>{page.eyebrow}</p>
          <h1 className="mt-3 font-display text-[clamp(2.2rem,5vw,3.75rem)] font-bold leading-[1.02] tracking-[-0.035em] text-ink-high">
            {titleA}
            {titleB && (
              <>
                <br />
                <span className={cn("bg-gradient-to-r bg-clip-text text-transparent", a.grad)}>{titleB}</span>
              </>
            )}
          </h1>
          <p className="mt-5 max-w-md text-lg leading-relaxed text-ink-medium">{page.sub}</p>
          <ul className="mt-6 flex flex-col gap-2.5">
            {page.bullets.map((b) => (
              <li key={b} className="flex items-start gap-2.5 text-ink-medium">
                <Check className="mt-0.5 h-4 w-4 shrink-0 text-success" /> {b}
              </li>
            ))}
          </ul>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link href={page.ctaHref}>
              <Button size="lg" className="gap-2">{page.ctaLabel} <ArrowRight className="h-4 w-4" /></Button>
            </Link>
            <Link href="/#nang-luc">
              <Button variant="glass" size="lg">Xem tất cả năng lực</Button>
            </Link>
          </div>
        </Reveal>

        {/* RIGHT — đổi hình học theo heroVariant */}
        <Reveal delay={0.12} className="flex justify-center lg:justify-end">
          {page.heroVariant === "kol" && page.kols?.length ? (
            <div className="relative w-full max-w-[320px]">
              <div className={cn("relative aspect-[3/4] overflow-hidden rounded-[24px] glass-bordered ring-2", a.ring)}>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={page.kols[0].img} alt={page.kols[0].name} className="h-full w-full object-cover" />
                <div className="absolute inset-0 bg-gradient-to-t from-bg-base/70 to-transparent" />
                <span className="absolute bottom-3 left-3 rounded-md bg-bg-base/70 px-2 py-1 text-[11px] font-medium text-ink-high backdrop-blur-sm">
                  Gương mặt AI · giữ nhất quán
                </span>
              </div>
              <div className="absolute -bottom-6 -right-3 w-[120px] sm:w-[130px]">
                <MiniReel poster={`/samples/${page.heroSample}.png`} video={`/samples/${page.heroSample}.mp4`} captions={reelCaptions} className="w-full rounded-[16px]" />
              </div>
            </div>
          ) : page.heroVariant === "transform" && page.beforeAfter ? (
            <div className="flex w-full max-w-[360px] items-center gap-2">
              <div className="flex-1">
                <div className="relative aspect-[9/16] overflow-hidden rounded-2xl glass-bordered">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={page.beforeAfter.before} alt="" className="h-full w-full object-cover opacity-90 grayscale" />
                </div>
                <p className="mt-1.5 text-center text-[11px] text-ink-low">Ảnh sản phẩm</p>
              </div>
              <span className={cn("grid h-9 w-9 shrink-0 place-items-center rounded-full bg-gradient-to-br ring-1", a.tile, a.ring)}>
                <ArrowRight className={cn("h-4 w-4", a.icon)} />
              </span>
              <div className="flex-1">
                <MiniReel poster={page.beforeAfter.after} video={page.beforeAfter.afterVideo} captions={reelCaptions} className="w-full rounded-2xl" />
                <p className="mt-1.5 text-center text-[11px] text-ink-medium">Video 60s</p>
              </div>
            </div>
          ) : page.io ? (
            <div className="w-full max-w-[420px]">
              <IoPanel io={page.io} accent={page.accent} />
            </div>
          ) : (
            <MiniReel poster={`/samples/${page.heroSample}.png`} video={`/samples/${page.heroSample}.mp4`} captions={reelCaptions} className="w-full max-w-[300px]" />
          )}
        </Reveal>
      </div>
    </section>
  );
}
