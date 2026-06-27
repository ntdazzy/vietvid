"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Loader2, CheckCircle2, XCircle } from "lucide-react";
import { AuthShell } from "@/components/auth/auth-shell";
import { Button } from "@/components/ui/button";
import { verifyEmail } from "@/lib/auth/local";

export default function VerifyEmailPage() {
  const [state, setState] = useState<"loading" | "ok" | "error">("loading");

  useEffect(() => {
    const token = new URLSearchParams(window.location.search).get("token") || "";
    if (!token) {
      setState("error");
      return;
    }
    verifyEmail(token)
      .then(() => setState("ok"))
      .catch(() => setState("error"));
  }, []);

  return (
    <AuthShell title="Xác minh email">
      {state === "loading" && (
        <div className="flex items-center gap-3 text-ink-medium">
          <Loader2 className="h-5 w-5 animate-spin text-violet-300" /> Đang xác minh...
        </div>
      )}
      {state === "ok" && (
        <>
          <div className="flex items-center gap-3 rounded-xl border border-success/30 bg-success/[0.08] p-4 text-sm text-ink-medium">
            <CheckCircle2 className="h-5 w-5 shrink-0 text-success" />
            Email đã được xác minh. Tài khoản của bạn đã kích hoạt đầy đủ.
          </div>
          <Link href="/app" className="mt-6 block">
            <Button size="lg" className="w-full">
              Vào ứng dụng
            </Button>
          </Link>
        </>
      )}
      {state === "error" && (
        <>
          <div className="flex items-start gap-3 rounded-xl border border-danger/30 bg-danger/[0.1] p-4 text-sm text-danger">
            <XCircle className="mt-0.5 h-5 w-5 shrink-0" />
            <span>Link xác minh không hợp lệ hoặc đã hết hạn. Hãy yêu cầu gửi lại từ trong ứng dụng.</span>
          </div>
          <Link href="/app" className="mt-6 block text-center text-sm text-violet-300 hover:text-violet-200">
            Vào ứng dụng
          </Link>
        </>
      )}
    </AuthShell>
  );
}
