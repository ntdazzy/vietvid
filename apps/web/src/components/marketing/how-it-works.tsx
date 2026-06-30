"use client";

import { motion } from "framer-motion";
import { useTranslations } from "next-intl";
import { Reveal } from "@/components/marketing/reveal";
import { SectionHeading } from "@/components/marketing/section-heading";

const STEP_KEYS = ["upload", "pick", "render", "measure"] as const;

export function HowItWorks() {
  const t = useTranslations("home");
  const STEPS = STEP_KEYS.map((k) => ({ t: t(`step_${k}_t`), d: t(`step_${k}_d`) }));
  return (
    <div className="mx-auto max-w-[1600px] px-4">
      <SectionHeading
        align="center"
        eyebrow={t("howEyebrow")}
        title={t.rich("howTitle", { grad: (c) => <span className="text-gradient">{c}</span> })}
      />
      <div className="relative mt-12 grid gap-6 md:grid-cols-4">
        {/* đường nối "vẽ" ngang (desktop) */}
        <motion.div
          aria-hidden
          initial={{ scaleX: 0 }}
          whileInView={{ scaleX: 1 }}
          viewport={{ once: true, margin: "-60px" }}
          transition={{ duration: 1, ease: [0.22, 1, 0.36, 1] }}
          style={{ transformOrigin: "left" }}
          className="absolute left-0 right-0 top-12 hidden h-px bg-gradient-to-r from-violet-500/50 via-violet-500/30 to-transparent md:block"
        />
        {STEPS.map((s, i) => (
          <Reveal key={s.t} delay={0.1 * i}>
            <div className="glass relative flex h-full flex-col gap-2 rounded-2xl p-5">
              <span className="font-display text-4xl font-extrabold text-gradient">{i + 1}</span>
              <h3 className="font-display text-base font-semibold text-ink-high">{s.t}</h3>
              <p className="text-sm text-ink-low">{s.d}</p>
            </div>
          </Reveal>
        ))}
      </div>
    </div>
  );
}
