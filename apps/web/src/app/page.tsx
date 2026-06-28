import Link from "next/link";
import { Logo } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
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
import { Intro } from "@/components/marketing/intro";

const SAMPLES = [
  { file: "fashion", label: "Thời trang" },
  { file: "beauty", label: "Mỹ phẩm" },
  { file: "tech", label: "Công nghệ" },
  { file: "home", label: "Gia dụng" },
  { file: "food", label: "Ẩm thực" },
];

export default function LandingPage() {
  return (
    <div className="relative min-h-dvh mesh-bg">
      <Intro />
      <SiteHeader />

      {/* S0 — HERO */}
      <LandingHero />

      {/* S1 — MARQUEE 2 chiều: mẫu output thật */}
      <section className="py-16 lg:py-20">
        <div className="mx-auto max-w-6xl px-4">
          <h2 className="font-display text-sm font-semibold uppercase tracking-[0.18em] text-ink-low">
            Mẫu output thật · chưa qua chỉnh sửa · 9:16
          </h2>
        </div>
        <div className="mt-7 flex flex-col gap-4">
          <SampleMarquee tiles={SAMPLES} direction="left" />
          <SampleMarquee tiles={[...SAMPLES].reverse()} direction="right" />
        </div>
        <p className="mt-5 text-center text-xs text-ink-low">Di chuột vào mỗi mẫu để xem clip chạy.</p>
      </section>

      {/* §5 — FEATURED KOL (mirror autovis, slot chờ ảnh thật) */}
      <FeaturedKol />

      {/* S1.5 — LOẠI NỘI DUNG (đa dạng chủ đề, không chỉ quảng cáo SP) */}
      <UseCases />

      {/* S2 — LƯỚI 6 NĂNG LỰC 01–06 (đấu autovis, demo sống) */}
      <section id="nang-luc" className="mx-auto max-w-6xl px-4 py-24 lg:py-28">
        <SectionHeading
          align="center"
          eyebrow="Bên trong studio"
          title={<>Sáu năng lực. <span className="text-gradient italic">Không cái nào đứng yên</span> để bạn xem.</>}
          sub="Mỗi ô tự chạy ngay tại đây — bấm, kéo, đổi. Không phải ảnh chụp màn hình."
        />
        <div className="mt-12">
          <CapabilityGrid />
        </div>
      </section>

      {/* S3 — ACT · Photo → Video (01) */}
      <CinematicAct
        index={1}
        side="right"
        badge={{ tone: "core", label: "Năng lực lõi" }}
        eyebrow="01 · Ảnh → Video"
        title={<>Ảnh sản phẩm nằm im. <span className="text-gradient">Vyra cho nó nói tiếng Việt.</span></>}
        bullets={[
          "Chọn 1 trong 7 giọng Việt thật",
          "Phụ đề khớp khung — timing lấy từ kịch bản, không đoán bằng ASR",
          "Xuất đủ 3 tỉ lệ: dọc 9:16 · vuông 1:1 · ngang 16:9",
        ]}
        cta={{ label: "Thử với ảnh của bạn", href: "/login" }}
        demo={
          <div className="grid grid-cols-2 gap-4">
            <BeforeAfter />
            <MiniReel
              poster="/samples/tech.png"
              className="w-full"
              captions={["Mở hộp em này nè…", "Chống ồn đỉnh thật sự!", "Bấm giỏ hàng nha!"]}
            />
          </div>
        }
      />

      {/* S4 — ACT-LỚN · MOAT (climax) — id winner-loop · đóng khung CHƯƠNG RIÊNG (autovis không có) */}
      <section id="winner-loop" className="relative bg-bg-base">
        <div className="mx-auto h-px max-w-4xl bg-gradient-to-r from-transparent via-violet-500/60 to-transparent" />
        <div className="glow-radial pointer-events-none absolute inset-x-0 -top-10 mx-auto h-64 max-w-3xl" />
        <CinematicAct
          index={2}
          side="center"
          badge={{ tone: "moat", label: "Độc quyền" }}
          eyebrow="· Không đối thủ Việt nào có"
          title={<>Đối thủ tạo video. <span className="text-gradient">Vyra tìm ra video ra đơn.</span></>}
          sub="Tạo nhiều biến thể từ một sản phẩm → mỗi bản một short-link riêng → đo click thật → xếp hạng → nhân bản bản thắng."
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
        badge={{ tone: "new", label: "Kịch bản AI" }}
        eyebrow="04 · Bộ máy kịch bản"
        title={<>Nhập sản phẩm. <span className="text-gradient">Nhận kịch bản theo timecode.</span> Sửa từng câu.</>}
        sub="Chọn 1 trong 6 góc thuyết phục. Engine trả về hook + từng beat theo timecode — sửa tay trước khi dựng. Phụ đề lấy timing thẳng từ kịch bản."
        demo={<ScriptEngineMock />}
      />

      {/* S6 — ACT · 7 giọng Việt (03) */}
      <CinematicAct
        index={3}
        side="right"
        badge={{ tone: "hot", label: "Giọng Việt" }}
        eyebrow="03 · Giọng đọc"
        title={<><span className="text-gradient">7 giọng Việt</span> có cá tính. Mỗi giọng một tính cách.</>}
        sub="Mai, Linh, Trang, Bống, Khoa, Hùng, Tú — trẻ trung, nhẹ nhàng, trầm ấm, dí dỏm. Chọn giọng hợp ngành hàng, nghe thử trong app."
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
        badge={{ tone: "new", label: "Xuất file" }}
        eyebrow="05 · Đa tỉ lệ"
        title={<>Một lần dựng. <span className="text-gradient">Dọc, vuông, ngang.</span></>}
        sub="Dọc 9:16 cho TikTok/Reels, vuông 1:1 cho feed, ngang 16:9 cho YouTube — từ cùng một lần dựng."
        demo={<RatioBento />}
      />

      {/* §15 — MANIFESTO (mirror "SẴN SÀNG·KHỞI TẠO·TỎA SÁNG" của autovis, giọng Vyra) */}
      <Manifesto />

      {/* S9 — Cách Vyra hoạt động */}
      <section className="py-24 lg:py-28">
        <HowItWorks />
      </section>

      {/* S10 — So sánh */}
      <section className="py-20 lg:py-24">
        <CompareTable />
      </section>

      {/* S11 — Minh bạch credit */}
      <section className="mx-auto max-w-6xl px-4 py-12">
        <div className="glass-bordered relative overflow-hidden p-8 lg:p-12">
          <div className="relative grid items-center gap-8 lg:grid-cols-12">
            <div className="lg:col-span-5">
              <h2 className="font-display text-[clamp(1.5rem,3.5vw,2.25rem)] font-bold leading-tight text-ink-high">
                Bạn luôn biết tốn bao nhiêu, <span className="text-gradient">trước</span> khi tiêu credit.
              </h2>
              <p className="mt-4 text-ink-medium">
                Khác nỗi lo "tự trừ tiền": Vyra ước tính trước, chỉ tạm giữ, dùng bao nhiêu tính
                bấy nhiêu, và hoàn 100% nếu lỗi hệ thống.
              </p>
              <Link href="/login" className="mt-6 inline-block">
                <Button>Dùng thử miễn phí</Button>
              </Link>
            </div>
            <div className="flex flex-col gap-3 lg:col-span-7">
              {[
                ["Ước tính trước", "Thấy ~bao nhiêu credit trước khi tạo."],
                ["Chỉ giữ tạm", "Giữ tối đa, dùng bao nhiêu tính bấy nhiêu."],
                ["Hoàn khi lỗi", "Lỗi hệ thống thì hoàn 100%, không trừ oan."],
              ].map(([t, d]) => (
                <div key={t} className="glass flex items-start gap-3 rounded-xl p-4">
                  <span className="mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-lg bg-violet-500/15 text-xs font-bold text-violet-300">✓</span>
                  <div>
                    <div className="font-medium text-ink-high">{t}</div>
                    <div className="text-sm text-ink-low">{d}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* S11b — CTA đóng phim */}
      <section className="relative overflow-hidden px-4 py-28 text-center">
        <div className="glow-radial pointer-events-none absolute inset-x-0 -top-10 mx-auto h-64 max-w-2xl" />
        <span className="pointer-events-none absolute inset-x-0 top-1/2 -z-10 -translate-y-1/2 select-none text-center font-display text-[clamp(5rem,22vw,18rem)] font-extrabold leading-none text-white/[0.03]">
          VYRA
        </span>
        <div className="relative mx-auto max-w-3xl">
          <div className="mx-auto mb-8 h-px max-w-xs bg-gradient-to-r from-transparent via-violet-500/70 to-transparent" />
          <h2 className="font-display text-[clamp(2rem,5vw,3.4rem)] font-extrabold tracking-[-0.02em] text-ink-high">
            Đừng đoán video nào ra đơn. <span className="text-gradient">Để số liệu chỉ.</span>
          </h2>
          <p className="mx-auto mt-4 max-w-md text-ink-medium">
            Tặng 300 credit, không cần thẻ. 7 giọng Việt thật. Không watermark ở gói trả phí.
          </p>
          <div className="mt-8 flex justify-center">
            <Link href="/login">
              <Button size="lg">Tạo loạt video đầu tiên</Button>
            </Link>
          </div>
          <p className="mt-3 text-xs text-ink-low">Mất ~60 giây để có video đầu tiên.</p>
        </div>
      </section>

      <footer className="border-t border-white/[0.06] px-4 py-8">
        <div className="mx-auto flex max-w-6xl flex-col items-center gap-4 sm:flex-row sm:justify-between">
          <Logo />
          <nav className="flex flex-wrap items-center justify-center gap-x-5 gap-y-2 text-sm text-ink-low">
            <Link href="/pricing" className="hover:text-ink-medium">Bảng giá</Link>
            <Link href="/terms" className="hover:text-ink-medium">Điều khoản</Link>
            <Link href="/privacy" className="hover:text-ink-medium">Bảo mật</Link>
          </nav>
          <p className="text-xs text-ink-disabled">© 2026 Vyra · Video AI giọng Việt</p>
        </div>
      </footer>
    </div>
  );
}
