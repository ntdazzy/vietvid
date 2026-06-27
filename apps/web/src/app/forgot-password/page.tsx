"use client";

import { useState } from "react";
import Link from "next/link";
import { Mail, Loader2, CheckCircle2 } from "lucide-react";
import { AuthShell } from "@/components/auth/auth-shell";
import { Button } from "@/components/ui/button";
import { Field, inputCls } from "@/components/ui/field";
import { forgotPassword } from "@/lib/auth/local";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      await forgotPassword(email.trim().toLowerCase());
      setSent(true);
    } finally {
      setLoading(false);
    }
  }

  if (sent) {
    return (
      <AuthShell title="Kiểm tra email">
        <div className="flex items-start gap-3 rounded-xl border border-success/30 bg-success/[0.08] p-4 text-sm text-ink-medium">
          <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-success" />
          <span>
            Nếu <b className="text-ink-high">{email}</b> có tài khoản, chúng tôi đã gửi link đặt lại
            mật khẩu (hết hạn sau 1 giờ).
          </span>
        </div>
        <Link href="/login" className="mt-6 block text-center text-sm text-violet-300 hover:text-violet-200">
          Quay lại đăng nhập
        </Link>
      </AuthShell>
    );
  }

  return (
    <AuthShell title="Quên mật khẩu" subtitle="Nhập email để nhận link đặt lại.">
      <form onSubmit={submit} className="flex flex-col gap-4">
        <Field label="Email">
          <div className="relative">
            <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-low" />
            <input
              type="email"
              required
              className={`${inputCls} pl-9`}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="ban@email.com"
            />
          </div>
        </Field>
        <Button type="submit" size="lg" disabled={loading}>
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Gửi link đặt lại"}
        </Button>
      </form>
      <Link href="/login" className="mt-5 block text-center text-sm text-ink-low hover:text-ink-medium">
        Quay lại đăng nhập
      </Link>
    </AuthShell>
  );
}
