"use client";

import { useRef, useState } from "react";
import { useTranslations } from "next-intl";
import { useQuery } from "@tanstack/react-query";
import { AlertTriangle } from "lucide-react";
import { useWallet, useLedger } from "@/lib/query/hooks";
import { useTopup } from "@/lib/query/mutations";
import { api } from "@/lib/api/endpoints";
import { FilmLabel } from "@/components/ui/cinematic";
import { Reveal } from "@/components/marketing/reveal";
import { WalletHero } from "@/components/billing/wallet-hero";
import { TrustProof } from "@/components/billing/trust-proof";
import { PackCard } from "@/components/billing/pack-card";
import { PlanCard } from "@/components/billing/plan-card";
import { MethodGrid, type Method } from "@/components/billing/method-grid";
import { CustomAmount } from "@/components/billing/custom-amount";
import { QrPayPanel } from "@/components/billing/qr-pay-panel";
import { LedgerStatement } from "@/components/billing/ledger-statement";
import type { LedgerKind, TopupResponse } from "@/lib/api/types";

type Filter = LedgerKind | "ALL";

export default function BillingPage() {
  const t = useTranslations("billing");
  const wallet = useWallet();
  const ledger = useLedger(80);
  const packsQuery = useQuery({ queryKey: ["packs"], queryFn: api.billingPacks });
  const plansQuery = useQuery({ queryKey: ["plans"], queryFn: api.billingPlans });
  const topup = useTopup();
  const [method, setMethod] = useState<Method>("bank_qr");
  const [qrPayment, setQrPayment] = useState<TopupResponse | null>(null);
  const [filter, setFilter] = useState<Filter>("ALL");

  const ledgerRef = useRef<HTMLDivElement>(null);
  const packsRef = useRef<HTMLDivElement>(null);

  // giá trị thật — tính từ giá, KHÔNG theo index (vá lỗi "Phổ biến" được tô nhưng đắt nhất).
  const packs = packsQuery.data ?? [];
  const perCredit = (amount: number, credits: number) => Math.round(amount / credits);
  const basePer = packs.length ? Math.max(...packs.map((p) => p.amount_vnd / p.credits)) : 150;
  const best = packs.length
    ? packs.reduce((a, b) => (a.amount_vnd / a.credits <= b.amount_vnd / b.credits ? a : b))
    : null;
  const savePct = (amount: number, credits: number) => Math.round((1 - amount / credits / basePer) * 100);

  function scrollToHeld() {
    setFilter("HOLD");
    ledgerRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }
  function scrollToPacks() {
    packsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function buy(body: { pack_id?: string; plan_code?: string; amount_vnd?: number }) {
    topup.mutate(
      { ...body, provider: method },
      { onSuccess: (res) => res.provider === "bank_qr" && res.qr_image_url && setQrPayment(res) },
    );
  }

  const plans = plansQuery.data ?? [];

  const topupError = topup.isError
    ? topup.error instanceof Error
      ? topup.error.message
      : t("topupFailed")
    : null;

  return (
    <div className="mx-auto flex max-w-[1040px] flex-col gap-12">
      {/* ── KÉT: hero số dư full-bleed (bố cục RIÊNG của màn ví) ───────── */}
      <Reveal delay={0.05}>
        <WalletHero
          wallet={wallet.data}
          loading={wallet.isLoading}
          onScrollToHeld={scrollToHeld}
          onScrollToPacks={scrollToPacks}
        />
      </Reveal>

      {/* ── GÓI THÁNG: chủ đạo — rẻ hơn đối thủ, xu reset mỗi 30 ngày ───── */}
      {plans.length > 0 && (
        <Reveal delay={0.1}>
          <section className="grid gap-8 lg:grid-cols-[200px_1fr] lg:gap-12">
            <SectionRail step="01" label={t("planLabel")} title={t("planTitle")} note={t("planNote")} />
            {plansQuery.isLoading ? (
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                {Array.from({ length: 4 }).map((_, i) => (
                  <div key={i} className="h-72 w-full animate-pulse rounded-2xl bg-white/[0.04]" />
                ))}
              </div>
            ) : (
              <div className="grid items-stretch gap-4 sm:grid-cols-2 lg:grid-cols-4">
                {plans.map((p, i) => (
                  <PlanCard
                    key={p.code}
                    plan={p}
                    isRecommended={i === 1}
                    pending={topup.isPending && topup.variables?.plan_code === p.code}
                    disabled={topup.isPending}
                    onBuy={() => buy({ plan_code: p.code })}
                  />
                ))}
              </div>
            )}
          </section>
        </Reveal>
      )}

      {/* ── NẠP LẺ: gói credit / số tiền tuỳ ý (xu không hết hạn) ───────── */}
      <Reveal delay={0.16}>
        <section
          ref={packsRef}
          className="grid scroll-mt-28 gap-8 lg:grid-cols-[200px_1fr] lg:gap-12"
        >
          <SectionRail
            step="02"
            label={t("step1Label")}
            title={t("step1Title")}
            note={t("step1Note")}
          />

          <div className="flex flex-col gap-5">
            <MethodGrid method={method} setMethod={setMethod} />

            {topupError && (
              <div className="flex items-start gap-2 rounded-xl border border-danger/30 bg-danger/[0.08] px-3 py-2.5 text-sm text-ink-medium">
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-danger" />
                <span>{topupError}</span>
              </div>
            )}

            {packsQuery.isLoading ? (
              <div className="grid gap-4 sm:grid-cols-3">
                {Array.from({ length: 3 }).map((_, i) => (
                  <div key={i} className="h-52 w-full animate-pulse rounded-2xl bg-white/[0.04]" />
                ))}
              </div>
            ) : (
              <div className="grid items-stretch gap-4 sm:grid-cols-3">
                {packs.map((p) => (
                  <PackCard
                    key={p.id}
                    pack={p}
                    isBest={best?.id === p.id}
                    isRecommended={p.name === "Phổ biến"}
                    perCredit={perCredit(p.amount_vnd, p.credits)}
                    savePct={savePct(p.amount_vnd, p.credits)}
                    pending={topup.isPending && topup.variables?.pack_id === p.id}
                    disabled={topup.isPending}
                    onBuy={() => buy({ pack_id: p.id })}
                  />
                ))}
              </div>
            )}

            <CustomAmount
              pending={topup.isPending && topup.variables?.amount_vnd != null}
              disabled={topup.isPending}
              onBuy={(amountVnd) => buy({ amount_vnd: amountVnd })}
            />

            {topup.isSuccess && topup.data?.status === "succeeded" && (
              <p className="text-sm text-success">
                {t("topupSuccess", { credits: topup.data.credits.toLocaleString("vi-VN") })}
              </p>
            )}
          </div>
        </section>
      </Reveal>

      {/* ── BẢO CHỨNG: tiền được giữ ra sao ─────────────────────────────── */}
      <Reveal delay={0.18}>
        <section className="grid gap-8 lg:grid-cols-[200px_1fr] lg:gap-12">
          <SectionRail
            step="03"
            label={t("step2Label")}
            title={t("step2Title")}
            note={t("step2Note")}
          />
          <TrustProof entries={ledger.data} balance={wallet.data?.balance_credits ?? 0} />
        </section>
      </Reveal>

      {/* ── SỔ CÁI: sao kê đầy đủ ────────────────────────────────────────── */}
      <Reveal delay={0.24}>
        <section ref={ledgerRef} className="grid scroll-mt-28 gap-8 lg:grid-cols-[200px_1fr] lg:gap-12">
          <SectionRail
            step="04"
            label={t("step3Label")}
            title={t("step3Title")}
            note={t("step3Note")}
          />
          <LedgerStatement
            entries={ledger.data}
            isLoading={ledger.isLoading}
            filter={filter}
            setFilter={setFilter}
          />
        </section>
      </Reveal>

      {qrPayment && <QrPayPanel payment={qrPayment} onClose={() => setQrPayment(null)} />}
    </div>
  );
}

/** Cột nhãn bên trái của mỗi khối — số thứ tự + eyebrow Vyra + tiêu đề + ghi chú. */
function SectionRail({
  step,
  label,
  title,
  note,
}: {
  step: string;
  label: string;
  title: string;
  note: string;
}) {
  return (
    <div className="lg:sticky lg:top-28 lg:self-start">
      <div className="flex items-center gap-3 lg:flex-col lg:items-start lg:gap-4">
        <span className="font-numeric text-2xl font-bold tabular text-ink-disabled">{step}</span>
        <div className="hidden h-8 w-px bg-gradient-to-b from-emerald-400/40 to-transparent lg:block" />
        <FilmLabel className="text-emerald-300/80">{label}</FilmLabel>
      </div>
      <h2 className="mt-3 font-display text-xl font-bold text-ink-high lg:mt-5 lg:text-2xl">{title}</h2>
      <p className="mt-2 hidden max-w-[18ch] text-sm leading-relaxed text-ink-low lg:block">{note}</p>
    </div>
  );
}
