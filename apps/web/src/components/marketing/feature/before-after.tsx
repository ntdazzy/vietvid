import { ArrowRight } from "lucide-react";
import type { FeaturePage } from "@/lib/feature-pages";
import { ACCENTS } from "@/lib/accents";
import { SectionHeading } from "@/components/marketing/section-heading";
import { MiniReel } from "@/components/marketing/mini-reel";
import { Reveal } from "@/components/marketing/reveal";
import { cn } from "@/lib/utils/cn";

export function BeforeAfter({ page }: { page: FeaturePage }) {
  const a = ACCENTS[page.accent];
  const b = page.beforeAfter;
  if (!b) return null;
  return (
    <section className="mx-auto max-w-5xl px-4 py-16">
      <SectionHeading align="center" eyebrow="Trước → Sau" title={<>Từ ảnh phẳng tới video sống</>} />
      <Reveal>
        <div className="mt-10 flex flex-col items-center gap-5 sm:flex-row sm:items-center sm:justify-center">
          <div className="flex w-full max-w-[210px] flex-col gap-2">
            <div className="relative aspect-[9/16] overflow-hidden rounded-2xl glass-bordered">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={b.before} alt="" className="h-full w-full object-cover opacity-90 grayscale" />
            </div>
            <span className="text-center text-xs text-ink-low">{b.beforeLabel}</span>
          </div>

          <span className={cn("grid h-10 w-10 shrink-0 rotate-90 place-items-center rounded-full bg-gradient-to-br ring-1 sm:rotate-0", a.tile, a.ring)}>
            <ArrowRight className={cn("h-5 w-5", a.icon)} />
          </span>

          <div className="flex w-full max-w-[210px] flex-col gap-2">
            <div className={cn("relative aspect-[9/16] overflow-hidden rounded-2xl ring-2", a.ring)}>
              {b.afterVideo ? (
                <MiniReel poster={b.after} video={b.afterVideo} captions={[b.afterLabel]} className="h-full w-full rounded-2xl" />
              ) : (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={b.after} alt="" className="h-full w-full object-cover" />
              )}
            </div>
            <span className="text-center text-xs text-ink-medium">{b.afterLabel}</span>
          </div>
        </div>
        <p className="mt-6 text-center text-sm text-ink-low">{b.note}</p>
      </Reveal>
    </section>
  );
}
