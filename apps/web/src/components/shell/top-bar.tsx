"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { LogOut, Plus } from "lucide-react";
import { CreditBadge } from "./credit-badge";
import { Button } from "@/components/ui/button";
import { Logo } from "@/components/brand/logo";
import { clearSession } from "@/lib/auth/session";
import { vi } from "@/lib/i18n/vi";

export function TopBar() {
  const router = useRouter();
  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-white/[0.06] bg-bg-base/70 px-4 backdrop-blur-xl lg:px-6">
      <div className="lg:hidden">
        <Link href="/app">
          <Logo showWord={false} />
        </Link>
      </div>
      <div className="hidden text-sm text-ink-low lg:block">Bảng điều khiển</div>
      <div className="flex items-center gap-3">
        <CreditBadge />
        <Link href="/app/create" className="hidden sm:block">
          <Button size="sm" className="gap-1.5">
            <Plus className="h-4 w-4" /> {vi.nav.create}
          </Button>
        </Link>
        <button
          onClick={() => {
            clearSession();
            router.push("/");
          }}
          className="grid h-9 w-9 place-items-center rounded-lg text-ink-low transition-colors hover:bg-white/[0.05] hover:text-ink-medium"
          aria-label="Đăng xuất"
        >
          <LogOut className="h-[18px] w-[18px]" />
        </button>
      </div>
    </header>
  );
}
