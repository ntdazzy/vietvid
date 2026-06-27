"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Mail, Lock, User, Zap, AlertCircle, Loader2 } from "lucide-react";
import { Logo } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
import { GlassCard } from "@/components/ui/glass-card";
import { Field, inputCls } from "@/components/ui/field";
import { registerLocal, loginLocal } from "@/lib/auth/local";
import { devLogin } from "@/lib/auth/dev";
import { supabaseConfigured } from "@/lib/config";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [loading, setLoading] = useState<null | "form" | "dev">(null);
  const [error, setError] = useState<string | null>(null);
  const hasSupabase = supabaseConfigured();

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading("form");
    setError(null);
    try {
      if (mode === "register") await registerLocal(email, password, name);
      else await loginLocal(email, password);
      router.push("/app");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Có lỗi xảy ra");
      setLoading(null);
    }
  }

  async function quickDev() {
    setLoading("dev");
    setError(null);
    try {
      await devLogin();
      router.push("/app");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Dev login lỗi");
      setLoading(null);
    }
  }

  return (
    <div className="relative grid min-h-dvh place-items-center overflow-hidden mesh-bg px-4">
      <Link href="/" className="absolute left-6 top-6">
        <Logo />
      </Link>

      <GlassCard bordered className="w-full max-w-md p-8">
        <h1 className="text-center text-2xl font-bold text-ink-high">
          {mode === "register" ? "Tạo tài khoản VietVid" : "Đăng nhập VietVid"}
        </h1>
        <p className="mt-2 text-center text-sm text-ink-low">
          {mode === "register" ? "Tặng 300 credit để tạo video đầu tiên." : "Chào mừng trở lại."}
        </p>

        {/* tab */}
        <div className="mt-6 grid grid-cols-2 gap-1 rounded-lg border border-white/10 bg-white/[0.02] p-1">
          {(["login", "register"] as const).map((m) => (
            <button
              key={m}
              onClick={() => {
                setMode(m);
                setError(null);
              }}
              className={`rounded-md py-2 text-sm font-medium transition-colors ${
                mode === m ? "bg-violet-500/20 text-ink-high" : "text-ink-low hover:text-ink-medium"
              }`}
            >
              {m === "login" ? "Đăng nhập" : "Đăng ký"}
            </button>
          ))}
        </div>

        <form onSubmit={submit} className="mt-5 flex flex-col gap-4">
          {mode === "register" && (
            <Field label="Tên của bạn">
              <div className="relative">
                <User className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-low" />
                <input className={`${inputCls} pl-9`} value={name} onChange={(e) => setName(e.target.value)} placeholder="Nguyễn Văn A" />
              </div>
            </Field>
          )}
          <Field label="Email">
            <div className="relative">
              <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-low" />
              <input type="email" required className={`${inputCls} pl-9`} value={email} onChange={(e) => setEmail(e.target.value)} placeholder="ban@email.com" />
            </div>
          </Field>
          <Field label="Mật khẩu">
            <div className="relative">
              <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-low" />
              <input type="password" required minLength={6} className={`${inputCls} pl-9`} value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Tối thiểu 6 ký tự" />
            </div>
          </Field>

          {error && (
            <div className="flex items-start gap-2 rounded-lg border border-danger/30 bg-danger/[0.1] p-3 text-sm text-danger">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <Button type="submit" size="lg" disabled={loading !== null}>
            {loading === "form" ? <Loader2 className="h-4 w-4 animate-spin" /> : mode === "register" ? "Đăng ký" : "Đăng nhập"}
          </Button>
        </form>

        {hasSupabase && (
          <Button variant="glass" size="lg" className="mt-3 w-full gap-2">
            <svg className="h-4 w-4" viewBox="0 0 24 24" aria-hidden>
              <path fill="currentColor" d="M12 11v2.8h4.6c-.2 1.2-1.4 3.5-4.6 3.5-2.8 0-5-2.3-5-5.1s2.2-5.1 5-5.1c1.6 0 2.6.7 3.2 1.2l2.2-2.1C16 3.6 14.2 3 12 3 7 3 3 7 3 12s4 9 9 9c5.2 0 8.6-3.6 8.6-8.7 0-.6-.1-1-.2-1.3H12Z" />
            </svg>
            Tiếp tục với Google
          </Button>
        )}

        {!hasSupabase && (
          <button
            onClick={quickDev}
            disabled={loading !== null}
            className="mt-4 flex w-full items-center justify-center gap-1.5 text-xs text-ink-low hover:text-ink-medium"
          >
            {loading === "dev" ? <Loader2 className="h-3 w-3 animate-spin" /> : <Zap className="h-3 w-3" />}
            Hoặc đăng nhập nhanh (Dev) để thử
          </button>
        )}
      </GlassCard>
    </div>
  );
}
