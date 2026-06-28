"use client";

import { useRef } from "react";
import type { ReactNode } from "react";
import Link from "next/link";
import { motion, useScroll, useTransform, useReducedMotion } from "framer-motion";
import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Reveal } from "@/components/marketing/reveal";
import { ActBadge, type Tone } from "@/components/marketing/act-badge";
import { cn } from "@/lib/utils/cn";

// Một "act" điện ảnh full-width: số 0N khổng lồ mờ (parallax) + copy + demo, xen trái/phải/giữa.
export function CinematicAct({
  index,
  side = "right",
  badge,
  eyebrow,
  title,
  sub,
  bullets,
  cta,
  demo,
  id,
}: {
  index: number;
  side?: "left" | "right" | "center";
  badge?: { tone: Tone; label: string };
  eyebrow: string;
  title: ReactNode;
  sub?: ReactNode;
  bullets?: string[];
  cta?: { label: string; href: string };
  demo: ReactNode;
  id?: string;
}) {
  const reduce = useReducedMotion();
  const ref = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start end", "end start"] });
  const yRaw = useTransform(scrollYProgress, [0, 1], [60, -60]);
  const y = reduce ? 0 : yRaw;

  const num = String(index).padStart(2, "0");
  const center = side === "center";

  const copy = (
    <div className={cn("relative", center ? "text-center" : "")}>
      {badge && (
        <div className={cn("mb-3", center && "flex justify-center")}>
          <ActBadge tone={badge.tone} label={badge.label} />
        </div>
      )}
      <span className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-300">{eyebrow}</span>
      <h2 className="mt-2 font-display text-[clamp(1.9rem,4.2vw,3rem)] font-bold leading-[1.06] tracking-tight text-ink-high">
        {title}
      </h2>
      {sub && <p className={cn("mt-4 text-ink-medium", center && "mx-auto max-w-2xl")}>{sub}</p>}
      {bullets && bullets.length > 0 && (
        <ul className={cn("mt-6 flex flex-col gap-2.5", center && "mx-auto max-w-md text-left")}>
          {bullets.map((b) => (
            <li key={b} className="flex items-start gap-3 text-ink-medium">
              <span className="mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-lg bg-violet-500/15 text-xs font-bold text-violet-300">✓</span>
              {b}
            </li>
          ))}
        </ul>
      )}
      {cta && (
        <Link href={cta.href} className={cn("mt-6 inline-block", center && "")}>
          <Button variant="glass" className="gap-2">
            {cta.label} <ArrowRight className="h-4 w-4" />
          </Button>
        </Link>
      )}
    </div>
  );

  return (
    <section id={id} ref={ref} className={cn("relative overflow-hidden", center ? "py-32 lg:py-44" : "py-28 lg:py-40")}>
      {/* số 0N khổng lồ mờ — parallax */}
      <motion.span
        aria-hidden
        style={{ y }}
        className={cn(
          "pointer-events-none absolute -z-10 font-display font-bold leading-none text-white/[0.04] will-change-transform",
          "text-[clamp(7rem,18vw,16rem)]",
          center ? "left-1/2 top-6 -translate-x-1/2" : side === "right" ? "left-2 top-6" : "right-2 top-6",
        )}
      >
        {num}
      </motion.span>

      <div className="mx-auto max-w-7xl px-4">
        {/* act divider */}
        <div className="mx-auto mb-12 h-px max-w-xs bg-gradient-to-r from-transparent via-violet-500/40 to-transparent" />

        {center ? (
          <div className="mx-auto max-w-3xl">
            <Reveal>{copy}</Reveal>
            <Reveal delay={0.12} className="mt-12">{demo}</Reveal>
          </div>
        ) : (
          <div className="grid items-center gap-12 lg:grid-cols-12">
            <Reveal className={cn("lg:col-span-5", side === "left" ? "lg:order-2 lg:col-start-8" : "")}>
              {copy}
            </Reveal>
            <Reveal delay={0.12} className={cn("lg:col-span-7", side === "left" ? "lg:order-1" : "")}>
              {demo}
            </Reveal>
          </div>
        )}
      </div>
    </section>
  );
}
