"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api/endpoints";
import { Menu, X, LogOut, Plus } from "lucide-react";
import { Logo } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
import { CreditBadge } from "@/components/shell/credit-badge";
import { NotifBell } from "@/components/shell/notif-bell";
import { LocaleSwitcher } from "@/components/shell/locale-switcher";
import { clearSession } from "@/lib/auth/session";
import { DEV_TOKEN_KEY, AUTH_COOKIE } from "@/lib/config";
import {
  CONTENT_GROUPS, MODELS_GROUPS, FEATURES_GROUPS, RESOURCES_GROUPS, type FeatureGroup,
} from "@/lib/features";
import { MegaPanel } from "./header/mega-panel";
import { NavLink, Trigger } from "./header/nav-primitives";
import { MobileMenu } from "./header/mobile-menu";
import { useHoverMenu, type MenuKey } from "./header/use-hover-menu";

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

  // IA kiểu openart — MỖI menu là 1 mega-panel (spotlight + bento), thả XUỐNG DƯỚI đúng trigger.
  const MENUS: { k: MenuKey; label: string; groups: FeatureGroup[]; cols: number }[] = [
    { k: "tools", label: t("aiTools"), groups: CONTENT_GROUPS, cols: 3 },
    { k: "models", label: t("aiModels"), groups: MODELS_GROUPS, cols: 3 },
    { k: "features", label: t("features"), groups: FEATURES_GROUPS, cols: 3 },
    { k: "resources", label: t("resources"), groups: RESOURCES_GROUPS, cols: 2 },
  ];

  return (
    <header className="fixed inset-x-0 top-0 z-50">
      {/* dải accent tím mảnh trên đỉnh — chữ ký header full-width (kiểu openart) */}
      <div className="h-0.5 w-full bg-gradient-to-r from-violet-500/0 via-violet-500/70 to-indigo-500/0" />
      <div className="flex items-center gap-6 border-b border-white/[0.07] bg-bg-base/80 px-5 py-3 backdrop-blur-xl lg:gap-10 lg:px-10">
        {/* Logo LUÔN về trang chủ marketing (/). Vào workspace qua menu "Bảng điều khiển". */}
        <Link href="/" className="shrink-0 rounded-lg outline-none focus-visible:ring-2 focus-visible:ring-violet-400/60">
          <Logo />
        </Link>

        {/* desktop nav — mỗi mục: trigger + mega-panel thả NGAY DƯỚI nó (anchor left-0 per-trigger) */}
        <nav
          className="hidden flex-1 items-center gap-1.5 lg:flex"
          onMouseLeave={scheduleClose}
          onMouseEnter={cancelClose}
        >
          {/* Lối vào workspace cho người đã đăng nhập (logo giờ về home, cần menu này) */}
          {isAuthed && <NavLink href="/app" onEnter={() => openMenu(null)}>{t("dashboard")}</NavLink>}
          {MENUS.map((m) => (
            <div key={m.k} className="relative" onMouseEnter={() => openMenu(m.k)}>
              <Trigger label={m.label} active={open === m.k} onEnter={() => openMenu(m.k)} />
              {open === m.k && (
                <div className="absolute left-0 top-full z-50 pt-3">
                  <MegaPanel kind={m.k} groups={m.groups} cols={m.cols} />
                </div>
              )}
            </div>
          ))}
          <NavLink href="/pricing" onEnter={() => openMenu(null)}>{t("pricing")}</NavLink>
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
              {/* Avatar → trang cá nhân (monogram từ email, dữ liệu thật) */}
              <Link
                href="/app/profile"
                aria-label={t("profile")}
                className="hidden h-9 w-9 place-items-center rounded-full bg-gradient-to-br from-violet-500 to-indigo-500 text-sm font-bold text-white outline-none ring-1 ring-white/10 transition hover:ring-violet-400/50 focus-visible:ring-2 focus-visible:ring-violet-400/60 sm:grid"
              >
                {(me.data?.email?.trim()[0] || "V").toUpperCase()}
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
