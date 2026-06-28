import type { FeaturePage } from "@/lib/feature-pages";
import { ACCENTS } from "@/lib/accents";
import { SectionHeading } from "@/components/marketing/section-heading";
import { Reveal } from "@/components/marketing/reveal";
import { cn } from "@/lib/utils/cn";

export function UseCaseStrip({ page }: { page: FeaturePage }) {
  const a = ACCENTS[page.accent];
  const items = page.useCases ?? [];
  if (!items.length) return null;
  return (
    <section className="mx-auto max-w-6xl px-4 py-12">
      <SectionHeading align="center" eyebrow="Dùng để làm gì" title={<>Ai cũng làm được</>} />
      <div className="mt-8 grid gap-4 sm:grid-cols-3">
        {items.map((u, i) => (
          <Reveal key={u.t} delay={0.06 * i}>
            <div className="flex h-full flex-col gap-2 rounded-2xl glass p-4">
              <span className={cn("w-fit rounded-full border px-2.5 py-0.5 text-[11px] font-medium", a.chip)}>{u.tag}</span>
              <div className="font-display text-sm font-semibold text-ink-high">{u.t}</div>
              <p className="text-xs leading-relaxed text-ink-low">{u.d}</p>
            </div>
          </Reveal>
        ))}
      </div>
    </section>
  );
}
