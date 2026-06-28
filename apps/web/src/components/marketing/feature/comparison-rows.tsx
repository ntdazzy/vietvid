import { Check, X } from "lucide-react";
import type { FeaturePage } from "@/lib/feature-pages";
import { ACCENTS } from "@/lib/accents";
import { SectionHeading } from "@/components/marketing/section-heading";
import { Reveal } from "@/components/marketing/reveal";

export function ComparisonRows({ page }: { page: FeaturePage }) {
  const a = ACCENTS[page.accent];
  const c = page.comparison;
  if (!c) return null;
  return (
    <section className="mx-auto max-w-5xl px-4 py-16">
      <SectionHeading align="center" eyebrow="So sánh" title={<>Cách cũ <span className="text-ink-low">vs</span> với Vyra</>} />
      <Reveal>
        <div className="relative mt-8 grid overflow-hidden rounded-3xl glass-bordered lg:grid-cols-2">
          {/* cách cũ */}
          <div className="p-6 sm:p-7">
            <div className="mb-4 text-sm font-semibold uppercase tracking-wider text-ink-low">Cách cũ</div>
            <ul className="flex flex-col gap-3">
              {c.oldWay.map((t) => (
                <li key={t} className="flex items-start gap-2.5 text-sm text-ink-disabled">
                  <X className="mt-0.5 h-4 w-4 shrink-0" /> {t}
                </li>
              ))}
            </ul>
          </div>
          {/* với vyra */}
          <div className="relative border-t border-white/[0.06] p-6 sm:p-7 lg:border-l lg:border-t-0">
            <div
              className="pointer-events-none absolute inset-0"
              style={{ background: `radial-gradient(70% 100% at 80% 0%, ${a.glow}, transparent 70%)` }}
            />
            <div className="relative mb-4 text-sm font-semibold uppercase tracking-wider text-ink-high">
              Với Vyra · ~60s
            </div>
            <ul className="relative flex flex-col gap-3">
              {c.vyraWay.map((t) => (
                <li key={t} className="flex items-start gap-2.5 text-sm text-ink-medium">
                  <Check className="mt-0.5 h-4 w-4 shrink-0 text-success" /> {t}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </Reveal>
    </section>
  );
}
