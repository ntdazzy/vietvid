"use client";

import { use } from "react";
import Link from "next/link";
import { Download, Sparkles, Mic, ShieldCheck, ArrowRight } from "lucide-react";
import { API_BASE_URL } from "@/lib/config";
import { Logo } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
import { FilmLabel } from "@/components/ui/cinematic";
import { Reveal } from "@/components/marketing/reveal";
import { ACCENTS } from "@/lib/accents";

const a = ACCENTS.sky;

export default function SharePage({
  params,
}: {
  params: Promise<{ id: string; token: string }>;
}) {
  const { id, token } = use(params);
  const videoUrl = `${API_BASE_URL}/v1/media/video/${id}?token=${encodeURIComponent(token)}`;

  return (
    <div className="mesh-bg relative flex min-h-dvh flex-col">
      {/* 1 vầng glow accent duy nhất */}
      <div
        className="pointer-events-none absolute left-1/2 top-0 h-72 w-[36rem] -translate-x-1/2 rounded-full blur-3xl"
        style={{ background: a.glow }}
      />

      {/* HÀNG TIÊU ĐỀ — dải "marquee" rạp chiếu: mark Vyra trái, nhãn chia sẻ giữa, CTA phải */}
      <header className="relative z-10 mx-auto flex w-full max-w-6xl items-center justify-between gap-3 px-4 py-5">
        <Link href="/" className="rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400/60">
          <Logo />
        </Link>
        <FilmLabel className="hidden sm:inline-flex">Video chia sẻ công khai</FilmLabel>
        <Link href="/login">
          <Button size="sm" variant="glass" className="gap-1.5">
            Tạo video của bạn <ArrowRight className="h-3.5 w-3.5" />
          </Button>
        </Link>
      </header>

      {/* SÂN KHẤU — player là nhân vật chính; bên phải là "vé" thông tin + CTA. Bất đối xứng. */}
      <main className="relative z-10 mx-auto grid w-full max-w-6xl flex-1 grid-cols-1 items-stretch gap-5 px-4 pb-14 lg:grid-cols-[minmax(0,1fr)_22rem]">
        {/* MÀN HÌNH CHIẾU */}
        <Reveal className="flex flex-col gap-3">
          <div className="group relative overflow-hidden rounded-3xl border border-white/10 bg-black shadow-[0_30px_90px_-30px_rgba(0,0,0,0.9)]">
            {/* viền sáng accent mảnh phía trên — gợi đèn màn hình */}
            <div className={`pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent ${a.line} to-transparent`} />
            {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
            <video
              src={videoUrl}
              controls
              autoPlay
              loop
              playsInline
              className="mx-auto block max-h-[74vh] w-full bg-black object-contain"
            />
          </div>
          {/* dải chân màn hình — nhãn nhỏ, giọng người */}
          <div className="flex items-center justify-between gap-3 px-1 text-[11px] uppercase tracking-[0.18em] text-ink-low">
            <span className="inline-flex items-center gap-2">
              <span className={`h-1.5 w-1.5 rounded-full ${a.bar}`} />
              Đang phát
            </span>
            <span className="hidden sm:inline">Bấm để bật tiếng</span>
          </div>
        </Reveal>

        {/* VÉ THÔNG TIN — cột hẹp, glass viền-gradient, dồn nội dung dọc */}
        <Reveal delay={0.08} className="flex">
          <aside className="flex w-full flex-col gap-6 rounded-3xl glass-bordered p-6">
            <div>
              <span className={`text-xs font-semibold uppercase tracking-[0.2em] ${a.text}`}>
                Tạo bằng Vyra
              </span>
              <h1 className="mt-3 font-display text-2xl font-extrabold leading-tight text-ink-high">
                Video bán hàng <span className="text-gradient">giọng Việt thật</span>
              </h1>
              <p className="mt-2 text-sm leading-relaxed text-ink-medium">
                Vyra dựng video từ một tấm ảnh sản phẩm — kịch bản, lồng tiếng và dựng cảnh đều bằng AI.
              </p>
            </div>

            {/* điểm nhấn — không số bịa, chỉ năng lực thật */}
            <ul className="flex flex-col gap-3 border-y border-white/10 py-5">
              <Point icon={Mic} text="Giọng đọc tiếng Việt, nghe như người thật" />
              <Point icon={Sparkles} text="Một ảnh sản phẩm thành video 60 giây" />
              <Point icon={ShieldCheck} text="Hoàn 100% credit nếu lỗi hệ thống" />
            </ul>

            {/* CTA — tải về + tạo video */}
            <div className="flex flex-col gap-3">
              <Link href="/login" className="block">
                <Button className="w-full gap-2">
                  <Sparkles className="h-4 w-4" /> Tạo video AI giọng Việt
                </Button>
              </Link>
              <a href={videoUrl} download={`vietvid-${id}.mp4`} className="block">
                <Button variant="outline" className="w-full gap-2">
                  <Download className="h-4 w-4" /> Tải MP4
                </Button>
              </a>
              <p className="text-center text-xs text-ink-low">Miễn phí dùng thử, không cần thẻ.</p>
            </div>
          </aside>
        </Reveal>
      </main>
    </div>
  );
}

function Point({ icon: Icon, text }: { icon: typeof Mic; text: string }) {
  return (
    <li className="flex items-start gap-3 text-sm text-ink-medium">
      <span className={`mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-lg bg-gradient-to-br ${a.tile} ${a.icon} ring-1 ${a.ring}`}>
        <Icon className="h-3.5 w-3.5" />
      </span>
      <span className="leading-snug">{text}</span>
    </li>
  );
}
