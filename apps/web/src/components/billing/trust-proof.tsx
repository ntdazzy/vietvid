"use client";

import { Lock, Check, RotateCcw, ShieldCheck } from "lucide-react";
import type { LedgerEntry } from "@/lib/api/types";
import { GlassCard } from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";
import { HoldMeter } from "@/components/create/hold-meter";

interface Triple {
  hold: number;
  used: number;
  refunded: number;
  real: boolean;
}

// Lấy bộ HOLD→SETTLE/REFUND THẬT mới nhất của user từ ledger; không có → ví dụ minh hoạ.
function deriveTriple(entries: LedgerEntry[] | undefined): Triple {
  const ILLUSTRATIVE: Triple = { hold: 180, used: 140, refunded: 40, real: false };
  if (!entries?.length) return ILLUSTRATIVE;

  const byJob = new Map<string, LedgerEntry[]>();
  for (const e of entries) {
    if (!e.job_id) continue;
    const arr = byJob.get(e.job_id) ?? [];
    arr.push(e);
    byJob.set(e.job_id, arr);
  }

  let best: { maxId: number; rows: LedgerEntry[] } | null = null;
  for (const rows of byJob.values()) {
    const hasHold = rows.some((r) => r.entry_type === "HOLD");
    const closed = rows.some((r) => r.entry_type === "SETTLE" || r.entry_type === "REFUND");
    if (!hasHold || !closed) continue;
    const maxId = Math.max(...rows.map((r) => r.id));
    if (!best || maxId > best.maxId) best = { maxId, rows };
  }
  if (!best) return ILLUSTRATIVE;

  const hold = Math.abs(best.rows.find((r) => r.entry_type === "HOLD")!.delta_credits);
  const settle = best.rows.find((r) => r.entry_type === "SETTLE");
  const refund = best.rows.find((r) => r.entry_type === "REFUND");
  const returned = (settle?.delta_credits ?? 0) + (refund?.delta_credits ?? 0);
  return { hold, used: Math.max(0, hold - returned), refunded: returned, real: true };
}

/** Khối tin cậy: kể câu chuyện GIỮ → DÙNG → HOÀN bằng giao dịch thật (hoặc minh hoạ). */
export function TrustProof({
  entries,
  balance,
}: {
  entries: LedgerEntry[] | undefined;
  balance: number;
}) {
  const t = deriveTriple(entries);
  return (
    <GlassCard bordered className="flex flex-col gap-5 p-6 lg:p-7">
      <div>
        <h2 className="flex items-center gap-2 font-display text-xl font-bold text-ink-high">
          <ShieldCheck className="h-5 w-5 text-violet-300" /> Không bao giờ trừ tiền âm thầm
        </h2>
        <p className="mt-1 text-sm text-ink-medium">
          Tạm giữ tối đa, dùng bao nhiêu tính bấy nhiêu, hoàn 100% nếu lỗi hệ thống.
        </p>
      </div>

      {/* chú giải 3 bước — cùng màu với hàng ledger bên dưới */}
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-sm">
        <span className="flex items-center gap-1.5 text-hold">
          <Lock className="h-4 w-4" /> Giữ
        </span>
        <span className="text-ink-disabled">→</span>
        <span className="flex items-center gap-1.5 text-ink-medium">
          <Check className="h-4 w-4" /> Dùng
        </span>
        <span className="text-ink-disabled">→</span>
        <span className="flex items-center gap-1.5 text-refund">
          <RotateCcw className="h-4 w-4" /> Hoàn
        </span>
        <Badge tone="neutral" className="ml-auto">
          {t.real ? "Giao dịch thật của bạn" : "Ví dụ minh hoạ"}
        </Badge>
      </div>

      <HoldMeter
        phase="settled"
        balance={balance}
        estCredits={t.hold}
        holdCredits={t.hold}
        usedCredits={t.used}
        refundedCredits={t.refunded}
      />
    </GlassCard>
  );
}
