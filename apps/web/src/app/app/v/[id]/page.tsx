"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Loader2, AlertTriangle, RotateCcw } from "lucide-react";
import { useJob } from "@/lib/query/hooks";
import { VideoPlayer } from "@/components/library/video-player";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { GlassCard } from "@/components/ui/glass-card";
import { Skeleton } from "@/components/ui/skeleton";
import { CreditValue } from "@/components/ui/credit-value";
import { statusTone, statusLabel, formatDate } from "@/lib/job-status";

export default function VideoDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params?.id ?? "";
  const { data: job, isLoading } = useJob(id);

  const ready = job?.status === "READY";
  const terminal = job ? ["QA_FAIL", "FAILED", "REFUNDED", "CANCELLED"].includes(job.status) : false;

  return (
    <div className="flex flex-col gap-6">
      <Link href="/app/library" className="inline-flex items-center gap-1.5 text-sm text-ink-low hover:text-ink-medium">
        <ArrowLeft className="h-4 w-4" /> Thư viện
      </Link>

      {isLoading || !job ? (
        <div className="flex flex-col items-center gap-4">
          <Skeleton className="h-72 w-44 rounded-xl" />
        </div>
      ) : (
        <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
          <div>
            {ready ? (
              <VideoPlayer jobId={job.id} />
            ) : terminal ? (
              <GlassCard className="flex flex-col items-center gap-3 py-16 text-center">
                <div className="grid h-12 w-12 place-items-center rounded-xl bg-danger/[0.12]">
                  <AlertTriangle className="h-6 w-6 text-danger" />
                </div>
                <p className="text-ink-high">
                  {job.status === "REFUNDED" || job.status === "FAILED"
                    ? "Lỗi hệ thống. Credit đã hoàn 100%."
                    : "Video chưa đạt yêu cầu."}
                </p>
                {job.error && <p className="max-w-md text-sm text-ink-low">{job.error}</p>}
              </GlassCard>
            ) : (
              <GlassCard className="flex flex-col items-center gap-3 py-16 text-center">
                <Loader2 className="h-6 w-6 animate-spin text-violet-300" />
                <p className="text-ink-low">Đang tạo video…</p>
              </GlassCard>
            )}
          </div>

          <GlassCard bordered className="h-fit p-5">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-ink-high">Chi tiết</h2>
              <Badge tone={statusTone(job.status)}>{statusLabel(job.status)}</Badge>
            </div>
            <dl className="mt-4 flex flex-col divide-y divide-white/[0.06] text-sm">
              <Row k="Loại" v={job.kind} />
              <Row k="Thời lượng" v={`${job.seconds}s · ${job.resolution}`} />
              <Row k="Tỉ lệ" v={job.aspect} />
              <Row k="Ước tính" v={<CreditValue value={job.est_credits} className="text-sm" />} />
              <Row k="Tạo lúc" v={formatDate(job.created_at)} />
              {job.finished_at && <Row k="Xong lúc" v={formatDate(job.finished_at)} />}
            </dl>
            <Link href="/app/create" className="mt-5 block">
              <Button variant="glass" className="w-full gap-2">
                <RotateCcw className="h-4 w-4" /> Tạo video khác
              </Button>
            </Link>
          </GlassCard>
        </div>
      )}
    </div>
  );
}

function Row({ k, v }: { k: string; v: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between py-2.5">
      <dt className="text-ink-low">{k}</dt>
      <dd className="text-ink-high">{v}</dd>
    </div>
  );
}
