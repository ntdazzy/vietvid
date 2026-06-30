"use client";

import Link from "next/link";
import { FilmLabel } from "@/components/ui/cinematic";
import { Reveal } from "@/components/marketing/reveal";
import { HoverVideo } from "@/components/ui/hover-video";

// "Một studio, MỌI thể loại" — 11 clip THẬT v2 (Seedance) trải mọi ngành nội dung. Tỉ lệ khớp ô:
// clip DỌC 9:16 → ô CAO (row-span-2); clip NGANG 16:9 → ô RỘNG (col-span-2). grid-flow-dense lấp kín.
// Poster = frame của chính clip → rê chuột chạy clip khớp 100%. Hardcode nhãn Việt (Vyra = Việt-first).
const GENRES: { key: string; label: string; note: string; wide?: boolean }[] = [
  { key: "genre-travel-broll-traveler", label: "Du lịch · b-roll", note: "cảnh đẹp, không cần quay", wide: true },
  { key: "genre-cafe-streetfood-eating", label: "Ẩm thực đường phố", note: "review món, lên trend" },
  { key: "genre-street-fashion-walk", label: "Thời trang đường phố", note: "lookbook, sải bước" },
  { key: "genre-cozy-cafe-latte-broll", label: "Cà phê · quán xá", note: "b-roll ấm, mood chậm", wide: true },
  { key: "genre-home-cooking-pov", label: "Nấu ăn POV", note: "góc nhìn thứ nhất" },
  { key: "genre-shortfilm-rainy-car-night", label: "Phim ngắn · Mood", note: "kể chuyện điện ảnh", wide: true },
  { key: "genre-cute-pet-no-person", label: "Thú cưng", note: "không cần người, vẫn viral" },
  { key: "genre-storyteller-window", label: "Kể chuyện", note: "tâm sự, đời thường" },
  { key: "genre-real-estate-walkthrough", label: "Bất động sản", note: "dẫn tour căn hộ", wide: true },
  { key: "genre-mom-baby-tender", label: "Mẹ & Bé", note: "ấm áp, chân thật" },
];

export function GenreWall() {
  return (
    <section className="mx-auto max-w-[1600px] px-4 py-20 lg:py-24">
      <Reveal>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div className="max-w-xl">
            <FilmLabel>Mọi thể loại nội dung</FilmLabel>
            <h2 className="mt-3 font-display text-[clamp(1.75rem,4vw,2.6rem)] font-bold leading-[1.08] tracking-tight text-ink-high">
              Một studio. <span className="text-gradient italic">Mọi thể loại video.</span>
            </h2>
          </div>
          <p className="max-w-xs text-sm text-ink-low sm:text-right">
            Ẩm thực, du lịch, thời trang, fitness, phim ngắn, thú cưng, bất động sản... Rê chuột để xem clip thật chạy.
          </p>
        </div>
      </Reveal>

      <div className="mt-9 grid auto-rows-[150px] grid-flow-dense grid-cols-2 gap-3 sm:auto-rows-[168px] sm:grid-cols-4 lg:auto-rows-[200px] lg:grid-cols-4 lg:gap-4">
        {GENRES.map((g, i) => {
          const src = `/showcase/v2/${g.key}`;
          return (
            <Reveal key={g.key} delay={0.03 * i} className={g.wide ? "col-span-2" : "row-span-2"}>
              <Link
                href="/login"
                className="group relative block h-full overflow-hidden rounded-2xl glass-bordered transition-all duration-200 hover:-translate-y-1 hover:ring-1 hover:ring-violet-400/30"
              >
                <HoverVideo
                  poster={`${src}.jpg`}
                  video={`${src}.mp4`}
                  alt={g.label}
                  badge={false}
                  objectClass="object-center"
                  className="absolute inset-0 h-full w-full opacity-[0.9] transition-opacity duration-500 group-hover:opacity-100"
                />
                <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-bg-base via-bg-base/25 to-transparent" />
                <div className="pointer-events-none absolute inset-x-0 bottom-0 p-3.5">
                  <div className="font-display text-sm font-semibold leading-tight text-ink-high">{g.label}</div>
                  <div className="mt-0.5 text-[11px] text-ink-low">{g.note}</div>
                </div>
                <span className="pointer-events-none absolute right-2.5 top-2.5 grid h-6 w-6 place-items-center rounded-full bg-black/40 opacity-0 backdrop-blur-sm transition-opacity group-hover:opacity-100">
                  <span className="ml-0.5 block h-0 w-0 border-y-[5px] border-l-[8px] border-y-transparent border-l-white/90" />
                </span>
              </Link>
            </Reveal>
          );
        })}
      </div>
    </section>
  );
}
