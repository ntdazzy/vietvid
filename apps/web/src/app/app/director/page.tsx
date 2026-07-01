"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { Clapperboard, ImageIcon, UserRound, Drama, AudioLines, Layers, Play, Plus, Loader2, FolderKanban } from "lucide-react";
import { StudioShell } from "@/components/studio/studio-shell";
import { useJobs } from "@/lib/query/hooks";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { CreditValue } from "@/components/ui/credit-value";
import { FilmLabel } from "@/components/ui/cinematic";
import { Reveal } from "@/components/marketing/reveal";
import { statusLabel, formatDate, isTerminal } from "@/lib/job-status";
import { cn } from "@/lib/utils/cn";
import type { Job } from "@/lib/api/types";

// MÀN DỰ ÁN (/app/director) — "bàn dựng" của studio: tụ mọi công cụ + việc gần đây về một chỗ,
// đứng sau nút "Dự án" ở rail (trước đây 404). Dữ liệu THẬT từ listJobs; không bịa.

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

// Công cụ studio (đồng bộ rail) — mỗi ô mở thẳng một "phòng".
const TOOLS = [
  { key: "video", href: "/app/create", icon: Clapperboard, accent: "from-violet-500/25 to-indigo-500/5 text-violet-200" },
  { key: "batch", href: "/app/batch", icon: Layers, accent: "from-sky-500/25 to-blue-500/5 text-sky-200" },
  { key: "image", href: "/app/image-gen", icon: ImageIcon, accent: "from-cyan-500/25 to-teal-500/5 text-cyan-200" },
  { key: "kol", href: "/app/kol", icon: UserRound, accent: "from-rose-500/25 to-pink-500/5 text-rose-200" },
  { key: "character", href: "/app/character", icon: Drama, accent: "from-amber-500/25 to-orange-500/5 text-amber-200" },
  { key: "audio", href: "/app/audio", icon: AudioLines, accent: "from-emerald-500/25 to-teal-500/5 text-emerald-200" },
] as const;

export default function DirectorPage() {
  const t = useTranslations("director");
  const { data, isLoading } = useJobs(24);
  const jobs = data?.items ?? [];
  const running = jobs.filter((j) => !isTerminal(j.status)).length;
  const ready = jobs.filter((j) => j.status === "READY").length;

  return (
    <StudioShell>
      <div className="flex flex-col gap-8 pb-16">
        {/* ===== HERO: bàn dựng ===== */}
        <section className="relative overflow-hidden rounded-3xl glass-bordered">
          <div className="pointer-events-none absolute -top-24 -right-10 h-64 w-64 rounded-full bg-violet-500/20 blur-3xl" />
          <div className="pointer-events-none absolute -bottom-24 left-10 h-56 w-56 rounded-full bg-indigo-500/10 blur-3xl" />
          <div className="relative flex flex-col gap-6 px-6 py-8 sm:px-10">
            <div className="flex flex-wrap items-end justify-between gap-4">
              <div className="max-w-xl">
                <FilmLabel>{t("eyebrow")}</FilmLabel>
                <h1 className="mt-3 font-display text-3xl font-extrabold leading-[1.05] text-ink-high sm:text-[40px]">
                  {t("title")}
                </h1>
                <p className="mt-2 text-ink-medium">{t("subtitle")}</p>
              </div>
              <Link href="/app/create" className="shrink-0">
                <Button className="gap-1.5 active:scale-95">
                  <Plus className="h-4 w-4" /> {t("newProject")}
                </Button>
              </Link>
            </div>
            {/* thống kê THẬT */}
            <div className="flex flex-wrap gap-x-8 gap-y-3 border-t border-white/10 pt-5">
              <Stat label={t("statTotal")} value={jobs.length} loading={isLoading} cls="text-ink-high" />
              <Stat label={t("statDone")} value={ready} loading={isLoading} cls="text-success" />
              <Stat label={t("statRunning")} value={running} loading={isLoading} cls="text-violet-300" />
            </div>
          </div>
        </section>

        {/* ===== BẮT ĐẦU NHANH — lối vào từng phòng ===== */}
        <section>
          <div className="mb-4 flex items-center gap-2">
            <FolderKanban className="h-4 w-4 text-violet-300" />
            <h2 className="text-sm font-semibold uppercase tracking-wide text-ink-medium">{t("quickStart")}</h2>
          </div>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
            {TOOLS.map((tool) => {
              const Icon = tool.icon;
              return (
                <Link
                  key={tool.key}
                  href={tool.href}
                  className="group relative flex flex-col items-start gap-3 overflow-hidden rounded-2xl glass-bordered p-4 transition-all duration-200 hover:-translate-y-1 hover:ring-1 hover:ring-violet-400/30"
                >
                  <span className={cn("grid h-11 w-11 place-items-center rounded-xl bg-gradient-to-br", tool.accent)}>
                    <Icon className="h-5 w-5" />
                  </span>
                  <div>
                    <div className="text-sm font-semibold text-ink-high">{t(`tool_${tool.key}_label`)}</div>
                    <div className="mt-0.5 text-[11px] leading-tight text-ink-low">{t(`tool_${tool.key}_desc`)}</div>
                  </div>
                  <span className="pointer-events-none absolute bottom-0 left-0 h-0.5 w-0 bg-grad-brand transition-all duration-500 group-hover:w-full" />
                </Link>
              );
            })}
          </div>
        </section>

        {/* ===== GẦN ĐÂY — việc đang/đã dựng ===== */}
        <section>
          <div className="mb-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Clapperboard className="h-4 w-4 text-violet-300" />
              <h2 className="text-sm font-semibold uppercase tracking-wide text-ink-medium">{t("recent")}</h2>
            </div>
            <Link href="/app/library" className="text-sm text-ink-low transition hover:text-ink-medium">
              {t("viewAll")} →
            </Link>
          </div>

          {isLoading ? (
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
              {Array.from({ length: 8 }).map((_, i) => (
                <Skeleton key={i} className="aspect-[9/16] w-full rounded-[18px]" />
              ))}
            </div>
          ) : jobs.length === 0 ? (
            <EmptyState />
          ) : (
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
              {jobs.map((j, i) => (
                <Reveal key={j.id} delay={Math.min(i, 6) * 0.04}>
                  <ProjectCard job={j} />
                </Reveal>
              ))}
            </div>
          )}
        </section>
      </div>
    </StudioShell>
  );
}

function Stat({ label, value, loading, cls }: { label: string; value: number; loading?: boolean; cls: string }) {
  return (
    <div>
      <div className={cn("font-numeric text-2xl font-bold leading-none", cls)}>
        {loading ? <span className="text-ink-disabled">—</span> : value}
      </div>
      <div className="mt-1 text-[11px] uppercase tracking-[0.16em] text-ink-low">{label}</div>
    </div>
  );
}

function ProjectCard({ job }: { job: Job }) {
  const t = useTranslations("director");
  const ready = job.status === "READY";
  const running = !isTerminal(job.status);
  const kindLabel = job.kind === "kol_full" ? t("kindKol") : t("kindProduct");
  return (
    <Link
      href={`/app/v/${job.id}`}
      className="group relative flex aspect-[9/16] flex-col justify-between overflow-hidden rounded-[18px] glass-bordered p-3 transition-transform hover:-translate-y-1"
    >
      <div className="absolute inset-0 bg-gradient-to-br from-violet-500/15 via-transparent to-indigo-500/10 opacity-60 transition-opacity group-hover:opacity-100" />
      <span className="pointer-events-none absolute inset-0 rounded-[18px] ring-1 ring-violet-400/0 transition group-hover:ring-violet-400/30" />
      <span className="pointer-events-none absolute bottom-0 left-0 h-0.5 w-0 bg-grad-brand transition-all duration-500 group-hover:w-full" />

      <div className="relative flex items-start justify-between">
        <span className={cn("rounded-md px-2 py-0.5 text-[10px] font-semibold", STATUS_CLS[job.status] ?? "bg-white/[0.06] text-ink-low")}>
          {statusLabel(job.status)}
        </span>
      </div>

      {ready ? (
        <div className="absolute inset-0 grid place-items-center">
          <span className="grid h-12 w-12 place-items-center rounded-full bg-violet-500/25 backdrop-blur-sm transition-transform group-hover:scale-110">
            <Play className="h-5 w-5 translate-x-0.5 text-white" aria-hidden />
          </span>
        </div>
      ) : running ? (
        <div className="absolute inset-0 grid place-items-center">
          <Loader2 className="h-6 w-6 animate-spin text-violet-300/80" aria-hidden />
        </div>
      ) : null}

      <div className="relative text-[11px] text-ink-low">
        <div className="truncate font-medium text-ink-medium">{kindLabel}</div>
        <div className="mt-0.5 font-numeric">{job.seconds}s · {job.resolution} · {job.aspect}</div>
        <div className="mt-1 flex items-center justify-between">
          <CreditValue value={job.est_credits} className="text-[11px] text-ink-medium" />
          <span className="text-ink-disabled">{formatDate(job.created_at)}</span>
        </div>
      </div>
    </Link>
  );
}

function EmptyState() {
  const t = useTranslations("director");
  return (
    <div className="relative flex flex-col items-center gap-4 overflow-hidden rounded-3xl glass-bordered py-16 text-center">
      <div className="pointer-events-none absolute -top-16 left-1/2 h-48 w-48 -translate-x-1/2 rounded-full bg-violet-500/15 blur-3xl" />
      <div className="relative grid h-16 w-16 place-items-center rounded-2xl bg-violet-500/10">
        <FolderKanban className="h-7 w-7 text-violet-200" aria-hidden />
      </div>
      <p className="relative max-w-xs text-ink-medium">{t("empty")}</p>
      <Link href="/app/create" className="relative">
        <Button variant="glass" size="sm" className="gap-1.5 active:scale-95">
          <Plus className="h-4 w-4" /> {t("newProject")}
        </Button>
      </Link>
    </div>
  );
}
