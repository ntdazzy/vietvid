"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import {
  Sparkles, ArrowRight, Film, Wallet, Plus, UserSquare2, Palette,
  AudioLines, Trophy, Clapperboard,
} from "lucide-react";
import { useMe, useJobs } from "@/lib/query/hooks";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { CreditValue } from "@/components/ui/credit-value";
import { cn } from "@/lib/utils/cn";
import type { JobStatus } from "@/lib/api/types";

// nhãn Việt cho trạng thái job (không lộ enum thô READY/QUEUED…)
const STATUS_VI: Record<string, { label: string; cls: string }> = {
  READY: { label: "Hoàn tất", cls: "bg-success/15 text-success" },
  RUNNING: { label: "Đang dựng", cls: "bg-violet-500/15 text-violet-200" },
  QUEUED: { label: "Đang chờ", cls: "bg-hold/15 text-hold" },
  WAITING_CONFIG: { label: "Chờ cấu hình", cls: "bg-hold/15 text-hold" },
  FAILED: { label: "Lỗi", cls: "bg-danger/15 text-danger" },
  QA_FAIL: { label: "Lỗi kiểm tra", cls: "bg-danger/15 text-danger" },
  CANCELLED: { label: "Đã huỷ", cls: "bg-white/[0.06] text-ink-low" },
  REFUNDED: { label: "Đã hoàn", cls: "bg-refund/15 text-refund" },
};

const ACTIONS = [
  { icon: Clapperboard, title: "Video bán hàng", desc: "1 ảnh → video chốt đơn 60 giây", href: "/features/product_ad", hot: true },
  { icon: UserSquare2, title: "KOL AI", desc: "Gương mặt ảo review, lookbook", href: "/app/kol" },
  { icon: Trophy, title: "Auto-series đo bản thắng", desc: "Tạo nhiều biến thể, đo click thật", href: "/app/create" },
  { icon: Palette, title: "Tạo ảnh AI", desc: "Mô tả một câu, AI vẽ ảnh", href: "/app/image-gen" },
  { icon: AudioLines, title: "Tạo âm thanh", desc: "Văn bản → 7 giọng Việt thật", href: "/app/audio" },
  { icon: Film, title: "Thư viện video", desc: "Xem, tải, chia sẻ video đã tạo", href: "/app/library" },
];

export default function DashboardPage() {
  const me = useMe();
  const jobs = useJobs(8);
  const name = me.data?.email?.split("@")[0] || "bạn";
  const balance = me.data?.balance_credits ?? null;
  const held = me.data?.held_credits ?? 0;

  return (
    <div className="flex flex-col gap-10">
      {/* header */}
      <div>
        <h1 className="font-display text-xl font-bold text-ink-high sm:text-2xl lg:text-[34px]">
          Chào, <span className="text-gradient">{name}</span> 👋
        </h1>
        <p className="mt-1.5 text-ink-low">Biến 1 ảnh sản phẩm thành video chốt đơn, giọng Việt thật.</p>
      </div>

      {/* hero create + credit */}
      <div className="grid gap-5 lg:grid-cols-3">
        <GlassCard bordered className="relative overflow-hidden p-7 lg:col-span-2">
          <div className="glow-radial pointer-events-none absolute inset-x-0 -top-24 h-48" />
          <div className="relative flex h-full flex-col items-start justify-between gap-5 sm:flex-row sm:items-center">
            <div>
              <span className="inline-flex items-center gap-1 rounded-full border border-violet-400/30 bg-violet-500/[0.08] px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide text-violet-200">
                <Sparkles className="h-3 w-3" /> Tạo nhanh
              </span>
              <h2 className="mt-3 font-display text-2xl font-bold text-ink-high">Tạo video mới</h2>
              <p className="mt-1.5 max-w-md text-sm text-ink-low">
                Thấy trước <span className="text-ink-medium">~số credit</span> trước khi tạo · giữ tạm,
                dùng bao nhiêu tính bấy nhiêu · hoàn 100% nếu lỗi hệ thống.
              </p>
            </div>
            <Link href="/app/create" className="shrink-0">
              <Button size="lg" className="gap-2">Tạo video <ArrowRight className="h-4 w-4" /></Button>
            </Link>
          </div>
        </GlassCard>

        {/* credit card */}
        <GlassCard className="flex flex-col justify-between p-6">
          <div className="flex items-center gap-2 text-sm font-medium text-ink-medium">
            <Wallet className="h-4 w-4 text-violet-300" /> Số dư credit
          </div>
          <div className="mt-3">
            {balance === null ? (
              <Skeleton className="h-9 w-28" />
            ) : (
              <div className="font-numeric text-4xl font-bold text-gradient">{balance.toLocaleString("vi-VN")}</div>
            )}
            <div className="mt-1 text-xs text-ink-low">
              credit · 1 credit = 150đ{held > 0 && <> · đang giữ <span className="text-hold">{held.toLocaleString("vi-VN")}</span></>}
            </div>
          </div>
          <Link href="/app/billing" className="mt-5">
            <Button variant="glass" size="sm" className="w-full gap-1.5"><Plus className="h-4 w-4" /> Nạp credit</Button>
          </Link>
        </GlassCard>
      </div>

      {/* launchpad */}
      <section className="flex flex-col gap-5">
        <h3 className="text-sm font-semibold uppercase tracking-[0.16em] text-ink-low">Bắt đầu nhanh</h3>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {ACTIONS.map((a) => (
            <ActionCard key={a.title} {...a} />
          ))}
        </div>
      </section>

      {/* recent videos */}
      <section className="flex flex-col gap-5">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold uppercase tracking-[0.16em] text-ink-low">Video gần đây</h3>
          <Link href="/app/library" className="text-sm text-violet-300 transition hover:text-violet-200">Xem tất cả →</Link>
        </div>

        {jobs.isLoading ? (
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="aspect-[9/16] w-full rounded-xl" />
            ))}
          </div>
        ) : !jobs.data || jobs.data.items.length === 0 ? (
          <GlassCard className="flex flex-col items-center gap-3 py-16 text-center">
            <div className="grid h-14 w-14 place-items-center rounded-2xl bg-white/[0.04]">
              <Film className="h-6 w-6 text-ink-low" />
            </div>
            <p className="text-ink-low">Chưa có video nào. Tạo video đầu tiên của bạn.</p>
            <Link href="/app/create">
              <Button variant="glass" size="sm">Tạo video</Button>
            </Link>
          </GlassCard>
        ) : (
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
            {jobs.data.items.map((j) => {
              const st = STATUS_VI[j.status as JobStatus] ?? { label: j.status, cls: "bg-white/[0.06] text-ink-low" };
              return (
                <Link key={j.id} href="/app/library" className="group relative aspect-[9/16] overflow-hidden rounded-[18px] glass-bordered">
                  <div className="absolute inset-0 bg-grad-brand-soft opacity-30 transition-opacity group-hover:opacity-60" />
                  <div className="relative flex h-full flex-col justify-between p-3">
                    <span className={cn("w-fit rounded-md px-2 py-0.5 text-[10px] font-semibold", st.cls)}>{st.label}</span>
                    <div className="text-[11px] text-ink-low">
                      <div className="truncate text-ink-medium">{j.kind === "kol_full" ? "KOL AI" : "Video sản phẩm"}</div>
                      <div className="mt-0.5 font-numeric">{j.seconds}s · {j.resolution} · {j.aspect}</div>
                      {j.est_credits > 0 && <CreditValue value={j.est_credits} className="mt-1 text-[11px] text-ink-medium" />}
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}

function ActionCard({ icon: Icon, title, desc, href, hot }: {
  icon: typeof Film; title: string; desc: string; href: string; hot?: boolean;
}): ReactNode {
  return (
    <Link href={href} className="group relative overflow-hidden rounded-2xl glass-bordered p-5 transition-all duration-300 hover:-translate-y-1">
      <span className="pointer-events-none absolute inset-0 rounded-2xl ring-1 ring-violet-400/0 transition group-hover:ring-violet-400/30" />
      <div className="relative flex items-start gap-3">
        <span className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-violet-500/[0.12] text-violet-300 transition-colors group-hover:bg-violet-500/20">
          <Icon className="h-5 w-5" />
        </span>
        <div className="min-w-0">
          <div className="flex items-center gap-1.5">
            <span className="font-display font-semibold text-ink-high">{title}</span>
            {hot && <span className="rounded bg-violet-500/20 px-1.5 py-0.5 text-[9px] font-bold uppercase text-violet-200">Hot</span>}
          </div>
          <p className="mt-0.5 text-sm leading-snug text-ink-low">{desc}</p>
        </div>
        <ArrowRight className="ml-auto h-4 w-4 shrink-0 text-ink-low opacity-0 transition group-hover:translate-x-0.5 group-hover:opacity-100" />
      </div>
    </Link>
  );
}
