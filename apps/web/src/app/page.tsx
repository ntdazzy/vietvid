import Link from "next/link";
import { getTranslations } from "next-intl/server";
import { Logo } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
import { FilmLabel } from "@/components/ui/cinematic";
import { Reveal } from "@/components/marketing/reveal";
import { SiteHeader } from "@/components/marketing/site-header";
import { ScrollToTop } from "@/components/marketing/scroll-to-top";
import { LandingHero } from "@/components/marketing/landing-hero";
import { SectionHeading } from "@/components/marketing/section-heading";
import { LibrarySection } from "@/components/marketing/video-library";
import { Solutions } from "@/components/marketing/solutions";
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
import { ModelWall } from "@/components/marketing/model-wall";
import { SocialProof } from "@/components/marketing/social-proof";
import { PricingBand } from "@/components/marketing/pricing-band";

export default async function LandingPage() {
  const t = await getTranslations("home");

  return (
    <div className="relative min-h-dvh mesh-bg">
      <Intro />
      <SiteHeader />
      <ScrollToTop />

      {/* S0 — HERO */}
      <LandingHero />

      {/* S0b — TƯỜNG MODEL (moat tổng hợp) */}
      <ModelWall />

      {/* S1 — THƯ VIỆN VYRA (tường video thật, tile động) — gộp REEL + Marquee + GenreWall + ProductReel */}
      <LibrarySection />

      {/* S1c — GIẢI PHÁP (đau người bán → Vyra lo) — đối ứng 'solutions' autovis, mạnh hơn */}
      <Solutions />

      {/* §5b — SOCIAL PROOF (KOL/TikTok + đu trend Douyin) */}
      <SocialProof />

      {/* §5 — FEATURED KOL (9 gương mặt) */}
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
              poster="/samples/gen/review.jpg"
              video="/samples/gen/review.mp4"
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

      {/* §16 — BẢNG GIÁ trên trang chủ (seller thấy giá VND trước khi rời) */}
      <PricingBand />

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

      <footer className="border-t border-white/[0.06] px-4 py-10">
        <div className="mx-auto max-w-[1600px]">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
            <div className="max-w-xs">
              <Logo />
              <p className="mt-3 text-sm text-ink-low">
                Studio AI tạo mọi nội dung — ảnh, video, KOL, giọng Việt. Một nơi, nhiều model.
              </p>
            </div>
            <nav className="flex flex-wrap gap-x-6 gap-y-2 text-sm text-ink-low">
              <Link href="/pricing" className="hover:text-ink-medium">{t("footerPricing")}</Link>
              <a href="#nang-luc" className="hover:text-ink-medium">Tính năng</a>
              <Link href="/terms" className="hover:text-ink-medium">{t("footerTerms")}</Link>
              <Link href="/privacy" className="hover:text-ink-medium">{t("footerPrivacy")}</Link>
            </nav>
            {/* phương thức thanh toán — trust cho seller Việt */}
            <div className="flex flex-col gap-2.5">
              <span className="text-[11px] font-semibold uppercase tracking-[0.18em] text-ink-low">Thanh toán</span>
              <div className="flex flex-wrap gap-2">
                <span className="rounded-md bg-[#a50064]/15 px-2.5 py-1 text-xs font-semibold text-[#ff4db8]">MoMo</span>
                <span className="rounded-md bg-[#0d5cb6]/15 px-2.5 py-1 text-xs font-semibold text-[#4d9bff]">VNPay</span>
                <span className="rounded-md bg-white/[0.06] px-2.5 py-1 text-xs font-semibold text-ink-medium">Chuyển khoản QR</span>
              </div>
            </div>
          </div>
          <div className="mt-8 flex flex-col items-center gap-2 border-t border-white/[0.05] pt-6 sm:flex-row sm:justify-between">
            <p className="text-xs text-ink-disabled">{t("footerCopyright")}</p>
            <p className="text-xs text-ink-disabled">Bảo mật TLS · hoàn 100% nếu lỗi hệ thống</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
