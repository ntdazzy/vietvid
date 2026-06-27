"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Zap, Mail, AlertCircle } from "lucide-react";
import { Logo } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
import { GlassCard } from "@/components/ui/glass-card";
import { devLogin } from "@/lib/auth/dev";
import { supabaseConfigured } from "@/lib/config";
import { vi } from "@/lib/i18n/vi";

export default function LoginPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const hasSupabase = supabaseConfigured();

  async function handleDevLogin() {
    setLoading(true);
    setError(null);
    try {
      await devLogin();
      router.push("/app");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Đăng nhập thất bại");
      setLoading(false);
    }
  }

  return (
    <div className="relative grid min-h-dvh place-items-center overflow-hidden mesh-bg px-4">
      <Link href="/" className="absolute left-6 top-6">
        <Logo />
      </Link>

      <GlassCard bordered className="w-full max-w-md p-8">
        <h1 className="text-center text-2xl font-bold text-ink-high">{vi.login.title}</h1>
        <p className="mt-2 text-center text-sm text-ink-low">
          Tặng credit free để bạn tạo video đầu tiên ngay.
        </p>

        <div className="mt-7 flex flex-col gap-3">
          {!hasSupabase && (
            <Button onClick={handleDevLogin} size="lg" disabled={loading} className="gap-2">
              <Zap className="h-4 w-4" />
              {loading ? "Đang tạo phiên…" : vi.login.dev}
            </Button>
          )}

          <Button variant="glass" size="lg" disabled={!hasSupabase} className="gap-2">
            <svg className="h-4 w-4" viewBox="0 0 24 24" aria-hidden>
              <path
                fill="currentColor"
                d="M12 11v2.8h4.6c-.2 1.2-1.4 3.5-4.6 3.5-2.8 0-5-2.3-5-5.1s2.2-5.1 5-5.1c1.6 0 2.6.7 3.2 1.2l2.2-2.1C16 3.6 14.2 3 12 3 7 3 3 7 3 12s4 9 9 9c5.2 0 8.6-3.6 8.6-8.7 0-.6-.1-1-.2-1.3H12Z"
              />
            </svg>
            {vi.login.google}
          </Button>

          <Button variant="ghost" size="lg" disabled={!hasSupabase} className="gap-2">
            <Mail className="h-4 w-4" /> {vi.login.email}
          </Button>
        </div>

        {error && (
          <div className="mt-4 flex items-start gap-2 rounded-lg border border-danger/30 bg-danger/[0.1] p-3 text-sm text-danger">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {!hasSupabase && (
          <p className="mt-5 text-center text-[11px] leading-relaxed text-ink-disabled">
            {vi.login.devHint}
          </p>
        )}
      </GlassCard>
    </div>
  );
}
