"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { CheckCircle2, XCircle, Loader2, Coins } from "lucide-react";
import { AuthShell } from "@/components/auth/auth-shell";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api/endpoints";

type Result = "pending" | "ok" | "failed";

export default function BillingReturnPage() {
  const [result, setResult] = useState<Result>("pending");
  const [balance, setBalance] = useState<number | null>(null);

  useEffect(() => {
    const q = new URLSearchParams(window.location.search);
    // VNPay trả vnp_ResponseCode "00" = thành công. Cổng dev: ?status=ok.
    const code = q.get("vnp_ResponseCode") || q.get("status") || "";
    const success = code === "00" || code === "ok";
    setResult(success ? "ok" : code ? "failed" : "ok");

    // Credit về ví qua IPN (bất đồng bộ). Poll số dư vài lần để phản ánh.
    let n = 0;
    const tick = async () => {
      try {
        const w = await api.wallet();
        setBalance(w.balance_credits);
      } catch {
        /* bỏ qua */
      }
      if (++n < 5) setTimeout(tick, 2000);
    };
    if (success) void tick();
  }, []);

  return (
    <AuthShell title="Kết quả thanh toán">
      {result === "failed" ? (
        <div className="flex items-start gap-3 rounded-xl border border-danger/30 bg-danger/[0.1] p-4 text-sm text-danger">
          <XCircle className="mt-0.5 h-5 w-5 shrink-0" />
          <span>Thanh toán chưa hoàn tất hoặc đã bị huỷ. Bạn có thể thử lại.</span>
        </div>
      ) : (
        <div className="flex items-start gap-3 rounded-xl border border-success/30 bg-success/[0.08] p-4 text-sm text-ink-medium">
          <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-success" />
          <span>
            Thanh toán đã ghi nhận. Credit đang được cộng vào ví của bạn.
            {balance !== null && (
              <span className="mt-2 flex items-center gap-1.5 font-numeric text-ink-high">
                <Coins className="h-4 w-4 text-violet-300" /> Số dư: {balance.toLocaleString("vi-VN")} credit
              </span>
            )}
            {balance === null && (
              <span className="mt-2 flex items-center gap-1.5 text-ink-low">
                <Loader2 className="h-4 w-4 animate-spin" /> Đang cập nhật số dư...
              </span>
            )}
          </span>
        </div>
      )}
      <div className="mt-6 flex gap-3">
        <Link href="/app/billing">
          <Button>Về trang nạp credit</Button>
        </Link>
        <Link href="/app">
          <Button variant="glass">Vào ứng dụng</Button>
        </Link>
      </div>
    </AuthShell>
  );
}
