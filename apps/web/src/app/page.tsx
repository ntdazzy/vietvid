import Link from "next/link";
import { UserSquare2, Clapperboard, Mic, ShieldCheck } from "lucide-react";
import { Logo } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
import { GlassCard } from "@/components/ui/glass-card";
import { LandingHero } from "@/components/marketing/landing-hero";
import { SiteHeader } from "@/components/marketing/site-header";

const FEATURES = [
  {
    icon: UserSquare2,
    title: "KOL AI",
    desc: "Tạo gương mặt đại diện ảo, làm review · lookbook · trend mà không cần quay.",
  },
  {
    icon: Clapperboard,
    title: "Video bán hàng",
    desc: "1 ảnh sản phẩm thành video chốt đơn 60 giây, đủ tỉ lệ dọc/vuông.",
  },
  {
    icon: Mic,
    title: "Giọng Việt thật",
    desc: "Lồng tiếng tự nhiên, nghe thử từng giọng trước khi tạo.",
  },
  {
    icon: ShieldCheck,
    title: "Minh bạch giá",
    desc: "Thấy trước số credit, chỉ trừ khi dùng, hoàn 100% nếu lỗi hệ thống.",
  },
];

const STEPS = [
  { title: "Đưa 1 ảnh", desc: "Ảnh sản phẩm hoặc gương mặt KOL. Ảnh đầu làm khung video." },
  { title: "Chọn phong cách & giọng", desc: "Engine, thời lượng, giọng Việt. Thấy giá credit ngay." },
  { title: "Nhận video 60 giây", desc: "Xem tiến trình từng bước, tải MP4 không watermark." },
];

export default function LandingPage() {
  return (
    <div className="relative min-h-dvh mesh-bg">
      <SiteHeader />

      <LandingHero />

      {/* tools / features (autovis: Công cụ) */}
      <section id="features" className="mx-auto max-w-6xl px-4 py-20">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-[clamp(1.75rem,4vw,2.75rem)] font-bold tracking-tight text-ink-high">
            Một nền tảng, <span className="text-gradient">đủ công cụ</span> để bán hàng bằng video
          </h2>
        </div>
        <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {FEATURES.map((f) => (
            <GlassCard key={f.title} className="p-6">
              <div className="grid h-11 w-11 place-items-center rounded-xl bg-grad-brand-soft">
                <f.icon className="h-5 w-5 text-violet-300" />
              </div>
              <h3 className="mt-4 font-semibold text-ink-high">{f.title}</h3>
              <p className="mt-1.5 text-sm text-ink-low">{f.desc}</p>
            </GlassCard>
          ))}
        </div>
      </section>

      {/* how it works */}
      <section id="how" className="mx-auto max-w-6xl px-4 py-20">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-[clamp(1.75rem,4vw,2.75rem)] font-bold tracking-tight text-ink-high">
            Không cần thiết bị, <span className="text-gradient">không cần ekip</span>
          </h2>
          <p className="mt-3 text-ink-medium">Ba bước, có video trong 60 giây.</p>
        </div>
        <ol className="mt-14 grid gap-10 md:grid-cols-3 md:gap-6">
          {STEPS.map((s, i) => (
            <li key={s.title} className="relative">
              {i < STEPS.length - 1 && (
                <span className="absolute left-14 top-6 hidden h-px w-[calc(100%-2.5rem)] bg-gradient-to-r from-violet-500/40 to-transparent md:block" />
              )}
              <div className="flex items-start gap-4 md:flex-col">
                <span className="font-display grid h-12 w-12 shrink-0 place-items-center rounded-2xl border border-violet-500/30 bg-violet-500/[0.08] text-lg font-bold text-violet-200">
                  0{i + 1}
                </span>
                <div className="md:mt-5">
                  <h3 className="font-display text-lg font-semibold text-ink-high">{s.title}</h3>
                  <p className="mt-1.5 max-w-xs text-sm text-ink-low">{s.desc}</p>
                </div>
              </div>
            </li>
          ))}
        </ol>
      </section>

      {/* transparency — wedge VietVid */}
      <section className="mx-auto max-w-6xl px-4 py-20">
        <div className="glass-bordered relative overflow-hidden p-8 lg:p-12">
          <div className="glow-radial pointer-events-none absolute inset-x-0 -top-24 h-48" />
          <div className="relative grid items-center gap-8 lg:grid-cols-2">
            <div>
              <h2 className="text-[clamp(1.5rem,3.5vw,2.25rem)] font-bold leading-tight text-ink-high">
                Bạn luôn biết tốn bao nhiêu, <span className="text-gradient">trước</span> khi tiêu credit.
              </h2>
              <p className="mt-4 text-ink-medium">
                Khác với nỗi lo "tự trừ tiền": VietVid ước tính trước, chỉ tạm giữ, dùng bao nhiêu
                tính bấy nhiêu, và hoàn 100% nếu lỗi hệ thống.
              </p>
              <Link href="/login" className="mt-6 inline-block">
                <Button>Dùng thử miễn phí</Button>
              </Link>
            </div>
            <div className="flex flex-col gap-3">
              {[
                ["Ước tính trước", "Thấy ~bao nhiêu credit trước khi tạo."],
                ["Chỉ giữ tạm", "Giữ tối đa, dùng bao nhiêu tính bấy nhiêu."],
                ["Hoàn khi lỗi", "Lỗi hệ thống thì hoàn 100%, không trừ oan."],
              ].map(([t, d]) => (
                <div key={t} className="glass flex items-start gap-3 rounded-xl p-4">
                  <span className="mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-lg bg-violet-500/15 text-xs font-bold text-violet-300">
                    ✓
                  </span>
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

      {/* CTA */}
      <section className="mx-auto max-w-3xl px-4 py-24 text-center">
        <h2 className="text-[clamp(2rem,5vw,3.25rem)] font-extrabold tracking-[-0.02em] text-ink-high">
          Biến ý tưởng thành <span className="text-gradient">đơn hàng</span>.
        </h2>
        <p className="mx-auto mt-4 max-w-md text-ink-medium">
          Tặng 300 credit. Giọng Việt thật. Không watermark ở gói trả phí.
        </p>
        <div className="mt-8 flex justify-center">
          <Link href="/login">
            <Button size="lg">Tạo video ngay</Button>
          </Link>
        </div>
      </section>

      <footer className="border-t border-white/[0.06] px-4 py-8">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 text-sm text-ink-low sm:flex-row">
          <Logo />
          <p className="text-ink-disabled">© 2026 VietVid · Video AI giọng Việt</p>
        </div>
      </footer>
    </div>
  );
}
