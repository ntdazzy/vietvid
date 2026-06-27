"use client";

import Link from "next/link";
import { Sparkles, ArrowRight, Film } from "lucide-react";
import { useMe, useJobs } from "@/lib/query/hooks";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { CreditValue } from "@/components/ui/credit-value";
import { vi } from "@/lib/i18n/vi";
import type { JobStatus } from "@/lib/api/types";

type Tone = "neutral" | "brand" | "hold" | "success" | "refund" | "danger";
const STATUS_TONE: Partial<Record<JobStatus, Tone>> = {
  READY: "success",
  FAILED: "danger",
  QA_FAIL: "danger",
  REFUNDED: "refund",
  QUEUED: "hold",
  RUNNING: "brand",
};

export default function DashboardPage() {
  const me = useMe();
  const jobs = useJobs(8);
  const name = me.data?.email?.split("@")[0] ?? "bạn";

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="text-xl font-bold text-ink-high sm:text-2xl lg:text-[34px]">
          Chào, <span className="text-gradient">{name}</span> 👋
        </h1>
        <p className="mt-1 text-ink-low">Biến 1 ảnh sản phẩm thành video chốt đơn, giọng Việt thật.</p>
      </div>

      {/* Quick create — hero card */}
      <GlassCard bordered className="relative overflow-hidden p-8">
        <div className="glow-radial pointer-events-none absolute inset-x-0 -top-24 h-48" />
        <div className="relative flex flex-col items-start gap-5 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <Badge tone="brand" className="mb-3">
              <Sparkles className="h-3 w-3" /> Tạo nhanh
            </Badge>
            <h2 className="text-xl font-bold text-ink-high">Tạo video mới</h2>
            <p className="mt-1 max-w-md text-sm text-ink-low">
              Thấy trước <span className="text-ink-medium">~số credit</span> trước khi tạo · giữ tạm,
              hoàn phần thừa · {vi.credit.refundPromise.toLowerCase()}.
            </p>
          </div>
          <Link href="/app/create">
            <Button size="lg" className="gap-2">
              {vi.nav.create} <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
        </div>
      </GlassCard>

      {/* Recent jobs rail */}
      <section className="flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-ink-low">Video gần đây</h3>
          <Link href="/app/library" className="text-sm text-violet-300 hover:text-violet-200">
            Xem tất cả
          </Link>
        </div>

        {jobs.isLoading ? (
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="aspect-[9/16] w-full rounded-xl" />
            ))}
          </div>
        ) : !jobs.data || jobs.data.items.length === 0 ? (
          <GlassCard className="flex flex-col items-center gap-3 py-14 text-center">
            <div className="grid h-14 w-14 place-items-center rounded-2xl bg-white/[0.04]">
              <Film className="h-6 w-6 text-ink-low" />
            </div>
            <p className="text-ink-low">{vi.states.empty_jobs}</p>
            <Link href="/app/create">
              <Button variant="glass" size="sm">
                {vi.nav.create}
              </Button>
            </Link>
          </GlassCard>
        ) : (
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
            {jobs.data.items.map((j) => (
              <Link
                key={j.id}
                href={`/app/library`}
                className="group glass-bordered aspect-[9/16] overflow-hidden p-0"
              >
                <div className="relative flex h-full flex-col justify-between p-3">
                  <div className="flex items-start justify-between">
                    <Badge tone={STATUS_TONE[j.status] ?? "neutral"}>{j.status}</Badge>
                  </div>
                  <div className="absolute inset-0 -z-10 bg-grad-brand-soft opacity-40 transition-opacity group-hover:opacity-70" />
                  <div className="text-[11px] text-ink-low">
                    <div className="truncate text-ink-medium">{j.kind}</div>
                    <div className="mt-0.5 font-mono">
                      {j.seconds}s · {j.resolution}
                    </div>
                    {j.est_credits > 0 && (
                      <div className="mt-1">
                        <CreditValue value={j.est_credits} className="text-[11px] text-ink-medium" />
                      </div>
                    )}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
