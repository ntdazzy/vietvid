"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Mail, Lock, User, Zap, AlertCircle, Loader2, ShieldCheck } from "lucide-react";
import { Logo } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
import { Field, inputCls } from "@/components/ui/field";
import { registerLocal, loginLocal } from "@/lib/auth/local";
import { devLogin } from "@/lib/auth/dev";
import { supabaseConfigured } from "@/lib/config";

const STATS = [
  { v: "60s", l: "mỗi video" },
  { v: "9", l: "công cụ AI" },
  { v: "300", l: "credit tặng" },
];

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
    <div className="grid min-h-dvh lg:grid-cols-2">
      {/* LEFT — branding (ẩn trên mobile) */}
      <div className="relative hidden flex-col justify-between overflow-hidden bg-bg-surface p-10 lg:flex">
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.35]"
          style={{
            backgroundImage:
              "linear-gradient(rgba(255,255,255,.04) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.04) 1px, transparent 1px)",
            backgroundSize: "40px 40px",
            maskImage: "radial-gradient(120% 90% at 30% 20%, black, transparent 75%)",
          }}
        />
        <div className="glow-radial pointer-events-none absolute -left-20 top-0 h-[420px] w-[420px]" />

        <Logo />

        <div className="relative">
          <h1 className="max-w-md text-[clamp(2rem,3.4vw,3rem)] font-extrabold leading-[1.08] tracking-[-0.02em] text-ink-high">
            Video bán hàng AI,
            <br />
            <span className="text-gradient">giọng Việt thật.</span>
          </h1>
          <p className="mt-4 max-w-sm text-ink-medium">
            Từ 1 ảnh sản phẩm tới video chốt đơn trong 60 giây. Minh bạch giá, hoàn 100% nếu lỗi hệ thống.
          </p>
          <div className="mt-8 flex gap-8">
            {STATS.map((s) => (
              <div key={s.l}>
                <div className="font-numeric text-3xl font-bold text-ink-high">{s.v}</div>
                <div className="text-sm text-ink-low">{s.l}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="relative flex items-center gap-2 text-sm text-ink-low">
          <span className="h-2 w-2 rounded-full bg-success shadow-glow-success" />
          Giọng Việt thật · không cần máy quay, không cần ekip
        </div>
      </div>

      {/* RIGHT — form */}
      <div className="relative grid place-items-center overflow-hidden mesh-bg px-4 py-10">
        <Link href="/" className="absolute left-6 top-6 lg:hidden">
          <Logo />
        </Link>

        <div className="w-full max-w-sm">
          <h2 className="text-2xl font-bold text-ink-high">
            {mode === "register" ? "Tạo tài khoản" : "Đăng nhập"}
          </h2>
          <p className="mt-1 text-sm text-ink-low">
            {mode === "register" ? "Tặng 300 credit để tạo video đầu tiên." : "Chào mừng trở lại VietVid."}
          </p>

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

          <p className="mt-6 flex items-center justify-center gap-1.5 text-[11px] text-ink-disabled">
            <ShieldCheck className="h-3.5 w-3.5" /> Bảo mật TLS · dữ liệu của bạn được cách ly riêng
          </p>
        </div>
      </div>
    </div>
  );
}
