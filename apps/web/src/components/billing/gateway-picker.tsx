"use client";

import { FlaskConical, Wallet, Landmark, AlertTriangle, type LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils/cn";

export type Gateway = "dev" | "momo" | "vnpay";

const GATEWAYS: { id: Gateway; label: string; sub: string; icon: LucideIcon }[] = [
  { id: "dev", label: "Dev (thử)", sub: "nạp tức thì", icon: FlaskConical },
  { id: "momo", label: "MoMo", sub: "", icon: Wallet },
  { id: "vnpay", label: "VNPay", sub: "", icon: Landmark },
];

/** Chọn cổng thanh toán — tên thật + glyph lucide, KHÔNG logo Visa/MC giả. */
export function GatewayPicker({
  provider,
  setProvider,
  error,
}: {
  provider: Gateway;
  setProvider: (p: Gateway) => void;
  error?: string | null;
}) {
  const current = GATEWAYS.find((g) => g.id === provider)!;
  return (
    <div className="flex flex-col gap-2">
      <span className="text-xs text-ink-low">Cổng thanh toán</span>
      <div className="flex flex-wrap gap-2">
        {GATEWAYS.map((g) => {
          const active = provider === g.id;
          return (
            <button
              key={g.id}
              type="button"
              onClick={() => setProvider(g.id)}
              aria-pressed={active}
              aria-label={`Thanh toán bằng ${g.label}`}
              className={cn(
                "flex items-center gap-2 rounded-lg border px-3 py-2 text-xs font-medium transition-colors",
                active
                  ? "border-violet-400/40 bg-violet-500/20 text-ink-high"
                  : "border-white/10 text-ink-low hover:text-ink-medium",
              )}
            >
              <g.icon className="h-4 w-4" />
              <span>{g.label}</span>
              {g.sub && <span className={cn("font-normal", active ? "text-violet-200/80" : "text-ink-disabled")}>· {g.sub}</span>}
            </button>
          );
        })}
      </div>

      {error ? (
        <div className="flex items-start gap-2 rounded-xl border border-danger/30 bg-danger/[0.08] px-3 py-2.5 text-sm text-danger">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <span className="text-ink-medium">
            <span className="font-medium text-danger">{current.label}</span> có thể chưa được cấu hình. Dùng cổng{" "}
            <button type="button" onClick={() => setProvider("dev")} className="font-medium text-violet-300 underline">
              Dev
            </button>{" "}
            để nạp thử, hoặc liên hệ chủ shop.
          </span>
        </div>
      ) : (
        <p className="text-xs text-ink-disabled">
          MoMo/VNPay bật khi chủ shop cấu hình khoá merchant; cổng "Dev" nạp tức thì để thử.
        </p>
      )}
    </div>
  );
}
