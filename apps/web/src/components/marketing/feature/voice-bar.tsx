import { Volume2 } from "lucide-react";
import type { FeaturePage } from "@/lib/feature-pages";
import { ACCENTS } from "@/lib/accents";
import { SectionHeading } from "@/components/marketing/section-heading";
import { Reveal } from "@/components/marketing/reveal";
import { cn } from "@/lib/utils/cn";

export function VoiceBar({ page }: { page: FeaturePage }) {
  const a = ACCENTS[page.accent];
  const voices = page.voices ?? [];
  if (!voices.length) return null;
  return (
    <section className="mx-auto max-w-5xl px-4 py-14">
      <SectionHeading align="center" eyebrow="Giọng Việt thật" title={<>7 giọng, mỗi giọng một cá tính</>} />
      <Reveal>
        <div className="mt-8 flex flex-wrap justify-center gap-2.5">
          {voices.map((v) => (
            <span
              key={v.name}
              className={cn("flex items-center gap-2 rounded-full border bg-white/[0.02] px-3.5 py-2 ring-1 ring-inset", a.ring)}
            >
              <Volume2 className={cn("h-4 w-4", a.icon)} />
              <span className="text-sm font-medium text-ink-high">{v.name}</span>
              <span className="text-xs text-ink-low">· {v.vibe}</span>
            </span>
          ))}
        </div>
        <p className="mt-4 text-center text-xs text-ink-low">Nghe thử trực tiếp trong app trước khi tạo.</p>
      </Reveal>
    </section>
  );
}
