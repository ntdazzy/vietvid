"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { isAuthed } from "@/lib/auth/session";
import { Logo } from "@/components/brand/logo";

/** Chặn route /app khi chưa đăng nhập → đẩy về /login. */
export function AuthGate({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [ok, setOk] = useState<boolean | null>(null);

  useEffect(() => {
    let alive = true;
    isAuthed().then((authed) => {
      if (!alive) return;
      if (!authed) router.replace("/login");
      setOk(authed);
    });
    return () => {
      alive = false;
    };
  }, [router]);

  if (ok === null || ok === false) {
    return (
      <div className="grid min-h-dvh place-items-center">
        <div className="flex animate-pulse flex-col items-center gap-4">
          <Logo showWord={false} className="scale-125" />
          <p className="text-sm text-ink-low">Đang tải…</p>
        </div>
      </div>
    );
  }
  return <>{children}</>;
}
