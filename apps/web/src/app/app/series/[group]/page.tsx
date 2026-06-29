"use client";

import { use } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Trophy, MousePointerClick, Play, Loader2, Sparkles, Layers, Crown } from "lucide-react";
import { api } from "@/lib/api/endpoints";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { FilmLabel } from "@/components/ui/cinematic";
import { Reveal } from "@/components/marketing/reveal";
import { ACCENTS } from "@/lib/accents";
import { cn } from "@/lib/utils/cn";
import type { VariantPerf } from "@/lib/api/types";

const A = ACCENTS.amber;

export default function SeriesPerfPage({ params }: { params: Promise<{ group: string }> }) {
  const { group } = use(params);
  const perf = useQuery({
    queryKey: ["series-perf", group],
    queryFn: () => api.seriesPerformance(group),
    refetchInterval: 15_000, // click dồn về theo thời gian
  });

  const rows = perf.data ?? [];
  const totalClicks = rows.reduce((a, v) => a + v.clicks, 0);
  const maxClicks = rows.reduce((a, v) => Math.max(a, v.clicks), 0);
  // bản thắng do hệ thống đánh dấu; nếu chưa có thì lấy bản đang dẫn click để "spotlight".
  const winner = rows.find((v) => v.is_winner) ?? (maxClicks > 0 ? rows.find((v) => v.clicks === maxClicks) : undefined);
  const leadConfirmed = rows.some((v) => v.is_winner);

  return (
    <div className="flex max-w-4xl flex-col gap-8">
      {/* ── HEADER: dải eyebrow + tiêu đề + trạng thái cập nhật trực tiếp ── */}
      <header className="relative overflow-hidden rounded-3xl glass-bordered p-6 sm:p-8">
        <div
          className="pointer-events-none absolute -right-16 -top-20 h-56 w-56 rounded-full blur-3xl"
          style={{ background: A.glow }}
        />
        <div className="relative flex flex-col gap-4">
          <div className="flex items-center justify-between gap-3">
            <FilmLabel>Đường đua click</FilmLabel>
            {perf.isFetching ? (
              <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-400/25 bg-amber-500/10 px-2.5 py-1 text-[11px] font-medium text-amber-200">
                <Loader2 className="h-3 w-3 animate-spin" /> đang cập nhật
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 rounded-full border border-white/10 px-2.5 py-1 text-[11px] font-medium text-ink-low">
                <span className="h-1.5 w-1.5 rounded-full bg-amber-400/80" /> cập nhật mỗi 15 giây
              </span>
            )}
          </div>
          <div>
            <h1 className="font-display text-2xl font-bold leading-tight text-ink-high lg:text-[34px]">
              Biến thể nào <span className="text-gradient">kéo nhiều click</span> nhất?
            </h1>
            <p className="mt-2 max-w-xl text-ink-medium">
              Mỗi biến thể có một link đo riêng. Chia sẻ chúng đi, hệ thống xếp hạng theo click thật rồi
              chỉ ra bản nên nhân thêm.
            </p>
          </div>
        </div>
      </header>

      {perf.isLoading ? (
        <SeriesSkeleton />
      ) : rows.length === 0 ? (
        <EmptyState />
      ) : (
        <>
          {/* ── BENTO: spotlight bản dẫn đầu (rộng) + cột số liệu (hẹp) ── */}
          <Reveal>
            <div className="grid gap-4 lg:grid-cols-12">
              {/* Spotlight — bản dẫn đầu */}
              <div className="lg:col-span-7">
                {winner ? <WinnerSpotlight v={winner} confirmed={leadConfirmed} share={pct(winner.clicks, totalClicks)} /> : <NoLeadYet />}
              </div>

              {/* Cột số liệu thật */}
              <div className="grid grid-cols-2 gap-4 lg:col-span-5 lg:grid-cols-1">
                <StatTile icon={MousePointerClick} label="Tổng click" value={totalClicks} hint="trên tất cả biến thể" />
                <StatTile icon={Layers} label="Số biến thể" value={rows.length} hint="đang chạy A/B" />
              </div>
            </div>
          </Reveal>

          {/* ── ĐƯỜNG ĐUA: mỗi biến thể là một làn, thanh dài theo tỉ lệ click ── */}
          <Reveal delay={0.05}>
            <section className="flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold uppercase tracking-[0.16em] text-ink-low">Bảng xếp hạng</h2>
                <FilmLabel dot={false} className="hidden sm:inline-flex">
                  {rows.length} làn đua
                </FilmLabel>
              </div>
              <div className="flex flex-col gap-2.5">
                {rows.map((v, i) => (
                  <RaceLane key={v.job_id} v={v} rank={i + 1} share={pct(v.clicks, maxClicks)} />
                ))}
              </div>
            </section>
          </Reveal>

          {/* ── CTA: nhân bản bản thắng ── */}
          <div className="flex flex-wrap items-center gap-3">
            <Link href="/app/create">
              <Button size="lg" className="gap-2">
                <Sparkles className="h-4 w-4" /> Nhân bản bản thắng
              </Button>
            </Link>
            <span className="text-sm text-ink-low">
              {leadConfirmed
                ? "Dựng thêm các biến thể giống bản đang thắng."
                : "Cần thêm click để hệ thống chốt bản thắng — cứ chia sẻ link đi đã."}
            </span>
          </div>
        </>
      )}
    </div>
  );
}

/* ── Spotlight bản dẫn đầu: số click lớn + thanh tỉ lệ + nút xem ── */
function WinnerSpotlight({ v, confirmed, share }: { v: VariantPerf; confirmed: boolean; share: number }) {
  return (
    <GlassCard
      bordered
      className="relative flex h-full flex-col gap-5 overflow-hidden p-6 ring-1 ring-amber-400/30"
    >
      <div
        className="pointer-events-none absolute -bottom-16 -left-10 h-48 w-48 rounded-full blur-3xl"
        style={{ background: A.glow }}
      />
      <div className="relative flex items-start justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <span className={cn("grid h-11 w-11 place-items-center rounded-2xl bg-gradient-to-br ring-1 ring-amber-400/25", A.tile, A.icon)}>
            <Crown className="h-5 w-5" />
          </span>
          <div>
            <FilmLabel dot={false}>{confirmed ? "Bản thắng" : "Đang dẫn đầu"}</FilmLabel>
            <div className="mt-0.5 truncate font-display text-lg font-bold text-ink-high">
              {v.label || "Biến thể"}
            </div>
          </div>
        </div>
        {confirmed && (
          <span className="inline-flex items-center gap-1 rounded-full border border-amber-400/30 bg-amber-500/15 px-2.5 py-1 text-[11px] font-semibold text-amber-200">
            <Trophy className="h-3 w-3" /> Thắng
          </span>
        )}
      </div>

      <div className="relative">
        <div className="flex items-baseline gap-2">
          <span className="font-numeric text-5xl font-bold tabular text-ink-high">{v.clicks}</span>
          <span className="text-sm text-ink-low">click</span>
        </div>
        <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-white/[0.06]">
          <div
            className="h-full rounded-full bg-gradient-to-r from-amber-500 to-orange-500"
            style={{ width: `${share}%` }}
          />
        </div>
        <div className="mt-1.5 text-xs text-ink-low">
          {share}% tổng click · {viStatus(v.status)}
        </div>
      </div>

      <div className="relative mt-auto">
        {v.has_video ? (
          <Link href={`/app/v/${v.job_id}`}>
            <Button variant="glass" className="gap-1.5">
              <Play className="h-4 w-4" /> Xem bản này
            </Button>
          </Link>
        ) : (
          <span className="text-sm text-ink-low">Video đang dựng…</span>
        )}
      </div>
    </GlassCard>
  );
}

/* ── Một làn đua: rank + nhãn + thanh tỉ lệ click ── */
function RaceLane({ v, rank, share }: { v: VariantPerf; rank: number; share: number }) {
  const win = v.is_winner;
  return (
    <div
      className={cn(
        "group relative overflow-hidden rounded-2xl glass-bordered p-4 transition-all duration-200",
        win && "ring-1 ring-amber-400/40",
      )}
    >
      {/* thanh tỉ lệ làm nền — đo bằng click thật so với bản cao nhất */}
      <div
        className={cn(
          "pointer-events-none absolute inset-y-0 left-0 transition-[width] duration-700 ease-out",
          win ? "bg-gradient-to-r from-amber-500/20 to-transparent" : "bg-white/[0.04]",
        )}
        style={{ width: `${Math.max(share, 4)}%` }}
        aria-hidden
      />
      <div className="relative flex items-center gap-4">
        <span
          className={cn(
            "grid h-9 w-9 shrink-0 place-items-center rounded-xl font-numeric text-sm font-bold tabular",
            win ? "bg-amber-400/15 text-amber-300" : "bg-white/[0.05] text-ink-low",
          )}
        >
          {win ? <Trophy className="h-4 w-4" /> : rank}
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="truncate text-sm font-medium text-ink-high">{v.label || "Biến thể"}</span>
            {win && <Badge tone="brand">Thắng</Badge>}
          </div>
          <div className="text-xs text-ink-low">{viStatus(v.status)}</div>
        </div>
        <div className="shrink-0 text-right">
          <div className="font-numeric text-base font-bold tabular text-ink-high">{v.clicks}</div>
          <div className="text-[11px] text-ink-low">click</div>
        </div>
        {v.has_video && (
          <Link href={`/app/v/${v.job_id}`} aria-label={`Xem ${v.label || "biến thể"}`}>
            <Button size="sm" variant="glass" className="gap-1.5">
              <Play className="h-3.5 w-3.5" /> Xem
            </Button>
          </Link>
        )}
      </div>
    </div>
  );
}

function StatTile({
  icon: Icon,
  label,
  value,
  hint,
}: {
  icon: typeof MousePointerClick;
  label: string;
  value: number;
  hint: string;
}) {
  return (
    <GlassCard className="flex flex-col justify-between gap-3 p-5">
      <span className={cn("grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br ring-1 ring-amber-400/20", A.tile, A.icon)}>
        <Icon className="h-4 w-4" />
      </span>
      <div>
        <div className="font-numeric text-2xl font-bold tabular text-ink-high">{value}</div>
        <div className="text-sm text-ink-medium">{label}</div>
        <div className="text-xs text-ink-low">{hint}</div>
      </div>
    </GlassCard>
  );
}

function NoLeadYet() {
  return (
    <GlassCard bordered className="flex h-full flex-col items-start justify-center gap-2 p-6">
      <FilmLabel dot={false}>Chưa có bản dẫn đầu</FilmLabel>
      <div className="font-display text-lg font-bold text-ink-high">Chưa có click nào</div>
      <p className="text-sm text-ink-low">Chia sẻ link đo của từng biến thể để bắt đầu cuộc đua.</p>
    </GlassCard>
  );
}

function EmptyState() {
  return (
    <GlassCard bordered className="flex flex-col items-center gap-3 px-6 py-14 text-center">
      <span className={cn("grid h-12 w-12 place-items-center rounded-2xl bg-gradient-to-br ring-1 ring-amber-400/20", A.tile, A.icon)}>
        <Trophy className="h-6 w-6" />
      </span>
      <div className="font-display text-lg font-bold text-ink-high">Loạt này chưa có biến thể nào</div>
      <p className="max-w-sm text-sm text-ink-low">
        Tạo một loạt A/B từ trang tạo video — mỗi biến thể sẽ xuất hiện ở đây kèm số click riêng.
      </p>
      <Link href="/app/create" className="mt-1">
        <Button className="gap-2">
          <Sparkles className="h-4 w-4" /> Tạo loạt biến thể
        </Button>
      </Link>
    </GlassCard>
  );
}

function SeriesSkeleton() {
  return (
    <div className="flex flex-col gap-8">
      <div className="grid gap-4 lg:grid-cols-12">
        <Skeleton className="h-56 rounded-3xl lg:col-span-7" />
        <div className="grid grid-cols-2 gap-4 lg:col-span-5 lg:grid-cols-1">
          <Skeleton className="h-24 rounded-xl" />
          <Skeleton className="h-24 rounded-xl" />
        </div>
      </div>
      <div className="flex flex-col gap-2.5">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-[68px] rounded-2xl" />
        ))}
      </div>
    </div>
  );
}

/* tỉ lệ % an toàn (tránh chia 0) */
function pct(n: number, base: number): number {
  if (base <= 0) return 0;
  return Math.round((n / base) * 100);
}

function viStatus(s: string): string {
  const m: Record<string, string> = {
    QUEUED: "đang chờ", RUNNING: "đang tạo", READY: "xong", FAILED: "lỗi",
    QA_FAIL: "lỗi QA", REFUNDED: "đã hoàn", CANCELLED: "đã huỷ", WAITING_CONFIG: "chờ cấu hình",
  };
  return m[s] ?? s;
}
