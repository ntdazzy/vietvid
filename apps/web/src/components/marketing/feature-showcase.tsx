import Link from "next/link";
import { ArrowRight, Check } from "lucide-react";
import { Logo } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
import { SiteHeader } from "@/components/marketing/site-header";
import { SampleMarquee } from "@/components/marketing/sample-marquee";
import { MiniReel } from "@/components/marketing/mini-reel";
import { Reveal } from "@/components/marketing/reveal";
import { SectionHeading } from "@/components/marketing/section-heading";
import type { FeaturePage } from "@/lib/feature-pages";

const LABELS: Record<string, string> = {
  fashion: "Thời trang", beauty: "Mỹ phẩm", tech: "Công nghệ", home: "Gia dụng", food: "Ẩm thực",
};

export function FeatureShowcase({ page }: { page: FeaturePage }) {
  const [titleA, titleB] = page.title.split("|");
  const tiles = page.gallery.map((f) => ({ file: f, label: LABELS[f] ?? f }));

  return (
    <div className="relative min-h-dvh mesh-bg">
      <SiteHeader />

      {/* HERO */}
      <section className="relative isolate overflow-hidden pt-32 pb-16">
        <div
          className="pointer-events-none absolute right-[8%] top-[4%] h-[420px] w-[520px] opacity-60"
          style={{ background: "radial-gradient(50% 50% at 50% 50%, rgba(124,58,237,0.18), transparent 70%)" }}
        />
        <div className="mx-auto grid max-w-6xl items-center gap-10 px-4 lg:grid-cols-[1.05fr_0.95fr]">
          <Reveal>
            {page.badge && (
              <span className="inline-flex items-center rounded-full border border-violet-400/30 bg-violet-500/[0.08] px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide text-violet-200">
                {page.badge}
              </span>
            )}
            <p className="mt-3 text-xs font-semibold uppercase tracking-[0.18em] text-violet-300">{page.eyebrow}</p>
            <h1 className="mt-3 font-display text-[clamp(2.2rem,5vw,3.75rem)] font-bold leading-[1.02] tracking-[-0.035em] text-ink-high">
              {titleA}
              {titleB && (<><br /><span className="text-gradient">{titleB}</span></>)}
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

          <Reveal delay={0.12} className="flex justify-center lg:justify-end">
            <MiniReel
              poster={`/samples/${page.heroSample}.png`}
              video={`/samples/${page.heroSample}.mp4`}
              className="w-full max-w-[300px]"
              captions={["Mẫu dựng từ engine Vyra", "Giọng Việt thật, phụ đề khớp", "Sẵn đăng trong ~60 giây"]}
            />
          </Reveal>
        </div>
      </section>

      {/* GALLERY */}
      <section className="py-12">
        <div className="mx-auto max-w-6xl px-4">
          <h2 className="font-display text-sm font-semibold uppercase tracking-[0.18em] text-ink-low">
            Mẫu output thật · chưa qua chỉnh sửa
          </h2>
        </div>
        <div className="mt-7">
          <SampleMarquee tiles={tiles} direction="left" />
        </div>
        <p className="mt-4 text-center text-xs text-ink-low">Di chuột vào mẫu để xem clip chạy.</p>
      </section>

      {/* HOW IT WORKS */}
      <section className="mx-auto max-w-6xl px-4 py-24">
        <SectionHeading align="center" eyebrow="Ba bước" title={<>Nhanh, không cần biết dựng phim.</>} />
        <div className="mt-12 grid gap-6 md:grid-cols-3">
          {page.steps.map((s, i) => (
            <Reveal key={s.t} delay={0.1 * i}>
              <div className="glass flex h-full flex-col gap-2 rounded-2xl p-5">
                <span className="font-display text-4xl font-extrabold text-gradient">{i + 1}</span>
                <h3 className="font-display text-base font-semibold text-ink-high">{s.t}</h3>
                <p className="text-sm text-ink-low">{s.d}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="relative overflow-hidden px-4 py-24 text-center">
        <div className="glow-radial pointer-events-none absolute inset-x-0 -top-10 mx-auto h-56 max-w-2xl" />
        <div className="relative mx-auto max-w-2xl">
          <div className="mx-auto mb-8 h-px max-w-xs bg-gradient-to-r from-transparent via-violet-500/70 to-transparent" />
          <h2 className="font-display text-[clamp(1.8rem,4.5vw,2.75rem)] font-extrabold tracking-[-0.02em] text-ink-high">
            Thử ngay với <span className="text-gradient">300 credit tặng.</span>
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
