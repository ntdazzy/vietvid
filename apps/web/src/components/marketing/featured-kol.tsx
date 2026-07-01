"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { SectionHeading } from "@/components/marketing/section-heading";
import { Reveal } from "@/components/marketing/reveal";
import { HoverVideo } from "@/components/ui/hover-video";

// KOL AI — 9 gương mặt do AI tạo, đa dạng ngành & phong cách. Mỗi persona = 1 CLIP THẬT 9:16 sắc nét
// (poster = frame của chính clip nên rê chuột khớp 100%). Tất cả đều người lớn, da trắng mịn, photoreal.
// Card đầu (Linh) FEATURED 2×2; 8 card còn lại lấp kín lưới 4 cột (grid-flow-dense → không hở đáy).
const PERSONAS = [
  { name: "Linh", industry: "Thời trang · Lifestyle", key: "face-girl-next-door-bedroom-vlogger", featured: true },
  { name: "Hà", industry: "Mỹ phẩm · Skincare", key: "face-skincare-vanity-warm-lamp" },
  { name: "An", industry: "Công nghệ", key: "face-tech-reviewer-messy-desk-male" },
  { name: "Trâm", industry: "Lookbook · Mood", key: "face-pale-elegant-rainy-cafe" },
  { name: "Mây", industry: "Gen Z · Beauty", key: "face-genz-student-freckles-selfie" },
  { name: "Khoa", industry: "Streetwear nam", key: "face-streetwear-golden-hour-male" },
  { name: "Thảo", industry: "Mẹ & Bé", key: "face-young-mom-kitchen-baby" },
  { name: "Vy", industry: "Fitness · Yoga", key: "face-morning-yoga-dewy" },
  { name: "Ngọc", industry: "Tri thức · Sách", key: "face-bookshop-shy-reader" },
];

export function FeaturedKol() {
  return (
    <section className="mx-auto max-w-[1600px] px-4 py-14 sm:py-20 lg:py-28">
      <SectionHeading
        eyebrow="KOL AI · 9 gương mặt do AI tạo"
        title={<>Chín gương mặt KOL. <span className="text-gradient italic">Mỗi người một ngành, một outfit nhất quán.</span></>}
        sub="KOL AI giữ gương mặt và phong cách xuyên suốt mọi video — review, lookbook, bắt trend, mẹ&bé, fitness. Rê chuột để xem persona chuyển động; tạo persona của riêng bạn trong app."
      />

      {/* Lưới KOL: featured 2×2 + 8 ô 1×1 lấp KÍN (mobile 2 cột · sm 4 cột=4×3 · lg 6 cột=6×2).
          auto-rows CAO hơn bề rộng cột để mỗi ô MẶT là ô DỌC (không crop mặt thành dải ngang). */}
      <div className="mt-10 grid auto-rows-[200px] grid-flow-dense grid-cols-2 gap-3 sm:auto-rows-[230px] sm:grid-cols-4 lg:auto-rows-[300px] lg:grid-cols-6 lg:gap-4">
        {PERSONAS.map((p, i) => {
          const src = `/showcase/v2/${p.key}`;
          return (
            <Reveal key={p.name} delay={0.04 * i} className={p.featured ? "col-span-2 row-span-2" : ""}>
              <Link href="/login" className="group block h-full">
                <HoverVideo
                  poster={`${src}.jpg`}
                  video={`${src}.mp4`}
                  alt={`KOL AI ${p.name}`}
                  badge={false}
                  objectClass="object-top"
                  className="h-full w-full rounded-[20px] ring-1 ring-white/[0.08] transition duration-500 group-hover:ring-violet-400/40 group-hover:-translate-y-1"
                >
                  {/* scrim đáy để chữ nổi rõ trên mọi clip */}
                  <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-black/85 via-black/10 to-transparent" />

                  {p.featured ? (
                    <span className="absolute left-3 top-3 rounded-md bg-violet-500/85 px-2 py-0.5 text-[10px] font-semibold text-white backdrop-blur-sm">
                      Giữ outfit nhất quán
                    </span>
                  ) : (
                    <span className="absolute right-2.5 top-2.5 rounded-md bg-black/45 px-2 py-0.5 text-[9px] font-medium text-violet-100 backdrop-blur-sm">
                      KOL AI
                    </span>
                  )}

                  <div className="absolute inset-x-0 bottom-0 flex items-end justify-between p-3 sm:p-3.5">
                    <div className="min-w-0">
                      <div className={p.featured ? "font-display text-lg font-bold text-white" : "font-display text-sm font-bold text-white"}>{p.name}</div>
                      <div className={p.featured ? "text-xs text-white/75" : "text-[11px] text-white/65"}>{p.industry}</div>
                    </div>
                    <span className="shrink-0 translate-y-1 text-[11px] font-medium text-violet-200 opacity-0 transition duration-300 group-hover:translate-y-0 group-hover:opacity-100">
                      xem →
                    </span>
                  </div>
                </HoverVideo>
              </Link>
            </Reveal>
          );
        })}
      </div>

      <Reveal delay={0.12}>
        <div className="mt-9 flex flex-col items-center gap-3 text-center">
          <p className="max-w-xl text-sm text-ink-medium">
            Một persona — gương mặt và phong cách giữ nguyên qua mọi video: review, lookbook, bắt trend,
            đu trend Douyin, mẹ&amp;bé, fitness. Không thuê người, không lệch outfit.
          </p>
          <Link href="/login">
            <Button className="gap-1.5">Tạo KOL AI của bạn</Button>
          </Link>
        </div>
      </Reveal>
    </section>
  );
}
