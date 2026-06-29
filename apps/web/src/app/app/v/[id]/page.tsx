"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft, Loader2, AlertTriangle, RotateCcw, Clapperboard,
  Clock, Monitor, Proportions, Coins, CalendarDays, CheckCircle2,
} from "lucide-react";
import { useJob } from "@/lib/query/hooks";
import { VideoPlayer } from "@/components/library/video-player";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { GlassCard } from "@/components/ui/glass-card";
import { Skeleton } from "@/components/ui/skeleton";
import { CreditValue } from "@/components/ui/credit-value";
import { FilmLabel } from "@/components/ui/cinematic";
import { Reveal } from "@/components/marketing/reveal";
import { ACCENTS } from "@/lib/accents";
import { statusTone, statusLabel, formatDate } from "@/lib/job-status";
import { cn } from "@/lib/utils/cn";

const a = ACCENTS.sky;

export default function VideoDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params?.id ?? "";
  const { data: job, isLoading } = useJob(id);

  const ready = job?.status === "READY";
  const terminal = job ? ["QA_FAIL", "FAILED", "REFUNDED", "CANCELLED"].includes(job.status) : false;

  return (
    <div className="flex flex-col gap-6">
      <Link
        href="/app/library"
        className="inline-flex w-fit items-center gap-1.5 rounded-lg text-sm text-ink-low transition-colors hover:text-ink-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400/50"
      >
        <ArrowLeft className="h-4 w-4" /> Thư viện
      </Link>

      {isLoading || !job ? (
        <LoadingState />
      ) : (
        <Reveal>
          {/* PHÒNG CHIẾU — màn chiếu lớn (trái) + bảng kỹ thuật dọc (phải). Bố cục riêng 60/40. */}
          <div className="grid gap-5 lg:grid-cols-[1.5fr_1fr] lg:items-start">
            {/* MÀN CHIẾU */}
            <section className="relative overflow-hidden rounded-3xl glass-bordered">
              {/* vầng glow sky sau màn chiếu */}
              <div
                className="pointer-events-none absolute -top-20 left-1/2 h-56 w-72 -translate-x-1/2 rounded-full blur-3xl"
                style={{ background: a.glow }}
              />
              <div className="relative flex items-center justify-between gap-3 px-5 pt-5 sm:px-6">
                <FilmLabel>Phòng chiếu</FilmLabel>
                <span className="text-[11px] font-semibold uppercase tracking-[0.18em] text-ink-low">
                  {statusLabel(job.status)}
                </span>
              </div>

              <div className="relative px-3 pb-5 pt-4 sm:px-6 sm:pb-6">
                {/* nền sân khấu tối cho phần khung phim */}
                <div className="relative grid place-items-center overflow-hidden rounded-2xl border border-white/10 bg-black/60 px-3 py-4 sm:px-6 sm:py-6">
                  <div
                    className="pointer-events-none absolute inset-x-10 top-0 h-px"
                    style={{ background: "linear-gradient(90deg,transparent,rgba(56,189,248,.5),transparent)" }}
                  />
                  {ready ? (
                    <VideoPlayer jobId={job.id} />
                  ) : terminal ? (
                    <TerminalState job={job} />
                  ) : (
                    <PendingState />
                  )}
                </div>
              </div>
            </section>

            {/* BẢNG KỸ THUẬT */}
            <aside className="flex flex-col gap-4 lg:sticky lg:top-6">
              <div className="flex items-center justify-between gap-3">
                <FilmLabel dot={false}>Bảng kỹ thuật</FilmLabel>
                <Badge tone={statusTone(job.status)}>{statusLabel(job.status)}</Badge>
              </div>

              {/* két thông số — dạng tile, không phải hàng-thẻ đối xứng */}
              <div className="grid grid-cols-2 gap-3">
                <SpecTile icon={Clock} k="Thời lượng" v={`${job.seconds}s`} />
                <SpecTile icon={Monitor} k="Độ phân giải" v={job.resolution} />
                <SpecTile icon={Proportions} k="Tỉ lệ khung" v={job.aspect} />
                <SpecTile icon={Clapperboard} k="Loại" v={job.kind} />
              </div>

              <GlassCard bordered className="p-4">
                <div className="flex items-center justify-between">
                  <span className="inline-flex items-center gap-2 text-sm text-ink-low">
                    <Coins className="h-4 w-4 text-sky-300" /> Chi phí ước tính
                  </span>
                  <CreditValue value={job.est_credits} className="text-base text-ink-high" />
                </div>
                <div className="mt-3 flex flex-col divide-y divide-white/[0.06] text-sm">
                  <TimeRow icon={CalendarDays} k="Tạo lúc" v={formatDate(job.created_at)} />
                  {job.finished_at && (
                    <TimeRow icon={CheckCircle2} k="Hoàn tất" v={formatDate(job.finished_at)} />
                  )}
                </div>
              </GlassCard>

              {/* hành động — tạo lại video với cùng cấu hình */}
              <Link href="/app/create" className="block">
                <Button
                  variant="glass"
                  className="w-full gap-2 hover:ring-1 hover:ring-sky-400/30"
                >
                  <RotateCcw className="h-4 w-4 text-sky-300" /> Tạo video khác
                </Button>
              </Link>

              {ready && (
                <p className="text-center text-xs text-ink-low">
                  Nút tải MP4 và chia sẻ nằm ngay dưới màn chiếu.
                </p>
              )}
            </aside>
          </div>
        </Reveal>
      )}
    </div>
  );
}

/* —— trạng thái —— */

function LoadingState() {
  return (
    <div className="grid gap-5 lg:grid-cols-[1.5fr_1fr]">
      <Skeleton className="aspect-video w-full rounded-3xl" />
      <div className="flex flex-col gap-3">
        <div className="grid grid-cols-2 gap-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-20 rounded-2xl" />
          ))}
        </div>
        <Skeleton className="h-28 w-full rounded-2xl" />
        <Skeleton className="h-12 w-full rounded-xl" />
      </div>
    </div>
  );
}

function PendingState() {
  return (
    <div className="flex flex-col items-center gap-3 py-20 text-center">
      <Loader2 className="h-7 w-7 animate-spin text-sky-300" />
      <p className="text-ink-medium">Đang dựng video…</p>
      <p className="max-w-xs text-sm text-ink-low">Cứ để tab này mở, video sẽ tự hiện khi xong.</p>
    </div>
  );
}

function TerminalState({ job }: { job: { status: string; error?: string } }) {
  const refunded = job.status === "REFUNDED" || job.status === "FAILED";
  return (
    <div className="flex flex-col items-center gap-3 py-16 text-center">
      <div className="grid h-12 w-12 place-items-center rounded-xl bg-danger/[0.12]">
        <AlertTriangle className="h-6 w-6 text-danger" />
      </div>
      <p className="text-ink-high">
        {refunded ? "Lỗi hệ thống. Credit đã hoàn 100%." : "Video chưa đạt yêu cầu."}
      </p>
      {job.error && <p className="max-w-md text-sm text-ink-low">{job.error}</p>}
    </div>
  );
}

/* —— mảnh nhỏ —— */

function SpecTile({
  icon: Icon, k, v,
}: { icon: React.ComponentType<{ className?: string }>; k: string; v: string }) {
  return (
    <div className="flex flex-col gap-2 rounded-2xl glass-bordered p-3.5">
      <span className={cn("grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br ring-1", a.tile, a.ring)}>
        <Icon className={cn("h-4 w-4", a.icon)} />
      </span>
      <div className="min-w-0">
        <div className="text-[11px] uppercase tracking-wide text-ink-low">{k}</div>
        <div className="truncate font-display text-sm font-semibold text-ink-high">{v}</div>
      </div>
    </div>
  );
}

function TimeRow({
  icon: Icon, k, v,
}: { icon: React.ComponentType<{ className?: string }>; k: string; v: string }) {
  return (
    <div className="flex items-center justify-between py-2.5">
      <dt className="inline-flex items-center gap-2 text-ink-low">
        <Icon className="h-3.5 w-3.5 text-ink-low" /> {k}
      </dt>
      <dd className="text-ink-high">{v}</dd>
    </div>
  );
}
