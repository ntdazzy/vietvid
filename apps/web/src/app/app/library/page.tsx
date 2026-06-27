"use client";

import { useState } from "react";
import Link from "next/link";
import { Film, Play, Sparkles } from "lucide-react";
import { useJobs } from "@/lib/query/hooks";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { CreditValue } from "@/components/ui/credit-value";
import { GlassCard } from "@/components/ui/glass-card";
import { statusTone, statusLabel, formatDate } from "@/lib/job-status";
import { cn } from "@/lib/utils/cn";
import type { Job } from "@/lib/api/types";

const FILTERS = [
  { key: "all", label: "Tất cả" },
  { key: "READY", label: "Hoàn tất" },
  { key: "RUNNING", label: "Đang tạo" },
  { key: "FAILED", label: "Lỗi" },
] as const;

export default function LibraryPage() {
  const { data, isLoading } = useJobs(60);
  const [filter, setFilter] = useState<string>("all");

  const items = (data?.items ?? []).filter((j) =>
    filter === "all" ? true : filter === "RUNNING" ? !isTerminal(j.status) : j.status === filter,
  );

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-ink-high lg:text-[34px]">Thư viện</h1>
        <Link href="/app/create">
          <Button size="sm" className="gap-1.5">
            <Sparkles className="h-4 w-4" /> Tạo video
          </Button>
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
                : "border-white/10 text-ink-low hover:text-ink-medium",
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
          <p className="text-ink-low">Chưa có video. Tạo video đầu tiên của bạn.</p>
          <Link href="/app/create">
            <Button variant="glass" size="sm">
              Tạo video
            </Button>
          </Link>
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
  return (
    <Link
      href={`/app/v/${job.id}`}
      className="group glass-bordered relative flex aspect-[9/16] flex-col justify-between overflow-hidden p-3"
    >
      <div className="absolute inset-0 -z-10 bg-grad-brand-soft opacity-30 transition-opacity group-hover:opacity-60" />
      <div className="flex items-start justify-between">
        <Badge tone={statusTone(job.status)}>{statusLabel(job.status)}</Badge>
      </div>

      {ready && (
        <div className="absolute inset-0 grid place-items-center">
          <span className="grid h-12 w-12 place-items-center rounded-full bg-bg-base/50 backdrop-blur-sm transition-transform group-hover:scale-110">
            <Play className="h-5 w-5 translate-x-0.5 text-white" />
          </span>
        </div>
      )}

      <div className="text-[11px] text-ink-low">
        <div className="truncate text-ink-medium">{job.kind}</div>
        <div className="mt-0.5 font-mono">
          {job.seconds}s · {job.resolution}
        </div>
        <div className="mt-1 flex items-center justify-between">
          <CreditValue
            value={ready ? job.est_credits : job.est_credits}
            className="text-[11px] text-ink-medium"
          />
          <span className="text-ink-disabled">{formatDate(job.created_at)}</span>
        </div>
      </div>
    </Link>
  );
}

function isTerminal(s: string) {
  return ["READY", "QA_FAIL", "FAILED", "REFUNDED", "CANCELLED"].includes(s);
}
