"use client";

import { useTranslations } from "next-intl";
import { motion } from "framer-motion";
import Link from "next/link";
import { Lock, ArrowRight, ArrowDown } from "lucide-react";
import type { WalletResponse } from "@/lib/api/types";
import { FilmLabel } from "@/components/ui/cinematic";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { CreditValue } from "@/components/ui/credit-value";
import { Skeleton } from "@/components/ui/skeleton";
import { ACCENTS } from "@/lib/accents";

const VND_PER_CREDIT = 150; // CREDIT_PRICE_VND
const CREDITS_PER_VIDEO = 150; // ~trung điểm 100–180 credit/video

/** Két Vyra: hero full-bleed (ảnh bàn làm việc + glow emerald). Số dư là tâm điểm, bên phải là
 *  "làm được ~N video" + CTA, đáy là dải credit đang giữ. Bố cục RIÊNG của màn ví. */
export function WalletHero({
  wallet,
  loading,
  onScrollToHeld,
  onScrollToPacks,
}: {
  wallet?: WalletResponse;
  loading: boolean;
  onScrollToHeld: () => void;
  onScrollToPacks: () => void;
}) {
  const t = useTranslations("billing");
  const a = ACCENTS.emerald;
  const balance = wallet?.balance_credits ?? 0;
  const held = wallet?.held_credits ?? 0;
  const low = balance > 0 && balance < 100;
  const capacity = Math.floor(balance / CREDITS_PER_VIDEO);

  return (
    <section className="relative overflow-hidden rounded-3xl glass-bordered">
      {/* nền két: ảnh bàn làm việc, tối dần về phải để chữ rõ */}
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src="/bg/desk.jpg"
        alt=""
        className="absolute inset-0 h-full w-full animate-kenburns object-cover opacity-25"
      />
      <div className="absolute inset-0 bg-gradient-to-br from-bg-base/95 via-bg-base/90 to-bg-base/60" />
      <div
        className="pointer-events-none absolute -top-24 -left-10 h-64 w-64 rounded-full blur-3xl"
        style={{ background: a.glow }}
      />

      <div className="relative grid gap-8 p-6 sm:p-8 lg:grid-cols-12 lg:p-10">
        {/* TRÁI — số dư trong két */}
        <div className="lg:col-span-7">
          <FilmLabel className="text-emerald-300/80">{t("heroEyebrow")}</FilmLabel>

          <div className="mt-5 flex items-baseline gap-3">
            <span className="text-sm text-ink-low">{t("availableBalance")}</span>
            {low && <Badge tone="hold">{t("lowBalance")}</Badge>}
          </div>
          <div className="mt-1">
            {loading ? (
              <Skeleton className="h-14 w-56" />
            ) : (
              <motion.span
                key={balance}
                initial={{ opacity: 0.4 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.25 }}
                className="inline-block"
              >
                <CreditValue
                  value={balance}
                  suffix={null}
                  className="text-5xl font-extrabold leading-none tracking-tight text-ink-high sm:text-6xl lg:text-[68px]"
                />
                <span className="ml-2 align-baseline text-lg font-medium text-ink-low">credit</span>
              </motion.span>
            )}
          </div>
          <div className="mt-2 text-sm text-ink-low">
            {t("balanceInVnd", { vnd: (balance * VND_PER_CREDIT).toLocaleString("vi-VN") })}
          </div>

          {held > 0 && (
            <button
              type="button"
              onClick={onScrollToHeld}
              aria-label={t("viewHeldAria")}
              className="mt-6 flex w-full max-w-sm items-center gap-3 rounded-xl border border-hold/30 bg-hold/[0.1] px-3.5 py-2.5 text-left transition-colors hover:border-hold/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-hold/50"
            >
              <Lock className="h-4 w-4 shrink-0 text-hold" />
              <span className="min-w-0">
                <span className="flex items-center gap-1.5 text-sm font-medium text-hold">
                  {t.rich("heldAmount", {
                    value: () => <CreditValue value={held} suffix={null} className="text-sm" />,
                  })}
                </span>
                <span className="block text-xs text-ink-low">
                  {t("heldSub")}
                </span>
              </span>
            </button>
          )}
        </div>

        {/* PHẢI — sức chứa: số dư này làm được bao nhiêu video */}
        <div className="lg:col-span-5 lg:border-l lg:border-emerald-400/15 lg:pl-8">
          <div className="flex h-full flex-col justify-center rounded-2xl border-t border-white/[0.06] pt-6 lg:border-0 lg:pt-0">
            <span className="text-sm text-ink-low">{t("capacityLabel")}</span>
            <div className="mt-1">
              {loading ? (
                <Skeleton className="h-9 w-24" />
              ) : low ? (
                <div className="text-2xl font-bold text-hold">{t("notEnoughForOne")}</div>
              ) : (
                <div className="font-numeric text-5xl font-bold text-emerald-300">
                  ~{capacity.toLocaleString("vi-VN")}
                  <span className="ml-1.5 font-sans text-base font-normal text-ink-low">{t("videoUnit")}</span>
                </div>
              )}
            </div>
            {!low && (
              <p className="mt-1.5 text-xs text-ink-low">
                {t("capacityNote")}
              </p>
            )}

            <div className="mt-6">
              {balance === 0 ? (
                <Button variant="glass" size="sm" className="gap-1.5" onClick={onScrollToPacks}>
                  {t("chooseTopupPack")} <ArrowDown className="h-4 w-4" />
                </Button>
              ) : (
                <Link href="/app/create">
                  <Button variant="glass" size="sm" className="gap-1.5">
                    {t("createVideo")} <ArrowRight className="h-4 w-4" />
                  </Button>
                </Link>
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
