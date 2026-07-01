"use client";

import { useTranslations } from "next-intl";
import { Wallet, ShieldCheck, Infinity as InfinityIcon } from "lucide-react";
import { FilmLabel } from "@/components/ui/cinematic";
import { Reveal } from "@/components/marketing/reveal";

// 3 con hào Vyra CÓ THẬT trong code (thanh toán bản địa · HOLD-hoàn-tiền · xu không hết hạn).
// Đối thủ ngoại về cấu trúc không match rẻ được — nên "hét to" ở đây, không chôn ở dòng nhỏ.
const ITEMS = [
  { icon: Wallet, k: "trust1" },
  { icon: ShieldCheck, k: "trust2" },
  { icon: InfinityIcon, k: "trust3" },
] as const;

export function PricingTrustBand() {
  const t = useTranslations("pricing");
  return (
    <section className="mx-auto max-w-6xl px-4 pb-14">
      <Reveal>
        <div className="text-center">
          <div className="flex justify-center">
            <FilmLabel>{t("trustEyebrow")}</FilmLabel>
          </div>
          <h2 className="mt-3 font-display text-[clamp(1.5rem,3.2vw,2.2rem)] font-bold leading-tight text-ink-high">
            {t("trustHeading")}
          </h2>
        </div>
        <div className="mt-8 grid gap-4 sm:grid-cols-3">
          {ITEMS.map(({ icon: Icon, k }) => (
            <div key={k} className="rounded-3xl glass-bordered p-6">
              <span className="grid h-11 w-11 place-items-center rounded-2xl border border-emerald-400/25 bg-emerald-500/10 text-emerald-300">
                <Icon className="h-5 w-5" />
              </span>
              <div className="mt-4 font-display text-lg font-bold text-ink-high">{t(`${k}Title`)}</div>
              <p className="mt-1.5 text-sm leading-relaxed text-ink-medium">{t(`${k}Desc`)}</p>
            </div>
          ))}
        </div>
      </Reveal>
    </section>
  );
}
