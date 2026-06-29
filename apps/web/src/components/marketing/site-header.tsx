"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api/endpoints";
import {
  Flame,
  Menu,
  X,
  LogOut,
  Plus,
  Library,
  LayoutTemplate,
  Link2,
  BarChart3,
  Webhook,
  ShieldCheck,
  HelpCircle,
  RefreshCcw,
  Mail,
  type LucideIcon,
} from "lucide-react";
import { Logo } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
import { CreditBadge } from "@/components/shell/credit-badge";
import { NotifBell } from "@/components/shell/notif-bell";
import { LocaleSwitcher } from "@/components/shell/locale-switcher";
import { clearSession } from "@/lib/auth/session";
import { DEV_TOKEN_KEY, AUTH_COOKIE } from "@/lib/config";
import { CONTENT_GROUPS } from "@/lib/features";
import { MegaPanel, TOOLS_GROUPS } from "./header/mega-panel";
import { IconListPanel } from "./header/icon-list-panel";
import { NavLink, Trigger } from "./header/nav-primitives";
import { MobileMenu } from "./header/mobile-menu";
import { useHoverMenu } from "./header/use-hover-menu";

export function SiteHeader({ authed = false }: { authed?: boolean }) {
  const { open, openMenu, scheduleClose, cancelClose } = useHoverMenu();
  const [mobile, setMobile] = useState(false);
  const router = useRouter();
  const t = useTranslations("nav");
  const tc = useTranslations("common");
  // Header phải nhận trạng thái đăng nhập THẬT (kể cả trên trang marketing /) — không chỉ dựa prop.
  const [signedIn, setSignedIn] = useState(false);
  useEffect(() => {
    if (typeof window === "undefined") return;
    setSignedIn(Boolean(localStorage.getItem(DEV_TOKEN_KEY)) || document.cookie.includes(`${AUTH_COOKIE}=1`));
  }, []);
  const isAuthed = authed || signedIn;
  const me = useQuery({ queryKey: ["me"], queryFn: api.me, enabled: isAuthed });

  // Mục "Quản lý" — tách icon để panel có khí chất "bảng điều khiển", không phải list trơn.
  const manageItems: { label: string; href: string; icon: LucideIcon }[] = [
    { label: "Thư viện video", href: "/app/library", icon: Library },
    { label: "Mẫu", href: "/app/templates", icon: LayoutTemplate },
    { label: "Affiliate", href: "/app/affiliate", icon: Link2 },
    { label: "Báo cáo", href: "/app/reports", icon: BarChart3 },
    { label: "API & Webhook", href: "/app/api", icon: Webhook },
    ...(me.data?.is_admin ? [{ label: "Quản trị", href: "/app/admin", icon: ShieldCheck }] : []),
  ];

  const supportItems: { label: string; href: string; icon: LucideIcon }[] = [
    { label: "Câu hỏi thường gặp", href: "/#faq", icon: HelpCircle },
    { label: "Lỗi có hoàn tiền?", href: "/#faq", icon: RefreshCcw },
    { label: "Liên hệ", href: "mailto:support@vietvid.vn", icon: Mail },
  ];

  return (
    <header className="fixed inset-x-0 top-0 z-50">
      <div className="mx-auto mt-4 flex max-w-6xl items-center justify-between rounded-2xl border border-white/[0.07] bg-bg-base/70 px-4 py-2.5 backdrop-blur-xl lg:px-5">
        <Link href={isAuthed ? "/app" : "/"} className="rounded-lg outline-none focus-visible:ring-2 focus-visible:ring-violet-400/60">
          <Logo />
        </Link>

        {/* desktop nav */}
        <nav
          className="hidden items-center gap-1 lg:flex"
          onMouseLeave={scheduleClose}
          onMouseEnter={cancelClose}
        >
          <NavLink href={isAuthed ? "/app" : "/"} onEnter={() => openMenu(null)}>
            {isAuthed ? t("dashboard") : t("home")}
          </NavLink>
          <Link
            href={isAuthed ? "/app/kol" : "/login"}
            onMouseEnter={() => openMenu(null)}
            className="flex items-center gap-1.5 whitespace-nowrap rounded-lg px-3 py-2 text-sm font-medium text-violet-200 outline-none transition-colors hover:bg-white/[0.05] focus-visible:ring-2 focus-visible:ring-violet-400/60"
          >
            KOL AI <Flame className="h-3.5 w-3.5 text-orange-400" />
          </Link>

          <Trigger label={t("content")} active={open === "content"} onEnter={() => openMenu("content")} />
          <Trigger label={t("tools")} active={open === "tools"} onEnter={() => openMenu("tools")} />
          {isAuthed ? (
            <Trigger label={t("manage")} active={open === "manage"} onEnter={() => openMenu("manage")} />
          ) : (
            <>
              <NavLink href="/app/library" onEnter={() => openMenu(null)}>{t("library")}</NavLink>
              <NavLink href="/pricing" onEnter={() => openMenu(null)}>{t("pricing")}</NavLink>
            </>
          )}
          <Trigger label={t("support")} active={open === "support"} onEnter={() => openMenu("support")} />

          {/* mega panels — bố cục spotlight-trái + bento-phải (chữ ký riêng của header Vyra) */}
          {open === "content" && <MegaPanel kind="content" groups={CONTENT_GROUPS} cols={3} />}
          {open === "tools" && <MegaPanel kind="tools" groups={TOOLS_GROUPS} cols={2} />}
          {open === "manage" && <IconListPanel title="Quản lý" items={manageItems} />}
          {open === "support" && <IconListPanel title="Hỗ trợ" items={supportItems} />}
        </nav>

        <div className="flex items-center gap-2">
          <LocaleSwitcher />
          {isAuthed ? (
            <>
              <NotifBell />
              <div className="hidden sm:block">
                <CreditBadge />
              </div>
              <Link href="/app/create" className="hidden sm:block">
                <Button size="sm" className="gap-1.5">
                  <Plus className="h-4 w-4" /> {tc("createVideo")}
                </Button>
              </Link>
              <button
                onClick={() => {
                  clearSession();
                  router.push("/");
                }}
                className="hidden h-9 w-9 place-items-center rounded-lg text-ink-low outline-none hover:bg-white/[0.05] hover:text-ink-medium focus-visible:ring-2 focus-visible:ring-violet-400/60 sm:grid"
                aria-label={tc("logout")}
              >
                <LogOut className="h-[18px] w-[18px]" />
              </button>
            </>
          ) : (
            <Link href="/login" className="hidden sm:block">
              <Button size="sm">{tc("login")}</Button>
            </Link>
          )}
          <button
            className="grid h-9 w-9 place-items-center rounded-lg text-ink-medium outline-none hover:bg-white/[0.05] focus-visible:ring-2 focus-visible:ring-violet-400/60 lg:hidden"
            onClick={() => setMobile((v) => !v)}
            aria-label={mobile ? tc("closeMenu") : tc("openMenu")}
            aria-expanded={mobile}
          >
            {mobile ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {/* mobile menu */}
      {mobile && (
        <MobileMenu
          isAuthed={isAuthed}
          isAdmin={Boolean(me.data?.is_admin)}
          onClose={() => setMobile(false)}
          onLogout={() => {
            setMobile(false);
            clearSession();
            router.push("/");
          }}
        />
      )}
    </header>
  );
}
