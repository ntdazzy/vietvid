"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Sparkles, FolderOpen, Wallet, Settings } from "lucide-react";
import { Logo } from "@/components/brand/logo";
import { cn } from "@/lib/utils/cn";
import { vi } from "@/lib/i18n/vi";

const NAV = [
  { href: "/app", label: vi.nav.dashboard, icon: LayoutDashboard, exact: true },
  { href: "/app/create", label: vi.nav.create, icon: Sparkles },
  { href: "/app/library", label: vi.nav.library, icon: FolderOpen },
  { href: "/app/billing", label: vi.nav.billing, icon: Wallet },
  { href: "/app/settings", label: vi.nav.settings, icon: Settings },
];

export function Sidebar() {
  const path = usePathname();
  return (
    <aside className="sticky top-0 hidden h-dvh w-64 shrink-0 flex-col border-r border-white/[0.06] bg-bg-surface/60 px-4 py-5 backdrop-blur-xl lg:flex">
      <div className="px-2">
        <Link href="/">
          <Logo />
        </Link>
      </div>
      <nav className="mt-8 flex flex-col gap-1">
        {NAV.map(({ href, label, icon: Icon, exact }) => {
          const active = exact ? path === href : path.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition-colors",
                active
                  ? "bg-white/[0.06] text-ink-high"
                  : "text-ink-low hover:bg-white/[0.04] hover:text-ink-medium",
              )}
            >
              {active && (
                <span className="absolute left-0 top-1/2 h-5 w-0.5 -translate-y-1/2 rounded-full bg-grad-brand shadow-glow-sm" />
              )}
              <Icon className={cn("h-[18px] w-[18px]", active && "text-violet-300")} />
              {label}
            </Link>
          );
        })}
      </nav>
      <div className="mt-auto px-2 text-[11px] text-ink-disabled">Vyra · M1 · dark cinematic</div>
    </aside>
  );
}
