"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Plus,
  Gift,
  Lock,
  Check,
  RotateCcw,
  ArrowDownToLine,
  Loader2,
  Sparkles,
} from "lucide-react";
import { useWallet, useLedger } from "@/lib/query/hooks";
import { useTopup } from "@/lib/query/mutations";
import { api } from "@/lib/api/endpoints";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { CreditValue } from "@/components/ui/credit-value";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { formatDate } from "@/lib/job-status";
import { cn } from "@/lib/utils/cn";
import type { LedgerKind } from "@/lib/api/types";

const META: Record<LedgerKind, { label: string; icon: typeof Plus; color: string }> = {
  TOPUP: { label: "Nạp credit", icon: ArrowDownToLine, color: "text-success" },
  BONUS: { label: "Tặng", icon: Gift, color: "text-violet-300" },
  HOLD: { label: "Tạm giữ", icon: Lock, color: "text-hold" },
  SETTLE: { label: "Quyết toán", icon: Check, color: "text-ink-medium" },
  REFUND: { label: "Hoàn lại", icon: RotateCcw, color: "text-refund" },
  ADJUST: { label: "Điều chỉnh", icon: Plus, color: "text-ink-medium" },
  EXPIRE: { label: "Hết hạn", icon: RotateCcw, color: "text-ink-low" },
};

const vnd = (n: number) => n.toLocaleString("vi-VN") + "đ";

export default function BillingPage() {
  const wallet = useWallet();
  const ledger = useLedger(80);
  const packs = useQuery({ queryKey: ["packs"], queryFn: api.billingPacks });
  const topup = useTopup();
  const [provider, setProvider] = useState<"dev" | "momo" | "vnpay">("dev");

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-bold text-ink-high lg:text-[34px]">Ví & Sổ cái</h1>

      {/* balance */}
      <GlassCard bordered className="relative overflow-hidden p-7">
        <div className="glow-radial pointer-events-none absolute inset-x-0 -top-20 h-40" />
        <div className="relative">
          <span className="text-sm text-ink-low">Số dư khả dụng</span>
          <div className="mt-1 font-numeric text-4xl font-bold text-ink-high">
            {wallet.isLoading ? (
              <Skeleton className="h-10 w-40" />
            ) : (
              <CreditValue value={wallet.data?.balance_credits ?? 0} />
            )}
          </div>
          {(wallet.data?.held_credits ?? 0) > 0 && (
            <div className="mt-2 inline-flex items-center gap-1.5 rounded-full border border-hold/30 bg-hold/[0.12] px-3 py-1 text-xs text-hold">
              <Lock className="h-3.5 w-3.5" /> Đang giữ{" "}
              <CreditValue value={wallet.data!.held_credits} suffix={null} className="text-xs" />
            </div>
          )}
        </div>
      </GlassCard>

      {/* nạp credit */}
      <div>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wider text-ink-low">Nạp credit</h2>
        {packs.isLoading || !packs.data ? (
          <div className="grid gap-4 sm:grid-cols-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-40 w-full rounded-xl" />
            ))}
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-3">
            {packs.data.map((p, i) => (
              <GlassCard key={p.id} bordered={i === 1} className={cn("p-5", i === 1 && "scale-[1.02]")}>
                {i === 1 && (
                  <Badge tone="brand" className="mb-2">
                    <Sparkles className="h-3 w-3" /> Phổ biến
                  </Badge>
                )}
                <h3 className="font-semibold text-ink-high">{p.name}</h3>
                <div className="mt-2 font-numeric text-3xl font-bold text-ink-high">
                  {p.credits.toLocaleString("vi-VN")}
                  <span className="ml-1 text-sm font-normal text-ink-low">credit</span>
                </div>
                <div className="mt-1 text-ink-medium">{vnd(p.amount_vnd)}</div>
                <Button
                  className="mt-4 w-full gap-2"
                  variant={i === 1 ? "primary" : "glass"}
                  disabled={topup.isPending}
                  onClick={() => topup.mutate({ packId: p.id, provider })}
                >
                  {topup.isPending && topup.variables?.packId === p.id ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Plus className="h-4 w-4" />
                  )}
                  Nạp
                </Button>
              </GlassCard>
            ))}
          </div>
        )}
        {topup.isSuccess && topup.data?.status === "succeeded" && (
          <p className="mt-3 text-sm text-success">
            Đã nạp {topup.data.credits.toLocaleString("vi-VN")} credit. Số dư đã cập nhật.
          </p>
        )}
        <div className="mt-4 flex flex-wrap items-center gap-2">
          <span className="text-xs text-ink-low">Cổng:</span>
          {([
            ["dev", "Dev (thử)"],
            ["momo", "MoMo"],
            ["vnpay", "VNPay"],
          ] as const).map(([v, label]) => (
            <button
              key={v}
              onClick={() => setProvider(v)}
              className={cn(
                "rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors",
                provider === v
                  ? "border-violet-400/40 bg-violet-500/20 text-ink-high"
                  : "border-white/10 text-ink-low hover:text-ink-medium",
              )}
            >
              {label}
            </button>
          ))}
        </div>
        {topup.isError && (
          <p className="mt-2 text-sm text-danger">
            {topup.error instanceof Error ? topup.error.message : "Nạp lỗi"} — cổng có thể chưa được cấu hình.
          </p>
        )}
        <p className="mt-2 text-xs text-ink-disabled">
          MoMo/VNPay bật khi chủ shop cấu hình khoá merchant; cổng "Dev" nạp tức thì để thử.
        </p>
      </div>

      {/* ledger */}
      <div>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wider text-ink-low">
          Lịch sử minh bạch
        </h2>
        <GlassCard className="divide-y divide-white/[0.05] p-0">
          {ledger.isLoading ? (
            <div className="flex items-center gap-2 p-5 text-ink-low">
              <Loader2 className="h-4 w-4 animate-spin" /> Đang tải…
            </div>
          ) : !ledger.data || ledger.data.length === 0 ? (
            <p className="p-6 text-center text-ink-low">Chưa có giao dịch.</p>
          ) : (
            ledger.data.map((e) => {
              const m = META[e.entry_type] ?? META.ADJUST;
              const positive = e.delta_credits > 0;
              return (
                <div key={e.id} className="flex items-center gap-3 px-4 py-3">
                  <span className={cn("grid h-9 w-9 place-items-center rounded-lg bg-white/[0.05]", m.color)}>
                    <m.icon className="h-4 w-4" />
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="text-sm text-ink-high">{m.label}</div>
                    <div className="truncate text-xs text-ink-low">{e.note || formatDate(e.created_at)}</div>
                  </div>
                  <div className="text-right">
                    <div className={cn("font-numeric text-sm font-semibold tabular", positive ? "text-success" : "text-ink-medium")}>
                      {positive ? "+" : ""}
                      {e.delta_credits.toLocaleString("vi-VN")}
                    </div>
                    <div className="font-mono text-[11px] text-ink-disabled">
                      dư {e.balance_after.toLocaleString("vi-VN")}
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </GlassCard>
        <p className="mt-3 text-center text-xs text-ink-low">
          Mọi lần giữ, dùng, hoàn đều ghi lại. Không bao giờ trừ tiền âm thầm.
        </p>
      </div>
    </div>
  );
}
