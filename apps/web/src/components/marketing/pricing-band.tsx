import Link from "next/link";
import { Check, Sparkles } from "lucide-react";
import { Reveal } from "@/components/marketing/reveal";
import { Button } from "@/components/ui/button";
import { FilmLabel } from "@/components/ui/cinematic";
import { cn } from "@/lib/utils/cn";

// Bảng giá GỌN ngay trên trang chủ (khớp /pricing): seller thấy giá VND trước khi rời trang.
// Số liệu thật từ màn /pricing — 1 credit = 150đ, không bịa.
const PACKS = [
  { name: "Dùng thử", credits: "300", price: "Miễn phí", note: "Tặng khi đăng ký", featured: false,
    cta: "Tạo thử ngay", feats: ["Không cần thẻ", "Đủ tạo video đầu tiên", "Xem credit trước khi tạo"] },
  { name: "Cơ bản", credits: "2.000", price: "300.000đ", note: "≈150đ / credit", featured: true,
    cta: "Chọn gói Cơ bản", feats: ["~20 video 60s", "7 giọng Việt thật", "Đủ 3 tỉ lệ", "Credit không hết hạn"] },
  { name: "Pro", credits: "7.000", price: "900.000đ", note: "Tiết kiệm hơn ~14%", featured: false,
    cta: "Chọn gói Pro", feats: ["~70 video 60s", "Ưu tiên hàng đợi", "API + webhook B2B"] },
];

export function PricingBand() {
  return (
    <section id="bang-gia" className="mx-auto max-w-[1600px] px-4 py-14 sm:py-20 lg:py-28">
      <Reveal>
        <div className="mx-auto max-w-2xl text-center">
          <FilmLabel className="justify-center">Bảng giá minh bạch</FilmLabel>
          <h2 className="mt-3 font-display text-[clamp(1.75rem,4vw,2.6rem)] font-bold leading-tight text-ink-high">
            Thấy credit trước khi tạo. <span className="text-gradient">Không cần thẻ để thử.</span>
          </h2>
          <p className="mt-3 text-ink-medium">
            Trả theo credit, dùng bao nhiêu tính bấy nhiêu, hoàn 100% nếu lỗi hệ thống. Hủy bất cứ lúc nào.
          </p>
        </div>
      </Reveal>

      <div className="mx-auto mt-10 grid max-w-5xl gap-5 sm:grid-cols-3">
        {PACKS.map((p, i) => (
          <Reveal key={p.name} delay={0.06 * i}>
            <div
              className={cn(
                "relative flex h-full flex-col overflow-hidden rounded-2xl p-6 transition-all duration-200",
                p.featured
                  ? "ring-1 ring-violet-400/40 bg-violet-500/[0.07] shadow-[0_0_44px_-14px_rgba(124,58,237,0.6)]"
                  : "glass-bordered hover:-translate-y-1 hover:ring-1 hover:ring-white/15",
              )}
            >
              <div className="flex items-center gap-2">
                <h3 className="font-display text-lg font-semibold text-ink-high">{p.name}</h3>
                {p.featured && (
                  <span className="inline-flex items-center gap-1 rounded-full bg-violet-500/20 px-2 py-0.5 text-[11px] font-semibold text-violet-100">
                    <Sparkles className="h-3 w-3" /> Phổ biến
                  </span>
                )}
              </div>
              <div className="mt-3 flex items-baseline gap-1.5">
                <span className={cn("font-numeric text-4xl font-bold tabular-nums", p.featured ? "text-violet-200" : "text-ink-high")}>
                  {p.credits}
                </span>
                <span className="text-sm text-ink-low">credit</span>
              </div>
              <div className="mt-1.5 text-ink-medium">{p.price}</div>
              <div className="text-sm text-ink-low">{p.note}</div>

              <ul className="mt-5 flex flex-1 flex-col gap-2.5">
                {p.feats.map((f) => (
                  <li key={f} className="flex items-start gap-2.5 text-sm text-ink-medium">
                    <Check className={cn("mt-0.5 h-4 w-4 shrink-0", p.featured ? "text-violet-300" : "text-success")} />
                    {f}
                  </li>
                ))}
              </ul>

              <Link href="/login" className="mt-6 block">
                <Button variant={p.featured ? "primary" : "glass"} className={cn("w-full", p.featured && "!bg-grad-brand")}>
                  {p.cta}
                </Button>
              </Link>
            </div>
          </Reveal>
        ))}
      </div>

      <div className="mt-6 text-center">
        <Link href="/pricing" className="text-sm font-medium text-violet-300 transition hover:text-violet-200">
          Xem chi tiết bảng giá →
        </Link>
      </div>
    </section>
  );
}
