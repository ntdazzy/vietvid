import Link from "next/link";
import { Logo } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
import { SiteHeader } from "@/components/marketing/site-header";
import { LandingHero } from "@/components/marketing/landing-hero";
import { SectionHeading } from "@/components/marketing/section-heading";
import { SampleMarquee } from "@/components/marketing/sample-marquee";
import { BeforeAfter } from "@/components/marketing/before-after";
import { VariantLeaderboard } from "@/components/marketing/winner-loop";
import { VoiceRail } from "@/components/marketing/voice-rail";
import { ScriptEngineMock } from "@/components/marketing/script-engine-mock";
import { RatioBento } from "@/components/marketing/ratio-bento";
import { IntegrationBand } from "@/components/marketing/integration-band";
import { Reveal } from "@/components/marketing/reveal";
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

      {/* S1 — MARQUEE mẫu output thật */}
      <section className="py-20 lg:py-28">
        <div className="mx-auto max-w-6xl px-4">
          <h2 className="font-display text-sm font-semibold uppercase tracking-[0.18em] text-ink-low">
            Mẫu thật từ engine · 9:16
          </h2>
        </div>
        <div className="mt-8">
          <SampleMarquee tiles={SAMPLES} />
        </div>
      </section>

      {/* S2 — BEFORE → AFTER */}
      <section className="mx-auto max-w-6xl px-4 py-24 lg:py-32">
        <div className="grid items-center gap-10 lg:grid-cols-12">
          <Reveal className="flex justify-center lg:col-span-5 lg:justify-start">
            <BeforeAfter />
          </Reveal>
          <div className="lg:col-span-7">
            <SectionHeading
              title={<>Ảnh sản phẩm nằm im. <span className="text-gradient">Vyra cho nó nói tiếng Việt.</span></>}
            />
            <ul className="mt-6 flex flex-col gap-3">
              {[
                "Chọn 1 trong 7 giọng Việt thật",
                "Phụ đề khớp từng khung — timing lấy từ kịch bản, không đoán bằng ASR",
                "Xuất đủ 3 tỉ lệ: dọc 9:16 · vuông 1:1 · ngang 16:9",
              ].map((t) => (
                <li key={t} className="flex items-start gap-3 text-ink-medium">
                  <span className="mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-lg bg-violet-500/15 text-xs font-bold text-violet-300">✓</span>
                  {t}
                </li>
              ))}
            </ul>
            <Link href="/login" className="mt-6 inline-block">
              <Button variant="glass">Thử với ảnh của bạn</Button>
            </Link>
          </div>
        </div>
      </section>

      {/* S3 — THE WINNER LOOP (MOAT) */}
      <section id="winner-loop" className="relative py-24 lg:py-32">
        <div className="glow-radial pointer-events-none absolute inset-x-0 -top-10 mx-auto h-56 max-w-3xl" />
        <div className="relative mx-auto max-w-6xl px-4">
          <SectionHeading
            align="center"
            eyebrow="Chỉ Vyra có"
            title={<>Đối thủ tạo video. <span className="text-gradient">Vyra tìm ra video ra đơn.</span></>}
            sub="Tạo nhiều biến thể từ một sản phẩm → mỗi bản một short-link riêng → đo click thật → xếp hạng → nhân bản bản thắng."
          />
          <Reveal className="mt-10">
            <VariantLeaderboard />
          </Reveal>
        </div>
      </section>

      {/* S4 — 7 GIỌNG VIỆT */}
      <section className="py-24 lg:py-32">
        <div className="mx-auto max-w-6xl px-4">
          <SectionHeading
            title={<><span className="text-gradient">7 giọng Việt</span> có cá tính. Mỗi giọng một tính cách.</>}
            sub="Trẻ trung, nhẹ nhàng, trầm ấm, dí dỏm… chọn giọng hợp ngành hàng, nghe thử ngay trong app."
          />
          <div className="mt-10">
            <VoiceRail />
          </div>
        </div>
      </section>

      {/* S5 — BỘ MÁY KỊCH BẢN */}
      <section className="mx-auto max-w-6xl px-4 py-24 lg:py-32">
        <div className="grid items-center gap-10 lg:grid-cols-12">
          <div className="lg:col-span-5">
            <SectionHeading
              title={<>Nhập sản phẩm. <span className="text-gradient">Nhận kịch bản theo timecode.</span> Sửa được từng câu.</>}
              sub="Chọn 1 trong 6 góc thuyết phục. Engine trả về hook + từng beat theo timecode — sửa tay trước khi dựng. Phụ đề lấy timing thẳng từ kịch bản."
            />
          </div>
          <Reveal delay={0.1} className="lg:col-span-7">
            <ScriptEngineMock />
          </Reveal>
        </div>
      </section>

      {/* S6 — ĐA TỈ LỆ */}
      <section className="mx-auto max-w-6xl px-4 py-24 lg:py-32">
        <SectionHeading title={<>Một lần dựng. <span className="text-gradient">Dọc, vuông, ngang.</span></>} />
        <div className="mt-10">
          <RatioBento />
        </div>
      </section>

      {/* S7 — MINH BẠCH CREDIT */}
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

      {/* S8 — DÁN LINK + API */}
      <section className="mx-auto max-w-6xl px-4 py-24 lg:py-32">
        <IntegrationBand />
      </section>

      {/* S9 — CTA cuối */}
      <section className="mx-auto max-w-3xl px-4 py-24 text-center">
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
      </section>

      <footer className="border-t border-white/[0.06] px-4 py-8">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 text-sm text-ink-low sm:flex-row">
          <Logo />
          <p className="text-ink-disabled">© 2026 Vyra · Video AI giọng Việt</p>
        </div>
      </footer>
    </div>
  );
}
