"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { Reveal } from "@/components/marketing/reveal";

// Mirror manifesto "SẴN SÀNG · KHỞI TẠO · TỎA SÁNG" của autovis, giọng Vyra.
// KHÔNG dùng chữ-nền khổng lồ (motif đó để dành cho tagline cuối) — dùng divider + 3-nhịp nền sạch.
export function Manifesto() {
  const t = useTranslations("home");
  return (
    <section className="px-4 py-28 lg:py-32">
      <Reveal className="mx-auto max-w-3xl text-center">
        <div className="mx-auto mb-8 h-px max-w-xs bg-gradient-to-r from-transparent via-violet-500/70 to-transparent" />
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-300">
          {t("manifestoEyebrow")}
        </p>
        <h2 className="mt-4 font-display text-[clamp(1.9rem,5vw,3rem)] font-bold leading-[1.06] tracking-tight text-ink-high">
          {t.rich("manifestoTitle", { grad: (c) => <span className="text-gradient">{c}</span> })}
        </h2>
        <p className="mx-auto mt-5 max-w-xl text-ink-medium">
          {t("manifestoBody")}
        </p>
        <div className="mt-8 flex flex-wrap justify-center gap-3">
          <Link href="/login">
            <Button size="lg">{t("ctaCreateFirst")}</Button>
          </Link>
          <a href="#nang-luc">
            <Button variant="glass" size="lg">{t("manifestoSecondaryCta")}</Button>
          </a>
        </div>
      </Reveal>
    </section>
  );
}
