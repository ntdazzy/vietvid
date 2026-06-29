"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { X, Copy, Check, Loader2, ShieldCheck, BadgeCheck } from "lucide-react";
import type { TopupResponse } from "@/lib/api/types";
import { api } from "@/lib/api/endpoints";
import { Button } from "@/components/ui/button";
import { CreditValue } from "@/components/ui/credit-value";
import { cn } from "@/lib/utils/cn";

const vnd = (n: number) => n.toLocaleString("vi-VN") + "đ";

function CopyRow({ label, value }: { label: string; value: string }) {
  const t = useTranslations("billing");
  const [copied, setCopied] = useState(false);
  return (
    <div className="flex items-center justify-between gap-3 py-2.5">
      <span className="text-xs text-ink-low">{label}</span>
      <button
        type="button"
        onClick={() => {
          navigator.clipboard?.writeText(value).then(() => {
            setCopied(true);
            setTimeout(() => setCopied(false), 1400);
          });
        }}
        className="group flex items-center gap-1.5 text-right text-sm font-medium text-ink-high transition-colors hover:text-violet-200"
        aria-label={t("copyAria", { label })}
      >
        <span className="font-numeric tabular">{value}</span>
        {copied ? (
          <Check className="h-3.5 w-3.5 text-success" />
        ) : (
          <Copy className="h-3.5 w-3.5 text-ink-low transition-colors group-hover:text-violet-300" />
        )}
      </button>
    </div>
  );
}

/** Overlay "quét QR để nạp": VietQR + thông tin CK + poll trạng thái → tự cộng. */
export function QrPayPanel({ payment, onClose }: { payment: TopupResponse; onClose: () => void }) {
  const t = useTranslations("billing");
  const qc = useQueryClient();
  const status = useQuery({
    queryKey: ["payment", payment.payment_id],
    queryFn: () => api.paymentStatus(payment.payment_id),
    refetchInterval: (q) => {
      const st = q.state.data?.status;
      return st === "SUCCEEDED" || st === "FAILED" ? false : 3000;
    },
  });
  const paid = status.data?.status === "SUCCEEDED";

  useEffect(() => {
    if (paid) {
      qc.invalidateQueries({ queryKey: ["wallet"] });
      qc.invalidateQueries({ queryKey: ["ledger"] });
    }
  }, [paid, qc]);

  return (
    <AnimatePresence>
      <motion.div
        className="fixed inset-0 z-50 grid place-items-center bg-bg-base/70 p-4 backdrop-blur-sm"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
        role="presentation"
      >
        <motion.div
          role="dialog"
          aria-modal="true"
          aria-label={t("qrDialogAria")}
          onClick={(e) => e.stopPropagation()}
          onKeyDown={(e) => e.key === "Escape" && onClose()}
          initial={{ opacity: 0, y: 16, scale: 0.98 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 16, scale: 0.98 }}
          transition={{ type: "spring", stiffness: 320, damping: 30 }}
          className="glass-bordered relative w-full max-w-lg overflow-hidden rounded-2xl p-6"
        >
          <button
            type="button"
            onClick={onClose}
            aria-label={t("close")}
            className="absolute right-3 top-3 grid h-8 w-8 place-items-center rounded-lg text-ink-low transition-colors hover:bg-white/[0.06] hover:text-ink-high"
          >
            <X className="h-4 w-4" />
          </button>

          {paid ? (
            <div className="flex flex-col items-center gap-3 py-8 text-center">
              <motion.span
                initial={{ scale: 0.6, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ type: "spring", stiffness: 300, damping: 18 }}
                className="grid h-16 w-16 place-items-center rounded-full bg-success/15"
              >
                <BadgeCheck className="h-8 w-8 text-success" />
              </motion.span>
              <h3 className="font-display text-xl font-bold text-ink-high">{t("paymentReceived")}</h3>
              <p className="text-sm text-ink-low">
                {t.rich("creditedToWallet", {
                  value: () => <CreditValue value={payment.credits} className="text-ink-high" />,
                })}
              </p>
              <Button onClick={onClose} className="mt-2">{t("done")}</Button>
            </div>
          ) : (
            <>
              <div className="mb-4">
                <h3 className="font-display text-lg font-bold text-ink-high">{t("qrTitle")}</h3>
                <p className="mt-0.5 text-sm text-ink-low">
                  {t.rich("qrSub", {
                    em: (chunks) => <span className="text-ink-medium">{chunks}</span>,
                  })}
                </p>
              </div>

              <div className="grid gap-5 sm:grid-cols-[180px_1fr]">
                {/* QR */}
                <div className="flex flex-col items-center gap-2">
                  <div className="overflow-hidden rounded-xl bg-white p-2">
                    {payment.qr_image_url ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img src={payment.qr_image_url} alt={t("qrImageAlt")} className="h-40 w-40 object-contain" />
                    ) : (
                      <div className="grid h-40 w-40 place-items-center text-ink-low">QR</div>
                    )}
                  </div>
                  <span className="flex items-center gap-1.5 text-xs text-ink-low">
                    {status.isLoading ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <span className="relative flex h-2 w-2">
                        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-hold/60" />
                        <span className="relative inline-flex h-2 w-2 rounded-full bg-hold" />
                      </span>
                    )}
                    {t("waitingTransfer")}
                  </span>
                </div>

                {/* chi tiết CK */}
                <div className="flex flex-col">
                  <div className="divide-y divide-white/[0.06] rounded-xl bg-white/[0.02] px-3.5">
                    <div className="flex items-center justify-between gap-3 py-2.5">
                      <span className="text-xs text-ink-low">{t("bank")}</span>
                      <span className="text-sm font-medium text-ink-high">{payment.bank?.name || "—"}</span>
                    </div>
                    <CopyRow label={t("accountNumber")} value={payment.bank?.account_number || ""} />
                    <div className="flex items-center justify-between gap-3 py-2.5">
                      <span className="text-xs text-ink-low">{t("accountName")}</span>
                      <span className="truncate text-right text-sm font-medium text-ink-high">{payment.bank?.account_name || "—"}</span>
                    </div>
                    <CopyRow label={t("amount")} value={String(payment.amount_vnd)} />
                    <CopyRow label={t("transferMemo")} value={payment.memo || ""} />
                  </div>

                  <div className="mt-3 flex items-baseline justify-between rounded-xl border border-violet-400/20 bg-violet-500/[0.06] px-3.5 py-2.5">
                    <span className="text-xs text-ink-low">{t("youReceive")}</span>
                    <CreditValue value={payment.credits} className="text-lg font-bold text-ink-high" />
                  </div>

                  <p className="mt-3 flex items-start gap-1.5 text-[11px] text-ink-low">
                    <ShieldCheck className="mt-0.5 h-3.5 w-3.5 shrink-0 text-violet-300" />
                    {t.rich("transferAccurateNote", {
                      em: (chunks) => <span className="text-ink-medium">{chunks}</span>,
                    })}
                  </p>
                </div>
              </div>

              {/* công cụ thử (chỉ hiện ở môi trường dev) */}
              {process.env.NODE_ENV !== "production" && (
                <button
                  type="button"
                  onClick={() =>
                    api.devConfirmPayment(payment.payment_id).then(() => status.refetch())
                  }
                  className="mt-4 w-full rounded-lg border border-dashed border-white/12 py-2 text-xs text-ink-disabled transition-colors hover:text-ink-low"
                >
                  {t("simulatePayment")}
                </button>
              )}
            </>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
