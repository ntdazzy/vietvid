"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { Logo } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
import { SiteHeader } from "@/components/marketing/site-header";
import { SampleMarquee } from "@/components/marketing/sample-marquee";
import { SectionHeading } from "@/components/marketing/section-heading";
import { ACCENTS } from "@/lib/accents";
import type { FeaturePage, SectionId } from "@/lib/feature-pages";
import { FeatureHero } from "./feature/feature-hero";
import { FeatureHighlights } from "./feature/feature-highlights";
import { BeforeAfter } from "./feature/before-after";
import { ResultsShowcase } from "./feature/results-showcase";
import { UseCaseStrip } from "./feature/use-case-strip";
import { VoiceBar } from "./feature/voice-bar";
import { ComparisonRows } from "./feature/comparison-rows";
import { ProofBand } from "./feature/proof-band";
import { cn } from "@/lib/utils/cn";

const LABEL_KEYS = ["fashion", "beauty", "tech", "home", "food"] as const;

function renderSection(id: SectionId, page: FeaturePage) {
  switch (id) {
    case "highlights": return <FeatureHighlights key={id} page={page} />;
    case "beforeAfter": return <BeforeAfter key={id} page={page} />;
    case "results": return <ResultsShowcase key={id} page={page} />;
    case "useCases": return <UseCaseStrip key={id} page={page} />;
    case "voiceBar": return <VoiceBar key={id} page={page} />;
    case "comparison": return <ComparisonRows key={id} page={page} />;
    case "proof": return <ProofBand key={id} page={page} />;
    default: return null;
  }
}

export function FeatureShowcase({ page }: { page: FeaturePage }) {
  const t = useTranslations("feature");
  const a = ACCENTS[page.accent];
  const labels: Record<string, string> = Object.fromEntries(
    LABEL_KEYS.map((k) => [k, t(`label_${k}`)]),
  );
  // gallery keys (fashion/beauty/...) là tên file dưới /samples — prepend "samples/" để
  // SampleMarquee trỏ đúng /samples/<key>.jpg|.mp4 (trước đây trỏ /<key>.jpg → 404 ảnh vỡ).
  const tiles = page.gallery.map((f) => ({ file: `samples/${f}`, label: labels[f] ?? f }));

  return (
    <div className="relative min-h-dvh mesh-bg">
      <SiteHeader />
      <FeatureHero page={page} />

      {/* teaser marquee — đầu thanh có vạch gradient brand để neo, không phải tiêu đề trần */}
      <section className="py-10">
        <div className="mx-auto flex max-w-6xl items-center gap-3 px-4">
          <span className={cn("h-[3px] w-8 shrink-0 rounded-full bg-gradient-to-r", a.grad)} />
          <h2 className="font-display text-sm font-semibold uppercase tracking-[0.18em] text-ink-low">
            {t("marqueeHeading")}
          </h2>
        </div>
        <div className="mt-6"><SampleMarquee tiles={tiles} direction="left" /></div>
      </section>

      {/* các section giàu — bộ + thứ tự riêng theo từng feature */}
      {page.sections.map((id) => renderSection(id, page))}

      {/* steps — timeline nối nhau bằng rail gradient, KHÔNG hàng thẻ rời */}
      <section className="mx-auto max-w-5xl px-4 py-14">
        <SectionHeading align="left" eyebrow={t("stepsEyebrow")} title={<>{t("stepsTitle")}</>} />
        <ol className="relative mt-10 flex flex-col gap-0">
          {/* rail dọc chạy qua các mốc */}
          <span
            className={cn("pointer-events-none absolute left-[18px] top-3 bottom-3 w-px bg-gradient-to-b from-transparent to-transparent", a.line)}
            aria-hidden
          />
          {page.steps.map((s, i) => (
            <li key={s.t} className="relative flex gap-5 pb-7 last:pb-0">
              <span className={cn("relative z-10 grid h-9 w-9 shrink-0 place-items-center rounded-full bg-gradient-to-br font-numeric text-sm font-bold ring-1", a.tile, a.ring, a.icon)}>
                {i + 1}
              </span>
              <div className="pt-1">
                <h3 className="font-display text-base font-semibold text-ink-high">{s.t}</h3>
                <p className="mt-0.5 text-sm text-ink-low">{s.d}</p>
              </div>
            </li>
          ))}
        </ol>
      </section>

      {/* CTA */}
      <section className="relative overflow-hidden px-4 py-24 text-center">
        <div
          className="pointer-events-none absolute inset-x-0 -top-10 mx-auto h-56 max-w-2xl"
          style={{ background: `radial-gradient(50% 60% at 50% 0%, ${a.glow}, transparent 70%)` }}
        />
        <div className="relative mx-auto max-w-2xl">
          <div className={cn("mx-auto mb-8 h-px max-w-xs bg-gradient-to-r from-transparent to-transparent", a.line)} />
          <h2 className="font-display text-[clamp(1.8rem,4.5vw,2.75rem)] font-extrabold tracking-[-0.02em] text-ink-high">
            {t.rich("ctaTitle", {
              grad: (c) => <span className={cn("bg-gradient-to-r bg-clip-text text-transparent", a.grad)}>{c}</span>,
            })}
          </h2>
          <p className="mx-auto mt-3 max-w-md text-ink-medium">{t("ctaSub")}</p>
          <div className="mt-7 flex justify-center">
            <Link href={page.ctaHref}><Button size="lg">{page.ctaLabel}</Button></Link>
          </div>
        </div>
      </section>

      <footer className="border-t border-white/[0.06] px-4 py-8">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 text-sm text-ink-low sm:flex-row">
          <Logo />
          <p className="text-xs text-ink-disabled">© 2026 Vyra · {t("footerTagline")}</p>
        </div>
      </footer>
    </div>
  );
}
