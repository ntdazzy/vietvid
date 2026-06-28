"use client";

import { useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api/endpoints";
import { ChevronDown, Flame, Menu, X, LogOut, Plus } from "lucide-react";
import { Logo } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
import { CreditBadge } from "@/components/shell/credit-badge";
import { NotifBell } from "@/components/shell/notif-bell";
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
  const me = useQuery({ queryKey: ["me"], queryFn: api.me, enabled: authed });

  // Fix "di vào menu là mất": đóng có ĐỘ TRỄ; rê qua khe trigger→panel không bị đóng.
  const closeTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const cancelClose = () => {
    if (closeTimer.current) clearTimeout(closeTimer.current);
  };
  const openMenu = (k: "content" | "tools" | "support" | null) => {
    cancelClose();
    setOpen(k);
  };
  const scheduleClose = () => {
    cancelClose();
    closeTimer.current = setTimeout(() => setOpen(null), 180);
  };

  return (
    <header className="fixed inset-x-0 top-0 z-50">
      <div className="mx-auto mt-4 flex max-w-6xl items-center justify-between rounded-2xl border border-white/[0.07] bg-bg-base/70 px-4 py-2.5 backdrop-blur-xl lg:px-5">
        <Link href={authed ? "/app" : "/"}>
          <Logo />
        </Link>

        {/* desktop nav */}
        <nav
          className="hidden items-center gap-1 lg:flex"
          onMouseLeave={scheduleClose}
          onMouseEnter={cancelClose}
        >
          <NavLink href={authed ? "/app" : "/"} onEnter={() => openMenu(null)}>
            {authed ? "Bảng điều khiển" : "Trang chủ"}
          </NavLink>
          <Link
            href={authed ? "/app/kol" : "/login"}
            onMouseEnter={() => openMenu(null)}
            className="flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-medium text-violet-200 transition-colors hover:bg-white/[0.05]"
          >
            KOL AI <Flame className="h-3.5 w-3.5 text-orange-400" />
          </Link>

          <Trigger label="Tạo nội dung" active={open === "content"} onEnter={() => openMenu("content")} />
          <Trigger label="Công cụ" active={open === "tools"} onEnter={() => openMenu("tools")} />
          {authed && (
            <NavLink href="/app/templates" onEnter={() => openMenu(null)}>
              Mẫu
            </NavLink>
          )}
          <NavLink href="/app/library" onEnter={() => openMenu(null)}>
            Thư viện
          </NavLink>
          {authed && (
            <NavLink href="/app/affiliate" onEnter={() => openMenu(null)}>
              Affiliate
            </NavLink>
          )}
          {authed && (
            <NavLink href="/app/reports" onEnter={() => openMenu(null)}>
              Báo cáo
            </NavLink>
          )}
          {authed && (
            <NavLink href="/app/api" onEnter={() => openMenu(null)}>
              API
            </NavLink>
          )}
          {authed && me.data?.is_admin && (
            <NavLink href="/app/admin" onEnter={() => openMenu(null)}>
              Admin
            </NavLink>
          )}
          <Trigger label="Hỗ trợ" active={open === "support"} onEnter={() => openMenu("support")} />

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
              <NotifBell />
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
          <div className={cn(PANEL, "max-h-[78vh] overflow-y-auto p-3")}>
            {authed && (
              <div className="mb-3">
                <div className="mb-2 flex items-center justify-between px-1">
                  <CreditBadge />
                </div>
                <div className="grid grid-cols-2 gap-1.5">
                  {[
                    ["Bảng điều khiển", "/app"],
                    ["KOL AI", "/app/kol"],
                    ["Mẫu", "/app/templates"],
                    ["Thư viện", "/app/library"],
                    ["Affiliate", "/app/affiliate"],
                    ["Báo cáo", "/app/reports"],
                    ["API", "/app/api"],
                    ...(me.data?.is_admin ? ([["Admin", "/app/admin"]] as [string, string][]) : []),
                  ].map(([t, h]) => (
                    <Link
                      key={h}
                      href={h}
                      onClick={() => setMobile(false)}
                      className="rounded-lg border border-white/[0.06] bg-white/[0.02] px-3 py-2 text-sm font-medium text-ink-medium hover:bg-white/[0.05] hover:text-ink-high"
                    >
                      {t}
                    </Link>
                  ))}
                </div>
              </div>
            )}
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
            {authed && (
              <button
                onClick={() => {
                  setMobile(false);
                  clearSession();
                  router.push("/");
                }}
                className="mt-2 flex w-full items-center justify-center gap-2 rounded-lg py-2 text-sm text-ink-low hover:bg-white/[0.05] hover:text-ink-medium"
              >
                <LogOut className="h-4 w-4" /> Đăng xuất
              </button>
            )}
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
          "relative overflow-hidden rounded-3xl border border-white/[0.08] bg-bg-elevated/95 backdrop-blur-2xl",
          "shadow-[0_30px_90px_-24px_rgba(0,0,0,0.85)]",
          cols === 3 ? "w-[860px]" : "w-[620px]",
        )}
      >
        {/* dải accent tím mảnh trên đỉnh — chữ ký riêng của panel Vyra */}
        <div className="h-px w-full bg-gradient-to-r from-transparent via-violet-500/70 to-transparent" />

        <div
          className={cn(
            "grid gap-x-5 gap-y-0.5 p-4",
            cols === 3 ? "grid-cols-3" : "grid-cols-2",
          )}
        >
          {groups.map((g) => (
            <div key={g.title} className="px-1">
              <div className="mb-1 flex items-center gap-2 px-2.5 py-1.5">
                <span className="h-1 w-1 rounded-full bg-violet-400" />
                <span className="text-[10.5px] font-semibold uppercase tracking-[0.16em] text-violet-300/80">
                  {g.title}
                </span>
              </div>
              <div className="flex flex-col">
                {g.items.map((f) => (
                  <FeatureRow key={f.key} f={f} />
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* footer CTA — đẩy người dùng vào hành động (nét riêng, không phải menu thuần liệt kê) */}
        <div className="flex items-center justify-between border-t border-white/[0.06] bg-white/[0.015] px-5 py-3">
          <span className="text-xs text-ink-low">Tải 1 ảnh sản phẩm — ra video trong ~60 giây.</span>
          <Link
            href="/app/create"
            className="inline-flex items-center gap-1 text-xs font-semibold text-violet-300 transition hover:text-violet-200"
          >
            Tạo video ngay <ChevronDown className="h-3.5 w-3.5 -rotate-90" />
          </Link>
        </div>
      </div>
    </div>
  );
}

function FeatureRow({ f, onNav }: { f: Feature; onNav?: () => void }) {
  const inner = (
    <div
      className={cn(
        "group relative flex items-start gap-3 rounded-xl p-2.5 transition-all duration-200",
        f.available
          ? "hover:translate-x-0.5 hover:bg-violet-500/[0.07]"
          : "cursor-default opacity-55",
      )}
    >
      {/* thanh accent trái trượt vào khi hover (available) */}
      {f.available && (
        <span className="absolute left-0 top-1/2 h-0 w-[3px] -translate-y-1/2 rounded-full bg-violet-400 transition-all duration-200 group-hover:h-7" />
      )}
      <span
        className={cn(
          "mt-0.5 grid h-9 w-9 shrink-0 place-items-center rounded-xl transition-colors",
          f.available
            ? "bg-violet-500/[0.12] text-violet-300 group-hover:bg-violet-500/20"
            : "bg-white/[0.04] text-ink-low",
        )}
      >
        <f.icon className="h-[18px] w-[18px]" />
      </span>
      <div className="min-w-0 py-0.5">
        <div className="flex items-center gap-1.5">
          <span className="text-sm font-medium text-ink-high">{f.label}</span>
          {f.badge && (
            <span
              className={cn(
                "rounded px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wide",
                f.badge === "Sắp có"
                  ? "bg-white/[0.06] text-ink-low"
                  : "bg-violet-500/20 text-violet-200",
              )}
            >
              {f.badge}
            </span>
          )}
        </div>
        <div className="mt-0.5 text-xs leading-snug text-ink-low">{f.desc}</div>
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
