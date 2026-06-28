import Link from "next/link";
import { Check } from "lucide-react";
import { Logo } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
import { GlassCard } from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";
import { SiteHeader } from "@/components/marketing/site-header";

const PACKS = [
  {
    name: "Dùng thử",
    credits: 300,
    price: "Miễn phí",
    note: "Tặng khi đăng ký, không cần thẻ",
    featured: false,
    cta: "Đăng ký miễn phí",
    feats: ["300 credit đủ làm video đầu tiên", "7 giọng Việt thật", "Xuất 9:16 · 1:1 · 16:9", "Có watermark"],
  },
  {
    name: "Cơ bản",
    credits: 2000,
    price: "300.000đ",
    note: "~12 video 30 giây",
    featured: true,
    cta: "Bắt đầu",
    feats: ["Không watermark", "7 giọng Việt + bộ máy kịch bản", "Auto-series + đo click bản thắng", "Dán link sàn tự bóc", "Hỗ trợ qua email"],
  },
  {
    name: "Chuyên nghiệp",
    credits: 7000,
    price: "900.000đ",
    note: "+15% thưởng nạp",
    featured: false,
    cta: "Nâng cấp",
    feats: ["Tất cả gói Cơ bản", "API B2B + webhook", "Ưu tiên hàng đợi render", "Quản lý nhiều workspace"],
  },
];

export default function PricingPage() {
  return (
    <div className="min-h-dvh mesh-bg">
      <SiteHeader />

      <section className="mx-auto max-w-6xl px-4 pt-32 pb-10 text-center">
        <h1 className="font-display text-[clamp(2rem,5vw,3.25rem)] font-extrabold tracking-[-0.02em] text-ink-high">
          Trả theo <span className="text-gradient">credit</span>, nói bằng &ldquo;video&rdquo;
        </h1>
        <p className="mx-auto mt-4 max-w-xl text-ink-medium">
          1 credit = 150đ. Thấy trước số credit mỗi video, chỉ trừ khi dùng, hoàn 100% nếu lỗi hệ thống.
        </p>
      </section>

      <section className="mx-auto max-w-6xl px-4 pb-16">
        <div className="grid items-start gap-5 md:grid-cols-3">
          {PACKS.map((p) => (
            <GlassCard
              key={p.name}
              bordered={p.featured}
              className={p.featured ? "relative scale-[1.02] p-7 shadow-glow-sm" : "p-7"}
            >
              {p.featured && (
                <Badge tone="brand" className="absolute -top-3 left-1/2 -translate-x-1/2">Phổ biến</Badge>
              )}
              <h3 className="font-display font-semibold text-ink-high">{p.name}</h3>
              <div className="mt-4 font-numeric text-4xl font-bold text-ink-high">
                {p.credits.toLocaleString("vi-VN")}
                <span className="ml-1 text-sm font-normal text-ink-low">credit</span>
              </div>
              <div className="mt-2 text-ink-medium">{p.price}</div>
              <div className="mt-1 text-sm text-ink-low">{p.note}</div>

              <ul className="mt-5 flex flex-col gap-2.5 border-t border-white/[0.06] pt-5">
                {p.feats.map((f) => (
                  <li key={f} className="flex items-start gap-2.5 text-sm text-ink-medium">
                    <Check className="mt-0.5 h-4 w-4 shrink-0 text-success" /> {f}
                  </li>
                ))}
              </ul>

              <Link href="/login" className="mt-6 block">
                <Button variant={p.featured ? "primary" : "glass"} className="w-full">{p.cta}</Button>
              </Link>
            </GlassCard>
          ))}
        </div>

        <p className="mt-8 text-center text-sm text-ink-disabled">
          Cổng thanh toán: VNPay · MoMo · VietQR. Mọi gói đều minh bạch credit và hoàn 100% nếu lỗi hệ thống.
        </p>
      </section>

      {/* dẫn về FAQ trên trang chủ */}
      <section className="mx-auto max-w-3xl px-4 pb-24 text-center">
        <div className="mx-auto mb-6 h-px max-w-xs bg-gradient-to-r from-transparent via-violet-500/60 to-transparent" />
        <h2 className="font-display text-2xl font-bold text-ink-high">Còn thắc mắc?</h2>
        <p className="mt-2 text-ink-medium">Xem câu hỏi thường gặp hoặc tạo thử miễn phí ngay.</p>
        <div className="mt-6 flex flex-wrap justify-center gap-3">
          <Link href="/#faq"><Button variant="glass">Câu hỏi thường gặp</Button></Link>
          <Link href="/login"><Button>Tạo video đầu tiên</Button></Link>
        </div>
      </section>

      <footer className="border-t border-white/[0.06] px-4 py-8">
        <div className="mx-auto flex max-w-6xl flex-col items-center gap-4 sm:flex-row sm:justify-between">
          <Logo />
          <nav className="flex flex-wrap items-center justify-center gap-x-5 gap-y-2 text-sm text-ink-low">
            <Link href="/" className="hover:text-ink-medium">Trang chủ</Link>
            <Link href="/terms" className="hover:text-ink-medium">Điều khoản</Link>
            <Link href="/privacy" className="hover:text-ink-medium">Bảo mật</Link>
          </nav>
          <p className="text-xs text-ink-disabled">© 2026 Vyra · Video AI giọng Việt</p>
        </div>
      </footer>
    </div>
  );
}
