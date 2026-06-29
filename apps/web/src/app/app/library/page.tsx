"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { Film, Play, Plus, Clapperboard, Loader2 } from "lucide-react";
import { useJobs } from "@/lib/query/hooks";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { CreditValue } from "@/components/ui/credit-value";
import { FilmLabel } from "@/components/ui/cinematic";
import { Reveal } from "@/components/marketing/reveal";
import { statusLabel, formatDate, isTerminal } from "@/lib/job-status";
import { ACCENTS } from "@/lib/accents";
import { cn } from "@/lib/utils/cn";
import type { Job } from "@/lib/api/types";

const A = ACCENTS.emerald;

const FILTERS = [
  { key: "all", labelKey: "filterAll" },
  { key: "READY", labelKey: "filterDone" },
  { key: "RUNNING", labelKey: "filterCreating" },
  { key: "FAILED", labelKey: "filterFailed" },
] as const;

const STATUS_CLS: Record<string, string> = {
  READY: "bg-success/15 text-success",
  RUNNING: "bg-violet-500/15 text-violet-200",
  QUEUED: "bg-hold/15 text-hold",
  WAITING_CONFIG: "bg-hold/15 text-hold",
  HELD: "bg-hold/15 text-hold",
  FAILED: "bg-danger/15 text-danger",
  QA_FAIL: "bg-danger/15 text-danger",
  CANCELLED: "bg-white/[0.06] text-ink-low",
  REFUNDED: "bg-refund/15 text-refund",
};

function kindLabelKey(kind: string) {
  return kind === "kol_full" ? "kindKolAi" : "kindProduct";
}

/** Mép răng phim — motif "cuộn phim" của riêng màn Library. Thuần trang trí. */
function Perforations({ className }: { className?: string }) {
  return (
    <span aria-hidden className={cn("pointer-events-none flex flex-col justify-around py-2", className)}>
      {Array.from({ length: 8 }).map((_, i) => (
        <span key={i} className="h-1.5 w-2.5 rounded-[2px] bg-white/10" />
      ))}
    </span>
  );
}

export default function LibraryPage() {
  const t = useTranslations("library");
  const { data, isLoading, isError, refetch } = useJobs(60);
  const [filter, setFilter] = useState<string>("all");

  const all = data?.items ?? [];

  const counts = useMemo(() => {
    const c = { all: all.length, READY: 0, RUNNING: 0, FAILED: 0 };
    for (const j of all) {
      if (j.status === "READY") c.READY++;
      else if (!isTerminal(j.status)) c.RUNNING++;
      else if (j.status === "FAILED" || j.status === "QA_FAIL") c.FAILED++;
    }
    return c;
  }, [all]);

  const items = all.filter((j) =>
    filter === "all" ? true : filter === "RUNNING" ? !isTerminal(j.status) : j.status === filter,
  );

  // Featured = video hoàn tất mới nhất (mục đầu cuộn phim). Phần còn lại vào lưới.
  const featured = filter === "all" ? items.find((j) => j.status === "READY") : undefined;
  const rest = featured ? items.filter((j) => j.id !== featured.id) : items;

  return (
    <div className="flex flex-col gap-6">
      {/* ===== HERO: dải phim ngang, mép răng cưa, nền studio ===== */}
      <section className="relative overflow-hidden rounded-3xl glass-bordered">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/bg/studio.jpg" alt="" className="absolute inset-0 h-full w-full object-cover opacity-[0.18]" />
        <div className="absolute inset-0 bg-gradient-to-r from-bg-base via-bg-base/92 to-bg-base/55" />
        <div
          className="pointer-events-none absolute -top-20 right-10 h-56 w-56 rounded-full blur-3xl"
          style={{ background: A.glow }}
        />
        {/* hai dải răng phim chạy dọc hai mép — chữ ký "cuộn phim" */}
        <Perforations className="absolute left-0 top-0 h-full px-1" />
        <Perforations className="absolute right-0 top-0 h-full px-1" />

        <div className="relative flex flex-col gap-6 px-6 py-7 sm:px-12 sm:py-9">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <FilmLabel>{t("heroEyebrow")}</FilmLabel>
              <h1 className="mt-3 font-display text-3xl font-extrabold leading-[1.05] text-ink-high sm:text-[42px]">
                {t("heroTitle")}
              </h1>
              <p className="mt-2 max-w-md text-ink-medium">
                {t("heroSubtitle")}
              </p>
            </div>
            <Link href="/app/create" className="shrink-0">
              <Button size="sm" className="gap-1.5 active:scale-95">
                <Plus className="h-4 w-4" /> {t("newVideo")}
              </Button>
            </Link>
          </div>

          {/* Thống kê THẬT từ data — không bịa số */}
          <div className="flex flex-wrap gap-x-8 gap-y-3 border-t border-white/10 pt-5">
            <Stat label={t("statTotal")} value={counts.all} loading={isLoading} accentText="text-ink-high" />
            <Stat label={t("statDone")} value={counts.READY} loading={isLoading} accentText={A.text} />
            <Stat label={t("statCreating")} value={counts.RUNNING} loading={isLoading} accentText="text-violet-300" />
            <Stat label={t("statFailed")} value={counts.FAILED} loading={isLoading} accentText="text-danger" />
          </div>
        </div>
      </section>

      {/* ===== Thanh lọc dạng "khung cảnh" ===== */}
      <div className="flex flex-wrap items-center gap-2">
        <Clapperboard className={cn("mr-1 h-4 w-4", A.icon)} aria-hidden />
        {FILTERS.map((f) => {
          const active = filter === f.key;
          const n = counts[f.key as keyof typeof counts];
          return (
            <button
              key={f.key}
              onClick={() => setFilter(f.key)}
              aria-pressed={active}
              className={cn(
                "rounded-lg border px-3.5 py-1.5 text-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400/50",
                active
                  ? "border-emerald-400/50 bg-emerald-500/15 text-ink-high"
                  : "border-white/10 text-ink-low hover:border-white/25 hover:text-ink-medium",
              )}
            >
              {t(f.labelKey)}
              <span className={cn("ml-1.5 font-numeric text-xs", active ? A.text : "text-ink-disabled")}>{n}</span>
            </button>
          );
        })}
      </div>

      {/* ===== Nội dung ===== */}
      {isLoading ? (
        <LoadingGrid />
      ) : isError ? (
        <ErrorState onRetry={() => refetch()} />
      ) : items.length === 0 ? (
        <EmptyState filter={filter} />
      ) : (
        <div className="flex flex-col gap-4">
          {featured && (
            <Reveal>
              <FeaturedCard job={featured} />
            </Reveal>
          )}
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
            {rest.map((j, i) => (
              <Reveal key={j.id} delay={Math.min(i, 6) * 0.04}>
                <VideoCard job={j} />
              </Reveal>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function Stat({
  label,
  value,
  loading,
  accentText,
}: {
  label: string;
  value: number;
  loading?: boolean;
  accentText: string;
}) {
  return (
    <div>
      <div className={cn("font-numeric text-2xl font-bold leading-none", accentText)}>
        {loading ? <span className="text-ink-disabled">—</span> : value}
      </div>
      <div className="mt-1 text-[11px] uppercase tracking-[0.16em] text-ink-low">{label}</div>
    </div>
  );
}

/** Khung "đang chiếu" — ngang, lớn, có mép răng phim. Khác hẳn thẻ dọc bên dưới. */
function FeaturedCard({ job }: { job: Job }) {
  const t = useTranslations("library");
  return (
    <Link
      href={`/app/v/${job.id}`}
      className="group relative flex overflow-hidden rounded-[22px] glass-bordered transition-all duration-200 hover:-translate-y-1 hover:ring-1 hover:ring-emerald-400/30"
    >
      <Perforations className="px-1.5" />
      <div className="relative flex-1 overflow-hidden">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="/bg/desk.jpg"
          alt=""
          className="h-full w-full object-cover opacity-30 transition-transform duration-700 group-hover:scale-[1.04]"
        />
        <div className="absolute inset-0 bg-gradient-to-r from-bg-surface via-bg-surface/85 to-bg-surface/40" />
        {/* gạch scrub chạy ngang khi hover — gợi tua phim */}
        <span className="pointer-events-none absolute bottom-0 left-0 h-0.5 w-0 bg-grad-brand transition-all duration-500 group-hover:w-full" />

        <div className="relative flex h-full flex-col justify-between gap-4 p-5 sm:p-6">
          <div className="flex items-center justify-between gap-3">
            <FilmLabel>{t("latest")}</FilmLabel>
            <span className={cn("rounded-md px-2 py-0.5 text-[10px] font-semibold", STATUS_CLS[job.status] ?? "bg-white/[0.06] text-ink-low")}>
              {statusLabel(job.status)}
            </span>
          </div>

          <div className="flex items-end justify-between gap-4">
            <div className="min-w-0">
              <div className="font-display text-lg font-semibold text-ink-high">{t(kindLabelKey(job.kind))}</div>
              <div className="mt-1 font-numeric text-sm text-ink-low">
                {job.seconds}s · {job.resolution} · {job.aspect}
              </div>
              <div className="mt-2 flex items-center gap-4 text-[12px]">
                <CreditValue value={job.est_credits} className="text-ink-medium" />
                <span className="text-ink-disabled">{formatDate(job.created_at)}</span>
              </div>
            </div>
            <span className="grid h-12 w-12 shrink-0 place-items-center rounded-full bg-emerald-500/25 backdrop-blur-sm transition-transform group-hover:scale-110">
              <Play className="h-5 w-5 translate-x-0.5 text-white" aria-hidden />
            </span>
          </div>
        </div>
      </div>
      <Perforations className="px-1.5" />
    </Link>
  );
}

function VideoCard({ job }: { job: Job }) {
  const t = useTranslations("library");
  const ready = job.status === "READY";
  const running = !isTerminal(job.status);
  return (
    <Link
      href={`/app/v/${job.id}`}
      className="group relative flex aspect-[9/16] flex-col justify-between overflow-hidden rounded-[18px] glass-bordered p-3 transition-transform hover:-translate-y-1"
    >
      <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/15 via-transparent to-teal-500/10 opacity-60 transition-opacity group-hover:opacity-100" />
      <span className="pointer-events-none absolute inset-0 rounded-[18px] ring-1 ring-emerald-400/0 transition group-hover:ring-emerald-400/30" />
      {/* gạch scrub đáy khi hover */}
      <span className="pointer-events-none absolute bottom-0 left-0 h-0.5 w-0 bg-grad-brand transition-all duration-500 group-hover:w-full" />

      <div className="relative flex items-start justify-between">
        <span className={cn("rounded-md px-2 py-0.5 text-[10px] font-semibold", STATUS_CLS[job.status] ?? "bg-white/[0.06] text-ink-low")}>
          {statusLabel(job.status)}
        </span>
      </div>

      {ready ? (
        <div className="absolute inset-0 grid place-items-center">
          <span className="grid h-12 w-12 place-items-center rounded-full bg-emerald-500/25 backdrop-blur-sm transition-transform group-hover:scale-110">
            <Play className="h-5 w-5 translate-x-0.5 text-white" aria-hidden />
          </span>
        </div>
      ) : running ? (
        <div className="absolute inset-0 grid place-items-center">
          <Loader2 className="h-6 w-6 animate-spin text-violet-300/80" aria-hidden />
        </div>
      ) : null}

      <div className="relative text-[11px] text-ink-low">
        <div className="truncate font-medium text-ink-medium">{t(kindLabelKey(job.kind))}</div>
        <div className="mt-0.5 font-numeric">{job.seconds}s · {job.resolution} · {job.aspect}</div>
        <div className="mt-1 flex items-center justify-between">
          <CreditValue value={job.est_credits} className="text-[11px] text-ink-medium" />
          <span className="text-ink-disabled">{formatDate(job.created_at)}</span>
        </div>
      </div>
    </Link>
  );
}

function LoadingGrid() {
  return (
    <div className="flex flex-col gap-4">
      <Skeleton className="h-44 w-full rounded-[22px]" />
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <Skeleton key={i} className="aspect-[9/16] w-full rounded-[18px]" />
        ))}
      </div>
    </div>
  );
}

function EmptyState({ filter }: { filter: string }) {
  const t = useTranslations("library");
  const isAll = filter === "all";
  return (
    <div className="relative flex flex-col items-center gap-4 overflow-hidden rounded-3xl glass-bordered py-20 text-center">
      <Perforations className="absolute left-0 top-0 h-full px-1" />
      <Perforations className="absolute right-0 top-0 h-full px-1" />
      <div
        className="pointer-events-none absolute -top-16 left-1/2 h-48 w-48 -translate-x-1/2 rounded-full blur-3xl"
        style={{ background: A.glow }}
      />
      <div className="relative grid h-16 w-16 place-items-center rounded-2xl bg-emerald-500/10">
        <Film className={cn("h-7 w-7", A.icon)} aria-hidden />
      </div>
      <p className="relative max-w-xs text-ink-medium">
        {isAll ? t("emptyAll") : t("emptyFiltered")}
      </p>
      {isAll && (
        <Link href="/app/create" className="relative">
          <Button variant="glass" size="sm" className="gap-1.5 active:scale-95">
            <Plus className="h-4 w-4" /> {t("createVideo")}
          </Button>
        </Link>
      )}
    </div>
  );
}

function ErrorState({ onRetry }: { onRetry: () => void }) {
  const t = useTranslations("library");
  return (
    <div className="flex flex-col items-center gap-4 rounded-3xl glass-bordered py-20 text-center">
      <div className="grid h-16 w-16 place-items-center rounded-2xl bg-danger/10">
        <Film className="h-7 w-7 text-danger" aria-hidden />
      </div>
      <p className="max-w-xs text-ink-medium">{t("errorBody")}</p>
      <Button variant="glass" size="sm" onClick={onRetry} className="active:scale-95">
        {t("errorRetry")}
      </Button>
    </div>
  );
}
