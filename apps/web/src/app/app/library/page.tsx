"use client";

import { useState } from "react";
import Link from "next/link";
import { Film, Play, Sparkles } from "lucide-react";
import { useJobs } from "@/lib/query/hooks";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { CreditValue } from "@/components/ui/credit-value";
import { GlassCard } from "@/components/ui/glass-card";
import { statusLabel, formatDate } from "@/lib/job-status";
import { cn } from "@/lib/utils/cn";
import type { Job } from "@/lib/api/types";

const FILTERS = [
  { key: "all", label: "Tất cả" },
  { key: "READY", label: "Hoàn tất" },
  { key: "RUNNING", label: "Đang tạo" },
  { key: "FAILED", label: "Lỗi" },
] as const;

const STATUS_CLS: Record<string, string> = {
  READY: "bg-success/15 text-success",
  RUNNING: "bg-violet-500/15 text-violet-200",
  QUEUED: "bg-hold/15 text-hold",
  WAITING_CONFIG: "bg-hold/15 text-hold",
  FAILED: "bg-danger/15 text-danger",
  QA_FAIL: "bg-danger/15 text-danger",
  CANCELLED: "bg-white/[0.06] text-ink-low",
  REFUNDED: "bg-refund/15 text-refund",
};

export default function LibraryPage() {
  const { data, isLoading } = useJobs(60);
  const [filter, setFilter] = useState<string>("all");

  const all = data?.items ?? [];
  const items = all.filter((j) =>
    filter === "all" ? true : filter === "RUNNING" ? !isTerminal(j.status) : j.status === filter,
  );

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-end justify-between gap-4">
        <div className="flex items-center gap-3">
          <span className="grid h-11 w-11 place-items-center rounded-xl bg-grad-brand-soft">
            <Film className="h-5 w-5 text-violet-300" />
          </span>
          <div>
            <h1 className="font-display text-2xl font-bold text-ink-high lg:text-[32px]">Thư viện</h1>
            <p className="text-sm text-ink-low">
              {isLoading ? "Đang tải…" : `${all.length} video đã tạo`}
            </p>
          </div>
        </div>
        <Link href="/app/create">
          <Button size="sm" className="gap-1.5"><Sparkles className="h-4 w-4" /> Tạo video</Button>
        </Link>
      </div>

      <div className="flex flex-wrap gap-2">
        {FILTERS.map((f) => (
          <button
            key={f.key}
            onClick={() => setFilter(f.key)}
            className={cn(
              "rounded-lg border px-3.5 py-1.5 text-sm transition-colors",
              filter === f.key
                ? "border-violet-500/60 bg-violet-500/15 text-ink-high"
                : "border-white/10 text-ink-low hover:border-white/25 hover:text-ink-medium",
            )}
          >
            {f.label}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="aspect-[9/16] w-full rounded-xl" />
          ))}
        </div>
      ) : items.length === 0 ? (
        <GlassCard className="flex flex-col items-center gap-3 py-20 text-center">
          <div className="grid h-14 w-14 place-items-center rounded-2xl bg-white/[0.04]">
            <Film className="h-6 w-6 text-ink-low" />
          </div>
          <p className="text-ink-low">
            {filter === "all" ? "Chưa có video. Tạo video đầu tiên của bạn." : "Không có video ở bộ lọc này."}
          </p>
          {filter === "all" && (
            <Link href="/app/create"><Button variant="glass" size="sm">Tạo video</Button></Link>
          )}
        </GlassCard>
      ) : (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          {items.map((j) => (
            <VideoCard key={j.id} job={j} />
          ))}
        </div>
      )}
    </div>
  );
}

function VideoCard({ job }: { job: Job }) {
  const ready = job.status === "READY";
  const kind = job.kind === "kol_full" ? "KOL AI" : "Video sản phẩm";
  return (
    <Link
      href={`/app/v/${job.id}`}
      className="group relative flex aspect-[9/16] flex-col justify-between overflow-hidden rounded-[18px] glass-bordered p-3 transition-transform hover:-translate-y-1"
    >
      <div className="absolute inset-0 bg-grad-brand-soft opacity-25 transition-opacity group-hover:opacity-50" />
      <span className="pointer-events-none absolute inset-0 rounded-[18px] ring-1 ring-violet-400/0 transition group-hover:ring-violet-400/30" />

      <div className="relative flex items-start justify-between">
        <span className={cn("rounded-md px-2 py-0.5 text-[10px] font-semibold", STATUS_CLS[job.status] ?? "bg-white/[0.06] text-ink-low")}>
          {statusLabel(job.status)}
        </span>
      </div>

      {ready && (
        <div className="absolute inset-0 grid place-items-center">
          <span className="grid h-12 w-12 place-items-center rounded-full bg-violet-500/30 backdrop-blur-sm transition-transform group-hover:scale-110">
            <Play className="h-5 w-5 translate-x-0.5 text-white" />
          </span>
        </div>
      )}

      <div className="relative text-[11px] text-ink-low">
        <div className="truncate font-medium text-ink-medium">{kind}</div>
        <div className="mt-0.5 font-numeric">{job.seconds}s · {job.resolution} · {job.aspect}</div>
        <div className="mt-1 flex items-center justify-between">
          <CreditValue value={job.est_credits} className="text-[11px] text-ink-medium" />
          <span className="text-ink-disabled">{formatDate(job.created_at)}</span>
        </div>
      </div>
    </Link>
  );
}

function isTerminal(s: string) {
  return ["READY", "QA_FAIL", "FAILED", "REFUNDED", "CANCELLED"].includes(s);
}
