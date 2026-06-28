"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronUp, Loader2 } from "lucide-react";
import { useWizard } from "@/store/wizard";
import { useEstimate, useWallet } from "@/lib/query/hooks";
import { CreditValue } from "@/components/ui/credit-value";
import { HoldMeter } from "./hold-meter";
import { AspectFrame, ConfigDigest } from "./preview-rail";

/** Thanh chi phí dính đáy (chỉ mobile) — luôn thấy ~credit, chạm để mở tóm tắt + HoldMeter. */
export function MobileCostBar() {
  const w = useWizard();
  const est = useEstimate({ mode: w.videoType, purpose: w.purpose, seconds: w.seconds, resolution: w.resolution });
  const wallet = useWallet();
  const [open, setOpen] = useState(false);

  return (
    <>
      {/* sheet mở lên */}
      <AnimatePresence>
        {open && (
          <>
            <motion.div
              role="presentation"
              className="fixed inset-0 z-40 bg-bg-base/60 backdrop-blur-sm lg:hidden"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setOpen(false)}
            />
            <motion.div
              role="dialog"
              aria-modal="true"
              aria-label="Chi tiết ước tính & chi phí"
              onKeyDown={(e) => e.key === "Escape" && setOpen(false)}
              className="fixed inset-x-0 bottom-0 z-50 max-h-[80vh] overflow-y-auto rounded-t-2xl border-t border-white/10 bg-bg-elevated p-5 pb-[calc(env(safe-area-inset-bottom)+1.25rem)] lg:hidden"
              initial={{ y: "100%" }}
              animate={{ y: 0 }}
              exit={{ y: "100%" }}
              transition={{ type: "spring", stiffness: 320, damping: 34 }}
            >
              <div className="mx-auto mb-4 h-1 w-10 rounded-full bg-white/15" />
              <div className="flex flex-col gap-4">
                <ConfigDigest />
                {w.step === 4 && (
                  <HoldMeter
                    phase="estimate"
                    balance={wallet.data?.balance_credits ?? 0}
                    estCredits={est.data?.est_credits ?? 0}
                    holdCredits={est.data?.hold_credits ?? 0}
                  />
                )}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* thanh dính đáy */}
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        aria-label="Xem chi tiết ước tính và chi phí"
        className="glass fixed inset-x-0 bottom-0 z-30 flex items-center justify-between gap-3 border-t border-white/[0.08] px-4 py-2.5 pb-[calc(env(safe-area-inset-bottom)+0.625rem)] lg:hidden"
      >
        <span className="flex items-center gap-2.5">
          <span className="overflow-hidden rounded-md">
            <AspectFrame compact />
          </span>
          <span className="text-left">
            <span className="block text-[11px] text-ink-low">Ước tính</span>
            {est.isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin text-ink-low" />
            ) : (
              <span className="font-numeric text-base font-bold text-ink-high">
                ~<CreditValue value={est.data?.est_credits ?? 0} />
              </span>
            )}
          </span>
        </span>
        <span className="flex items-center gap-1 text-xs text-ink-low">
          Chi tiết
          <ChevronUp className={open ? "h-4 w-4 rotate-180 transition-transform" : "h-4 w-4 transition-transform"} />
        </span>
      </button>
    </>
  );
}
