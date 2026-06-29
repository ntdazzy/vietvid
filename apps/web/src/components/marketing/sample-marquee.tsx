"use client";

import { DemoTile } from "@/components/marketing/demo-tile";
import { cn } from "@/lib/utils/cn";

export type MarqueeTile = { file: string; label: string; ratio?: string };

const MASK = {
  maskImage: "linear-gradient(to right, transparent, #000 5%, #000 95%, transparent)",
  WebkitMaskImage: "linear-gradient(to right, transparent, #000 5%, #000 95%, transparent)",
} as const;

// Full-bleed marquee các mẫu output THẬT. Mỗi NỬA track phải rộng hơn viewport thì -50% mới
// loop liền vô tận (không lộ khoảng trống). 5 tile/lần lặp ~1.1k px → lặp 3 lần/nửa (~3.4k px)
// phủ mọi màn, rồi nhân đôi nửa → cả track 6 lần. Tốc độ cố định theo số tile (không phụ thuộc cỡ).
export function SampleMarquee({
  tiles,
  direction = "left",
}: {
  tiles: MarqueeTile[];
  direction?: "left" | "right";
}) {
  const half = [...tiles, ...tiles, ...tiles]; // 1 nửa: đủ rộng hơn viewport
  const track = [...half, ...half]; // cả track = 2 nửa → animate -50% liền mạch
  const durationS = half.length * 4.5; // px/giây cố định → tốc độ trôi đều

  return (
    <div className="relative left-1/2 right-1/2 -mx-[50vw] w-screen overflow-hidden" style={MASK}>
      <div
        className={cn(
          "flex w-max will-change-transform hover:[animation-play-state:paused]",
          direction === "right" ? "animate-marquee-rev" : "animate-marquee",
        )}
        style={{ animationDuration: `${durationS}s` }}
      >
        {track.map((t, i) => (
          <div key={`${t.file}-${i}`} className="relative mr-4 h-[300px] shrink-0 sm:h-[380px]">
            <span className="absolute left-2.5 top-2.5 z-10 rounded-md bg-black/55 px-1.5 py-0.5 font-numeric text-[10px] font-semibold text-white/90 backdrop-blur-sm">
              {t.ratio ?? "9:16"}
            </span>
            <DemoTile
              poster={`/samples/${t.file}.jpg`}
              video={`/samples/${t.file}.mp4`}
              hoverOnly
              label={t.label}
              className="h-full w-auto aspect-[9/16]"
            />
          </div>
        ))}
      </div>
    </div>
  );
}
