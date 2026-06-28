"use client";

import { UserSquare2, Star, Shirt, Package, TrendingUp, MessageSquare, GitCompare, Megaphone, Sparkles } from "lucide-react";
import { Reveal } from "@/components/marketing/reveal";
import { SectionHeading } from "@/components/marketing/section-heading";

// Khẳng định độ RỘNG: Vyra dựng đủ loại video, không chỉ quảng cáo sản phẩm.
const CASES = [
  { icon: UserSquare2, label: "KOL AI review", hot: true },
  { icon: Star, label: "Review sản phẩm" },
  { icon: Shirt, label: "Lookbook thời trang" },
  { icon: Package, label: "Mở hộp / unboxing" },
  { icon: TrendingUp, label: "Bắt trend", hot: true },
  { icon: MessageSquare, label: "Cảm nhận khách hàng" },
  { icon: GitCompare, label: "So sánh sản phẩm" },
  { icon: Megaphone, label: "Quảng cáo bán hàng" },
  { icon: Sparkles, label: "Giới thiệu dịch vụ" },
];

export function UseCases() {
  return (
    <section className="mx-auto max-w-6xl px-4 py-24 lg:py-28">
      <SectionHeading
        eyebrow="Một engine, nhiều loại nội dung"
        title={<>Không chỉ quảng cáo sản phẩm. <span className="text-gradient">Vyra dựng đủ loại video.</span></>}
        sub="KOL ảo review, lookbook, mở hộp, bắt trend, cảm nhận khách… cùng một quy trình, cùng giọng Việt thật."
      />
      <div className="mt-10 flex flex-wrap gap-3">
        {CASES.map((c, i) => (
          <Reveal key={c.label} delay={0.04 * i}>
            <div className="group flex items-center gap-2.5 rounded-2xl border border-white/[0.08] bg-white/[0.025] px-4 py-3 transition-colors hover:border-violet-400/40 hover:bg-violet-500/[0.06]">
              <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-violet-500/[0.12] text-violet-300 transition-colors group-hover:bg-violet-500/20">
                <c.icon className="h-[18px] w-[18px]" />
              </span>
              <span className="text-sm font-medium text-ink-high">{c.label}</span>
              {c.hot && <span className="rounded-md bg-danger/15 px-1.5 py-0.5 text-[10px] font-bold uppercase text-danger">Hot</span>}
            </div>
          </Reveal>
        ))}
      </div>
    </section>
  );
}
