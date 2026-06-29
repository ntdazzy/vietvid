"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import Link from "next/link";
import {
  User,
  Mic,
  KeyRound,
  LogOut,
  Lock,
  Users,
  Loader2,
  BadgeCheck,
  ArrowRight,
  ShieldCheck,
  Palette,
  type LucideIcon,
} from "lucide-react";
import { useMe } from "@/lib/query/hooks";
import { api } from "@/lib/api/endpoints";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ChipGroup, Field, inputCls } from "@/components/ui/field";
import { FilmLabel } from "@/components/ui/cinematic";
import { Reveal } from "@/components/marketing/reveal";
import { ACCENTS, type Accent } from "@/lib/accents";
import { clearSession } from "@/lib/auth/session";
import { cn } from "@/lib/utils/cn";

const VOICE_KEY = "vietvid_default_voice";

// Mỗi nhóm cài đặt 1 accent riêng → viền màu phân biệt, không 5 card giống hệt.
type Group = { id: string; label: string; icon: LucideIcon; accent: Accent };
const GROUPS: Group[] = [
  { id: "account", label: "account", icon: User, accent: "slate" },
  { id: "profile", label: "profile", icon: BadgeCheck, accent: "violet" },
  { id: "security", label: "security", icon: ShieldCheck, accent: "rose" },
  { id: "studio", label: "studio", icon: Mic, accent: "sky" },
  { id: "workspace", label: "workspace", icon: Users, accent: "emerald" },
  { id: "developer", label: "developer", icon: KeyRound, accent: "cyan" },
];

export default function SettingsPage() {
  const t = useTranslations("settings");
  const me = useMe();
  const router = useRouter();
  const isLocal = me.data?.auth_mode === "dev";

  const [voice, setVoice] = useState<"female" | "male">("female");
  const [name, setName] = useState("");
  const [savingName, setSavingName] = useState(false);
  const [nameMsg, setNameMsg] = useState("");

  const [curPw, setCurPw] = useState("");
  const [newPw, setNewPw] = useState("");
  const [pwBusy, setPwBusy] = useState(false);
  const [pwMsg, setPwMsg] = useState<{ kind: "ok" | "err"; text: string } | null>(null);

  useEffect(() => {
    const v = localStorage.getItem(VOICE_KEY);
    if (v === "male" || v === "female") setVoice(v);
  }, []);

  function pickVoice(v: "female" | "male") {
    setVoice(v);
    localStorage.setItem(VOICE_KEY, v);
  }

  async function saveName(e: React.FormEvent) {
    e.preventDefault();
    setSavingName(true);
    setNameMsg("");
    try {
      await api.updateProfile({ full_name: name.trim() });
      setNameMsg(t("profile.saved"));
    } finally {
      setSavingName(false);
    }
  }

  async function changePw(e: React.FormEvent) {
    e.preventDefault();
    setPwBusy(true);
    setPwMsg(null);
    try {
      await api.changePassword(curPw, newPw);
      setPwMsg({ kind: "ok", text: t("security.changeOk") });
      setCurPw("");
      setNewPw("");
    } catch (err) {
      setPwMsg({ kind: "err", text: err instanceof Error ? err.message : t("security.changeErr") });
    } finally {
      setPwBusy(false);
    }
  }

  // chữ cái đầu cho avatar monogram (email là dữ liệu thật duy nhất luôn có).
  const monogram = (me.data?.email?.[0] ?? "V").toUpperCase();
  // các nhóm thực sự hiển thị (đổi mật khẩu chỉ cho local-auth) → rail khớp nội dung.
  const visibleGroups = GROUPS.filter((g) => g.id !== "security" || isLocal);

  return (
    <div className="mx-auto w-full max-w-5xl">
      {/* —— Bảng đầu màn: console nhận diện, KHÔNG dùng ScreenHero để có bố cục riêng —— */}
      <Reveal>
        <header className="relative overflow-hidden rounded-3xl glass-bordered p-6 sm:p-8">
          <div
            className="pointer-events-none absolute -right-16 -top-20 h-56 w-56 rounded-full blur-3xl"
            style={{ background: ACCENTS.slate.glow }}
          />
          <div className="relative flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-4">
              <span
                aria-hidden
                className={cn(
                  "grid h-16 w-16 shrink-0 place-items-center rounded-2xl bg-gradient-to-br font-display text-2xl font-bold text-ink-high ring-1",
                  ACCENTS.violet.tile,
                  ACCENTS.violet.ring,
                )}
              >
                {monogram}
              </span>
              <div className="min-w-0">
                <FilmLabel>{t("header.eyebrow")}</FilmLabel>
                <h1 className="mt-2 font-display text-3xl font-extrabold leading-tight text-ink-high sm:text-4xl">
                  {t("header.title")}
                </h1>
                <p className="mt-1 truncate text-sm text-ink-low">
                  {me.isLoading ? t("header.loading") : me.data?.email || t("header.devAccount")}
                </p>
              </div>
            </div>
            <Button
              variant="glass"
              className="gap-2 self-start sm:self-auto"
              onClick={() => {
                clearSession();
                router.push("/");
              }}
            >
              <LogOut className="h-4 w-4" /> {t("header.logout")}
            </Button>
          </div>
        </header>
      </Reveal>

      {/* —— Thân: rail danh mục dọc (sticky) + cột nội dung từng nhóm có viền màu —— */}
      <div className="mt-6 grid gap-6 lg:grid-cols-[210px_1fr]">
        {/* Rail điều hướng — chỉ desktop; mobile bỏ qua, cuộn thẳng */}
        <nav aria-label={t("nav.aria")} className="hidden lg:block">
          <ul className="sticky top-24 flex flex-col gap-1">
            {visibleGroups.map((g) => {
              const a = ACCENTS[g.accent];
              return (
                <li key={g.id}>
                  <a
                    href={`#${g.id}`}
                    className="group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-ink-low transition-colors hover:bg-white/[0.04] hover:text-ink-high focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/40"
                  >
                    <span className={cn("h-5 w-[3px] rounded-full bg-gradient-to-b", a.grad)} />
                    <g.icon className={cn("h-4 w-4 shrink-0", a.icon)} />
                    {t(`groups.${g.label}`)}
                  </a>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Cột nội dung */}
        <div className="flex min-w-0 flex-col gap-5">
          {/* TÀI KHOẢN — bento nhận diện, không phải hàng dl phẳng */}
          <Section group={GROUPS[0]} desc={t("account.desc")}>
            {me.isLoading || !me.data ? (
              <div className="grid gap-3 sm:grid-cols-2">
                <Skeleton className="h-20 w-full" />
                <Skeleton className="h-20 w-full" />
              </div>
            ) : (
              <div className="grid gap-3 sm:grid-cols-2">
                <Fact label={t("account.email")} accent="slate">
                  <span className="truncate text-ink-high">{me.data.email || "(dev)"}</span>
                </Fact>
                <Fact label={t("account.role")} accent="slate">
                  <Badge tone="brand">{me.data.role}</Badge>
                </Fact>
                <Fact label={t("account.workspace")} accent="slate">
                  <span className="truncate font-mono text-xs text-ink-medium">{me.data.org_id}</span>
                </Fact>
                <Fact label={t("account.authMode")} accent="slate">
                  <span className="text-ink-medium">{me.data.auth_mode}</span>
                </Fact>
              </div>
            )}
          </Section>

          {/* HỒ SƠ */}
          <Section group={GROUPS[1]} desc={t("profile.desc")}>
            <form onSubmit={saveName} className="flex flex-col gap-3 sm:flex-row sm:items-end">
              <div className="flex-1">
                <Field label={t("profile.displayName")}>
                  <input
                    className={inputCls}
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder={t("profile.displayNamePlaceholder")}
                  />
                </Field>
              </div>
              <Button type="submit" disabled={savingName}>
                {savingName ? <Loader2 className="h-4 w-4 animate-spin" /> : t("profile.save")}
              </Button>
            </form>
            {nameMsg && <p className="mt-2 text-sm text-success">{nameMsg}</p>}
          </Section>

          {/* BẢO MẬT — chỉ local-auth */}
          {isLocal && (
            <Section group={GROUPS[2]} desc={t("security.desc")}>
              <form onSubmit={changePw} className="flex flex-col gap-3">
                <div className="grid gap-3 sm:grid-cols-2">
                  <Field label={t("security.currentPassword")}>
                    <input
                      type="password"
                      required
                      className={inputCls}
                      value={curPw}
                      onChange={(e) => setCurPw(e.target.value)}
                    />
                  </Field>
                  <Field label={t("security.newPassword")}>
                    <input
                      type="password"
                      required
                      minLength={6}
                      className={inputCls}
                      value={newPw}
                      onChange={(e) => setNewPw(e.target.value)}
                      placeholder={t("security.newPasswordPlaceholder")}
                    />
                  </Field>
                </div>
                {pwMsg && (
                  <p className={`text-sm ${pwMsg.kind === "ok" ? "text-success" : "text-danger"}`}>
                    {pwMsg.text}
                  </p>
                )}
                <Button type="submit" disabled={pwBusy} className="self-start">
                  {pwBusy ? <Loader2 className="h-4 w-4 animate-spin" /> : t("security.submit")}
                </Button>
              </form>
            </Section>
          )}

          {/* STUDIO — giọng mặc định */}
          <Section group={GROUPS[3]} desc={t("studio.desc")}>
            <div className="flex items-center gap-2 text-sm text-ink-medium">
              <Mic className="h-4 w-4 text-sky-300" /> {t("studio.defaultVoice")}
            </div>
            <div className="mt-3">
              <ChipGroup
                value={voice}
                onChange={(v) => pickVoice(v as "female" | "male")}
                options={[
                  { value: "female", label: t("studio.female") },
                  { value: "male", label: t("studio.male") },
                ]}
              />
            </div>
          </Section>

          {/* WORKSPACE — thành viên + brand kits, dạng hàng-liên-kết */}
          <Section group={GROUPS[4]} desc={t("workspace.desc")}>
            <div className="flex flex-col divide-y divide-white/[0.06]">
              <LinkRow
                href="/app/team"
                icon={Users}
                title={t("workspace.membersTitle")}
                desc={t("workspace.membersDesc")}
              />
              <LinkRow
                href="/app/brand-kits"
                icon={Palette}
                title={t("workspace.brandTitle")}
                desc={t("workspace.brandDesc")}
              />
            </div>
          </Section>

          {/* LẬP TRÌNH — API keys */}
          <Section group={GROUPS[5]} desc={t("developer.desc")}>
            <LinkRow
              href="/app/api"
              icon={KeyRound}
              title={t("developer.apiTitle")}
              desc={t("developer.apiDesc")}
              bare
            />
          </Section>
        </div>
      </div>
    </div>
  );
}

/** Khối một nhóm cài đặt: viền-trái accent + tiêu đề có icon + mô tả ngắn. */
function Section({
  group,
  desc,
  children,
}: {
  group: Group;
  desc: string;
  children: React.ReactNode;
}) {
  const t = useTranslations("settings");
  const a = ACCENTS[group.accent];
  return (
    <Reveal>
      <section
        id={group.id}
        className="relative scroll-mt-24 overflow-hidden rounded-2xl glass-bordered p-5 sm:p-6"
      >
        {/* viền-trái màu — dấu hiệu phân nhóm */}
        <span className={cn("absolute inset-y-0 left-0 w-[3px] bg-gradient-to-b", a.grad)} aria-hidden />
        <div className="mb-4 flex items-start gap-3 pl-1">
          <span
            className={cn(
              "grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-gradient-to-br ring-1",
              a.tile,
              a.ring,
            )}
          >
            <group.icon className={cn("h-4.5 w-4.5", a.icon)} aria-hidden />
          </span>
          <div className="min-w-0">
            <h2 className="font-display text-base font-semibold text-ink-high">{t(`groups.${group.label}`)}</h2>
            <p className="mt-0.5 text-sm text-ink-low">{desc}</p>
          </div>
        </div>
        <div className="pl-1">{children}</div>
      </section>
    </Reveal>
  );
}

/** Ô fact trong bento tài khoản — nhãn nhỏ trên, giá trị dưới, viền nhạt. */
function Fact({
  label,
  accent,
  children,
}: {
  label: string;
  accent: Accent;
  children: React.ReactNode;
}) {
  const a = ACCENTS[accent];
  return (
    <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-3.5">
      <div className={cn("text-[11px] font-semibold uppercase tracking-wider", a.text)}>{label}</div>
      <div className="mt-1.5 flex min-w-0 items-center text-sm">{children}</div>
    </div>
  );
}

/** Hàng dẫn tới trang khác — icon + tiêu đề/mô tả + mũi tên, hover lift nhẹ. */
function LinkRow({
  href,
  icon: Icon,
  title,
  desc,
  bare = false,
}: {
  href: string;
  icon: LucideIcon;
  title: string;
  desc: string;
  bare?: boolean;
}) {
  return (
    <Link
      href={href}
      className={cn(
        "group flex items-center gap-3.5 rounded-xl px-2 py-3 transition-colors hover:bg-white/[0.03] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/40",
        bare ? "px-3" : "first:pt-0 last:pb-0",
      )}
    >
      <span className="grid h-10 w-10 shrink-0 place-items-center rounded-lg border border-white/[0.07] bg-white/[0.02] text-ink-medium">
        <Icon className="h-4.5 w-4.5" aria-hidden />
      </span>
      <div className="min-w-0">
        <div className="font-medium text-ink-high">{title}</div>
        <p className="truncate text-sm text-ink-low">{desc}</p>
      </div>
      <ArrowRight className="ml-auto h-4 w-4 shrink-0 text-ink-low transition-transform group-hover:translate-x-0.5 group-hover:text-ink-medium" />
    </Link>
  );
}
