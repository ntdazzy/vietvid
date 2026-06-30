import Link from "next/link";
import { getTranslations } from "next-intl/server";
import { Logo } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
import { FilmLabel } from "@/components/ui/cinematic";
import { Reveal } from "@/components/marketing/reveal";
import { SiteHeader } from "@/components/marketing/site-header";
import { LandingHero } from "@/components/marketing/landing-hero";
import { SectionHeading } from "@/components/marketing/section-heading";
import { SampleMarquee } from "@/components/marketing/sample-marquee";
import { CapabilityGrid } from "@/components/marketing/capability-grid";
import { CinematicAct } from "@/components/marketing/cinematic-act";
import { BeforeAfter } from "@/components/marketing/before-after";
import { MiniReel } from "@/components/marketing/mini-reel";
import { VariantLeaderboard } from "@/components/marketing/winner-loop";
import { LoopStrip } from "@/components/marketing/loop-strip";
import { VoiceRail } from "@/components/marketing/voice-rail";
import { ScriptEngineMock } from "@/components/marketing/script-engine-mock";
import { RatioBento } from "@/components/marketing/ratio-bento";
import { LogoTickerBand } from "@/components/marketing/logo-ticker-band";
import { HowItWorks } from "@/components/marketing/how-it-works";
import { CompareTable } from "@/components/marketing/compare-table";
import { UseCases } from "@/components/marketing/use-cases";
import { FeaturedKol } from "@/components/marketing/featured-kol";
import { ProofStrip } from "@/components/marketing/proof-strip";
import { Manifesto } from "@/components/marketing/manifesto";
import { Faq } from "@/components/marketing/faq";
import { Intro } from "@/components/marketing/intro";

export default async function LandingPage() {
  const t = await getTranslations("home");

  const SAMPLES = [
    { file: "fashion", label: t("sampleFashion") },
    { file: "beauty", label: t("sampleBeauty") },
    { file: "tech", label: t("sampleTech") },
    { file: "home", label: t("sampleHome") },
    { file: "food", label: t("sampleFood") },
  ];

  // Cuộn thể loại dùng ẢNH THẬT /showcase (candid) — "mục lục reel" của trang chủ.
  // Bố cục bất đối xứng: 1 ô lớn + bento ô nhỏ, không hàng-thẻ-đối-xứng.
  const REEL = [
    { img: "/showcase/kol.jpg", title: t("reelKolTitle"), note: t("reelKolNote"), href: "/app/kol", big: true },
    { img: "/showcase/lookbook.jpg", title: t("reelLookbookTitle"), note: t("reelLookbookNote"), href: "/login" },
    { img: "/showcase/food.jpg", title: t("reelFoodTitle"), note: t("reelFoodNote"), href: "/login" },
    { img: "/showcase/product.jpg", title: t("reelProductTitle"), note: t("reelProductNote"), href: "/login" },
    { img: "/showcase/trend.jpg", title: t("reelTrendTitle"), note: t("reelTrendNote"), href: "/login" },
    { img: "/showcase/explainer.jpg", title: t("reelExplainerTitle"), note: t("reelExplainerNote"), href: "/login" },
  ];

  return (
    <div className="relative min-h-dvh mesh-bg">
      <Intro />
      <SiteHeader />

      {/* S0 — HERO */}
      <LandingHero />

      {/* S1 — CUỘN THỂ LOẠI (ảnh thật /showcase) — signature "mục lục reel" của trang chủ */}
      <section className="mx-auto max-w-[1600px] px-4 py-20 lg:py-24">
        <Reveal>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div className="max-w-xl">
              <FilmLabel>{t("s1Label")}</FilmLabel>
              <h2 className="mt-3 font-display text-[clamp(1.75rem,4vw,2.6rem)] font-bold leading-[1.08] tracking-tight text-ink-high">
                {t.rich("s1Title", { grad: (c) => <span className="text-gradient">{c}</span> })}
              </h2>
            </div>
            <p className="max-w-xs text-sm text-ink-low sm:text-right">
              {t("s1Sub")}
            </p>
          </div>
        </Reveal>

        {/* bento bất đối xứng: ô đầu chiếm 2 cột × 2 hàng, còn lại xếp quanh */}
        <div className="mt-9 grid auto-rows-[150px] grid-cols-2 gap-3 sm:auto-rows-[170px] lg:grid-cols-4 lg:gap-4">
          {REEL.map((r, i) => (
            <Reveal
              key={r.title}
              delay={0.05 * i}
              className={r.big ? "col-span-2 row-span-2" : ""}
            >
              <Link
                href={r.href}
                className="group relative block h-full overflow-hidden rounded-2xl glass-bordered transition-all duration-200 hover:-translate-y-1 hover:ring-1 hover:ring-violet-400/30"
              >
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={r.img}
                  alt=""
                  loading="lazy"
                  className="absolute inset-0 h-full w-full object-cover opacity-70 transition-transform duration-500 group-hover:scale-[1.05] group-hover:opacity-90"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-bg-base via-bg-base/40 to-transparent" />
                <div className="absolute inset-x-0 bottom-0 p-4">
                  <div className={r.big ? "font-display text-xl font-bold text-ink-high" : "font-display text-sm font-semibold text-ink-high"}>
                    {r.title}
                  </div>
                  <div className="mt-0.5 text-xs text-ink-low">{r.note}</div>
                </div>
                <span className="absolute right-3 top-3 h-[3px] w-5 rounded-full bg-grad-brand opacity-0 transition-opacity group-hover:opacity-100" />
              </Link>
            </Reveal>
          ))}
        </div>
      </section>

      {/* S1b — MARQUEE 2 chiều: mẫu output thật 9:16 */}
      <section className="py-12 lg:py-16">
        <div className="mx-auto max-w-[1600px] px-4">
          <FilmLabel>{t("s1bLabel")}</FilmLabel>
        </div>
        <div className="mt-7 flex flex-col gap-4">
          <SampleMarquee tiles={SAMPLES} direction="left" />
          <SampleMarquee tiles={[...SAMPLES].reverse()} direction="right" />
        </div>
        <p className="mt-5 text-center text-xs text-ink-low">{t("s1bHint")}</p>
      </section>

      {/* §5 — FEATURED KOL */}
      <FeaturedKol />

      {/* S1.5 — LOẠI NỘI DUNG (đa dạng chủ đề, không chỉ quảng cáo SP) */}
      <UseCases />

      {/* S2 — LƯỚI 6 NĂNG LỰC 01–06 (demo sống) */}
      <section id="nang-luc" className="mx-auto max-w-[1600px] px-4 py-24 lg:py-28">
        <SectionHeading
          align="center"
          eyebrow={t("s2Eyebrow")}
          title={t.rich("s2Title", { grad: (c) => <span className="text-gradient italic">{c}</span> })}
          sub={t("s2Sub")}
        />
        <div className="mt-12">
          <CapabilityGrid />
        </div>
      </section>

      {/* S3 — ACT · Photo → Video (01) */}
      <CinematicAct
        index={1}
        side="right"
        badge={{ tone: "core", label: t("act1Badge") }}
        eyebrow={t("act1Eyebrow")}
        title={t.rich("act1Title", { grad: (c) => <span className="text-gradient">{c}</span> })}
        bullets={[
          t("act1Bullet1"),
          t("act1Bullet2"),
          t("act1Bullet3"),
        ]}
        cta={{ label: t("act1Cta"), href: "/login" }}
        demo={
          <div className="grid grid-cols-2 gap-4">
            <BeforeAfter />
            <MiniReel
              poster="/samples/tech.jpg"
              className="w-full"
              captions={[t("act1Caption1"), t("act1Caption2"), t("act1Caption3")]}
            />
          </div>
        }
      />

      {/* S4 — ACT-LỚN · MOAT (climax) — id winner-loop · đóng khung CHƯƠNG RIÊNG */}
      <section id="winner-loop" className="relative bg-bg-base">
        <div className="mx-auto h-px max-w-4xl bg-gradient-to-r from-transparent via-violet-500/60 to-transparent" />
        <div className="glow-radial pointer-events-none absolute inset-x-0 -top-10 mx-auto h-64 max-w-3xl" />
        <CinematicAct
          index={2}
          side="center"
          badge={{ tone: "moat", label: t("act2Badge") }}
          eyebrow={t("act2Eyebrow")}
          title={t.rich("act2Title", { grad: (c) => <span className="text-gradient">{c}</span> })}
          sub={t("act2Sub")}
          demo={
            <div>
              <VariantLeaderboard />
              <LoopStrip />
            </div>
          }
        />
        <div className="mx-auto h-px max-w-4xl bg-gradient-to-r from-transparent via-violet-500/60 to-transparent" />
      </section>

      {/* §10 — PROOF STRIP (số THẬT, nhịp nghỉ sau climax) */}
      <ProofStrip />

      {/* S5 — ACT · Kịch bản 6 góc (04) */}
      <CinematicAct
        index={4}
        side="left"
        badge={{ tone: "new", label: t("act4Badge") }}
        eyebrow={t("act4Eyebrow")}
        title={t.rich("act4Title", { grad: (c) => <span className="text-gradient">{c}</span> })}
        sub={t("act4Sub")}
        demo={<ScriptEngineMock />}
      />

      {/* S6 — ACT · 7 giọng Việt (03) */}
      <CinematicAct
        index={3}
        side="right"
        badge={{ tone: "hot", label: t("act3Badge") }}
        eyebrow={t("act3Eyebrow")}
        title={t.rich("act3Title", { grad: (c) => <span className="text-gradient">{c}</span> })}
        sub={t("act3Sub")}
        demo={<VoiceRail />}
      />

      {/* S7 — TICKER tích hợp */}
      <div className="py-6">
        <LogoTickerBand />
      </div>

      {/* S8 — ACT · Đa tỉ lệ (05) */}
      <CinematicAct
        index={5}
        side="right"
        badge={{ tone: "new", label: t("act5Badge") }}
        eyebrow={t("act5Eyebrow")}
        title={t.rich("act5Title", { grad: (c) => <span className="text-gradient">{c}</span> })}
        sub={t("act5Sub")}
        demo={<RatioBento />}
      />

      {/* §15 — MANIFESTO */}
      <Manifesto />

      {/* S9 — Cách Vyra hoạt động */}
      <section className="py-24 lg:py-28">
        <HowItWorks />
      </section>

      {/* S10 — So sánh */}
      <section className="py-20 lg:py-24">
        <CompareTable />
      </section>

      {/* S11 — Minh bạch credit — khối "bảng ví" bất đối xứng, ảnh nền /bg/desk */}
      <section className="mx-auto max-w-[1600px] px-4 py-12">
        <Reveal>
          <div className="glass-bordered relative overflow-hidden p-8 lg:p-12">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="/bg/desk.jpg"
              alt=""
              className="pointer-events-none absolute inset-0 h-full w-full object-cover opacity-[0.12]"
            />
            <div className="absolute inset-0 bg-gradient-to-r from-bg-base via-bg-base/90 to-bg-base/55" />
            <div className="relative grid items-center gap-8 lg:grid-cols-12">
              <div className="lg:col-span-5">
                <FilmLabel>{t("creditLabel")}</FilmLabel>
                <h2 className="mt-3 font-display text-[clamp(1.5rem,3.5vw,2.25rem)] font-bold leading-tight text-ink-high">
                  {t.rich("creditTitle", { grad: (c) => <span className="text-gradient">{c}</span> })}
                </h2>
                <p className="mt-4 text-ink-medium">
                  {t("creditBody")}
                </p>
                <Link href="/login" className="mt-6 inline-block">
                  <Button>{t("creditCta")}</Button>
                </Link>
              </div>
              <div className="flex flex-col gap-3 lg:col-span-7">
                {[
                  [t("creditItem1Title"), t("creditItem1Desc")],
                  [t("creditItem2Title"), t("creditItem2Desc")],
                  [t("creditItem3Title"), t("creditItem3Desc")],
                ].map(([title, d]) => (
                  <div key={title} className="glass flex items-start gap-3 rounded-xl p-4">
                    <span className="mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-lg bg-violet-500/15 text-xs font-bold text-violet-300">✓</span>
                    <div>
                      <div className="font-medium text-ink-high">{title}</div>
                      <div className="text-sm text-ink-low">{d}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Reveal>
      </section>

      {/* §FAQ */}
      <Faq />

      {/* S11b — CTA đóng trang */}
      <section className="relative overflow-hidden px-4 py-28 text-center">
        <div className="glow-radial pointer-events-none absolute inset-x-0 -top-10 mx-auto h-64 max-w-2xl" />
        <span className="pointer-events-none absolute inset-x-0 top-1/2 -z-10 -translate-y-1/2 select-none text-center font-display text-[clamp(5rem,22vw,18rem)] font-extrabold leading-none text-white/[0.03]">
          VYRA
        </span>
        <div className="relative mx-auto max-w-3xl">
          <div className="mx-auto mb-8 h-px max-w-xs bg-gradient-to-r from-transparent via-violet-500/70 to-transparent" />
          <h2 className="font-display text-[clamp(2rem,5vw,3.4rem)] font-extrabold tracking-[-0.02em] text-ink-high">
            {t.rich("ctaTitle", { grad: (c) => <span className="text-gradient">{c}</span> })}
          </h2>
          <p className="mx-auto mt-4 max-w-md text-ink-medium">
            {t("ctaSub")}
          </p>
          <div className="mt-8 flex justify-center">
            <Link href="/login">
              <Button size="lg">{t("ctaButton")}</Button>
            </Link>
          </div>
          <p className="mt-3 text-xs text-ink-low">{t("ctaHint")}</p>
        </div>
      </section>

      <footer className="border-t border-white/[0.06] px-4 py-8">
        <div className="mx-auto flex max-w-[1600px] flex-col items-center gap-4 sm:flex-row sm:justify-between">
          <Logo />
          <nav className="flex flex-wrap items-center justify-center gap-x-5 gap-y-2 text-sm text-ink-low">
            <Link href="/pricing" className="hover:text-ink-medium">{t("footerPricing")}</Link>
            <Link href="/terms" className="hover:text-ink-medium">{t("footerTerms")}</Link>
            <Link href="/privacy" className="hover:text-ink-medium">{t("footerPrivacy")}</Link>
          </nav>
          <p className="text-xs text-ink-disabled">{t("footerCopyright")}</p>
        </div>
      </footer>
    </div>
  );
}
