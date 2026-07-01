"use client";

import Link from "next/link";
import { motion, useScroll, useTransform, useReducedMotion } from "framer-motion";
import { ArrowRight, Boxes, Clock, Gift } from "lucide-react";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { ScriptPlayground } from "@/components/marketing/script-playground";

const fadeUp = {
  hidden: { opacity: 0, y: 18 },
  show: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: 0.06 * i, duration: 0.6, ease: [0.22, 1, 0.36, 1] },
  }),
};

export function LandingHero() {
  const t = useTranslations("home");
  const reduce = useReducedMotion();
  const { scrollY } = useScroll();
  const glowYRaw = useTransform(scrollY, [0, 500], [0, -80]);
  const glowY = reduce ? 0 : glowYRaw;

  return (
    <section className="relative isolate overflow-hidden pt-28 pb-20">
      {/* backdrop AI sinh (Gemini) — dải aurora tím rất mờ tạo chiều sâu, fade dần xuống đáy
          để không có mép cứng; nằm DƯỚI mọi nội dung (first child) + pointer-events-none */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 -z-10 bg-cover bg-center opacity-[0.16]"
        style={{
          backgroundImage: "url(/bg/gen/mesh-aurora.jpg)",
          maskImage: "linear-gradient(to bottom, black 0%, black 45%, transparent 92%)",
          WebkitMaskImage: "linear-gradient(to bottom, black 0%, black 45%, transparent 92%)",
        }}
      />
      {/* glow tím 1-điểm (nguồn sáng tím duy nhất của hero) — parallax nhẹ khi cuộn */}
      <motion.div
        style={{ y: glowY }}
        className="pointer-events-none absolute right-[6%] top-[2%] h-[440px] w-[560px] opacity-60 will-change-transform"
      >
        <div
          className="h-full w-full"
          style={{ background: "radial-gradient(50% 50% at 50% 50%, rgba(124,58,237,0.20), transparent 70%)" }}
        />
      </motion.div>

      <div className="mx-auto grid max-w-[1600px] items-center gap-10 px-4 lg:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)]">
        {/* cột trái — copy canh trái */}
        <div className="text-left">
          <motion.span
            custom={0} variants={fadeUp} initial="hidden" animate="show"
            className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.03] px-3.5 py-1.5 text-[12px] font-medium text-ink-medium"
          >
            <span className="h-1.5 w-1.5 rounded-full bg-success shadow-glow-success" />
            {t("heroBadge")}
          </motion.span>

          <motion.h1
            custom={1} variants={fadeUp} initial="hidden" animate="show"
            className="font-display mt-6 max-w-xl text-[clamp(2.4rem,5.4vw,4.25rem)] font-bold leading-[1.0] tracking-[-0.04em] text-ink-high"
          >
            {t.rich("heroTitle", {
              br: () => <br />,
              grad: (c) => <span className="text-gradient">{c}</span>,
            })}
          </motion.h1>

          <motion.p
            custom={2} variants={fadeUp} initial="hidden" animate="show"
            className="mt-6 max-w-md text-lg leading-relaxed text-ink-medium"
          >
            {t("heroSub")}
          </motion.p>

          <motion.div
            custom={3} variants={fadeUp} initial="hidden" animate="show"
            className="mt-8 flex flex-wrap items-center gap-3"
          >
            <Link href="/login">
              <Button size="lg" className="gap-2">
                {t("ctaCreateFirst")} <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <a href="#winner-loop">
              <Button variant="glass" size="lg">
                {t("heroSecondaryCta")}
              </Button>
            </a>
          </motion.div>

          {/* 3 ô stat — đối ứng "50.000+" của autovis nhưng bằng số THẬT (static, không count-up) */}
          <motion.div
            custom={4} variants={fadeUp} initial="hidden" animate="show"
            className="mt-8 grid max-w-md grid-cols-3 gap-3"
          >
            {[
              { n: "~60s", l: t("statPerVideo"), I: Clock },
              { n: "10+", l: t("statTools"), I: Boxes },
              { n: "300", l: t("statCredits"), I: Gift },
            ].map(({ n, l, I }) => (
              <div key={l} className="rounded-2xl border border-white/[0.07] bg-white/[0.025] px-3 py-3">
                <I className="h-3.5 w-3.5 text-violet-300" />
                <div className="mt-1.5 font-numeric text-[clamp(1.4rem,3vw,1.9rem)] font-bold leading-none text-gradient">{n}</div>
                <div className="mt-1 text-xs text-ink-low">{l}</div>
              </div>
            ))}
          </motion.div>
        </div>

        {/* cột phải — playground sống */}
        <ScriptPlayground />
      </div>
    </section>
  );
}
