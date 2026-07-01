"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { Wallet, Clock, Film, CreditCard, Settings, FolderKanban, LogOut, ShieldCheck, Mail, Sparkles } from "lucide-react";
import { useMe, useWallet, useJobs } from "@/lib/query/hooks";
import { CreditValue } from "@/components/ui/credit-value";
import { FilmLabel } from "@/components/ui/cinematic";
import { Button } from "@/components/ui/button";
import { clearSession } from "@/lib/auth/session";
import { isTerminal } from "@/lib/job-status";
import { cn } from "@/lib/utils/cn";

// TRANG CÁ NHÂN (/app/profile) — hub cá nhân: danh tính + số dư + thống kê thật + lối tắt.
// Dữ liệu THẬT (me/wallet/jobs). Email là định danh luôn có → monogram từ email.

const ROLE_KEY: Record<string, string> = { owner: "roleOwner", admin: "roleAdmin", member: "roleMember", editor: "roleEditor" };

export default function ProfilePage() {
  const t = useTranslations("profile");
  const router = useRouter();
  const me = useMe();
  const wallet = useWallet();
  const jobs = useJobs(60);

  const email = me.data?.email ?? "";
  const initial = (email.trim()[0] || "V").toUpperCase();
  const role = me.data?.role ?? "";
  const roleLabel = ROLE_KEY[role] ? t(ROLE_KEY[role]) : role || "—";
  const balance = wallet.data?.balance_credits ?? me.data?.balance_credits ?? 0;
  const held = me.data?.held_credits ?? 0;
  const all = jobs.data?.items ?? [];
  const videoCount = all.length;
  const doneCount = all.filter((j) => j.status === "READY").length;
  const runningCount = all.filter((j) => !isTerminal(j.status)).length;

  function logout() {
    clearSession();
    router.push("/");
  }

  return (
    <div className="mx-auto w-full max-w-4xl">
      {/* ===== HERO danh tính ===== */}
      <section className="relative overflow-hidden rounded-3xl glass-bordered">
        <div className="pointer-events-none absolute -right-16 -top-16 h-56 w-56 rounded-full bg-violet-500/20 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-16 left-10 h-44 w-44 rounded-full bg-indigo-500/10 blur-3xl" />
        <div className="relative flex flex-col gap-5 p-6 sm:flex-row sm:items-center sm:gap-6 sm:p-8">
          <span className="grid h-20 w-20 shrink-0 place-items-center rounded-2xl bg-gradient-to-br from-violet-500 to-indigo-500 font-display text-3xl font-bold text-white shadow-glow-sm">
            {initial}
          </span>
          <div className="min-w-0 flex-1">
            <FilmLabel>{t("eyebrow")}</FilmLabel>
            <h1 className="mt-2 flex items-center gap-2 font-display text-2xl font-bold text-ink-high sm:text-3xl">
              <Mail className="h-5 w-5 shrink-0 text-ink-low" />
              <span className="truncate">{email || "—"}</span>
            </h1>
            <div className="mt-2 flex flex-wrap items-center gap-2">
              <span className="rounded-md bg-violet-500/10 px-2.5 py-1 text-xs font-semibold text-violet-200">{roleLabel}</span>
              {me.data?.is_admin && (
                <span className="inline-flex items-center gap-1 rounded-md bg-amber-500/10 px-2.5 py-1 text-xs font-semibold text-amber-200">
                  <ShieldCheck className="h-3.5 w-3.5" /> {t("adminBadge")}
                </span>
              )}
            </div>
          </div>
          <Link href="/app/create" className="shrink-0">
            <Button className="gap-1.5 active:scale-95"><Sparkles className="h-4 w-4" /> {t("createCta")}</Button>
          </Link>
        </div>
      </section>

      {/* ===== Thống kê THẬT ===== */}
      <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatCard icon={Wallet} label={t("statCredits")} value={<CreditValue value={balance} className="text-2xl" />} accent="text-violet-300" />
        <StatCard icon={Clock} label={t("statHeld")} value={<CreditValue value={held} className="text-2xl" />} accent="text-hold" />
        <StatCard icon={Film} label={t("statVideos")} value={<span className="font-numeric">{videoCount}</span>} accent="text-ink-high" />
        <StatCard icon={Sparkles} label={t("statDone")} value={<span className="font-numeric">{doneCount}</span>} accent="text-success" sub={runningCount > 0 ? t("running", { n: runningCount }) : undefined} />
      </div>

      {/* ===== Lối tắt ===== */}
      <div className="mt-6">
        <div className="mb-3 flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-ink-medium">
          <FolderKanban className="h-4 w-4 text-violet-300" /> {t("quickTitle")}
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          <QuickLink href="/app/billing" icon={CreditCard} title={t("topup")} desc={t("topupDesc")} />
          <QuickLink href="/app/library" icon={Film} title={t("library")} desc={t("libraryDesc")} />
          <QuickLink href="/app/settings" icon={Settings} title={t("settings")} desc={t("settingsDesc")} />
          <QuickLink href="/app/director" icon={FolderKanban} title={t("projects")} desc={t("projectsDesc")} />
        </div>
      </div>

      {/* ===== Đăng xuất ===== */}
      <div className="mt-6 flex justify-center">
        <button
          onClick={logout}
          className="inline-flex items-center gap-2 rounded-xl border border-white/10 px-5 py-2.5 text-sm font-medium text-ink-low transition hover:border-danger/40 hover:bg-danger/[0.06] hover:text-danger"
        >
          <LogOut className="h-4 w-4" /> {t("logout")}
        </button>
      </div>
    </div>
  );
}

function StatCard({ icon: Icon, label, value, accent, sub }: { icon: typeof Wallet; label: string; value: React.ReactNode; accent: string; sub?: string }) {
  return (
    <div className="rounded-2xl glass-bordered p-4">
      <Icon className={cn("h-5 w-5", accent)} />
      <div className={cn("mt-3 text-2xl font-bold leading-none", accent)}>{value}</div>
      <div className="mt-1.5 text-[11px] uppercase tracking-[0.14em] text-ink-low">{label}</div>
      {sub && <div className="mt-0.5 text-[11px] text-violet-300/80">{sub}</div>}
    </div>
  );
}

function QuickLink({ href, icon: Icon, title, desc }: { href: string; icon: typeof Wallet; title: string; desc: string }) {
  return (
    <Link
      href={href}
      className="group flex items-center gap-3 rounded-2xl glass-bordered p-4 transition-all hover:-translate-y-0.5 hover:ring-1 hover:ring-violet-400/30"
    >
      <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-violet-500/10 text-violet-200 transition-colors group-hover:bg-violet-500/20">
        <Icon className="h-5 w-5" />
      </span>
      <div className="min-w-0">
        <div className="text-sm font-semibold text-ink-high">{title}</div>
        <div className="truncate text-[11px] text-ink-low">{desc}</div>
      </div>
    </Link>
  );
}
