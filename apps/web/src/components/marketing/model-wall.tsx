"use client";

import type { LucideIcon } from "lucide-react";
import { Clapperboard, Image as ImageIcon, Speech, ScanFace, Mic2 } from "lucide-react";
import { FilmLabel } from "@/components/ui/cinematic";
import { Reveal } from "@/components/marketing/reveal";

// "Tổng hợp nhiều model AI" — khối QUẢNG CÁO chính: Vyra gom mọi model xịn vào 1 tài khoản.
// Seedance 2.5 làm ĐIỂM NHẤN (spotlight ảnh nền + hiệu ứng hover). Dữ liệu model THẬT
// (khớp provider CometAPI/Runware) — không khoe model chưa tích hợp như đã có.
type Model = { n: string; tag?: "hot" | "soon" };
const V = "/showcase/v2";
const GROUPS: { cat: string; note: string; icon: LucideIcon; img: string; models: Model[] }[] = [
  { cat: "Video", note: "chữ/ảnh → clip", icon: Clapperboard, img: `${V}/genre-cinematic-film-noir.jpg`, models: [{ n: "Seedance 2.5", tag: "soon" }, { n: "Seedance 2.0" }, { n: "Kling 3.0" }, { n: "Veo 3.1" }, { n: "Wan 2.6" }, { n: "Hailuo" }] },
  { cat: "Ảnh", note: "KOL + sản phẩm", icon: ImageIcon, img: `${V}/prod-jewelry-gold-sparkle.jpg`, models: [{ n: "Grok Img 1.5", tag: "hot" }, { n: "FLUX.2" }, { n: "Seedream 5" }, { n: "Nano-Banana" }, { n: "Ideogram" }] },
  { cat: "Mặt nói bán hàng", note: "ảnh + giọng → nói", icon: Speech, img: `${V}/idol-vlogger.jpg`, models: [{ n: "OmniHuman 1.5", tag: "hot" }, { n: "Kling Avatar 2.0" }] },
  { cat: "Khoá mặt KOL", note: "1 gương mặt nhất quán", icon: ScanFace, img: `${V}/face-streetwear-golden-hour-male.jpg`, models: [{ n: "InstantID" }, { n: "PuLID" }, { n: "DreamO" }] },
  { cat: "Giọng Việt", note: "đọc tự nhiên, cảm xúc", icon: Mic2, img: `${V}/face-skincare-vanity-warm-lamp.jpg`, models: [{ n: "VieNeu-TTS" }, { n: "Fish Audio" }] },
];

// Đếm THẬT từ dữ liệu — số hiển thị không bao giờ lệch danh sách (trước để cứng "10+").
const MODEL_COUNT = GROUPS.reduce((s, g) => s + g.models.length, 0);

function chipCls(tag?: "hot" | "soon") {
  if (tag === "soon") return "border-violet-400/40 bg-violet-500/10 text-violet-200";
  if (tag === "hot") return "border-amber-400/40 bg-amber-500/10 text-amber-200";
  return "border-white/10 bg-white/[0.04] text-ink-medium group-hover:border-white/20";
}

export function ModelWall() {
  return (
    <section className="relative overflow-hidden py-14 sm:py-20 lg:py-28">
      {/* Nền cinematic + scrim tan xuống bg-base + 1 vầng glow (đúng luật 1 glow/màn). */}
      <div className="pointer-events-none absolute inset-0 -z-10">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="/showcase/v2/genre-storyteller-window.jpg"
          alt=""
          className="h-full w-full object-cover object-top opacity-[0.16]"
        />
        <div className="absolute inset-0 bg-gradient-to-b from-bg-base/70 via-bg-base/92 to-bg-base" />
        <div className="glow-radial absolute left-1/3 top-[-6rem] h-[520px] w-[820px] -translate-x-1/2 opacity-70" />
      </div>

      <div className="mx-auto max-w-[1600px] px-4">
        {/* HEADER — căn TRÁI (đồng bộ với các section khác), nhưng lớn & nổi bật */}
        <Reveal>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div className="max-w-2xl">
              <FilmLabel>Tổng hợp nhiều model AI hàng đầu</FilmLabel>
              <h2 className="mt-3 font-display text-[clamp(2rem,4.4vw,3rem)] font-bold leading-[1.12] tracking-tight text-ink-high">
                Một tài khoản. <span className="text-gradient italic">Mọi model AI xịn nhất.</span>
              </h2>
            </div>
            <p className="max-w-sm text-sm leading-relaxed text-ink-low sm:text-right">
              Vyra gom {MODEL_COUNT} model hàng đầu thế giới vào một chỗ, tự chọn cái tốt + rẻ cho từng
              việc. Bạn khỏi nhiều tài khoản nước ngoài, khỏi thẻ Visa, khỏi rành kỹ thuật.
            </p>
          </div>
        </Reveal>

        <div className="mt-10 grid gap-4 lg:grid-cols-3">
          {/* SPOTLIGHT Seedance 2.5 — ảnh nền cinematic + hover glow, chiếm 2/3 */}
          <Reveal className="lg:col-span-2">
            <div className="group relative h-full min-h-[300px] overflow-hidden rounded-3xl border border-white/[0.08]">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src="/showcase/v2/genre-shortfilm-rainy-car-night.jpg"
                alt=""
                className="absolute inset-0 h-full w-full object-cover opacity-50 transition-all duration-700 group-hover:scale-105 group-hover:opacity-65"
              />
              <div className="absolute inset-0 bg-gradient-to-tr from-bg-base via-bg-base/65 to-violet-950/30" />
              <div className="glow-radial pointer-events-none absolute -right-16 -top-16 h-72 w-72 opacity-0 transition-opacity duration-700 group-hover:opacity-70" />
              <div className="relative flex h-full flex-col justify-end p-7 lg:p-9">
                <span className="mb-3 inline-flex w-fit items-center gap-1.5 rounded-full border border-violet-400/40 bg-violet-500/15 px-3 py-1 text-[11px] font-semibold text-violet-200">
                  <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-violet-300" /> SẮP RA MẮT
                </span>
                <h3 className="font-display text-[clamp(1.8rem,3.5vw,2.8rem)] font-bold leading-tight text-ink-high">
                  Seedance <span className="text-gradient">2.5</span>
                </h3>
                <p className="mt-3 max-w-md text-sm leading-relaxed text-ink-medium">
                  Model video thế hệ mới — người thật hơn, chuyển động mượt hơn, bám prompt sát hơn.
                  Vyra tích hợp ngay khi ra mắt; bạn không phải đổi công cụ.
                </p>
              </div>
            </div>
          </Reveal>

          {/* Card phụ — chốt thông điệp "gộp 1 nơi" (số đếm THẬT + lợi ích) */}
          <Reveal delay={0.06}>
            <div className="flex h-full flex-col justify-between gap-5 rounded-3xl glass-bordered p-7">
              <div>
                <div className="flex items-baseline gap-1.5">
                  <span className="font-numeric text-6xl font-bold text-gradient">{MODEL_COUNT}</span>
                  <span className="font-numeric text-2xl font-bold text-violet-300/80">+</span>
                </div>
                <div className="mt-1.5 text-sm leading-snug text-ink-medium">
                  model AI hàng đầu · 5 nhóm việc · <span className="text-ink-high">1 tài khoản Vyra</span>
                </div>
              </div>
              <ul className="flex flex-col gap-2.5 text-sm text-ink-low">
                <li className="flex items-start gap-2"><span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-violet-400" /> Khỏi mở nhiều tài khoản nước ngoài, khỏi thẻ Visa</li>
                <li className="flex items-start gap-2"><span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-violet-400" /> Vyra tự chọn model rẻ nhất cho từng việc</li>
                <li className="flex items-start gap-2"><span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-violet-400" /> Trả bằng MoMo / chuyển khoản VND, tính đúng từng credit</li>
              </ul>
            </div>
          </Reveal>
        </div>

        {/* Lưới model theo nhóm — thẻ premium: icon + tiêu đề rõ + chip model dễ đọc */}
        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          {GROUPS.map((g, i) => (
            <Reveal key={g.cat} delay={0.03 * i}>
              <div className="group relative flex h-full flex-col overflow-hidden rounded-2xl border border-white/[0.09] p-4 shadow-[0_10px_30px_-18px_rgba(0,0,0,0.9)] transition-all duration-300 hover:-translate-y-0.5 hover:border-violet-400/30 hover:shadow-glow-sm">
                {/* ảnh nền cinematic + scrim đục → thẻ premium, chữ vẫn đọc rõ */}
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={g.img} alt="" loading="lazy" className="absolute inset-0 h-full w-full object-cover object-top opacity-[0.22] transition-all duration-500 group-hover:scale-105 group-hover:opacity-30" />
                <div className="absolute inset-0 bg-gradient-to-b from-bg-elevated/80 via-bg-elevated/90 to-bg-elevated/96" />
                <div className="pointer-events-none absolute -right-8 -top-8 h-24 w-24 rounded-full bg-violet-500/15 opacity-0 blur-2xl transition-opacity duration-500 group-hover:opacity-100" />
                <div className="relative mb-3 flex items-center gap-2.5">
                  <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl border border-violet-400/25 bg-violet-500/15 text-violet-200 backdrop-blur-sm transition-colors group-hover:bg-violet-500/25">
                    <g.icon className="h-[18px] w-[18px]" />
                  </span>
                  <div className="min-w-0">
                    <div className="font-display text-sm font-bold leading-tight text-ink-high">{g.cat}</div>
                    <div className="truncate text-[11px] text-ink-low">{g.note}</div>
                  </div>
                </div>
                <div className="relative flex flex-wrap gap-1.5">
                  {g.models.map((m) => (
                    <span
                      key={m.n}
                      className={"inline-flex items-center gap-1 rounded-lg border px-2.5 py-1 text-[11.5px] font-medium transition-colors " + chipCls(m.tag)}
                    >
                      {m.n}
                      {m.tag === "hot" && <span className="text-[9px] font-bold uppercase text-amber-300">hot</span>}
                      {m.tag === "soon" && <span className="text-[9px] font-bold uppercase text-violet-300">sắp</span>}
                    </span>
                  ))}
                </div>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
