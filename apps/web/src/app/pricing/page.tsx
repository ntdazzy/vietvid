"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { Check, Sparkles, ArrowRight } from "lucide-react";
import { Logo } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { SiteHeader } from "@/components/marketing/site-header";
import { FilmLabel } from "@/components/ui/cinematic";
import { Reveal } from "@/components/marketing/reveal";
import { PricingTrustBand } from "@/components/marketing/pricing-trust-band";
import { RoiCalculator } from "@/components/marketing/roi-calculator";
import { ACCENTS } from "@/lib/accents";
import { cn } from "@/lib/utils/cn";

const a = ACCENTS.emerald;

type Pack = {
  name: string;
  credits: number;
  price: string;
  note: string;
  featured: boolean;
  cta: string;
  feats: string[];
};

export default function PricingPage() {
  const t = useTranslations("pricing");

  const PACKS: Pack[] = [
    {
      name: t("packTrialName"),
      credits: 300,
      price: t("packTrialPrice"),
      note: t("packTrialNote"),
      featured: false,
      cta: t("packTrialCta"),
      feats: [t("packTrialFeat1"), t("packTrialFeat2"), t("packTrialFeat3"), t("packTrialFeat4")],
    },
    {
      name: t("packBasicName"),
      credits: 2000,
      price: "300.000đ",
      note: t("packBasicNote"),
      featured: true,
      cta: t("packBasicCta"),
      feats: [t("packBasicFeat1"), t("packBasicFeat2"), t("packBasicFeat3"), t("packBasicFeat4"), t("packBasicFeat5")],
    },
    {
      name: t("packProName"),
      credits: 7000,
      price: "900.000đ",
      note: t("packProNote"),
      featured: false,
      cta: t("packProCta"),
      feats: [t("packProFeat1"), t("packProFeat2"), t("packProFeat3"), t("packProFeat4")],
    },
  ];

  // Bán "nhiều thể loại" — ảnh candid showcase, KHÔNG số bịa, chỉ liệt kê thứ làm được.
  const GENRES = [
    { image: "/showcase/affiliate.jpg", title: t("genreAffiliate") },
    { image: "/showcase/kol.jpg", title: t("genreKol") },
    { image: "/showcase/trend.jpg", title: t("genreTrend") },
    { image: "/showcase/lookbook.jpg", title: t("genreLookbook") },
    { image: "/showcase/food.jpg", title: t("genreFood") },
    { image: "/showcase/explainer.jpg", title: t("genreExplainer") },
  ];

  return (
    <div className="min-h-dvh mesh-bg">
      <SiteHeader />

      <div className="mx-auto grid max-w-6xl gap-10 px-4 pt-28 pb-16 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)] lg:gap-12 lg:pt-32">
        {/* ── RAIL TRÁI — pitch giá trị, dính (signature: bảng giá kiểu split) ── */}
        <aside className="lg:sticky lg:top-28 lg:self-start">
          <Reveal>
            <div className="relative overflow-hidden rounded-3xl glass-bordered p-7 sm:p-8">
              {/* ảnh candid mờ làm chất nền, KHÔNG ken-burns ồn ào */}
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src="/bg/desk.jpg"
                alt=""
                className="pointer-events-none absolute inset-0 h-full w-full object-cover opacity-[0.14]"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-bg-surface via-bg-surface/85 to-bg-surface/40" />
              <div
                className="pointer-events-none absolute -top-16 -right-10 h-48 w-48 rounded-full blur-3xl"
                style={{ background: a.glow }}
              />

              <div className="relative">
                <FilmLabel>{t("filmLabel")}</FilmLabel>
                <h1 className="mt-4 font-display text-[clamp(1.9rem,4vw,2.75rem)] font-extrabold leading-[1.08] tracking-[-0.02em] text-ink-high">
                  {t("heroTitleLine1")}<br />
                  <span className={a.text}>{t("heroTitleLine2")}</span>
                </h1>
                <p className="mt-4 max-w-sm leading-relaxed text-ink-medium">
                  {t("heroSubtitle")}
                </p>

                {/* công thức giá — số bằng font numeric, chữ Việt thì không */}
                <div className="mt-7 flex items-baseline gap-2 rounded-2xl border border-emerald-400/20 bg-emerald-500/[0.06] px-4 py-3">
                  <span className="font-numeric text-2xl font-bold text-ink-high">1</span>
                  <span className="text-sm text-ink-medium">{t("creditUnit")}</span>
                  <span className="px-1 text-ink-low">=</span>
                  <span className="font-numeric text-2xl font-bold text-emerald-300">150</span>
                  <span className="text-sm text-ink-medium">{t("currencyUnit")}</span>
                </div>

                <ul className="mt-5 flex flex-col gap-2.5 text-sm text-ink-medium">
                  <li className="flex items-start gap-2.5">
                    <Check className="mt-0.5 h-4 w-4 shrink-0 text-emerald-400" />
                    {t("benefitPreview")}
                  </li>
                  <li className="flex items-start gap-2.5">
                    <Check className="mt-0.5 h-4 w-4 shrink-0 text-emerald-400" />
                    {t("benefitRefund")}
                  </li>
                  <li className="flex items-start gap-2.5">
                    <Check className="mt-0.5 h-4 w-4 shrink-0 text-emerald-400" />
                    {t("benefitNoExpiry")}
                  </li>
                </ul>
              </div>
            </div>
          </Reveal>

          {/* dải thể loại — bằng chứng "đủ mọi thể loại", ảnh candid */}
          <Reveal delay={0.08}>
            <div className="mt-5 rounded-3xl glass p-5">
              <div className="mb-3 text-[11px] font-semibold uppercase tracking-[0.2em] text-ink-low">
                {t("genresEyebrow")}
              </div>
              <div className="grid grid-cols-3 gap-2.5">
                {GENRES.map((g) => (
                  <div
                    key={g.title}
                    className="group relative overflow-hidden rounded-xl ring-1 ring-white/[0.06]"
                  >
                    <div className="aspect-square">
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src={g.image}
                        alt=""
                        loading="lazy"
                        className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-[1.07]"
                      />
                    </div>
                    <div className="absolute inset-0 bg-gradient-to-t from-bg-base/90 via-bg-base/20 to-transparent" />
                    <span className="absolute inset-x-1.5 bottom-1.5 text-[10px] font-medium leading-tight text-ink-high">
                      {g.title}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </Reveal>
        </aside>

        {/* ── CỘT PHẢI — chồng gói bất đối xứng, gói đề xuất nổi bằng MÀU ── */}
        <div className="flex flex-col gap-5">
          {PACKS.map((p, i) => (
            <Reveal key={p.name} delay={0.06 * i}>
              <PackRow pack={p} creditLabel={t("creditUnit")} featuredLabel={t("featuredBadge")} />
            </Reveal>
          ))}

          <p className="mt-1 text-sm text-ink-disabled">
            {t("paymentNote")}
          </p>
        </div>
      </div>

      {/* 3 con hào "hét to" — thanh toán bản địa · render lỗi không trừ tiền · xu không hết hạn */}
      <PricingTrustBand />

      {/* máy tính ROI — làm video bằng Vyra rẻ hơn thuê người bao nhiêu */}
      <RoiCalculator />

      {/* dẫn về FAQ trên trang chủ */}
      <section className="mx-auto max-w-3xl px-4 pb-24 text-center">
        <div className="mx-auto mb-6 h-px max-w-xs bg-gradient-to-r from-transparent via-emerald-500/60 to-transparent" />
        <h2 className="font-display text-2xl font-bold text-ink-high">{t("faqHeading")}</h2>
        <p className="mt-2 text-ink-medium">{t("faqSubtitle")}</p>
        <div className="mt-6 flex flex-wrap justify-center gap-3">
          <Link href="/#faq"><Button variant="glass">{t("faqCta")}</Button></Link>
          <Link href="/login"><Button>{t("faqCreateCta")}</Button></Link>
        </div>
      </section>

      <footer className="border-t border-white/[0.06] px-4 py-8">
        <div className="mx-auto flex max-w-6xl flex-col items-center gap-4 sm:flex-row sm:justify-between">
          <Logo />
          <nav className="flex flex-wrap items-center justify-center gap-x-5 gap-y-2 text-sm text-ink-low">
            <Link href="/" className="hover:text-ink-medium">{t("footerHome")}</Link>
            <Link href="/terms" className="hover:text-ink-medium">{t("footerTerms")}</Link>
            <Link href="/privacy" className="hover:text-ink-medium">{t("footerPrivacy")}</Link>
          </nav>
          <p className="text-xs text-ink-disabled">{t("footerTagline")}</p>
        </div>
      </footer>
    </div>
  );
}

// Một gói = một hàng ngang (số credit lớn bên trái, tính năng bên phải). Gói đề xuất
// đổi MÀU sang emerald (viền + glow + chip), không chỉ to/cao hơn.
function PackRow({
  pack: p,
  creditLabel,
  featuredLabel,
}: {
  pack: Pack;
  creditLabel: string;
  featuredLabel: string;
}) {
  return (
    <div
      className={cn(
        "group relative overflow-hidden rounded-2xl p-6 transition-all duration-200 sm:p-7",
        p.featured
          ? "ring-1 ring-emerald-400/40 bg-emerald-500/[0.06] shadow-[0_0_40px_-12px_rgba(16,185,129,0.5)]"
          : "glass-bordered hover:-translate-y-0.5 hover:ring-1 hover:ring-white/15",
      )}
    >
      {p.featured && (
        <div
          className="pointer-events-none absolute -top-20 right-0 h-44 w-44 rounded-full blur-3xl"
          style={{ background: a.glow }}
        />
      )}

      <div className="relative flex flex-col gap-6 sm:flex-row sm:items-start sm:gap-7">
        {/* khối giá — bên trái */}
        <div className="sm:w-44 sm:shrink-0">
          <div className="flex items-center gap-2">
            <h3 className="font-display text-lg font-semibold text-ink-high">{p.name}</h3>
            {p.featured && (
              <Badge tone="success" className="gap-1">
                <Sparkles className="h-3 w-3" /> {featuredLabel}
              </Badge>
            )}
          </div>
          <div className="mt-3 flex items-baseline gap-1.5">
            <span
              className={cn(
                "font-numeric text-4xl font-bold tabular-nums",
                p.featured ? "text-emerald-300" : "text-ink-high",
              )}
            >
              {p.credits.toLocaleString("vi-VN")}
            </span>
            <span className="text-sm text-ink-low">{creditLabel}</span>
          </div>
          <div className="mt-1.5 text-ink-medium">{p.price}</div>
          <div className="text-sm text-ink-low">{p.note}</div>

          <Link href="/login" className="mt-5 block">
            <Button
              variant={p.featured ? "primary" : "glass"}
              className={cn("w-full gap-1.5", p.featured && "!bg-grad-brand")}
            >
              {p.cta}
              <ArrowRight className="h-4 w-4 transition group-hover:translate-x-0.5" />
            </Button>
          </Link>
        </div>

        {/* tính năng — bên phải, ngăn cách bằng divider dọc trên desktop */}
        <ul className="grid flex-1 gap-2.5 border-t border-white/[0.06] pt-5 sm:grid-cols-2 sm:border-l sm:border-t-0 sm:pl-7 sm:pt-0">
          {p.feats.map((f) => (
            <li key={f} className="flex items-start gap-2.5 text-sm text-ink-medium">
              <Check
                className={cn(
                  "mt-0.5 h-4 w-4 shrink-0",
                  p.featured ? "text-emerald-400" : "text-success",
                )}
              />
              {f}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
