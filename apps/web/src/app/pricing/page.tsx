import Link from "next/link";
import { Logo } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
import { GlassCard } from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";

const PACKS = [
  { name: "Dùng thử", credits: 300, price: "Miễn phí", note: "Tặng khi đăng ký", featured: false },
  { name: "Cơ bản", credits: 2000, price: "300.000đ", note: "~12 video 30s", featured: true },
  { name: "Chuyên nghiệp", credits: 7000, price: "900.000đ", note: "+15% thưởng nạp", featured: false },
];

export default function PricingPage() {
  return (
    <div className="min-h-dvh mesh-bg">
      <nav className="mx-auto flex max-w-6xl items-center justify-between px-4 py-5">
        <Link href="/">
          <Logo />
        </Link>
        <Link href="/login">
          <Button size="sm">Đăng nhập</Button>
        </Link>
      </nav>

      <section className="mx-auto max-w-6xl px-4 py-16 text-center">
        <h1 className="text-[clamp(2rem,5vw,3.25rem)] font-extrabold tracking-[-0.02em] text-ink-high">
          Trả theo <span className="text-gradient">credit</span>, nói bằng "video"
        </h1>
        <p className="mx-auto mt-4 max-w-xl text-ink-medium">
          1 credit = 150đ. Thấy trước số credit mỗi video. Hoàn 100% nếu lỗi hệ thống.
        </p>

        <div className="mt-12 grid gap-5 md:grid-cols-3">
          {PACKS.map((p) => (
            <GlassCard
              key={p.name}
              bordered={p.featured}
              className={p.featured ? "relative scale-[1.03] p-7" : "p-7"}
            >
              {p.featured && (
                <Badge tone="brand" className="absolute -top-3 left-1/2 -translate-x-1/2">
                  Phổ biến
                </Badge>
              )}
              <h3 className="font-semibold text-ink-high">{p.name}</h3>
              <div className="mt-4 font-numeric text-4xl font-bold text-ink-high">
                {p.credits.toLocaleString("vi-VN")}
                <span className="ml-1 text-sm font-normal text-ink-low">credit</span>
              </div>
              <div className="mt-2 text-ink-medium">{p.price}</div>
              <div className="mt-1 text-sm text-ink-low">{p.note}</div>
              <Link href="/login" className="mt-6 block">
                <Button variant={p.featured ? "primary" : "glass"} className="w-full">
                  Bắt đầu
                </Button>
              </Link>
            </GlassCard>
          ))}
        </div>

        <p className="mt-10 text-sm text-ink-disabled">
          Cổng thanh toán (VNPay · Momo · VietQR · USDT) sẽ mở khi backend billing hoàn tất.
        </p>
      </section>
    </div>
  );
}
