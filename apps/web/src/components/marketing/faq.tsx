"use client";

import { useState } from "react";
import { ChevronDown } from "lucide-react";
import { useTranslations } from "next-intl";
import { SectionHeading } from "@/components/marketing/section-heading";
import { Reveal } from "@/components/marketing/reveal";
import { cn } from "@/lib/utils/cn";

const FAQ_KEYS = ["what", "noskill", "voice", "cost", "refund", "watermark", "types", "api"] as const;

function Item({ q, a }: { q: string; a: string }) {
  const [open, setOpen] = useState(false);
  return (
    <button
      type="button"
      onClick={() => setOpen((v) => !v)}
      className="w-full rounded-2xl border border-white/[0.08] bg-white/[0.02] p-5 text-left transition-colors hover:border-white/[0.16]"
    >
      <div className="flex items-center justify-between gap-4">
        <span className="font-medium text-ink-high">{q}</span>
        <ChevronDown className={cn("h-4 w-4 shrink-0 text-violet-300 transition-transform", open && "rotate-180")} />
      </div>
      <div className={cn("grid transition-all duration-300", open ? "mt-3 grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0")}>
        <p className="overflow-hidden text-sm leading-relaxed text-ink-low">{a}</p>
      </div>
    </button>
  );
}

export function Faq() {
  const t = useTranslations("home");
  return (
    <section id="faq" className="mx-auto max-w-3xl px-4 py-24 lg:py-28">
      <SectionHeading
        align="center"
        eyebrow={t("faqEyebrow")}
        title={t.rich("faqTitle", { grad: (c) => <span className="text-gradient">{c}</span> })}
      />
      <div className="mt-10 flex flex-col gap-3">
        {FAQ_KEYS.map((k, i) => (
          <Reveal key={k} delay={0.04 * i}>
            <Item q={t(`faq_${k}_q`)} a={t(`faq_${k}_a`)} />
          </Reveal>
        ))}
      </div>
    </section>
  );
}
