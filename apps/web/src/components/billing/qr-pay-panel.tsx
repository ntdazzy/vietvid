"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { X, Copy, Check, Loader2, ShieldCheck, BadgeCheck, RefreshCw, Clock } from "lucide-react";
import type { TopupResponse } from "@/lib/api/types";
import { api } from "@/lib/api/endpoints";
import { Button } from "@/components/ui/button";
import { CreditValue } from "@/components/ui/credit-value";
import { cn } from "@/lib/utils/cn";

const QR_TTL = 15 * 60; // QR còn hiệu lực 15 phút (cue khẩn trương, không khoá cứng)

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
          <motion.span initial={{ scale: 0.5 }} animate={{ scale: 1 }}>
            <Check className="h-3.5 w-3.5 text-success" />
          </motion.span>
        ) : (
          <Copy className="h-3.5 w-3.5 text-ink-low transition-colors group-hover:text-violet-300" />
        )}
      </button>
    </div>
  );
}

// Góc khung quét (viewfinder) — bản sắc Vyra (tím), gợi ý "đưa camera vào đây".
function Corner({ className }: { className: string }) {
  return <span aria-hidden className={cn("absolute h-5 w-5 border-violet-500/70", className)} />;
}

/** Overlay "quét QR để nạp": VietQR lớn + hiệu ứng quét + poll trạng thái → tự cộng credit. */
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

  // đếm ngược hiệu lực QR (cue trực quan; hết giờ thì gợi ý tạo lại, không tự đóng).
  const [left, setLeft] = useState(QR_TTL);
  useEffect(() => {
    if (paid) return;
    const id = setInterval(() => setLeft((s) => Math.max(0, s - 1)), 1000);
    return () => clearInterval(id);
  }, [paid]);
  const mmss = `${String(Math.floor(left / 60)).padStart(2, "0")}:${String(left % 60).padStart(2, "0")}`;
  const expired = left <= 0;

  useEffect(() => {
    if (paid) {
      qc.invalidateQueries({ queryKey: ["wallet"] });
      qc.invalidateQueries({ queryKey: ["ledger"] });
    }
  }, [paid, qc]);

  return (
    <AnimatePresence>
      <motion.div
        className="fixed inset-0 z-50 grid place-items-center overflow-y-auto bg-bg-base/70 p-4 backdrop-blur-sm"
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
          className="glass-bordered relative my-auto w-full max-w-md overflow-hidden rounded-3xl p-6"
        >
          <button
            type="button"
            onClick={onClose}
            aria-label={t("close")}
            className="absolute right-3 top-3 z-10 grid h-8 w-8 place-items-center rounded-lg text-ink-low transition-colors hover:bg-white/[0.06] hover:text-ink-high"
          >
            <X className="h-4 w-4" />
          </button>

          {paid ? (
            <div className="flex flex-col items-center gap-3 py-10 text-center">
              {/* vầng sáng bùng + tick */}
              <div className="relative grid place-items-center">
                <motion.span
                  className="absolute h-24 w-24 rounded-full bg-success/25 blur-2xl"
                  initial={{ scale: 0.4, opacity: 0 }}
                  animate={{ scale: [0.4, 1.6, 1.2], opacity: [0, 0.8, 0.5] }}
                  transition={{ duration: 0.9 }}
                />
                <motion.span
                  initial={{ scale: 0.5, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ type: "spring", stiffness: 300, damping: 16 }}
                  className="relative grid h-20 w-20 place-items-center rounded-full bg-success/15 ring-1 ring-success/40"
                >
                  <BadgeCheck className="h-10 w-10 text-success" />
                </motion.span>
              </div>
              <motion.h3
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.15 }}
                className="font-display text-2xl font-bold text-ink-high"
              >
                {t("paymentReceived")}
              </motion.h3>
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.25 }}
                className="text-sm text-ink-low"
              >
                {t.rich("creditedToWallet", {
                  value: () => <CreditValue value={payment.credits} className="text-base font-bold text-success" />,
                })}
              </motion.p>
              <Button onClick={onClose} size="lg" className="mt-3">{t("done")}</Button>
            </div>
          ) : (
            <>
              <div className="mb-5 pr-8">
                <h3 className="font-display text-xl font-bold text-ink-high">{t("qrTitle")}</h3>
                <p className="mt-1 text-sm text-ink-low">
                  {t.rich("qrSub", { em: (chunks) => <span className="text-ink-medium">{chunks}</span> })}
                </p>
              </div>

              {/* ── QR LỚN + hiệu ứng quét ─────────────────────────────── */}
              <div className="relative mx-auto w-fit">
                <div className="pointer-events-none absolute -inset-8 rounded-[44px] bg-violet-500/20 blur-3xl" />
                <div className="relative rounded-2xl bg-white p-3 shadow-[0_0_0_1px_rgba(124,58,237,.35),0_22px_70px_-14px_rgba(124,58,237,.55)]">
                  <div className="relative overflow-hidden rounded-lg">
                    {payment.qr_image_url ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        src={payment.qr_image_url}
                        alt={t("qrImageAlt")}
                        className={cn(
                          "block h-64 w-64 object-contain transition sm:h-72 sm:w-72",
                          expired && "opacity-30 blur-sm grayscale",
                        )}
                      />
                    ) : (
                      <div className="grid h-64 w-64 place-items-center text-ink-low sm:h-72 sm:w-72">QR</div>
                    )}
                    {/* tia quét chạy lên-xuống khi đang chờ */}
                    {!expired && (
                      <motion.div
                        aria-hidden
                        className="pointer-events-none absolute inset-x-0 h-14 bg-gradient-to-b from-transparent via-violet-500/40 to-transparent"
                        animate={{ top: ["2%", "86%", "2%"] }}
                        transition={{ repeat: Infinity, duration: 2.6, ease: "easeInOut" }}
                      />
                    )}
                    {/* hết hạn → phủ thông báo */}
                    {expired && (
                      <div className="absolute inset-0 grid place-items-center bg-bg-base/40 p-4 text-center text-xs font-medium text-ink-high backdrop-blur-[2px]">
                        {t("qrExpired")}
                      </div>
                    )}
                  </div>
                  {/* 4 góc khung quét */}
                  <Corner className="left-1.5 top-1.5 rounded-tl-md border-l-2 border-t-2" />
                  <Corner className="right-1.5 top-1.5 rounded-tr-md border-r-2 border-t-2" />
                  <Corner className="bottom-1.5 left-1.5 rounded-bl-md border-b-2 border-l-2" />
                  <Corner className="bottom-1.5 right-1.5 rounded-br-md border-b-2 border-r-2" />
                </div>
              </div>

              {/* status + countdown + check ngay */}
              <div className="mt-4 flex flex-wrap items-center justify-center gap-x-4 gap-y-2 text-xs">
                <span className="flex items-center gap-1.5 text-ink-low">
                  <span className="relative flex h-2 w-2">
                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-hold/60" />
                    <span className="relative inline-flex h-2 w-2 rounded-full bg-hold" />
                  </span>
                  {t("waitingTransfer")}
                </span>
                <span className="flex items-center gap-1.5 font-numeric tabular text-ink-low">
                  <Clock className="h-3.5 w-3.5" /> {t("qrValidFor")} {mmss}
                </span>
              </div>

              <Button
                variant="glass"
                onClick={() => status.refetch()}
                disabled={status.isFetching}
                className="mt-3 w-full gap-2"
              >
                {status.isFetching ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
                {t("iPaid")}
              </Button>

              {/* chi tiết chuyển khoản */}
              <div className="mt-4 divide-y divide-white/[0.06] rounded-2xl bg-white/[0.02] px-3.5">
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

              <div className="mt-3 flex items-baseline justify-between rounded-2xl border border-violet-400/20 bg-violet-500/[0.06] px-3.5 py-2.5">
                <span className="text-xs text-ink-low">{t("youReceive")}</span>
                <CreditValue value={payment.credits} className="text-lg font-bold text-ink-high" />
              </div>

              <p className="mt-3 flex items-start gap-1.5 text-[11px] text-ink-low">
                <ShieldCheck className="mt-0.5 h-3.5 w-3.5 shrink-0 text-violet-300" />
                {t.rich("transferAccurateNote", { em: (chunks) => <span className="text-ink-medium">{chunks}</span> })}
              </p>

              {/* công cụ thử (chỉ dev) */}
              {process.env.NODE_ENV !== "production" && (
                <button
                  type="button"
                  onClick={() => api.devConfirmPayment(payment.payment_id).then(() => status.refetch())}
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
