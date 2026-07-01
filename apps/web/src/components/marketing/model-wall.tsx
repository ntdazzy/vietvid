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

export function ModelWall() {
  return (
    <section className="mx-auto max-w-[1600px] px-4 py-16 lg:py-20">
      <Reveal>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div className="max-w-xl">
            <FilmLabel>Tổng hợp nhiều model AI hàng đầu</FilmLabel>
            <h2 className="mt-3 font-display text-[clamp(1.75rem,4vw,2.6rem)] font-bold leading-[1.08] tracking-tight text-ink-high">
              Một tài khoản. <span className="text-gradient italic">Mọi model AI xịn nhất.</span>
            </h2>
          </div>
          <p className="max-w-xs text-sm text-ink-low sm:text-right">
            Vyra tự chọn model tốt + rẻ cho từng việc. Bạn khỏi cần nhiều tài khoản, khỏi rành kỹ thuật.
          </p>
        </div>
      </Reveal>

      <div className="mt-9 grid gap-4 lg:grid-cols-3">
        {/* SPOTLIGHT Seedance 2.5 — ảnh nền cinematic + hover glow, chiếm 2/3 */}
        <Reveal className="lg:col-span-2">
          <div className="group relative h-full min-h-[280px] overflow-hidden rounded-3xl border border-white/[0.08]">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="/showcase/v2/genre-shortfilm-rainy-car-night.jpg"
              alt=""
              className="absolute inset-0 h-full w-full object-cover opacity-45 transition-all duration-700 group-hover:scale-105 group-hover:opacity-60"
            />
            <div className="absolute inset-0 bg-gradient-to-tr from-bg-base via-bg-base/70 to-violet-950/30" />
            <div className="glow-radial pointer-events-none absolute -right-16 -top-16 h-72 w-72 opacity-0 transition-opacity duration-700 group-hover:opacity-70" />
            <div className="relative flex h-full flex-col justify-end p-7 lg:p-9">
              <span className="mb-3 inline-flex w-fit items-center gap-1.5 rounded-full border border-violet-400/40 bg-violet-500/15 px-3 py-1 text-[11px] font-semibold text-violet-200">
                <span className="h-1.5 w-1.5 rounded-full bg-violet-300" /> SẮP RA MẮT
              </span>
              <h3 className="font-display text-[clamp(1.8rem,3.5vw,2.8rem)] font-bold leading-none text-ink-high">
                Seedance <span className="text-gradient">2.5</span>
              </h3>
              <p className="mt-3 max-w-md text-sm leading-relaxed text-ink-medium">
                Model video thế hệ mới — người thật hơn, chuyển động mượt hơn, bám prompt sát hơn.
                Vyra tích hợp ngay khi ra mắt; bạn không phải đổi công cụ.
              </p>
            </div>
          </div>
        </Reveal>

        {/* Card phụ — chốt thông điệp "1 nơi" */}
        <Reveal delay={0.06}>
          <div className="flex h-full flex-col justify-between gap-4 rounded-3xl glass-bordered p-7">
            <div>
              <div className="font-numeric text-5xl font-bold text-gradient">10+</div>
              <div className="mt-1 text-sm text-ink-medium">model AI hàng đầu, 1 tài khoản Vyra</div>
            </div>
            <ul className="flex flex-col gap-2 text-sm text-ink-low">
              <li className="flex items-center gap-2"><span className="h-1 w-1 rounded-full bg-violet-400" /> Không cần nhiều tài khoản nước ngoài</li>
              <li className="flex items-center gap-2"><span className="h-1 w-1 rounded-full bg-violet-400" /> Tự chọn model rẻ nhất cho từng việc</li>
              <li className="flex items-center gap-2"><span className="h-1 w-1 rounded-full bg-violet-400" /> Trả bằng MoMo / chuyển khoản VND</li>
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
    </section>
  );
}
