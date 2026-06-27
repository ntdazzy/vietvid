"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ChevronDown, Flame, Menu, X, LogOut, Plus } from "lucide-react";
import { Logo } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
import { CreditBadge } from "@/components/shell/credit-badge";
import { clearSession } from "@/lib/auth/session";
import { CONTENT_GROUPS, type Feature, type FeatureGroup } from "@/lib/features";
import { cn } from "@/lib/utils/cn";

const TOOLS_GROUPS = CONTENT_GROUPS.slice(1); // "Xây kênh" + "Ảnh & Âm thanh"

// panel dropdown ĐỤC (không để nội dung phía sau lọt qua)
const PANEL =
  "rounded-2xl border border-white/[0.1] bg-bg-elevated/95 backdrop-blur-2xl shadow-[0_24px_70px_-20px_rgba(0,0,0,0.8)]";

export function SiteHeader({ authed = false }: { authed?: boolean }) {
  const [open, setOpen] = useState<null | "content" | "tools" | "support">(null);
  const [mobile, setMobile] = useState(false);
  const router = useRouter();

  return (
    <header className="fixed inset-x-0 top-0 z-50">
      <div className="mx-auto mt-4 flex max-w-6xl items-center justify-between rounded-2xl border border-white/[0.07] bg-bg-base/70 px-4 py-2.5 backdrop-blur-xl lg:px-5">
        <Link href={authed ? "/app" : "/"}>
          <Logo />
        </Link>

        {/* desktop nav */}
        <nav className="hidden items-center gap-1 lg:flex" onMouseLeave={() => setOpen(null)}>
          <NavLink href={authed ? "/app" : "/"}>{authed ? "Bảng điều khiển" : "Trang chủ"}</NavLink>
          <Link
            href="/app/create?feature=review"
            className="flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-medium text-violet-200 transition-colors hover:bg-white/[0.05]"
          >
            KOL AI <Flame className="h-3.5 w-3.5 text-orange-400" />
          </Link>

          <Trigger label="Tạo nội dung" active={open === "content"} onEnter={() => setOpen("content")} />
          <Trigger label="Công cụ" active={open === "tools"} onEnter={() => setOpen("tools")} />
          <NavLink href="/app/library" onEnter={() => setOpen(null)}>
            Thư viện
          </NavLink>
          <Trigger label="Hỗ trợ" active={open === "support"} onEnter={() => setOpen("support")} />

          {/* mega panels */}
          {open === "content" && <MegaPanel groups={CONTENT_GROUPS} cols={3} />}
          {open === "tools" && <MegaPanel groups={TOOLS_GROUPS} cols={2} />}
          {open === "support" && (
            <div className="absolute left-1/2 top-full z-50 w-56 -translate-x-1/2 pt-3">
              <div className={cn(PANEL, "overflow-hidden p-2")}>
                {[
                  ["Câu hỏi thường gặp", "/#faq"],
                  ["Lỗi có hoàn tiền?", "/#faq"],
                  ["Liên hệ", "mailto:support@vietvid.vn"],
                ].map(([t, h]) => (
                  <Link key={t} href={h} className="block rounded-lg px-3 py-2 text-sm text-ink-medium hover:bg-white/[0.05] hover:text-ink-high">
                    {t}
                  </Link>
                ))}
              </div>
            </div>
          )}
        </nav>

        <div className="flex items-center gap-2">
          {authed ? (
            <>
              <div className="hidden sm:block">
                <CreditBadge />
              </div>
              <Link href="/app/create" className="hidden sm:block">
                <Button size="sm" className="gap-1.5">
                  <Plus className="h-4 w-4" /> Tạo video
                </Button>
              </Link>
              <button
                onClick={() => {
                  clearSession();
                  router.push("/");
                }}
                className="hidden h-9 w-9 place-items-center rounded-lg text-ink-low hover:bg-white/[0.05] hover:text-ink-medium sm:grid"
                aria-label="Đăng xuất"
              >
                <LogOut className="h-[18px] w-[18px]" />
              </button>
            </>
          ) : (
            <Link href="/login" className="hidden sm:block">
              <Button size="sm">Đăng nhập</Button>
            </Link>
          )}
          <button
            className="grid h-9 w-9 place-items-center rounded-lg text-ink-medium hover:bg-white/[0.05] lg:hidden"
            onClick={() => setMobile((v) => !v)}
            aria-label="Menu"
          >
            {mobile ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {/* mobile menu */}
      {mobile && (
        <div className="mx-auto mt-2 max-w-6xl px-4 lg:hidden">
          <div className={cn(PANEL, "max-h-[70vh] overflow-y-auto p-3")}>
            {CONTENT_GROUPS.map((g) => (
              <div key={g.title} className="mb-3">
                <div className="px-2 pb-1 text-[11px] font-semibold uppercase tracking-wider text-violet-300/70">
                  {g.title}
                </div>
                {g.items.map((f) => (
                  <FeatureRow key={f.key} f={f} onNav={() => setMobile(false)} />
                ))}
              </div>
            ))}
            <Link href={authed ? "/app/create" : "/login"} onClick={() => setMobile(false)}>
              <Button className="mt-1 w-full">{authed ? "Tạo video" : "Đăng nhập"}</Button>
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}

function NavLink({
  href,
  children,
  onEnter,
}: {
  href: string;
  children: React.ReactNode;
  onEnter?: () => void;
}) {
  return (
    <Link
      href={href}
      onMouseEnter={onEnter}
      className="rounded-lg px-3 py-2 text-sm font-medium text-ink-medium transition-colors hover:bg-white/[0.05] hover:text-ink-high"
    >
      {children}
    </Link>
  );
}

function Trigger({ label, active, onEnter }: { label: string; active: boolean; onEnter: () => void }) {
  return (
    <button
      onMouseEnter={onEnter}
      className={cn(
        "flex items-center gap-1 rounded-lg px-3 py-2 text-sm font-medium transition-colors hover:bg-white/[0.05]",
        active ? "text-ink-high" : "text-ink-medium hover:text-ink-high",
      )}
    >
      {label}
      <ChevronDown className={cn("h-3.5 w-3.5 transition-transform", active && "rotate-180")} />
    </button>
  );
}

function MegaPanel({ groups, cols }: { groups: FeatureGroup[]; cols: number }) {
  return (
    <div className="absolute left-1/2 top-full z-50 -translate-x-1/2 pt-3">
      <div
        className={cn(
          PANEL,
          "grid gap-x-6 gap-y-1 p-5",
          cols === 3 ? "w-[840px] grid-cols-3" : "w-[600px] grid-cols-2",
        )}
      >
        {groups.map((g) => (
          <div key={g.title}>
            <div className="mb-2 border-b border-white/[0.06] pb-2 text-[11px] font-semibold uppercase tracking-[0.14em] text-violet-300/70">
              {g.title}
            </div>
            <div className="flex flex-col">
              {g.items.map((f) => (
                <FeatureRow key={f.key} f={f} />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function FeatureRow({ f, onNav }: { f: Feature; onNav?: () => void }) {
  const inner = (
    <div
      className={cn(
        "group flex items-start gap-3 rounded-lg p-2.5 transition-colors",
        f.available ? "hover:bg-white/[0.05]" : "opacity-60",
      )}
    >
      <span
        className={cn(
          "mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-lg",
          f.available ? "bg-grad-brand-soft text-violet-300" : "bg-white/[0.04] text-ink-low",
        )}
      >
        <f.icon className="h-4 w-4" />
      </span>
      <div className="min-w-0">
        <div className="flex items-center gap-1.5">
          <span className="text-sm font-medium text-ink-high">{f.label}</span>
          {f.badge && (
            <span
              className={cn(
                "rounded px-1.5 py-0.5 text-[9px] font-semibold uppercase",
                f.badge === "Sắp có"
                  ? "bg-white/[0.06] text-ink-low"
                  : "bg-violet-500/20 text-violet-200",
              )}
            >
              {f.badge}
            </span>
          )}
        </div>
        <div className="text-xs text-ink-low">{f.desc}</div>
      </div>
    </div>
  );
  if (!f.available) return inner;
  return (
    <Link href={f.href} onClick={onNav}>
      {inner}
    </Link>
  );
}
