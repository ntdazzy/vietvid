"use client";

import { use } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Trophy, MousePointerClick, Play, Loader2, Sparkles } from "lucide-react";
import { api } from "@/lib/api/endpoints";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils/cn";

export default function SeriesPerfPage({ params }: { params: Promise<{ group: string }> }) {
  const { group } = use(params);
  const perf = useQuery({
    queryKey: ["series-perf", group],
    queryFn: () => api.seriesPerformance(group),
    refetchInterval: 15_000, // click dồn về theo thời gian
  });

  const rows = perf.data ?? [];
  const totalClicks = rows.reduce((a, v) => a + v.clicks, 0);
  const winner = rows.find((v) => v.is_winner);

  return (
    <div className="flex max-w-3xl flex-col gap-6">
      <div>
        <div className="flex items-center gap-2">
          <span className="grid h-10 w-10 place-items-center rounded-xl bg-grad-brand-soft">
            <Trophy className="h-5 w-5 text-violet-300" />
          </span>
          <h1 className="font-display text-2xl font-bold text-ink-high lg:text-[32px]">Hiệu suất loạt video</h1>
        </div>
        <p className="mt-1 text-ink-low">
          Mỗi biến thể có 1 link đo riêng. Chia sẻ chúng, hệ thống tự xếp hạng bản nào kéo nhiều click —
          rồi nhân bản bản thắng.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4 sm:max-w-sm">
        <GlassCard className="p-4">
          <MousePointerClick className="h-5 w-5 text-violet-300" />
          <div className="mt-3 font-numeric text-2xl font-bold text-ink-high">{totalClicks}</div>
          <div className="text-sm text-ink-low">Tổng click</div>
        </GlassCard>
        <GlassCard className="p-4">
          <Trophy className="h-5 w-5 text-amber-300" />
          <div className="mt-3 font-numeric text-2xl font-bold text-ink-high">
            {winner ? winner.clicks : "—"}
          </div>
          <div className="text-sm text-ink-low">Bản thắng</div>
        </GlassCard>
      </div>

      {perf.isLoading ? (
        <Skeleton className="h-48 w-full rounded-xl" />
      ) : (
        <div className="flex flex-col gap-3">
          {rows.map((v, i) => (
            <GlassCard
              key={v.job_id}
              className={cn("flex items-center gap-4 p-4", v.is_winner && "ring-1 ring-amber-400/40")}
            >
              <span
                className={cn(
                  "grid h-9 w-9 shrink-0 place-items-center rounded-xl font-numeric text-sm font-bold",
                  v.is_winner ? "bg-amber-400/15 text-amber-300" : "bg-white/[0.05] text-ink-low",
                )}
              >
                {v.is_winner ? <Trophy className="h-4 w-4" /> : i + 1}
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="truncate text-sm font-medium text-ink-high">
                    {v.label || "Biến thể"}
                  </span>
                  {v.is_winner && <Badge tone="brand">Thắng</Badge>}
                </div>
                <div className="text-xs text-ink-low">
                  {v.clicks} click · {viStatus(v.status)}
                </div>
              </div>
              {v.has_video && (
                <Link href={`/app/v/${v.job_id}`}>
                  <Button size="sm" variant="glass" className="gap-1.5">
                    <Play className="h-3.5 w-3.5" /> Xem
                  </Button>
                </Link>
              )}
            </GlassCard>
          ))}
        </div>
      )}

      <div className="flex items-center gap-3">
        <Link href="/app/create">
          <Button className="gap-2">
            <Sparkles className="h-4 w-4" /> Nhân bản bản thắng
          </Button>
        </Link>
        {perf.isFetching && (
          <span className="inline-flex items-center gap-1.5 text-xs text-ink-low">
            <Loader2 className="h-3.5 w-3.5 animate-spin" /> đang cập nhật click...
          </span>
        )}
      </div>
    </div>
  );
}

function viStatus(s: string): string {
  const m: Record<string, string> = {
    QUEUED: "đang chờ", RUNNING: "đang tạo", READY: "xong", FAILED: "lỗi",
    QA_FAIL: "lỗi QA", REFUNDED: "đã hoàn", CANCELLED: "đã huỷ", WAITING_CONFIG: "chờ cấu hình",
  };
  return m[s] ?? s;
}
