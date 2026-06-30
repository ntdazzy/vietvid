"use client";

import { useRef, useState, type ReactNode } from "react";
import { cn } from "@/lib/utils/cn";

/**
 * Ảnh tĩnh → rê chuột vào thì clip chạy (live portrait), rời chuột thì dừng.
 * Video chỉ tải khi hover (preload none) nên không nặng trang. Có video mới chạy,
 * không có thì chỉ là ảnh. `children` (overlay) phủ lên trên, vùng hover trùm cả thẻ.
 */
export function HoverVideo({
  poster,
  video,
  alt,
  className,
  children,
  badge = true,
}: {
  poster: string;
  video?: string;
  alt: string;
  className?: string;
  children?: ReactNode;
  /** Huy hiệu ▶ góc phải-trên báo "rê để xem clip". Tắt khi thẻ đã có nút ở góc đó. */
  badge?: boolean;
}) {
  const ref = useRef<HTMLVideoElement>(null);
  const [playing, setPlaying] = useState(false);

  function onEnter() {
    const v = ref.current;
    if (v) v.play().catch(() => {});
  }
  function onLeave() {
    const v = ref.current;
    if (v) {
      v.pause();
      v.currentTime = 0;
    }
  }

  return (
    <div className={cn("relative overflow-hidden", className)} onMouseEnter={onEnter} onMouseLeave={onLeave}>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={poster} alt={alt} className="h-full w-full object-cover" />
      {video && (
        <video
          ref={ref}
          src={video}
          poster={poster}
          muted
          loop
          playsInline
          preload="none"
          onPlaying={() => setPlaying(true)}
          onPause={() => setPlaying(false)}
          className={cn(
            "absolute inset-0 h-full w-full object-cover transition-opacity duration-300",
            playing ? "opacity-100" : "opacity-0",
          )}
        />
      )}
      {video && badge && (
        <span className="pointer-events-none absolute right-2 top-2 grid h-6 w-6 place-items-center rounded-full bg-black/45 backdrop-blur-sm">
          <span className="block h-0 w-0 border-y-[5px] border-l-[8px] border-y-transparent border-l-white/90" />
        </span>
      )}
      {children}
    </div>
  );
}
