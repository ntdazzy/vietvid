"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { SectionHeading } from "@/components/marketing/section-heading";
import { Reveal } from "@/components/marketing/reveal";
import { HoverVideo } from "@/components/ui/hover-video";

// KOL AI — gương mặt do AI tạo. Mỗi persona = 1 CLIP THẬT 9:16 sắc nét (poster = frame của chính
// clip nên rê chuột khớp 100%, không còn cảnh ảnh nét mà video vỡ). 4 ngành khác nhau, đều CHUYỂN
// ĐỘNG khi rê chuột. Linh dẫn đầu với pill "giữ outfit nhất quán".
const PERSONAS = [
  { name: "Linh", industry: "Thời trang", src: "/showcase/kol-hero", featured: true },
  { name: "Mai", industry: "Mỹ phẩm", src: "/showcase/gaixinh" },
  { name: "An", industry: "Công nghệ", src: "/showcase/presenter" },
  { name: "Hoa", industry: "Đu trend Douyin", src: "/showcase/trend-dance" },
];

export function FeaturedKol() {
  return (
    <section className="mx-auto max-w-[1600px] px-4 py-24 lg:py-28">
      <SectionHeading
        eyebrow="KOL AI · Gương mặt do AI tạo"
        title={<>Một gương mặt KOL. <span className="text-gradient italic">Nhiều video, một outfit nhất quán.</span></>}
        sub="KOL AI giữ gương mặt và phong cách xuyên suốt mọi video — review, lookbook, bắt trend. Rê chuột để xem persona chuyển động; tạo persona của riêng bạn trong app."
      />

      <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {PERSONAS.map((p, i) => (
          <Reveal key={p.name} delay={0.06 * i}>
            <Link href="/login" className="group block">
              <HoverVideo
                poster={`${p.src}.jpg`}
                video={`${p.src}.mp4`}
                alt={`KOL AI ${p.name}`}
                badge={false}
                objectClass="object-top"
                className="aspect-[3/4] w-full rounded-[20px] ring-1 ring-white/[0.08] transition duration-500 group-hover:ring-violet-400/40 group-hover:-translate-y-1"
              >
                {/* scrim đáy để chữ nổi rõ trên mọi clip */}
                <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-black/85 via-black/10 to-transparent" />

                {p.featured ? (
                  <span className="absolute left-3 top-3 rounded-md bg-violet-500/85 px-2 py-0.5 text-[10px] font-semibold text-white backdrop-blur-sm">
                    Giữ outfit nhất quán
                  </span>
                ) : (
                  <span className="absolute right-3 top-3 rounded-md bg-black/45 px-2 py-0.5 text-[10px] font-medium text-violet-100 backdrop-blur-sm">
                    KOL AI
                  </span>
                )}

                <div className="absolute inset-x-0 bottom-0 flex items-end justify-between p-3.5">
                  <div className="min-w-0">
                    <div className="font-display text-base font-bold text-white">{p.name}</div>
                    <div className="text-xs text-white/70">{p.industry}</div>
                  </div>
                  <span className="shrink-0 translate-y-1 text-[11px] font-medium text-violet-200 opacity-0 transition duration-300 group-hover:translate-y-0 group-hover:opacity-100">
                    xem persona →
                  </span>
                </div>
              </HoverVideo>
            </Link>
          </Reveal>
        ))}
      </div>

      <Reveal delay={0.12}>
        <div className="mt-9 flex flex-col items-center gap-3 text-center">
          <p className="max-w-xl text-sm text-ink-medium">
            Một persona — gương mặt và phong cách giữ nguyên qua mọi video: review, lookbook, bắt trend,
            đu trend Douyin. Không thuê người, không lệch outfit.
          </p>
          <Link href="/login">
            <Button className="gap-1.5">Tạo KOL AI của bạn</Button>
          </Link>
        </div>
      </Reveal>
    </section>
  );
}
