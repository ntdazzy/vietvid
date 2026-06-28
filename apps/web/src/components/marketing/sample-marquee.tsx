"use client";

import { DemoTile } from "@/components/marketing/demo-tile";
import { cn } from "@/lib/utils/cn";

export type MarqueeTile = { file: string; label: string; ratio?: string };

const MASK = {
  maskImage: "linear-gradient(to right, transparent, #000 6%, #000 94%, transparent)",
  WebkitMaskImage: "linear-gradient(to right, transparent, #000 6%, #000 94%, transparent)",
} as const;

// Full-bleed marquee các mẫu output THẬT (PNG). Track nhân đôi → loop liền.
export function SampleMarquee({
  tiles,
  direction = "left",
}: {
  tiles: MarqueeTile[];
  direction?: "left" | "right";
}) {
  const doubled = [...tiles, ...tiles];
  return (
    <div className="relative left-1/2 right-1/2 -mx-[50vw] w-screen overflow-hidden" style={MASK}>
      {/* mr-4 trên TỪNG tile (không dùng flex gap) → track nhân đôi rộng đúng 2× → -50% loop liền,
         không bị "nửa khe" ở điểm nối. */}
      <div
        className={cn(
          "flex w-max hover:[animation-play-state:paused]",
          direction === "right" ? "animate-marquee-rev" : "animate-marquee",
        )}
      >
        {doubled.map((t, i) => (
          <div key={`${t.file}-${i}`} className="relative mr-4 h-[300px] shrink-0 sm:h-[380px]">
            <span className="absolute left-2.5 top-2.5 z-10 rounded-md bg-black/55 px-1.5 py-0.5 font-numeric text-[10px] font-semibold text-white/90 backdrop-blur-sm">
              {t.ratio ?? "9:16"}
            </span>
            <DemoTile
              poster={`/samples/${t.file}.png`}
              label={t.label}
              className="h-full w-auto aspect-[9/16]"
            />
          </div>
        ))}
      </div>
    </div>
  );
}
