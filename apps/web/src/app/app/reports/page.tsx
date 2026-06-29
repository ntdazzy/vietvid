"use client";

import { Film, CheckCircle2, XCircle, Coins, TrendingUp, Link2, MousePointerClick, Activity, Wallet, ArrowUpRight } from "lucide-react";
import { useTranslations } from "next-intl";
import { useQuery } from "@tanstack/react-query";
import { useWallet, useLedger, useJobs } from "@/lib/query/hooks";
import { api } from "@/lib/api/endpoints";
import { GlassCard } from "@/components/ui/glass-card";
import { Skeleton } from "@/components/ui/skeleton";
import { FilmLabel } from "@/components/ui/cinematic";
import { Reveal } from "@/components/marketing/reveal";
import { isFailed } from "@/lib/job-status";
import { cn } from "@/lib/utils/cn";
import { SuccessGauge } from "@/components/reports/success-gauge";
import { FlowLegend, MetricCell, AffiliateRow } from "@/components/reports/report-cells";
import { ReportsSkeleton } from "@/components/reports/reports-skeleton";
import { ActivityChart } from "@/components/reports/activity-chart";

export default function ReportsPage() {
  const t = useTranslations("reports");
  const wallet = useWallet();
  const ledger = useLedger(200);
  const jobs = useJobs(100);
  const affiliate = useQuery({ queryKey: ["affiliate-stats"], queryFn: api.affiliateStats });

  const loading = wallet.isLoading || ledger.isLoading || jobs.isLoading;

  const items = jobs.data?.items ?? [];
  const total = items.length;
  const ready = items.filter((j) => j.status === "READY").length;
  const failed = items.filter((j) => isFailed(j.status)).length;
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

  if (loading) return <ReportsSkeleton />;

  return (
    <div className="flex flex-col gap-6">
      {/* ── BẢNG ĐIỀU KHIỂN — hero split: đồng hồ tỉ lệ thành công + nhịp 14 ngày ── */}
      <Reveal>
        <section className="relative overflow-hidden rounded-3xl glass-bordered">
          {/* glow nền + lưới mờ tạo cảm giác "bảng số liệu" */}
          <div
            className="pointer-events-none absolute -top-24 left-8 h-72 w-72 rounded-full blur-3xl"
            style={{ background: "rgba(16,185,129,0.18)" }}
          />
          <div
            className="pointer-events-none absolute inset-0 opacity-[0.05]"
            style={{
              backgroundImage:
                "linear-gradient(to right, rgba(255,255,255,0.6) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.6) 1px, transparent 1px)",
              backgroundSize: "44px 44px",
            }}
          />

          <div className="relative grid gap-0 lg:grid-cols-[minmax(0,0.85fr)_minmax(0,1.15fr)]">
            {/* TRÁI — đồng hồ tỉ lệ thành công (số thật) */}
            <div className="flex flex-col justify-between gap-6 border-b border-white/[0.06] p-6 sm:p-8 lg:border-b-0 lg:border-r">
              <div>
                <FilmLabel>{t("heroLabel")}</FilmLabel>
                <h1 className="mt-3 font-display text-3xl font-extrabold leading-[1.05] text-ink-high sm:text-4xl">
                  {t("heroTitle")}
                </h1>
                <p className="mt-2 max-w-sm text-sm text-ink-medium">
                  {t("heroSubtitle")}
                </p>
              </div>

              <div className="flex items-center gap-5">
                <SuccessGauge value={successRate} ariaLabel={t("gaugeAria", { value: successRate })} />
                <div className="min-w-0">
                  <div className="text-xs uppercase tracking-[0.16em] text-ink-low">{t("successRateLabel")}</div>
                  <div className="mt-1 flex flex-wrap items-baseline gap-x-2 text-sm text-ink-low">
                    <span className="font-numeric text-emerald-300">{ready.toLocaleString("vi-VN")}</span> {t("doneSuffix")}
                    {running > 0 && (
                      <>
                        <span className="text-ink-disabled">·</span>
                        <span className="font-numeric text-violet-300">{running.toLocaleString("vi-VN")}</span> {t("runningSuffix")}
                      </>
                    )}
                    {failed > 0 && (
                      <>
                        <span className="text-ink-disabled">·</span>
                        <span className="font-numeric text-rose-300">{failed.toLocaleString("vi-VN")}</span> {t("failedSuffix")}
                      </>
                    )}
                  </div>
                  <div className="mt-2 text-xs text-ink-low">
                    {t("ofRecentBefore")} <span className="font-numeric text-ink-medium">{total.toLocaleString("vi-VN")}</span> {t("ofRecentAfter")}
                  </div>
                </div>
              </div>
            </div>

            {/* PHẢI — nhịp tạo video 14 ngày */}
            <div className="flex flex-col p-6 sm:p-8">
              <ActivityChart days={days} maxDay={maxDay} t={t} />
              <p className="mt-4 text-xs text-ink-low">
                {total === 0
                  ? t("rhythmEmpty")
                  : t("rhythmSummary", { total: total.toLocaleString("vi-VN") })}
              </p>
            </div>
          </div>
        </section>
      </Reveal>

      {/* ── KÉT CREDIT — bento bất đối xứng: dòng tiền lớn + 3 chỉ số dọc ── */}
      <Reveal delay={0.05}>
        <section className="grid gap-4 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
          {/* dòng credit — thanh ngang lớn + chú thích */}
          <GlassCard className="flex flex-col p-6">
            <div className="mb-1 flex items-center gap-2 text-sm font-medium text-ink-medium">
              <Coins className="h-4 w-4 text-emerald-300" /> {t("creditFlow")}
            </div>
            <p className="mb-5 text-xs text-ink-low">{t("creditFlowSub")}</p>

            <div className="flex h-4 w-full overflow-hidden rounded-full bg-white/[0.05]">
              <div className="bg-violet-500/70 transition-all" style={{ width: `${pct(used)}%` }} />
              <div className="bg-hold/70 transition-all" style={{ width: `${pct(held)}%` }} />
              <div className="bg-emerald-500/70 transition-all" style={{ width: `${pct(balance)}%` }} />
            </div>

            <div className="mt-5 grid grid-cols-3 gap-3">
              <FlowLegend color="bg-violet-500/70" label={t("flowUsed")} value={used} sub={`${Math.round(pct(used))}%`} />
              <FlowLegend color="bg-hold/70" label={t("flowHeld")} value={held} sub={`${Math.round(pct(held))}%`} />
              <FlowLegend color="bg-emerald-500/70" label={t("flowRemaining")} value={balance} sub={`${Math.round(pct(balance))}%`} />
            </div>

            <div className="mt-auto flex flex-wrap items-center gap-x-6 gap-y-2 border-t border-white/[0.06] pt-4 text-xs text-ink-low">
              <span>
                {t("toppedUpBefore")} <span className="font-numeric text-ink-medium">{toppedUp.toLocaleString("vi-VN")}</span> {t("toppedUpAfter")}
              </span>
              <span>
                {t("refundedLabel")} <span className="font-numeric text-refund">{refunded.toLocaleString("vi-VN")}</span>
              </span>
            </div>
          </GlassCard>

          {/* số dư nổi bật — "mặt két" dọc */}
          <GlassCard bordered className="relative flex flex-col justify-between overflow-hidden p-6">
            <div
              className="pointer-events-none absolute -bottom-16 -right-10 h-44 w-44 rounded-full blur-3xl"
              style={{ background: "rgba(16,185,129,0.16)" }}
            />
            <div className="relative flex items-center gap-2 text-sm font-medium text-ink-medium">
              <Wallet className="h-4 w-4 text-emerald-300" /> {t("currentBalance")}
            </div>
            <div className="relative">
              <div className="font-numeric text-5xl font-extrabold tabular text-gradient">
                {balance.toLocaleString("vi-VN")}
              </div>
              <div className="mt-1 text-sm text-ink-low">{t("availableCredits")}</div>
              {held > 0 && (
                <div className="mt-3 inline-flex items-center gap-1.5 rounded-lg border border-hold/25 bg-hold/[0.08] px-2.5 py-1 text-xs text-hold">
                  {t("flowHeld")} <span className="font-numeric">{held.toLocaleString("vi-VN")}</span>
                </div>
              )}
            </div>
          </GlassCard>
        </section>
      </Reveal>

      {/* ── CHI TIẾT — video + affiliate trong một dải, bất đối xứng ── */}
      <Reveal delay={0.1}>
        <section className="grid gap-4 lg:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)]">
          {/* video — dòng chỉ số ngang */}
          <GlassCard className="flex flex-col p-6">
            <h2 className="mb-4 text-sm font-semibold uppercase tracking-[0.16em] text-ink-low">{t("videoSection")}</h2>
            <div className="grid grid-cols-3 divide-x divide-white/[0.06]">
              <MetricCell icon={Film} accent="text-sky-300" label={t("metricTotal")} value={total} />
              <MetricCell icon={CheckCircle2} accent="text-emerald-300" label={t("metricSuccess")} value={ready} hint={running > 0 ? t("runningHint", { count: running }) : undefined} />
              <MetricCell icon={XCircle} accent="text-rose-300" label={t("metricFailed")} value={failed} />
            </div>
          </GlassCard>

          {/* affiliate — bảng dọc gọn */}
          <GlassCard className="flex flex-col p-6">
            <h2 className="mb-4 text-sm font-semibold uppercase tracking-[0.16em] text-ink-low">{t("affiliateSection")}</h2>
            <div className="flex flex-col gap-3">
              <AffiliateRow icon={Link2} label={t("shortLinks")} value={affiliate.data?.links ?? 0} />
              <AffiliateRow icon={MousePointerClick} label={t("clicks")} value={affiliate.data?.clicks ?? 0} />
            </div>
          </GlassCard>
        </section>
      </Reveal>

      <p className="flex items-start gap-1.5 text-xs text-ink-low">
        <ArrowUpRight className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-300/70" />
        {t("footerNote")}
      </p>
    </div>
  );
}
