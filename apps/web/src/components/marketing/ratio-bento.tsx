import { Reveal } from "@/components/marketing/reveal";

// Cùng engine, 3 tỉ lệ. MỖI ô dùng ảnh ĐÚNG hướng khung (dọc/vuông/ngang) nên không méo/cắt hỏng.
const TILES = [
  { src: "/samples/fashion-v2.jpg", ratio: "9:16", aspect: "aspect-[9/16]", label: "Dọc · TikTok/Reels" },
  { src: "/samples/food.jpg", ratio: "1:1", aspect: "aspect-square", label: "Vuông · Feed" },
  { src: "/showcase/affiliate-w.jpg", ratio: "16:9", aspect: "aspect-video", label: "Ngang · YouTube" },
];

export function RatioBento() {
  return (
    <div className="grid gap-4 sm:grid-cols-3">
      {TILES.map((t, i) => (
        <Reveal key={t.src} delay={0.08 * i}>
          <div className={`group relative overflow-hidden rounded-[18px] ring-1 ring-white/[0.06] ${t.aspect}`}>
            <span className="absolute left-2.5 top-2.5 z-10 rounded-md bg-black/55 px-1.5 py-0.5 font-numeric text-[10px] font-semibold text-white/90 backdrop-blur-sm">
              {t.ratio}
            </span>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={t.src}
              alt={t.label}
              className="h-full w-full object-cover object-center transition-transform duration-700 group-hover:scale-105"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/70 to-transparent" />
            <span className="absolute inset-x-0 bottom-0 p-3 text-sm font-semibold text-white/95">{t.label}</span>
          </div>
        </Reveal>
      ))}
    </div>
  );
}
