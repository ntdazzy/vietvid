"use client";

import { Film, CheckCircle2, XCircle, Coins, ArrowDownToLine, RotateCcw, Lock, TrendingUp, Link2, MousePointerClick } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { useWallet, useLedger, useJobs } from "@/lib/query/hooks";
import { api } from "@/lib/api/endpoints";
import { GlassCard } from "@/components/ui/glass-card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils/cn";

const FAILED = new Set(["FAILED", "QA_FAIL", "REFUNDED"]);

export default function ReportsPage() {
  const wallet = useWallet();
  const ledger = useLedger(200);
  const jobs = useJobs(100);
  const affiliate = useQuery({ queryKey: ["affiliate-stats"], queryFn: api.affiliateStats });

  const loading = wallet.isLoading || ledger.isLoading || jobs.isLoading;

  const items = jobs.data?.items ?? [];
  const total = items.length;
  const ready = items.filter((j) => j.status === "READY").length;
  const failed = items.filter((j) => FAILED.has(j.status)).length;

  const led = ledger.data ?? [];
  const sum = (types: string[]) =>
    led.filter((e) => types.includes(e.entry_type)).reduce((a, e) => a + e.delta_credits, 0);
  const toppedUp = sum(["TOPUP", "BONUS"]);
  const refunded = sum(["REFUND"]);
  const balance = wallet.data?.balance_credits ?? 0;
  const held = wallet.data?.held_credits ?? 0;
  const used = Math.max(0, toppedUp - balance - held); // đã nạp - còn lại - đang giữ = đã dùng

  return (
    <div className="flex flex-col gap-8">
      <div>
        <div className="flex items-center gap-2">
          <span className="grid h-10 w-10 place-items-center rounded-xl bg-grad-brand-soft">
            <TrendingUp className="h-5 w-5 text-violet-300" />
          </span>
          <h1 className="font-display text-2xl font-bold text-ink-high lg:text-[32px]">Báo cáo</h1>
        </div>
        <p className="mt-1 text-ink-low">Tổng quan hoạt động & credit của bạn.</p>
      </div>

      {loading ? (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="h-28 w-full rounded-xl" />
          ))}
        </div>
      ) : (
        <>
          <section>
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wider text-ink-low">Video</h2>
            <div className="grid grid-cols-2 gap-4 lg:grid-cols-3">
              <Stat icon={Film} label="Tổng video" value={total} tone="brand" />
              <Stat icon={CheckCircle2} label="Thành công" value={ready} tone="success" />
              <Stat icon={XCircle} label="Lỗi / hoàn" value={failed} tone="danger" />
            </div>
          </section>

          <section>
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wider text-ink-low">Credit</h2>
            <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
              <Stat icon={ArrowDownToLine} label="Đã nạp/tặng" value={toppedUp} tone="success" />
              <Stat icon={TrendingUp} label="Đã dùng" value={used} tone="brand" />
              <Stat icon={RotateCcw} label="Đã hoàn" value={refunded} tone="refund" />
              <Stat icon={Lock} label="Đang giữ" value={held} tone="hold" />
              <Stat icon={Coins} label="Số dư" value={balance} tone="neutral" />
            </div>
          </section>

          <section>
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wider text-ink-low">Affiliate</h2>
            <div className="grid grid-cols-2 gap-4 lg:grid-cols-3">
              <Stat icon={Link2} label="Link rút gọn" value={affiliate.data?.links ?? 0} tone="brand" />
              <Stat icon={MousePointerClick} label="Lượt click" value={affiliate.data?.clicks ?? 0} tone="success" />
            </div>
          </section>

          <p className="text-xs text-ink-low">
            "Đã dùng" = đã nạp − số dư − đang giữ. Mọi con số lấy từ sổ cái minh bạch của bạn.
          </p>
        </>
      )}
    </div>
  );
}

const TONE: Record<string, string> = {
  brand: "text-violet-300",
  success: "text-success",
  danger: "text-danger",
  refund: "text-refund",
  hold: "text-hold",
  neutral: "text-ink-high",
};

function Stat({
  icon: Icon,
  label,
  value,
  tone,
}: {
  icon: typeof Film;
  label: string;
  value: number;
  tone: keyof typeof TONE;
}) {
  return (
    <GlassCard className="p-4">
      <Icon className={cn("h-5 w-5", TONE[tone])} />
      <div className="mt-3 font-numeric text-3xl font-bold tabular text-ink-high">
        {value.toLocaleString("vi-VN")}
      </div>
      <div className="mt-0.5 text-sm text-ink-low">{label}</div>
    </GlassCard>
  );
}
