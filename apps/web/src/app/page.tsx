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
import { SampleMarquee } from "@/components/marketing/sample-marquee";
import { CapabilityGrid } from "@/components/marketing/capability-grid";
import { CinematicAct } from "@/components/marketing/cinematic-act";
import { BeforeAfter } from "@/components/marketing/before-after";
import { MiniReel } from "@/components/marketing/mini-reel";
import { HoverVideo } from "@/components/ui/hover-video";
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
import { GenreWall } from "@/components/marketing/genre-wall";
import { ProductReel } from "@/components/marketing/product-reel";
import { ProofStrip } from "@/components/marketing/proof-strip";
import { Manifesto } from "@/components/marketing/manifesto";
import { Faq } from "@/components/marketing/faq";
import { Intro } from "@/components/marketing/intro";
import { ModelWall } from "@/components/marketing/model-wall";
import { SocialProof } from "@/components/marketing/social-proof";
import { PricingBand } from "@/components/marketing/pricing-band";

export default async function LandingPage() {
  const t = await getTranslations("home");

  // 9 THỂ LOẠI nội dung KHÁC nhau (đều clip thật 9:16 từ showcase) → marquee không lặp lại 1 nhóm
  // ảnh, mỗi tile 1 kiểu video web dựng được: KOL, đu trend, beauty, người dẫn, nhân vật AI,
  // mở hộp, ảnh SP, ẩm thực, nghệ thuật. Poster = frame của chính clip → rê chuột khớp 100%.
  const SAMPLES = [
    { file: "showcase/kol-hero", label: t("sampleKol") },
    { file: "showcase/trend-dance", label: t("sampleDouyin") },
    { file: "showcase/gaixinh", label: t("sampleBeauty") },
    { file: "showcase/presenter", label: t("samplePresenter") },
    { file: "showcase/character", label: t("sampleCharacter") },
    { file: "showcase/unbox-prod", label: t("sampleUnbox") },
    { file: "showcase/apple", label: t("sampleProduct") },
    { file: "showcase/food", label: t("sampleFood") },
    { file: "showcase/art", label: t("sampleArt") },
  ];

  // Bento NGANG-DỌC trộn (lưới 6 cột): MẶT người → ô DỌC 9:16 (ảnh 3:4 chỉ crop 2 bên, KHÔNG
  // mất đầu); sản phẩm/cảnh → ô NGANG 2:1 + video 16:9; vật thể → ô vuông. `obj` = object-position
  // (top giữ đầu/mặt khi crop). Card người dùng ẢNH THẬT kol/*.jpg (video người bị Seedance kiểm
  // duyệt nên để tĩnh); card sản phẩm/vật chạy video khớp tỉ lệ ô khi rê chuột.
  // Xếp thành 2 băng 6×2 ô để grid-flow-dense lấp KÍN 4 hàng (không hở đáy):
  // Băng A (hàng 1-2): lớn(2×2) + dọc + dọc + ngang(2×1) + vuông + vuông.
  // Băng B (hàng 3-4): dọc + dọc + ngang + ngang + vuông×4.
  // MỌI card đều video đúng chủ đề (Seedance): người = t2v (KOL/gái xinh/nhảy trend/presenter),
  // sản phẩm = Apple/unbox/quảng cáo. Poster = 1 frame trích từ chính clip → hover khớp 100%.
  const REEL = [
    { cls: "col-span-2 row-span-2", obj: "object-center", img: "/showcase/kol-hero.jpg", video: "/showcase/kol-hero.mp4", title: t("reelKolTitle"), note: t("reelKolNote"), href: "/app/kol" },
    { cls: "row-span-2", obj: "object-center", img: "/showcase/trend-dance.jpg", video: "/showcase/trend-dance.mp4", title: t("reelTrendTitle"), note: t("reelTrendNote"), href: "/login" },
    { cls: "row-span-2", obj: "object-center", img: "/showcase/gaixinh.jpg", video: "/showcase/gaixinh.mp4", title: t("reelKol2Title"), note: t("reelKol2Note"), href: "/app/kol" },
    { cls: "col-span-2", obj: "object-center", img: "/showcase/product.jpg", video: "/showcase/product-w.mp4", title: t("reelAdTitle"), note: t("reelAdNote"), href: "/login" },
    { cls: "", obj: "object-top", img: "/showcase/character.jpg", video: "/showcase/character.mp4", title: t("reelCharacterTitle"), note: t("reelCharacterNote"), href: "/app/character" },
    { cls: "", obj: "object-center", img: "/showcase/art.jpg", video: "/showcase/art.mp4", title: t("reelArtTitle"), note: t("reelArtNote"), href: "/app/image-gen" },
    { cls: "row-span-2", obj: "object-center", img: "/showcase/presenter.jpg", video: "/showcase/presenter.mp4", title: t("reelExplainerTitle"), note: t("reelExplainerNote"), href: "/login" },
    { cls: "row-span-2", obj: "object-center", img: "/showcase/apple.jpg", video: "/showcase/apple.mp4", title: t("reelProductShotTitle"), note: t("reelProductShotNote"), href: "/app/image-gen" },
    { cls: "col-span-2", obj: "object-center", img: "/showcase/affiliate-w.jpg", video: "/showcase/affiliate-w.mp4", title: t("reelAffiliateTitle"), note: t("reelAffiliateNote"), href: "/login" },
    { cls: "col-span-2", obj: "object-center", img: "/showcase/lookbook-w.jpg", video: "/showcase/lookbook-w.mp4", title: t("reelLookbookTitle"), note: t("reelLookbookNote"), href: "/login" },
    { cls: "", obj: "object-center", img: "/samples/food.jpg", video: "/showcase/food.mp4", title: t("reelFoodTitle"), note: t("reelFoodNote"), href: "/login" },
    { cls: "", obj: "object-center", img: "/samples/home.jpg", video: "/showcase/recreate.mp4", title: t("reelRecreateTitle"), note: t("reelRecreateNote"), href: "/login" },
    { cls: "", obj: "object-center", img: "/showcase/unbox-prod.jpg", video: "/showcase/unbox-prod.mp4", title: t("reelProductTitle"), note: t("reelProductNote"), href: "/login" },
    { cls: "", obj: "object-center", img: "/samples/gen/review.jpg", video: "/samples/gen/review.mp4", title: t("reelReviewTitle"), note: t("reelReviewNote"), href: "/login" },
  ];

  return (
    <div className="relative min-h-dvh mesh-bg">
      <Intro />
      <SiteHeader />
      <ScrollToTop />

      {/* S0 — HERO */}
      <LandingHero />

      {/* S0b — TƯỜNG MODEL (moat tổng hợp) */}
      <ModelWall />

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

        {/* bento NGANG-DỌC trộn (6 cột): ô vuông/dọc(9:16)/ngang(2:1)/lớn xen kẽ — tỉ lệ ô khớp ảnh
            nên KHÔNG cắt đầu/sản phẩm. grid-flow-dense lấp ô trống. Card vật/SP rê chuột chạy clip. */}
        <div className="mt-9 grid auto-rows-[148px] grid-flow-dense grid-cols-2 gap-3 sm:auto-rows-[172px] sm:grid-cols-4 lg:auto-rows-[210px] lg:grid-cols-6 lg:gap-4">
          {REEL.map((r, i) => {
            const featured = r.cls.includes("row-span-2") || r.cls.includes("col-span-2");
            return (
              <Reveal key={r.title} delay={0.03 * i} className={r.cls}>
                <Link
                  href={r.href}
                  className="group relative block h-full overflow-hidden rounded-2xl glass-bordered transition-all duration-200 hover:-translate-y-1 hover:ring-1 hover:ring-violet-400/30"
                >
                  <HoverVideo
                    poster={r.img}
                    video={r.video}
                    alt=""
                    badge={false}
                    objectClass={r.obj}
                    className="absolute inset-0 h-full w-full opacity-[0.88] transition-opacity duration-500 group-hover:opacity-100"
                  />
                  <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-bg-base via-bg-base/25 to-transparent" />
                  <div className="pointer-events-none absolute inset-x-0 bottom-0 p-3.5">
                    <div className={featured ? "font-display text-base font-bold leading-tight text-ink-high" : "font-display text-sm font-semibold leading-tight text-ink-high"}>
                      {r.title}
                    </div>
                    <div className="mt-0.5 text-[11px] text-ink-low">{r.note}</div>
                  </div>
                  <span className="pointer-events-none absolute right-2.5 top-2.5 grid h-6 w-6 place-items-center rounded-full bg-black/40 opacity-0 backdrop-blur-sm transition-opacity group-hover:opacity-100">
                    <span className="ml-0.5 block h-0 w-0 border-y-[5px] border-l-[8px] border-y-transparent border-l-white/90" />
                  </span>
                </Link>
              </Reveal>
            );
          })}
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

      {/* §5b — SOCIAL PROOF (KOL/TikTok + đu trend Douyin) */}
      <SocialProof />

      {/* §5 — FEATURED KOL (9 gương mặt) */}
      <FeaturedKol />

      {/* §5c — TƯỜNG THỂ LOẠI (11 clip v2: ẩm thực/du lịch/fitness/phim ngắn...) */}
      <GenreWall />

      {/* §5d — REEL SẢN PHẨM (6 clip v2: thời trang/công nghệ/décor...) */}
      <ProductReel />

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
