"use client";

import Link from "next/link";
import {
  Sparkles, ArrowRight, Wallet, Plus, Film, Palette, AudioLines, Drama, type LucideIcon,
} from "lucide-react";
import { useTranslations } from "next-intl";
import { useMe, useJobs } from "@/lib/query/hooks";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { CreditValue } from "@/components/ui/credit-value";
import { CineHero, ContentCard } from "@/components/ui/cinematic";
import { Reveal } from "@/components/marketing/reveal";
import { ACCENTS, type Accent } from "@/lib/accents";
import { cn } from "@/lib/utils/cn";
import type { JobStatus } from "@/lib/api/types";

// CSS class theo trạng thái job — nhãn hiển thị lấy từ i18n (statusKey).
const STATUS_STYLE: Record<string, { statusKey: string; cls: string }> = {
  READY: { statusKey: "ready", cls: "bg-success/15 text-success" },
  RUNNING: { statusKey: "running", cls: "bg-violet-500/15 text-violet-200" },
  QUEUED: { statusKey: "queued", cls: "bg-hold/15 text-hold" },
  WAITING_CONFIG: { statusKey: "waitingConfig", cls: "bg-hold/15 text-hold" },
  FAILED: { statusKey: "failed", cls: "bg-danger/15 text-danger" },
  QA_FAIL: { statusKey: "qaFail", cls: "bg-danger/15 text-danger" },
  CANCELLED: { statusKey: "cancelled", cls: "bg-white/[0.06] text-ink-low" },
  REFUNDED: { statusKey: "refunded", cls: "bg-refund/15 text-refund" },
};

// Thể loại studio (có ảnh showcase) — đường dẫn tới flow thật. titleKey/descKey lấy từ i18n.
const STUDIO: { titleKey: string; descKey: string; href: string; image: string; accent: Accent; label: string; badge?: string }[] = [
  { titleKey: "studioSalesTitle", descKey: "studioSalesDesc", href: "/features/product_ad", image: "/showcase/affiliate.jpg", accent: "violet", label: "AFFILIATE", badge: "HOT" },
  { titleKey: "studioKolTitle", descKey: "studioKolDesc", href: "/app/kol", image: "/showcase/kol.jpg", accent: "rose", label: "CASTING" },
  { titleKey: "studioSeriesTitle", descKey: "studioSeriesDesc", href: "/app/create", image: "/showcase/trend.jpg", accent: "amber", label: "SERIES" },
];

// Công cụ nhanh (thẻ icon — biến thể so với thẻ ảnh, tránh đồng loạt). titleKey/descKey lấy từ i18n.
const TOOLS: { icon: LucideIcon; titleKey: string; descKey: string; href: string; accent: Accent }[] = [
  { icon: Palette, titleKey: "toolImageTitle", descKey: "toolImageDesc", href: "/app/image-gen", accent: "sky" },
  { icon: Drama, titleKey: "toolCharacterTitle", descKey: "toolCharacterDesc", href: "/app/character", accent: "violet" },
  { icon: AudioLines, titleKey: "toolAudioTitle", descKey: "toolAudioDesc", href: "/app/audio", accent: "cyan" },
  { icon: Film, titleKey: "toolLibraryTitle", descKey: "toolLibraryDesc", href: "/app/library", accent: "emerald" },
];

export default function DashboardPage() {
  const t = useTranslations("dashboard");
  const me = useMe();
  const jobs = useJobs(8);
  const name = me.data?.email?.split("@")[0] || t("defaultName");
  const balance = me.data?.balance_credits ?? null;
  const held = me.data?.held_credits ?? 0;

  return (
    <div className="flex flex-col gap-10">
      {/* HERO ĐIỆN ẢNH */}
      <CineHero
        accent="violet"
        bg="/showcase/hero-create.jpg"
        label={t("heroLabel")}
        status={balance === null ? undefined : `${balance.toLocaleString("vi-VN")} CREDIT`}
        eyebrow={t("heroEyebrow")}
        title={t.rich("heroTitle", { name, grad: (chunks) => <span className="text-gradient">{chunks}</span> })}
        sub={t("heroSub")}
        actions={
          <>
            <Link href="/app/create">
              <Button size="lg" className="gap-2"><Sparkles className="h-4 w-4" /> {t("createVideo")} <ArrowRight className="h-4 w-4" /></Button>
            </Link>
            <Link href="/app/billing">
              <Button variant="outline" size="lg" className="gap-2"><Plus className="h-4 w-4" /> {t("topUpCredit")}</Button>
            </Link>
          </>
        }
      >
        <div className="flex flex-wrap items-end gap-x-8 gap-y-3">
          <HeroStat label={t("statBalance")} value={balance === null ? null : balance.toLocaleString("vi-VN")} loading={me.isLoading} accent />
          {held > 0 && <HeroStat label={t("statHeld")} value={held.toLocaleString("vi-VN")} tone="hold" />}
          <span className="flex items-center gap-1.5 pb-1 text-sm text-ink-medium">
            <Wallet className="h-4 w-4 text-violet-300" /> {t("creditRate")}
          </span>
        </div>
      </CineHero>

      {/* STUDIO — thể loại */}
      <Reveal>
        <section className="flex flex-col gap-5">
          <SectionLabel>{t("studioSectionLabel")}</SectionLabel>
          <div className="grid gap-4 lg:grid-cols-3">
            {STUDIO.map((s) => (
              <ContentCard key={s.titleKey} title={t(s.titleKey)} desc={t(s.descKey)} href={s.href} image={s.image} accent={s.accent} label={s.label} badge={s.badge} />
            ))}
          </div>
        </section>
      </Reveal>

      {/* CÔNG CỤ NHANH */}
      <Reveal>
        <section className="flex flex-col gap-5">
          <SectionLabel>{t("toolsSectionLabel")}</SectionLabel>
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            {TOOLS.map((tool) => (
              <ToolCard key={tool.titleKey} icon={tool.icon} title={t(tool.titleKey)} desc={t(tool.descKey)} href={tool.href} accent={tool.accent} />
            ))}
          </div>
        </section>
      </Reveal>

      {/* VIDEO GẦN ĐÂY */}
      <section className="flex flex-col gap-5">
        <div className="flex items-center justify-between">
          <SectionLabel>{t("recentSectionLabel")}</SectionLabel>
          <Link href="/app/library" className="text-sm text-violet-300 transition hover:text-violet-200">{t("viewAll")} →</Link>
        </div>

        {jobs.isLoading ? (
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="aspect-[9/16] w-full rounded-xl" />
            ))}
          </div>
        ) : !jobs.data || jobs.data.items.length === 0 ? (
          <GlassCard className="flex flex-col items-center gap-3 py-16 text-center">
            <div className="grid h-14 w-14 place-items-center rounded-2xl bg-white/[0.04]">
              <Film className="h-6 w-6 text-ink-low" />
            </div>
            <p className="text-ink-low">{t("emptyState")}</p>
            <Link href="/app/create">
              <Button variant="glass" size="sm">{t("createVideo")}</Button>
            </Link>
          </GlassCard>
        ) : (
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
            {jobs.data.items.map((j) => {
              const st = STATUS_STYLE[j.status as JobStatus];
              const stLabel = st ? t(`status.${st.statusKey}`) : j.status;
              const stCls = st?.cls ?? "bg-white/[0.06] text-ink-low";
              return (
                <Link key={j.id} href="/app/library" className="group relative aspect-[9/16] overflow-hidden rounded-[18px] glass-bordered">
                  <div className="absolute inset-0 bg-grad-brand-soft opacity-40 transition-opacity group-hover:opacity-60" />
                  {/* job chưa có ảnh thật → motif phim ở giữa để thẻ đọc rõ là "video", không như tải lỗi */}
                  <div className="pointer-events-none absolute inset-0 grid place-items-center">
                    <span className="grid h-12 w-12 place-items-center rounded-full bg-white/[0.06] ring-1 ring-white/10 backdrop-blur-sm transition-transform group-hover:scale-110">
                      <Film className="h-5 w-5 text-white/40" />
                    </span>
                  </div>
                  <div className="relative flex h-full flex-col justify-between p-3">
                    <span className={cn("w-fit rounded-md px-2 py-0.5 text-[10px] font-semibold", stCls)}>{stLabel}</span>
                    <div className="text-[11px] text-ink-low">
                      <div className="truncate text-ink-medium">{j.kind === "kol_full" ? t("kindKol") : t("kindProduct")}</div>
                      <div className="mt-0.5 font-numeric">{j.seconds}s · {j.resolution} · {j.aspect}</div>
                      {j.est_credits > 0 && <CreditValue value={j.est_credits} className="mt-1 text-[11px] text-ink-medium" />}
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return <h3 className="text-sm font-semibold uppercase tracking-[0.16em] text-ink-low">{children}</h3>;
}

function HeroStat({ label, value, loading, accent, tone }: { label: string; value: string | null; loading?: boolean; accent?: boolean; tone?: "hold" }) {
  return (
    <div>
      <div className="text-xs uppercase tracking-wide text-ink-low">{label}</div>
      {loading ? (
        <Skeleton className="mt-1 h-8 w-24" />
      ) : (
        // Khách chưa đăng nhập (không có dữ liệu) → "—" thay vì skeleton chạy mãi.
        <div className={cn("font-numeric text-3xl font-bold tabular", accent ? "text-gradient" : tone === "hold" ? "text-hold" : "text-ink-high")}>{value ?? "—"}</div>
      )}
    </div>
  );
}

function ToolCard({ icon: Icon, title, desc, href, accent }: { icon: LucideIcon; title: string; desc: string; href: string; accent: Accent }) {
  const a = ACCENTS[accent];
  return (
    <Link
      href={href}
      className="group relative flex items-start gap-3 overflow-hidden rounded-2xl glass-bordered p-5 transition-all duration-200 hover:-translate-y-1 hover:shadow-glow-sm"
    >
      <span className={cn("grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-gradient-to-br ring-1", a.tile, a.ring)}>
        <Icon className={cn("h-5 w-5", a.icon)} />
      </span>
      <div className="min-w-0">
        <div className="font-display font-semibold text-ink-high">{title}</div>
        <p className="mt-0.5 text-sm leading-snug text-ink-low">{desc}</p>
      </div>
      <ArrowRight className="ml-auto h-4 w-4 shrink-0 text-ink-low opacity-0 transition group-hover:translate-x-0.5 group-hover:opacity-100" />
    </Link>
  );
}
