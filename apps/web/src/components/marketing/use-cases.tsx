"use client";

import { UserSquare2, Star, Shirt, Package, TrendingUp, MessageSquare, GitCompare, Megaphone, Sparkles, Music2, UtensilsCrossed, Plane, Baby, Film, BookOpen, Home, Palette, Clapperboard, Ghost, Zap, Drama, Wand2, Goal } from "lucide-react";
import { useTranslations } from "next-intl";
import { Reveal } from "@/components/marketing/reveal";
import { SectionHeading } from "@/components/marketing/section-heading";

// Khẳng định độ RỘNG: Vyra dựng đủ loại video, không chỉ quảng cáo sản phẩm.
const CASES: { icon: typeof UserSquare2; key: string; hot?: boolean }[] = [
  { icon: UserSquare2, key: "kol", hot: true },
  { icon: Drama, key: "roleplay", hot: true },
  { icon: Star, key: "review" },
  { icon: Shirt, key: "lookbook" },
  { icon: Wand2, key: "outfit" },
  { icon: Package, key: "unboxing" },
  { icon: TrendingUp, key: "trend", hot: true },
  { icon: Music2, key: "douyin", hot: true },
  { icon: Goal, key: "football", hot: true },
  { icon: Palette, key: "animation" },
  { icon: Clapperboard, key: "movie" },
  { icon: Ghost, key: "horror" },
  { icon: Zap, key: "superhero" },
  { icon: MessageSquare, key: "testimonial" },
  { icon: GitCompare, key: "compare" },
  { icon: Megaphone, key: "ads" },
  { icon: UtensilsCrossed, key: "cooking" },
  { icon: Plane, key: "travel" },
  { icon: Baby, key: "mombaby" },
  { icon: Film, key: "shortfilm" },
  { icon: BookOpen, key: "story" },
  { icon: Home, key: "realestate" },
  { icon: Sparkles, key: "service" },
];

export function UseCases() {
  const t = useTranslations("home");
  return (
    <section className="mx-auto max-w-[1600px] px-4 py-14 sm:py-20 lg:py-28">
      <SectionHeading
        eyebrow={t("useCasesEyebrow")}
        title={t.rich("useCasesTitle", { grad: (c) => <span className="text-gradient">{c}</span> })}
        sub={t("useCasesSub")}
      />
      <div className="mt-10 flex flex-wrap gap-3">
        {CASES.map((c, i) => (
          <Reveal key={c.key} delay={0.04 * i}>
            <div className="group flex items-center gap-2.5 rounded-2xl border border-white/[0.08] bg-white/[0.025] px-4 py-3 transition-colors hover:border-violet-400/40 hover:bg-violet-500/[0.06]">
              <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-violet-500/[0.12] text-violet-300 transition-colors group-hover:bg-violet-500/20">
                <c.icon className="h-[18px] w-[18px]" />
              </span>
              <span className="text-sm font-medium text-ink-high">{t(`case_${c.key}`)}</span>
              {c.hot && <span className="rounded-md bg-danger/15 px-1.5 py-0.5 text-[10px] font-bold uppercase text-danger">{t("hotBadge")}</span>}
            </div>
          </Reveal>
        ))}
      </div>
    </section>
  );
}
