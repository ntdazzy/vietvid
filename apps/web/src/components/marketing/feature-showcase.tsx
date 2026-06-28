import Link from "next/link";
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

const LABELS: Record<string, string> = {
  fashion: "Thời trang", beauty: "Mỹ phẩm", tech: "Công nghệ", home: "Gia dụng", food: "Ẩm thực",
};

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
  const a = ACCENTS[page.accent];
  const tiles = page.gallery.map((f) => ({ file: f, label: LABELS[f] ?? f }));

  return (
    <div className="relative min-h-dvh mesh-bg">
      <SiteHeader />
      <FeatureHero page={page} />

      {/* teaser marquee */}
      <section className="py-10">
        <div className="mx-auto max-w-6xl px-4">
          <h2 className="font-display text-sm font-semibold uppercase tracking-[0.18em] text-ink-low">
            Mẫu output thật · di chuột để xem clip chạy
          </h2>
        </div>
        <div className="mt-6"><SampleMarquee tiles={tiles} direction="left" /></div>
      </section>

      {/* các section giàu — bộ + thứ tự riêng theo từng feature */}
      {page.sections.map((id) => renderSection(id, page))}

      {/* steps rail (đã bị giáng từ trung tâm xuống dải gọn) */}
      <section className="mx-auto max-w-6xl px-4 py-14">
        <SectionHeading align="center" eyebrow="Ba bước" title={<>Nhanh, không cần biết dựng phim.</>} />
        <div className="mt-10 grid gap-6 md:grid-cols-3">
          {page.steps.map((s, i) => (
            <div key={s.t} className="glass flex h-full flex-col gap-2 rounded-2xl p-5">
              <span className={cn("font-numeric text-4xl font-extrabold", a.text)}>{i + 1}</span>
              <h3 className="font-display text-base font-semibold text-ink-high">{s.t}</h3>
              <p className="text-sm text-ink-low">{s.d}</p>
            </div>
          ))}
        </div>
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
            Thử ngay với <span className={cn("bg-gradient-to-r bg-clip-text text-transparent", a.grad)}>300 credit tặng.</span>
          </h2>
          <p className="mx-auto mt-3 max-w-md text-ink-medium">Không cần thẻ. Mất ~60 giây để có kết quả đầu tiên.</p>
          <div className="mt-7 flex justify-center">
            <Link href={page.ctaHref}><Button size="lg">{page.ctaLabel}</Button></Link>
          </div>
        </div>
      </section>

      <footer className="border-t border-white/[0.06] px-4 py-8">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 text-sm text-ink-low sm:flex-row">
          <Logo />
          <p className="text-xs text-ink-disabled">© 2026 Vyra · Video AI giọng Việt</p>
        </div>
      </footer>
    </div>
  );
}
