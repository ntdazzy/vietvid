"use client";

import { FilmLabel } from "@/components/ui/cinematic";
import { Reveal } from "@/components/marketing/reveal";

// "Tổng hợp nhiều model AI" — khối QUẢNG CÁO chính: Vyra gom mọi model xịn vào 1 tài khoản.
// Seedance 2.5 làm ĐIỂM NHẤN (spotlight ảnh nền + hiệu ứng hover). Dữ liệu model THẬT
// (khớp provider CometAPI/Runware) — không khoe model chưa tích hợp như đã có.
const GROUPS: { cat: string; note: string; models: { n: string; tag?: "hot" | "soon" }[] }[] = [
  { cat: "Video", note: "chữ/ảnh → clip", models: [{ n: "Seedance 2.5", tag: "soon" }, { n: "Seedance 2.0" }, { n: "Kling 3.0" }, { n: "Veo 3.1" }, { n: "Wan 2.6" }, { n: "Hailuo" }] },
  { cat: "Ảnh", note: "KOL + sản phẩm", models: [{ n: "FLUX.2" }, { n: "Seedream 5" }, { n: "Nano-Banana", tag: "hot" }, { n: "Ideogram" }] },
  { cat: "Mặt nói bán hàng", note: "ảnh + giọng → nói", models: [{ n: "OmniHuman 1.5", tag: "hot" }, { n: "Kling Avatar 2.0" }] },
  { cat: "Khoá mặt KOL", note: "1 gương mặt nhất quán", models: [{ n: "InstantID" }, { n: "PuLID" }, { n: "DreamO" }] },
  { cat: "Giọng Việt", note: "đọc tự nhiên, cảm xúc", models: [{ n: "VieNeu-TTS" }, { n: "Fish Audio" }] },
];

// Đếm THẬT từ dữ liệu — số hiển thị không bao giờ lệch danh sách (trước để cứng "10+").
const MODEL_COUNT = GROUPS.reduce((s, g) => s + g.models.length, 0);

export function ModelWall() {
  return (
    <section className="relative overflow-hidden py-20 lg:py-28">
      {/* Nền cinematic + scrim tan xuống bg-base + 1 vầng glow (đúng luật 1 glow/màn).
          Ảnh chỉ hiện mờ ở đỉnh → tạo chiều sâu, KHÔNG đè lên thẻ phía dưới. */}
      <div className="pointer-events-none absolute inset-0 -z-10">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="/showcase/v2/genre-storyteller-window.jpg"
          alt=""
          className="h-full w-full object-cover object-top opacity-[0.16]"
        />
        <div className="absolute inset-0 bg-gradient-to-b from-bg-base/70 via-bg-base/92 to-bg-base" />
        <div className="glow-radial absolute left-1/2 top-[-6rem] h-[520px] w-[860px] -translate-x-1/2 opacity-70" />
      </div>

      <div className="mx-auto max-w-[1600px] px-4">
        {/* HEADER — căn giữa, nâng tầm: eyebrow + tiêu đề lớn (italic thật, hết cắt chữ) + dẫn */}
        <Reveal>
          <div className="mx-auto max-w-3xl text-center">
            <FilmLabel className="justify-center">Tổng hợp nhiều model AI hàng đầu</FilmLabel>
            <h2 className="mt-4 font-display text-[clamp(2rem,5vw,3.4rem)] font-bold leading-[1.12] tracking-tight text-ink-high">
              Một tài khoản. <span className="text-gradient italic">Mọi model AI xịn nhất.</span>
            </h2>
            <p className="mx-auto mt-4 max-w-xl text-base leading-relaxed text-ink-medium">
              Vyra gom {MODEL_COUNT} model hàng đầu thế giới vào một chỗ và tự chọn cái tốt + rẻ cho
              từng việc. Bạn khỏi cần nhiều tài khoản nước ngoài, khỏi thẻ Visa, khỏi rành kỹ thuật.
            </p>
          </div>
        </Reveal>

        <div className="mt-12 grid gap-4 lg:grid-cols-3">
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

        {/* Lưới model theo nhóm — mỗi nhóm 1 thẻ, chip model + hover */}
        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          {GROUPS.map((g, i) => (
            <Reveal key={g.cat} delay={0.03 * i}>
              <div className="group h-full rounded-2xl glass-bordered p-4 transition-colors hover:border-violet-400/25">
                <div className="font-display text-sm font-bold text-ink-high">{g.cat}</div>
                <div className="text-[11px] text-ink-low">{g.note}</div>
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {g.models.map((m) => (
                    <span
                      key={m.n}
                      className={
                        "rounded-lg border px-2 py-0.5 text-[11px] transition-colors " +
                        (m.tag === "soon"
                          ? "border-violet-400/40 bg-violet-500/10 text-violet-200"
                          : m.tag === "hot"
                            ? "border-amber-400/30 bg-amber-500/10 text-amber-200"
                            : "border-white/10 bg-white/[0.03] text-ink-medium group-hover:border-white/20")
                      }
                    >
                      {m.n}{m.tag === "soon" ? " · sắp" : m.tag === "hot" ? " · hot" : ""}
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
