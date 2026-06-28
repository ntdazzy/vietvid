"use client";

import { QrCode, Wallet, Landmark, CircleDollarSign, FlaskConical, type LucideIcon } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils/cn";

export type Method = "bank_qr" | "momo" | "vnpay" | "dev";

interface MethodDef {
  id: Method | "usdt";
  label: string;
  sub: string;
  icon: LucideIcon;
  recommended?: boolean;
  maintenance?: boolean;
  devOnly?: boolean;
}

const METHODS: MethodDef[] = [
  { id: "bank_qr", label: "Chuyển khoản QR", sub: "Quét VietQR · tự cộng", icon: QrCode, recommended: true },
  { id: "momo", label: "MoMo", sub: "Ví điện tử", icon: Wallet },
  { id: "vnpay", label: "VNPay", sub: "Thẻ / ATM nội địa", icon: Landmark },
  { id: "usdt", label: "USDT (TRC20)", sub: "Tiền mã hoá", icon: CircleDollarSign, maintenance: true },
  { id: "dev", label: "Thử nhanh", sub: "Cộng tức thì (dev)", icon: FlaskConical, devOnly: true },
];

/** Lưới chọn cách nạp (autovis-style): QR ngân hàng / MoMo / VNPay / USDT (bảo trì). */
export function MethodGrid({ method, setMethod }: { method: Method; setMethod: (m: Method) => void }) {
  const items = METHODS.filter((m) => !m.devOnly || process.env.NODE_ENV !== "production");
  return (
    <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-3 lg:grid-cols-5">
      {items.map((m) => {
        const active = method === m.id;
        const disabled = Boolean(m.maintenance);
        return (
          <button
            key={m.id}
            type="button"
            disabled={disabled}
            aria-pressed={active}
            aria-label={`Nạp bằng ${m.label}${m.maintenance ? " (đang bảo trì)" : ""}`}
            onClick={() => !disabled && setMethod(m.id as Method)}
            className={cn(
              "relative flex flex-col items-start gap-2 rounded-xl border p-3 text-left transition-colors",
              active
                ? "border-violet-500/60 bg-violet-500/10 shadow-glow-sm"
                : "border-white/10 hover:border-white/25",
              disabled && "cursor-not-allowed opacity-55 hover:border-white/10",
            )}
          >
            <span
              className={cn(
                "grid h-9 w-9 place-items-center rounded-lg",
                active ? "bg-grad-brand-soft text-violet-200" : "bg-white/[0.05] text-ink-low",
              )}
            >
              <m.icon className="h-5 w-5" />
            </span>
            <span className="min-w-0">
              <span className="block text-sm font-medium text-ink-high">{m.label}</span>
              <span className="block truncate text-[11px] text-ink-low">{m.sub}</span>
            </span>
            {m.recommended && (
              <Badge tone="brand" className="absolute right-2 top-2 px-1.5 py-0.5 text-[9px]">
                Khuyên dùng
              </Badge>
            )}
            {m.maintenance && (
              <Badge tone="hold" className="absolute right-2 top-2 px-1.5 py-0.5 text-[9px]">
                Bảo trì
              </Badge>
            )}
          </button>
        );
      })}
    </div>
  );
}
