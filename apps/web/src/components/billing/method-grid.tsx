"use client";

import { useTranslations } from "next-intl";
import { QrCode, Wallet, Landmark, CircleDollarSign, FlaskConical, type LucideIcon } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils/cn";

export type Method = "bank_qr" | "momo" | "vnpay" | "dev";

interface MethodDef {
  id: Method | "usdt";
  labelKey: string;
  subKey: string;
  icon: LucideIcon;
  recommended?: boolean;
  maintenance?: boolean;
  devOnly?: boolean;
}

const METHODS: MethodDef[] = [
  { id: "momo", labelKey: "methodMomo", subKey: "methodMomoSub", icon: Wallet },
  { id: "bank_qr", labelKey: "methodBankQr", subKey: "methodBankQrSub", icon: QrCode, recommended: true },
  { id: "vnpay", labelKey: "methodVnpay", subKey: "methodVnpaySub", icon: Landmark },
  { id: "usdt", labelKey: "methodUsdt", subKey: "methodUsdtSub", icon: CircleDollarSign, maintenance: true },
  { id: "dev", labelKey: "methodDev", subKey: "methodDevSub", icon: FlaskConical, devOnly: true },
];

/** Lưới chọn cách nạp (autovis-style): QR ngân hàng / MoMo / VNPay / USDT (bảo trì). */
export function MethodGrid({ method, setMethod }: { method: Method; setMethod: (m: Method) => void }) {
  const t = useTranslations("billing");
  const items = METHODS.filter((m) => !m.devOnly || process.env.NODE_ENV !== "production");
  return (
    <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-3 lg:grid-cols-5">
      {items.map((m) => {
        const active = method === m.id;
        const disabled = Boolean(m.maintenance);
        const label = t(m.labelKey);
        return (
          <button
            key={m.id}
            type="button"
            disabled={disabled}
            aria-pressed={active}
            aria-label={m.maintenance ? t("payWithAriaMaintenance", { label }) : t("payWithAria", { label })}
            onClick={() => !disabled && setMethod(m.id as Method)}
            className={cn(
              "relative flex flex-col items-start gap-2 rounded-xl border p-3 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400/40",
              active
                ? "border-emerald-400/50 bg-emerald-500/10 shadow-glow-success"
                : "border-white/10 hover:border-white/25",
              disabled && "cursor-not-allowed opacity-55 hover:border-white/10",
            )}
          >
            <span
              className={cn(
                "grid h-9 w-9 place-items-center rounded-lg",
                active ? "bg-emerald-500/15 text-emerald-200" : "bg-white/[0.05] text-ink-low",
              )}
            >
              <m.icon className="h-5 w-5" />
            </span>
            <span className="min-w-0">
              <span className="block text-sm font-medium text-ink-high">{label}</span>
              <span className="block truncate text-[11px] text-ink-low">{t(m.subKey)}</span>
            </span>
            {m.recommended && (
              <Badge tone="brand" className="absolute right-2 top-2 px-1.5 py-0.5 text-[9px]">
                {t("recommended")}
              </Badge>
            )}
            {m.maintenance && (
              <Badge tone="hold" className="absolute right-2 top-2 px-1.5 py-0.5 text-[9px]">
                {t("maintenance")}
              </Badge>
            )}
          </button>
        );
      })}
    </div>
  );
}
