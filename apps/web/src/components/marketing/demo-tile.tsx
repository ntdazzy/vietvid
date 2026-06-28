"use client";

import { useEffect, useRef } from "react";
import { cn } from "@/lib/utils/cn";

/**
 * Thẻ demo video-first: nếu có `video` (mp4) → tự chạy muted khi lọt khung / hover (không nút play
 * tròn — đó là dấu hiệu "AI-generic"). Chưa có mp4 thật → hiện poster (ảnh output thật) + Ken-Burns
 * nhẹ. Khi engine render thật, thả /samples/<x>.mp4 vào là tự lên video.
 */
export function DemoTile({
  poster,
  video,
  label,
  className,
  hoverOnly = false,
}: {
  poster: string;
  video?: string;
  label: string;
  className?: string;
  hoverOnly?: boolean; // chỉ phát khi hover (cho marquee — tránh hàng chục video chạy cùng lúc)
}) {
  const ref = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el || !video || hoverOnly) return; // hoverOnly → bỏ auto-play-khi-lọt-khung
    const io = new IntersectionObserver(
      ([e]) => {
        if (e.isIntersecting) el.play().catch(() => {});
        else el.pause();
      },
      { threshold: 0.4 },
    );
    io.observe(el);
    return () => io.disconnect();
  }, [video, hoverOnly]);

  return (
    <div
      className={cn(
        "group relative overflow-hidden rounded-[20px] bg-bg-surface2 ring-1 ring-white/[0.06]",
        "transition-[transform,box-shadow] duration-500 hover:-translate-y-1",
        "hover:shadow-[0_30px_80px_-30px_rgba(124,58,237,0.45)]",
        className,
      )}
      onMouseEnter={() => video && ref.current?.play().catch(() => {})}
      onMouseLeave={() => {
        const el = ref.current;
        if (video && el) {
          el.pause();
          el.currentTime = 0; // về poster khi rời chuột
        }
      }}
    >
      {video ? (
        <video
          ref={ref}
          poster={poster}
          src={video}
          muted
          loop
          playsInline
          preload="none"
          className="h-full w-full object-cover"
        />
      ) : (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={poster}
          alt={label}
          className="h-full w-full object-cover transition-transform duration-[1400ms] ease-out group-hover:scale-[1.07]"
        />
      )}

      {/* scrim đáy + viền tím khi hover (accent sắc, không gradient mesh) */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/75 via-black/5 to-transparent" />
      <div className="pointer-events-none absolute inset-0 rounded-[20px] ring-1 ring-violet-400/0 transition duration-500 group-hover:ring-violet-400/40" />

      <div className="absolute inset-x-0 bottom-0 flex items-center justify-between p-3.5">
        <span className="text-sm font-semibold tracking-tight text-white/95">{label}</span>
        <span className="translate-y-1 text-[11px] font-medium text-violet-200 opacity-0 transition duration-300 group-hover:translate-y-0 group-hover:opacity-100">
          xem mẫu →
        </span>
      </div>
    </div>
  );
}
