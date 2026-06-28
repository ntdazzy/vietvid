"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { SectionHeading } from "@/components/marketing/section-heading";
import { MiniReel } from "@/components/marketing/mini-reel";
import { ActBadge } from "@/components/marketing/act-badge";
import { Reveal } from "@/components/marketing/reveal";
import { cn } from "@/lib/utils/cn";

// Mirror "FEATURED KOL" của autovis — NHƯNG trung thực: không ảnh mặt người giả.
// Khung persona (avatar chữ-cái, kiểu VoiceRail) + clip SP thật chạy (MiniReel) + slot chờ ảnh.
// ⟶SLOT: khi persona có avatar_url → <img object-cover> đè lên. KHÔNG dùng stock.
const FEATURED = { name: "Linh", initial: "L", industry: "Thời trang", tone: "rose" as const };
const OTHERS = [
  { name: "Mai", initial: "M", industry: "Mỹ phẩm", tone: "rose" as const },
  { name: "An", initial: "A", industry: "Công nghệ", tone: "sky" as const },
  { name: "Hoa", initial: "H", industry: "Gia dụng", tone: "rose" as const },
];

function Avatar({ initial, tone, size = "sm" }: { initial: string; tone: "rose" | "sky"; size?: "sm" | "md" }) {
  return (
    <span
      className={cn(
        "grid shrink-0 place-items-center rounded-full font-bold",
        size === "md" ? "h-11 w-11 text-base" : "h-9 w-9 text-sm",
        tone === "rose" ? "bg-rose-500/15 text-rose-200" : "bg-sky-500/15 text-sky-200",
      )}
    >
      {initial}
    </span>
  );
}

export function FeaturedKol() {
  return (
    <section className="mx-auto max-w-6xl px-4 py-24 lg:py-28">
      <SectionHeading
        eyebrow="KOL AI · Khung nhân vật"
        title={<>Một gương mặt KOL. <span className="text-gradient italic">Nhiều video, một outfit nhất quán.</span></>}
        sub="Tạo persona KOL AI riêng trong app — đặt tên, gắn ngành hàng, giữ gương mặt xuyên suốt mọi video. Dưới đây là khung nhân vật mẫu; thả ảnh KOL của bạn để kích hoạt."
      />

      <div className="mt-10 grid gap-5 lg:grid-cols-12">
        {/* card lớn — clip SP thật + khung persona (slot chờ ảnh) */}
        <Reveal className="lg:col-span-7">
          <div className="flex h-full flex-col gap-4 rounded-[24px] border border-dashed border-violet-400/30 bg-white/[0.02] p-5 sm:flex-row sm:gap-5">
            <div className="w-[140px] shrink-0 sm:w-[150px]">
              <MiniReel
                poster="/samples/fashion.png"
                video="/samples/fashion.mp4"
                className="w-full"
                captions={["Linh review váy mới về…", "Outfit giữ nguyên mọi cảnh", "Bấm giỏ hàng nha!"]}
              />
            </div>
            <div className="flex min-w-0 flex-col">
              <ActBadge tone="new" label="Giữ outfit nhất quán" className="w-fit" />
              <div className="mt-3 flex items-center gap-2.5">
                <Avatar initial={FEATURED.initial} tone={FEATURED.tone} size="md" />
                <div>
                  <div className="font-display text-lg font-bold text-ink-high">{FEATURED.name}</div>
                  <div className="text-xs text-ink-low">{FEATURED.industry}</div>
                </div>
              </div>
              <p className="mt-3 text-sm text-ink-medium">
                Một persona KOL AI dựng review, lookbook, bắt trend — gương mặt và phong cách giữ
                nguyên qua mọi video, không lệch outfit.
              </p>
              <p className="mt-auto pt-3 text-[11px] text-ink-low">
                ◌ Khung KOL — thả ảnh gương mặt để kích hoạt.
              </p>
              <Link href="/login" className="mt-3">
                <Button className="gap-1.5">Tạo KOL AI</Button>
              </Link>
            </div>
          </div>
        </Reveal>

        {/* 3 card nhỏ — persona theo ngành (4 ngành riêng biệt) */}
        <div className="flex flex-col gap-4 lg:col-span-5">
          {OTHERS.map((p, i) => (
            <Reveal key={p.name} delay={0.08 * (i + 1)} className="flex-1">
              <div className="flex h-full items-center gap-3 rounded-2xl border border-dashed border-white/[0.1] bg-white/[0.02] p-4">
                <Avatar initial={p.initial} tone={p.tone} size="md" />
                <div className="min-w-0">
                  <div className="text-sm font-semibold text-ink-high">{p.name}</div>
                  <div className="text-xs text-ink-low">{p.industry}</div>
                </div>
                <span className="ml-auto rounded-md bg-white/[0.05] px-2 py-0.5 text-[10px] text-ink-low">Khung</span>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
