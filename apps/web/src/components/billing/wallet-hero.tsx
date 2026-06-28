"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { Lock, ArrowRight, ArrowDown } from "lucide-react";
import type { WalletResponse } from "@/lib/api/types";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { CreditValue } from "@/components/ui/credit-value";
import { Skeleton } from "@/components/ui/skeleton";

const VND_PER_CREDIT = 150; // CREDIT_PRICE_VND
const CREDITS_PER_VIDEO = 150; // ~trung điểm 100–180 credit/video

/** Hero ví: số dư (tick mượt) + quy đổi đ + credit đang giữ | "làm được ~N video" + CTA. */
export function WalletHero({
  wallet,
  loading,
  onScrollToHeld,
  onScrollToPacks,
}: {
  wallet?: WalletResponse;
  loading: boolean;
  onScrollToHeld: () => void;
  onScrollToPacks: () => void;
}) {
  const balance = wallet?.balance_credits ?? 0;
  const held = wallet?.held_credits ?? 0;
  const low = balance > 0 && balance < 100;
  const capacity = Math.floor(balance / CREDITS_PER_VIDEO);

  return (
    <GlassCard bordered className="relative overflow-hidden p-7 lg:p-8">
      <div className="glow-radial pointer-events-none absolute inset-x-0 -top-20 h-40" />
      <div className="relative grid gap-6 lg:grid-cols-12">
        {/* TRÁI — số dư */}
        <div className="lg:col-span-7">
          <span className="inline-flex items-center gap-2 text-sm text-ink-low">
            Số dư khả dụng
            {low && <Badge tone="hold">Số dư thấp</Badge>}
          </span>
          <div className="mt-1">
            {loading ? (
              <Skeleton className="h-12 w-48" />
            ) : (
              <motion.span
                key={balance}
                initial={{ opacity: 0.4 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.25 }}
                className="inline-block"
              >
                <CreditValue value={balance} className="text-4xl font-bold tracking-tight text-ink-high sm:text-5xl lg:text-6xl" />
              </motion.span>
            )}
          </div>
          <div className="mt-1 text-sm text-ink-low">
            ≈ {(balance * VND_PER_CREDIT).toLocaleString("vi-VN")}đ
          </div>

          {held > 0 && (
            <button
              type="button"
              onClick={onScrollToHeld}
              aria-label="Xem các khoản đang tạm giữ trong sổ cái"
              className="mt-4 flex w-full max-w-sm flex-col gap-1 rounded-xl border border-hold/30 bg-hold/[0.12] px-3.5 py-2.5 text-left transition-colors hover:border-hold/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-hold/50"
            >
              <span className="flex items-center gap-1.5 text-sm font-medium text-hold">
                <Lock className="h-3.5 w-3.5" /> Đang tạm giữ{" "}
                <CreditValue value={held} suffix={null} className="text-sm" />
              </span>
              <span className="text-xs text-ink-low">
                Credit của job đang chạy được giữ tạm — hoàn lại phần thừa khi xong.
              </span>
            </button>
          )}
        </div>

        {/* PHẢI — làm được bao nhiêu video */}
        <div className="lg:col-span-5 lg:border-l lg:border-white/[0.06] lg:pl-6">
          <div className="border-t border-white/[0.06] pt-6 lg:border-t-0 lg:pt-0">
            <span className="text-sm text-ink-low">Số dư này làm được</span>
            <div className="mt-1">
              {loading ? (
                <Skeleton className="h-9 w-24" />
              ) : low ? (
                <div className="text-2xl font-bold text-hold">Chưa đủ cho 1 video</div>
              ) : (
                <div className="font-numeric text-4xl font-bold text-ink-high">
                  ~{capacity.toLocaleString("vi-VN")}
                  <span className="ml-1.5 font-sans text-base font-normal text-ink-low">video</span>
                </div>
              )}
            </div>
            {!low && (
              <p className="mt-1 text-xs text-ink-low">ước tính theo ~150 credit/video; video ngắn tốn ít hơn.</p>
            )}

            <div className="mt-5">
              {balance === 0 ? (
                <Button variant="glass" size="sm" className="gap-1.5" onClick={onScrollToPacks}>
                  Chọn gói nạp <ArrowDown className="h-4 w-4" />
                </Button>
              ) : (
                <Link href="/app/create">
                  <Button variant="glass" size="sm" className="gap-1.5">
                    Tạo video <ArrowRight className="h-4 w-4" />
                  </Button>
                </Link>
              )}
            </div>
          </div>
        </div>
      </div>
    </GlassCard>
  );
}
