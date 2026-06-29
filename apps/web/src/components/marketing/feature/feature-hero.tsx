"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { ArrowRight, Check } from "lucide-react";
import type { FeaturePage } from "@/lib/feature-pages";
import { ACCENTS } from "@/lib/accents";
import { Button } from "@/components/ui/button";
import { MiniReel } from "@/components/marketing/mini-reel";
import { Reveal } from "@/components/marketing/reveal";
import { FilmLabel } from "@/components/ui/cinematic";
import { IoPanel } from "./io-panel";
import { cn } from "@/lib/utils/cn";

function useReelCaptions() {
  const t = useTranslations("feature");
  return [t("reelCaption1"), t("reelCaption2"), t("reelCaption3")];
}

/**
 * Hero của feature — KHÔNG còn một khung chung. Mỗi heroVariant là MỘT bố cục riêng:
 *  - kol       → "phòng casting": cột chữ + dải gương mặt + portrait lớn + reel nổi (bất đối xứng)
 *  - transform → "băng điện ảnh" full-bleed: nền media + scrim, diptych trước→sau đè đáy
 *  - tool      → "bảng điều khiển": chữ trái + console I/O có thanh tiêu đề bên phải
 */
export function FeatureHero({ page }: { page: FeaturePage }) {
  if (page.heroVariant === "transform" && page.beforeAfter) return <TransformHero page={page} />;
  if (page.heroVariant === "tool" && page.io) return <ToolHero page={page} />;
  return <KolHero page={page} />;
}

/* ── shared copy block ───────────────────────────────────────────── */
function HeadCopy({ page, compact = false }: { page: FeaturePage; compact?: boolean }) {
  const a = ACCENTS[page.accent];
  const [titleA, titleB] = page.title.split("|");
  return (
    <>
      <div className="flex flex-wrap items-center gap-3">
        <FilmLabel>{page.eyebrow}</FilmLabel>
        {page.badge && (
          <span className={cn("rounded-full border px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wide", a.chip)}>
            {page.badge}
          </span>
        )}
      </div>
      <h1
        className={cn(
          "mt-4 font-display font-bold leading-[1.02] tracking-[-0.035em] text-ink-high",
          compact ? "text-[clamp(2rem,4.2vw,3.1rem)]" : "text-[clamp(2.2rem,5vw,3.75rem)]",
        )}
      >
        {titleA}
        {titleB && (
          <>
            <br />
            <span className={cn("bg-gradient-to-r bg-clip-text text-transparent", a.grad)}>{titleB}</span>
          </>
        )}
      </h1>
      <p className="mt-5 max-w-md text-lg leading-relaxed text-ink-medium">{page.sub}</p>
    </>
  );
}

function Bullets({ page }: { page: FeaturePage }) {
  return (
    <ul className="mt-6 flex flex-col gap-2.5">
      {page.bullets.map((b) => (
        <li key={b} className="flex items-start gap-2.5 text-ink-medium">
          <Check className="mt-0.5 h-4 w-4 shrink-0 text-success" /> {b}
        </li>
      ))}
    </ul>
  );
}

function CtaRow({ page }: { page: FeaturePage }) {
  const t = useTranslations("feature");
  return (
    <div className="mt-8 flex flex-wrap gap-3">
      <Link href={page.ctaHref}>
        <Button size="lg" className="gap-2">
          {page.ctaLabel} <ArrowRight className="h-4 w-4" />
        </Button>
      </Link>
      <Link href="/#nang-luc">
        <Button variant="glass" size="lg">
          {t("seeAllCapabilities")}
        </Button>
      </Link>
    </div>
  );
}

/* ── KOL: phòng casting (bất đối xứng) ───────────────────────────── */
function KolHero({ page }: { page: FeaturePage }) {
  const t = useTranslations("feature");
  const reelCaptions = useReelCaptions();
  const a = ACCENTS[page.accent];
  const kols = page.kols ?? [];
  const lead = kols[0];
  const rest = kols.slice(1);

  return (
    <section className="relative isolate overflow-hidden pt-32 pb-16">
      <div
        className="pointer-events-none absolute right-[4%] top-[6%] h-[460px] w-[520px]"
        style={{ background: `radial-gradient(50% 50% at 50% 50%, ${a.glow}, transparent 70%)` }}
      />
      <div className="mx-auto grid max-w-6xl items-center gap-10 px-4 lg:grid-cols-[1fr_0.92fr]">
        <Reveal>
          <HeadCopy page={page} />
          <Bullets page={page} />
          <CtaRow page={page} />
        </Reveal>

        {/* phòng casting: portrait lớn + cột mặt phụ + reel nổi góc */}
        <Reveal delay={0.12}>
          {lead ? (
            <div className="relative mx-auto w-full max-w-[400px]">
              <div className="grid grid-cols-[1.6fr_1fr] gap-3">
                <div className={cn("relative aspect-[3/4] overflow-hidden rounded-[24px] glass-bordered ring-2", a.ring)}>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={lead.img} alt={lead.name} className="h-full w-full object-cover" />
                  <div className="absolute inset-0 bg-gradient-to-t from-bg-base/75 to-transparent" />
                  <div className="absolute inset-x-3 bottom-3">
                    <div className="font-display text-sm font-semibold text-white">{lead.name}</div>
                    <div className="text-[11px] text-white/70">{lead.industry} · {t("aiFace")}</div>
                  </div>
                </div>
                <div className="flex flex-col gap-3">
                  {rest.map((k) => (
                    <div key={k.name} className={cn("relative aspect-[3/4] flex-1 overflow-hidden rounded-2xl glass-bordered ring-1", a.ring)}>
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img src={k.img} alt={k.name} className="h-full w-full object-cover" />
                      <div className="absolute inset-0 bg-gradient-to-t from-bg-base/70 to-transparent" />
                      <span className="absolute inset-x-2 bottom-2 text-[11px] font-medium text-white/90">{k.name}</span>
                    </div>
                  ))}
                  {rest.length === 0 && (
                    <div className="grid flex-1 place-items-center rounded-2xl glass-bordered p-3 text-center text-[11px] leading-snug text-ink-low">
                      {t("oneFaceConsistent")}
                    </div>
                  )}
                </div>
              </div>
              <div className="absolute -bottom-6 -left-4 w-[118px] sm:w-[128px]">
                <MiniReel
                  poster={`/samples/${page.heroSample}.jpg`}
                  video={`/samples/${page.heroSample}.mp4`}
                  captions={reelCaptions}
                  className="w-full rounded-[16px] shadow-glow-sm"
                />
              </div>
            </div>
          ) : (
            <MiniReel poster={`/samples/${page.heroSample}.jpg`} video={`/samples/${page.heroSample}.mp4`} captions={reelCaptions} className="mx-auto w-full max-w-[300px]" />
          )}
        </Reveal>
      </div>
    </section>
  );
}

/* ── TRANSFORM: băng điện ảnh full-bleed, diptych trước→sau ───────── */
function TransformHero({ page }: { page: FeaturePage }) {
  const reelCaptions = useReelCaptions();
  const a = ACCENTS[page.accent];
  const b = page.beforeAfter!;

  return (
    <section className="relative isolate overflow-hidden pt-24 pb-14">
      <div className="mx-auto max-w-6xl px-4">
        <div className="relative overflow-hidden rounded-[28px] glass-bordered">
          {/* nền media mờ + scrim brand */}
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={`/bg/desk.jpg`} alt="" className="absolute inset-0 h-full w-full animate-kenburns object-cover opacity-[0.18]" />
          <div className="absolute inset-0 bg-gradient-to-br from-bg-base via-bg-base/92 to-bg-base/60" />
          <div
            className="pointer-events-none absolute -right-10 -top-10 h-72 w-72 rounded-full blur-3xl"
            style={{ background: a.glow }}
          />

          <div className="relative grid items-center gap-8 p-6 sm:p-9 lg:grid-cols-[1fr_0.85fr] lg:p-12">
            <Reveal>
              <HeadCopy page={page} compact />
              <Bullets page={page} />
              <CtaRow page={page} />
            </Reveal>

            {/* diptych: ảnh phẳng → video, lệch tầng */}
            <Reveal delay={0.12} className="flex items-center justify-center gap-3 lg:justify-end">
              <div className="w-[40%] max-w-[150px] translate-y-4">
                <div className="relative aspect-[9/16] overflow-hidden rounded-2xl glass-bordered">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={b.before} alt="" className="h-full w-full object-cover opacity-80 grayscale" />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
                  <span className="absolute inset-x-2 bottom-2 text-[10px] font-medium text-white/80">{b.beforeLabel}</span>
                </div>
              </div>
              <span className={cn("grid h-9 w-9 shrink-0 place-items-center rounded-full bg-gradient-to-br ring-1", a.tile, a.ring)}>
                <ArrowRight className={cn("h-4 w-4", a.icon)} />
              </span>
              <div className="w-[48%] max-w-[185px] -translate-y-3">
                <MiniReel poster={b.after} video={b.afterVideo} captions={reelCaptions} className="w-full rounded-2xl shadow-glow-sm" />
                <p className="mt-2 text-center text-[11px] text-ink-medium">{b.afterLabel}</p>
              </div>
            </Reveal>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ── TOOL: bảng điều khiển I/O với thanh tiêu đề ─────────────────── */
function ToolHero({ page }: { page: FeaturePage }) {
  const t = useTranslations("feature");
  const a = ACCENTS[page.accent];

  return (
    <section className="relative isolate overflow-hidden pt-32 pb-16">
      <div
        className="pointer-events-none absolute left-[8%] top-[4%] h-[400px] w-[520px]"
        style={{ background: `radial-gradient(50% 50% at 50% 50%, ${a.glow}, transparent 70%)` }}
      />
      <div className="mx-auto grid max-w-6xl items-center gap-10 px-4 lg:grid-cols-[0.92fr_1.08fr]">
        <Reveal>
          <HeadCopy page={page} />
          <Bullets page={page} />
          <CtaRow page={page} />
        </Reveal>

        {/* console: thanh tiêu đề + 3 chấm + thân I/O */}
        <Reveal delay={0.12}>
          <div className="relative w-full overflow-hidden rounded-[22px] glass-bordered">
            <div className="flex items-center gap-2 border-b border-white/[0.06] px-4 py-2.5">
              <span className="h-2.5 w-2.5 rounded-full bg-white/15" />
              <span className="h-2.5 w-2.5 rounded-full bg-white/15" />
              <span className="h-2.5 w-2.5 rounded-full bg-white/15" />
              <span className="ml-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-ink-low">
                {t("controlPanel")} · {page.eyebrow.split("·").pop()?.trim() ?? "Vyra"}
              </span>
              <span className={cn("ml-auto h-[3px] w-6 rounded-full bg-gradient-to-r", a.grad)} />
            </div>
            <div className="p-4 sm:p-5">
              <IoPanel io={page.io!} accent={page.accent} />
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
