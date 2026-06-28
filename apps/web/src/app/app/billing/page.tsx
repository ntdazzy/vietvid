"use client";

import { useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Wallet } from "lucide-react";
import { useWallet, useLedger } from "@/lib/query/hooks";
import { useTopup } from "@/lib/query/mutations";
import { api } from "@/lib/api/endpoints";
import { Reveal } from "@/components/marketing/reveal";
import { WalletHero } from "@/components/billing/wallet-hero";
import { TrustProof } from "@/components/billing/trust-proof";
import { PackCard } from "@/components/billing/pack-card";
import { GatewayPicker, type Gateway } from "@/components/billing/gateway-picker";
import { LedgerStatement } from "@/components/billing/ledger-statement";
import type { LedgerKind } from "@/lib/api/types";

type Filter = LedgerKind | "ALL";

export default function BillingPage() {
  const wallet = useWallet();
  const ledger = useLedger(80);
  const packsQuery = useQuery({ queryKey: ["packs"], queryFn: api.billingPacks });
  const topup = useTopup();
  const [provider, setProvider] = useState<Gateway>("dev");
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

  const topupError = topup.isError
    ? topup.error instanceof Error
      ? topup.error.message
      : "Nạp lỗi"
    : null;

  return (
    <div className="mx-auto flex max-w-[900px] flex-col gap-8">
      {/* header */}
      <div className="flex items-center gap-2">
        <span className="grid h-10 w-10 place-items-center rounded-xl bg-grad-brand-soft">
          <Wallet className="h-5 w-5 text-violet-300" />
        </span>
        <h1 className="font-display text-2xl font-bold text-ink-high lg:text-[32px]">Ví &amp; Sổ cái</h1>
        <p className="ml-auto hidden text-sm text-ink-low md:block">
          1 credit = 150đ · một video ≈ 100–180 credit
        </p>
      </div>

      {/* hero ví */}
      <Reveal delay={0.05}>
        <WalletHero
          wallet={wallet.data}
          loading={wallet.isLoading}
          onScrollToHeld={scrollToHeld}
          onScrollToPacks={scrollToPacks}
        />
      </Reveal>

      {/* tin cậy: GIỮ → DÙNG → HOÀN */}
      <Reveal delay={0.1}>
        <TrustProof entries={ledger.data} balance={wallet.data?.balance_credits ?? 0} />
      </Reveal>

      {/* nạp credit */}
      <Reveal delay={0.15}>
        <div ref={packsRef} className="flex flex-col gap-4 scroll-mt-28">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-ink-low">Nạp credit</h2>

          <GatewayPicker provider={provider} setProvider={setProvider} error={topupError} />

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
                  pending={topup.isPending && topup.variables?.packId === p.id}
                  disabled={topup.isPending}
                  onBuy={() => topup.mutate({ packId: p.id, provider })}
                />
              ))}
            </div>
          )}

          {topup.isSuccess && topup.data?.status === "succeeded" && (
            <p className="text-sm text-success">
              Đã nạp {topup.data.credits.toLocaleString("vi-VN")} credit. Số dư đã cập nhật.
            </p>
          )}
        </div>
      </Reveal>

      {/* sổ cái */}
      <Reveal delay={0.2}>
        <div ref={ledgerRef} className="scroll-mt-28">
          <LedgerStatement
            entries={ledger.data}
            isLoading={ledger.isLoading}
            filter={filter}
            setFilter={setFilter}
          />
        </div>
      </Reveal>
    </div>
  );
}
