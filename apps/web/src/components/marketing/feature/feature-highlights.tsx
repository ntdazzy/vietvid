import type { FeaturePage } from "@/lib/feature-pages";
import { ACCENTS } from "@/lib/accents";
import { icon } from "./icons";
import { SectionHeading } from "@/components/marketing/section-heading";
import { Reveal } from "@/components/marketing/reveal";
import { cn } from "@/lib/utils/cn";

export function FeatureHighlights({ page }: { page: FeaturePage }) {
  const a = ACCENTS[page.accent];
  const items = page.highlights ?? [];
  if (!items.length) return null;
  return (
    <section className="mx-auto max-w-6xl px-4 py-16">
      <SectionHeading align="center" eyebrow="Năng lực thật" title={<>Làm được gì cho bạn</>} />
      <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {items.map((h, i) => {
          const Ic = icon(h.icon);
          return (
            <Reveal key={h.t} delay={0.07 * i}>
              <div className="flex h-full flex-col gap-3 rounded-2xl glass-bordered p-5">
                <span className={cn("grid h-11 w-11 place-items-center rounded-xl bg-gradient-to-br ring-1", a.tile, a.ring)}>
                  <Ic className={cn("h-5 w-5", a.icon)} />
                </span>
                <div className="font-display font-semibold text-ink-high">{h.t}</div>
                <p className="text-sm leading-relaxed text-ink-low">{h.d}</p>
              </div>
            </Reveal>
          );
        })}
      </div>
    </section>
  );
}
