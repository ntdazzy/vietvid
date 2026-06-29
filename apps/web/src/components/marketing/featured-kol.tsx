"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { SectionHeading } from "@/components/marketing/section-heading";
import { MiniReel } from "@/components/marketing/mini-reel";
import { ActBadge } from "@/components/marketing/act-badge";
import { Reveal } from "@/components/marketing/reveal";
import { HoverVideo } from "@/components/ui/hover-video";
import { cn } from "@/lib/utils/cn";

// "FEATURED KOL" — gương mặt KOL do AI tạo (đúng thứ sản phẩm làm: KOL AI), giữ nhất quán mọi video.
const FEATURED = { name: "Linh", img: "/kol/linh.jpg", industry: "Thời trang", tone: "rose" as const };
const OTHERS = [
  { name: "Mai", img: "/kol/mai.jpg", industry: "Mỹ phẩm", tone: "rose" as const },
  { name: "An", img: "/kol/an.jpg", industry: "Công nghệ", tone: "sky" as const },
  { name: "Hoa", img: "/kol/hoa.jpg", industry: "Gia dụng", tone: "rose" as const },
];

function FaceAvatar({ img, name, size = "md" }: { img: string; name: string; size?: "md" | "lg" }) {
  return (
    <span
      className={cn(
        "block shrink-0 overflow-hidden rounded-full ring-1 ring-white/10",
        size === "lg" ? "h-14 w-14" : "h-11 w-11",
      )}
    >
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={img} alt={`KOL AI ${name}`} className="h-full w-full object-cover" />
    </span>
  );
}

export function FeaturedKol() {
  return (
    <section className="mx-auto max-w-6xl px-4 py-24 lg:py-28">
      <SectionHeading
        eyebrow="KOL AI · Gương mặt do AI tạo"
        title={<>Một gương mặt KOL. <span className="text-gradient italic">Nhiều video, một outfit nhất quán.</span></>}
        sub="KOL AI giữ gương mặt và phong cách xuyên suốt mọi video — review, lookbook, bắt trend. Dưới đây là vài persona mẫu; tạo persona của riêng bạn trong app."
      />

      <div className="mt-10 grid gap-5 lg:grid-cols-12">
        {/* card lớn — gương mặt KOL AI + clip SP thật */}
        <Reveal className="lg:col-span-7">
          <div className="flex h-full flex-col gap-4 rounded-[24px] border border-white/[0.08] bg-white/[0.02] p-5 sm:flex-row sm:gap-5">
            <HoverVideo
              poster={FEATURED.img}
              video={FEATURED.img.replace(/\.jpg$/, ".mp4")}
              alt={`KOL AI ${FEATURED.name}`}
              className="aspect-[3/4] w-[150px] shrink-0 rounded-2xl"
            >
              <span className="absolute bottom-2 left-2 rounded-md bg-bg-base/70 px-2 py-0.5 text-[10px] font-medium text-ink-high backdrop-blur-sm">
                Gương mặt AI
              </span>
            </HoverVideo>
            <div className="flex min-w-0 flex-col">
              <ActBadge tone="new" label="Giữ outfit nhất quán" className="w-fit" />
              <div className="mt-3 flex items-center gap-2.5">
                <FaceAvatar img={FEATURED.img} name={FEATURED.name} size="lg" />
                <div>
                  <div className="font-display text-lg font-bold text-ink-high">{FEATURED.name}</div>
                  <div className="text-xs text-ink-low">{FEATURED.industry} · KOL AI</div>
                </div>
              </div>
              <p className="mt-3 text-sm text-ink-medium">
                Một persona KOL AI dựng review, lookbook, bắt trend — gương mặt và phong cách giữ
                nguyên qua mọi video, không lệch outfit.
              </p>
              <div className="mt-4 w-[110px] shrink-0 sm:hidden">
                <MiniReel
                  poster="/samples/fashion.jpg"
                  video="/samples/fashion.mp4"
                  className="w-full"
                  captions={["Linh review váy mới về…", "Outfit giữ nguyên mọi cảnh", "Bấm giỏ hàng nha!"]}
                />
              </div>
              <Link href="/login" className="mt-auto pt-4">
                <Button className="gap-1.5">Tạo KOL AI</Button>
              </Link>
            </div>
            {/* clip SP thật — chỉ desktop để không chật mobile */}
            <div className="hidden w-[130px] shrink-0 sm:block">
              <MiniReel
                poster="/samples/fashion.jpg"
                video="/samples/fashion.mp4"
                className="w-full"
                captions={["Linh review váy mới về…", "Outfit giữ nguyên mọi cảnh", "Bấm giỏ hàng nha!"]}
              />
            </div>
          </div>
        </Reveal>

        {/* 3 card nhỏ — persona KOL AI theo ngành */}
        <div className="flex flex-col gap-4 lg:col-span-5">
          {OTHERS.map((p, i) => (
            <Reveal key={p.name} delay={0.08 * (i + 1)} className="flex-1">
              <div className="flex h-full items-center gap-3 rounded-2xl border border-white/[0.08] bg-white/[0.02] p-4">
                <FaceAvatar img={p.img} name={p.name} size="lg" />
                <div className="min-w-0">
                  <div className="text-sm font-semibold text-ink-high">{p.name}</div>
                  <div className="text-xs text-ink-low">{p.industry}</div>
                </div>
                <span className="ml-auto rounded-md bg-violet-500/[0.12] px-2 py-0.5 text-[10px] text-violet-200">KOL AI</span>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
