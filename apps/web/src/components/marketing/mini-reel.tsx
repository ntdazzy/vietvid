"use client";

import { useEffect, useRef, useState } from "react";
import { useReducedMotion } from "framer-motion";
import { cn } from "@/lib/utils/cn";

// "Động-trong-khung": ảnh output THẬT + Ken-Burns + caption Việt tự GÕ ra trên ảnh.
// Giải đúng điểm user chê "nhiều ảnh tĩnh" — chính khung sản phẩm cũng chuyển động.
// Có prop `video?` → khi engine bật key, thả mp4 vào là tự thành video thật.
export function MiniReel({
  poster,
  captions,
  video,
  className,
}: {
  poster: string;
  captions: string[];
  video?: string;
  className?: string;
}) {
  const reduce = useReducedMotion();
  const ref = useRef<HTMLVideoElement>(null);
  const [idx, setIdx] = useState(0);
  const [typed, setTyped] = useState(reduce ? captions[0] : "");

  // gõ caption hiện tại → xong chờ → sang caption kế (vòng).
  useEffect(() => {
    if (reduce || video) return;
    const full = captions[idx % captions.length];
    setTyped("");
    let i = 0;
    const type = setInterval(() => {
      i += 1;
      setTyped(full.slice(0, i));
      if (i >= full.length) {
        clearInterval(type);
      }
    }, 45);
    const next = setTimeout(() => setIdx((v) => (v + 1) % captions.length), full.length * 45 + 1900);
    return () => {
      clearInterval(type);
      clearTimeout(next);
    };
  }, [idx, captions, reduce, video]);

  useEffect(() => {
    const el = ref.current;
    if (!el || !video) return;
    el.play().catch(() => {});
  }, [video]);

  return (
    <div className={cn("relative aspect-[9/16] overflow-hidden rounded-[18px] ring-1 ring-white/[0.08]", className)}>
      {video ? (
        <video ref={ref} poster={poster} src={video} muted loop playsInline preload="none" className="h-full w-full object-cover" />
      ) : (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={poster}
          alt=""
          className="h-full w-full object-cover"
          style={reduce ? undefined : { animation: "vv-kenburns 9s ease-in-out infinite alternate" }}
        />
      )}
      <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/5 to-transparent" />

      <span className="absolute left-2.5 top-2.5 rounded-md bg-black/50 px-1.5 py-0.5 text-[10px] font-medium text-white/70 backdrop-blur-sm">
        Bản dựng minh hoạ
      </span>

      {!video && (
        <div className="absolute inset-x-0 bottom-0 p-3.5">
          <span className="font-display text-base font-semibold text-white drop-shadow">
            {typed}
            {!reduce && <span className="caret-blink text-violet-300">▍</span>}
          </span>
        </div>
      )}
    </div>
  );
}
