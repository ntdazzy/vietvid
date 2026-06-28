import type { FeaturePage } from "@/lib/feature-pages";
import { ACCENTS } from "@/lib/accents";
import { Reveal } from "@/components/marketing/reveal";
import { cn } from "@/lib/utils/cn";

export function ProofBand({ page }: { page: FeaturePage }) {
  const a = ACCENTS[page.accent];
  const items = page.proof ?? [];
  if (!items.length) return null;
  return (
    <section className="mx-auto max-w-5xl px-4 py-12">
      <Reveal>
        <div className="relative overflow-hidden rounded-3xl glass-bordered p-6 sm:p-8">
          <div
            className="pointer-events-none absolute inset-x-0 -top-16 h-32"
            style={{ background: `radial-gradient(55% 100% at 50% 0%, ${a.glow}, transparent 72%)` }}
          />
          <p className="relative text-center text-sm text-ink-medium">
            Vyra mới ra mắt — đây là <span className="text-ink-high">năng lực thật của engine</span>, không phải con số tô vẽ.
          </p>
          <div className="relative mt-6 grid grid-cols-3 gap-4">
            {items.map((p) => (
              <div key={p.label} className="text-center">
                <div className={cn("font-numeric text-2xl font-bold tabular sm:text-3xl", a.text)}>{p.stat}</div>
                <div className="mt-1 text-xs text-ink-low">{p.label}</div>
              </div>
            ))}
          </div>
        </div>
      </Reveal>
    </section>
  );
}
