"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Lock, Loader2, CheckCircle2, AlertCircle } from "lucide-react";
import { AuthShell } from "@/components/auth/auth-shell";
import { Button } from "@/components/ui/button";
import { Field, inputCls } from "@/components/ui/field";
import { resetPassword } from "@/lib/auth/local";

export default function ResetPasswordPage() {
  const router = useRouter();
  const [token, setToken] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  useEffect(() => {
    const t = new URLSearchParams(window.location.search).get("token") || "";
    setToken(t);
  }, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await resetPassword(token, password);
      setDone(true);
      setTimeout(() => router.push("/login"), 1800);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Token không hợp lệ hoặc đã hết hạn");
    } finally {
      setLoading(false);
    }
  }

  if (done) {
    return (
      <AuthShell title="Đã đặt lại mật khẩu">
        <div className="flex items-center gap-3 rounded-xl border border-success/30 bg-success/[0.08] p-4 text-sm text-ink-medium">
          <CheckCircle2 className="h-5 w-5 shrink-0 text-success" />
          Mật khẩu đã được cập nhật. Đang chuyển tới trang đăng nhập...
        </div>
      </AuthShell>
    );
  }

  return (
    <AuthShell title="Đặt mật khẩu mới" subtitle="Chọn mật khẩu mới cho tài khoản của bạn.">
      <form onSubmit={submit} className="flex flex-col gap-4">
        <Field label="Mật khẩu mới">
          <div className="relative">
            <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-low" />
            <input
              type="password"
              required
              minLength={6}
              className={`${inputCls} pl-9`}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Tối thiểu 6 ký tự"
            />
          </div>
        </Field>
        {!token && (
          <p className="text-xs text-warning">Thiếu token đặt lại — hãy mở đúng link trong email.</p>
        )}
        {error && (
          <div className="flex items-start gap-2 rounded-lg border border-danger/30 bg-danger/[0.1] p-3 text-sm text-danger">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}
        <Button type="submit" size="lg" disabled={loading || !token}>
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Đặt lại mật khẩu"}
        </Button>
      </form>
      <Link href="/login" className="mt-5 block text-center text-sm text-ink-low hover:text-ink-medium">
        Quay lại đăng nhập
      </Link>
    </AuthShell>
  );
}
