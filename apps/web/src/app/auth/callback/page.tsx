"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import type { AuthSession } from "@supabase/supabase-js";
import { getSupabase } from "@/lib/auth/supabase";
import { setAuthCookie } from "@/lib/auth/cookie";
import { Logo } from "@/components/brand/logo";

// Đích quay về sau OAuth: chỉ path nội bộ (chống open-redirect), mặc định /app.
function nextTarget() {
  if (typeof window === "undefined") return "/app";
  const n = new URLSearchParams(window.location.search).get("next");
  return n && n.startsWith("/") && !n.startsWith("//") ? n : "/app";
}

/**
 * Đích redirect của Supabase OAuth. Client Supabase (@supabase/ssr, detectSessionInUrl)
 * tự đổi ?code -> session; ta chờ phiên có thật rồi set cờ cookie phiên (cho middleware)
 * và quay về ?next. Lỗi/timeout -> về /login.
 */
export default function AuthCallbackPage() {
  const router = useRouter();

  useEffect(() => {
    const supabase = getSupabase();
    if (!supabase) {
      router.replace("/login");
      return;
    }
    let done = false;
    const finish = (hasSession: boolean) => {
      if (done) return;
      done = true;
      if (hasSession) {
        setAuthCookie();
        router.replace(nextTarget());
      } else {
        router.replace("/login?error=oauth");
      }
    };
    // Phiên có thể đã được đổi xong ngay khi client khởi tạo.
    supabase.auth.getSession().then(({ data }: { data: { session: AuthSession | null } }) => {
      if (data.session) finish(true);
    });
    // Hoặc lắng nghe sự kiện SIGNED_IN khi việc đổi code hoàn tất.
    const { data: sub } = supabase.auth.onAuthStateChange((_e: string, session: AuthSession | null) => {
      if (session) finish(true);
    });
    const timeout = setTimeout(() => finish(false), 8000);
    return () => {
      sub.subscription.unsubscribe();
      clearTimeout(timeout);
    };
  }, [router]);

  return (
    <div className="grid min-h-dvh place-items-center mesh-bg">
      <div className="flex animate-pulse flex-col items-center gap-4">
        <Logo showWord={false} className="scale-125" />
        <p className="text-sm text-ink-low">Đang hoàn tất đăng nhập…</p>
      </div>
    </div>
  );
}
