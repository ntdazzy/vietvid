"use client";

import { Film, CheckCircle2, XCircle, Coins, ArrowDownToLine, RotateCcw, Lock, TrendingUp, Link2, MousePointerClick, Activity, Wallet } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { useWallet, useLedger, useJobs } from "@/lib/query/hooks";
import { api } from "@/lib/api/endpoints";
import { GlassCard } from "@/components/ui/glass-card";
import { Skeleton } from "@/components/ui/skeleton";
import { ScreenHero, StatTile } from "@/components/app/screen-hero";
import { cn } from "@/lib/utils/cn";

const FAILED = new Set(["FAILED", "QA_FAIL", "REFUNDED"]);
const DOW = ["CN", "T2", "T3", "T4", "T5", "T6", "T7"];

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
  const running = total - ready - failed;
  const successRate = total ? Math.round((ready / total) * 100) : 0;

  const led = ledger.data ?? [];
  const sum = (types: string[]) =>
    led.filter((e) => types.includes(e.entry_type)).reduce((a, e) => a + e.delta_credits, 0);
  const toppedUp = sum(["TOPUP", "BONUS"]);
  const refunded = sum(["REFUND"]);
  const balance = wallet.data?.balance_credits ?? 0;
  const held = wallet.data?.held_credits ?? 0;
  const used = Math.max(0, toppedUp - balance - held);

  // hoạt động 14 ngày — đếm video tạo mỗi ngày từ created_at thật
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const days = Array.from({ length: 14 }, (_, i) => {
    const d = new Date(today);
    d.setDate(d.getDate() - (13 - i));
    return { d, count: 0 };
  });
  for (const j of items) {
    if (!j.created_at) continue;
    const jd = new Date(j.created_at);
    jd.setHours(0, 0, 0, 0);
    const idx = days.findIndex((b) => b.d.getTime() === jd.getTime());
    if (idx >= 0) days[idx].count++;
  }
  const maxDay = Math.max(1, ...days.map((b) => b.count));

  // dòng credit — tỉ lệ dùng / giữ / dư trên tổng đã nạp
  const flowTotal = Math.max(1, used + held + balance);
  const pct = (n: number) => (n / flowTotal) * 100;

  return (
    <div className="flex flex-col gap-6">
      <ScreenHero
        icon={TrendingUp}
        accent="emerald"
        title="Báo cáo"
        sub="Tổng quan hoạt động & credit — số liệu thật từ sổ cái của bạn."
      >
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <StatTile icon={Wallet} label="Số dư" value={loading ? "" : balance.toLocaleString("vi-VN")} loading={loading} accent="emerald" />
          <StatTile icon={TrendingUp} label="Đã dùng" value={loading ? "" : used.toLocaleString("vi-VN")} loading={loading} accent="violet" />
          <StatTile icon={Film} label="Tổng video" value={loading ? "" : total.toLocaleString("vi-VN")} loading={loading} accent="sky" />
          <StatTile icon={CheckCircle2} label="Tỉ lệ thành công" value={loading ? "" : `${successRate}%`} loading={loading} accent="emerald" />
        </div>
      </ScreenHero>

      {loading ? (
        <div className="grid gap-4 lg:grid-cols-2">
          <Skeleton className="h-56 w-full rounded-2xl" />
          <Skeleton className="h-56 w-full rounded-2xl" />
        </div>
      ) : (
        <>
          <div className="grid gap-4 lg:grid-cols-2">
            {/* hoạt động 14 ngày */}
            <GlassCard className="flex flex-col p-5">
              <div className="mb-4 flex items-center gap-2 text-sm font-medium text-ink-medium">
                <Activity className="h-4 w-4 text-emerald-300" /> Hoạt động 14 ngày
              </div>
              <div className="flex h-32 items-end gap-1.5">
                {days.map((b, i) => (
                  <div key={i} className="flex flex-1 flex-col items-center gap-1.5" title={`${b.count} video`}>
                    <div className="flex w-full flex-1 items-end">
                      <div
                        className="w-full rounded-t bg-gradient-to-t from-emerald-500/40 to-emerald-400/80 transition-all"
                        style={{ height: `${Math.max(4, (b.count / maxDay) * 100)}%` }}
                      />
                    </div>
                    <span className="text-[9px] text-ink-disabled">{DOW[b.d.getDay()]}</span>
                  </div>
                ))}
              </div>
              <p className="mt-3 text-xs text-ink-low">
                {total === 0 ? "Chưa có video nào — tạo video đầu tiên để thấy biểu đồ." : `Tổng ${total} video trong 100 lần gần nhất.`}
              </p>
            </GlassCard>

            {/* dòng credit */}
            <GlassCard className="flex flex-col p-5">
              <div className="mb-4 flex items-center gap-2 text-sm font-medium text-ink-medium">
                <Coins className="h-4 w-4 text-emerald-300" /> Dòng credit
              </div>
              <div className="flex h-3 w-full overflow-hidden rounded-full bg-white/[0.06]">
                <div className="bg-violet-500/70" style={{ width: `${pct(used)}%` }} />
                <div className="bg-hold/70" style={{ width: `${pct(held)}%` }} />
                <div className="bg-emerald-500/70" style={{ width: `${pct(balance)}%` }} />
              </div>
              <div className="mt-4 grid grid-cols-3 gap-3">
                <FlowLegend color="bg-violet-500/70" label="Đã dùng" value={used} />
                <FlowLegend color="bg-hold/70" label="Đang giữ" value={held} />
                <FlowLegend color="bg-emerald-500/70" label="Còn lại" value={balance} />
              </div>
              <p className="mt-auto pt-4 text-xs text-ink-low">
                Tổng đã nạp/tặng: <span className="font-numeric text-ink-medium">{toppedUp.toLocaleString("vi-VN")}</span> credit · đã hoàn{" "}
                <span className="font-numeric text-refund">{refunded.toLocaleString("vi-VN")}</span>.
              </p>
            </GlassCard>
          </div>

          {/* chi tiết video */}
          <section className="flex flex-col gap-3">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-ink-low">Video</h2>
            <div className="grid grid-cols-3 gap-4">
              <StatTile icon={Film} label="Tổng video" value={total.toLocaleString("vi-VN")} accent="sky" />
              <StatTile icon={CheckCircle2} label="Thành công" value={ready.toLocaleString("vi-VN")} accent="emerald" hint={running > 0 ? `${running} đang chạy` : undefined} />
              <StatTile icon={XCircle} label="Lỗi / hoàn" value={failed.toLocaleString("vi-VN")} accent="rose" />
            </div>
          </section>

          {/* affiliate */}
          <section className="flex flex-col gap-3">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-ink-low">Affiliate</h2>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
              <StatTile icon={Link2} label="Link rút gọn" value={(affiliate.data?.links ?? 0).toLocaleString("vi-VN")} accent="amber" />
              <StatTile icon={MousePointerClick} label="Lượt click" value={(affiliate.data?.clicks ?? 0).toLocaleString("vi-VN")} accent="amber" />
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

function FlowLegend({ color, label, value }: { color: string; label: string; value: number }) {
  return (
    <div>
      <div className="flex items-center gap-1.5 text-xs text-ink-low">
        <span className={cn("h-2.5 w-2.5 rounded-sm", color)} /> {label}
      </div>
      <div className="mt-1 font-numeric text-lg font-semibold tabular text-ink-high">{value.toLocaleString("vi-VN")}</div>
    </div>
  );
}
