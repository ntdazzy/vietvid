import { cn } from "@/lib/utils/cn";

/** Mark Vyra — chữ V + vòng "aura" (lan toả/viral) + điểm tín hiệu (vòng-lặp-bản-thắng).
 * Stroke-based để vẽ-dần được trong intro (gắn `animated` → class cho keyframe draw-on). */
export function VyraMark({ className, animated = false }: { className?: string; animated?: boolean }) {
  return (
    <svg viewBox="0 0 40 40" fill="none" className={className} aria-hidden>
      <defs>
        <linearGradient id="vyra-grad" x1="2" y1="4" x2="38" y2="36" gradientUnits="userSpaceOnUse">
          <stop stopColor="#7C4DFF" />
          <stop offset="0.5" stopColor="#6366F1" />
          <stop offset="1" stopColor="#3B82F6" />
        </linearGradient>
      </defs>
      {/* vòng aura */}
      <circle
        cx="20" cy="19.5" r="14.5"
        stroke="url(#vyra-grad)" strokeWidth="1.6" opacity="0.4"
        className={animated ? "vyra-orbit" : undefined}
      />
      {/* chữ V */}
      <path
        d="M10 10 L20 28 L30 10"
        stroke="url(#vyra-grad)" strokeWidth="4.2" strokeLinecap="round" strokeLinejoin="round"
        className={animated ? "vyra-stroke" : undefined}
      />
      {/* điểm tín hiệu (aura node) */}
      <circle cx="32.5" cy="9" r="3" fill="url(#vyra-grad)" className={animated ? "vyra-node" : undefined} />
    </svg>
  );
}

/** Logo Vyra — mark + wordmark. `size`: md (mặc định) | lg (to hơn, dùng ở login). */
export function Logo({
  className,
  showWord = true,
  size = "md",
}: {
  className?: string;
  showWord?: boolean;
  size?: "md" | "lg";
}) {
  const mark = size === "lg" ? "h-11 w-11" : "h-8 w-8";
  const word = size === "lg" ? "text-2xl" : "text-[19px]";
  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <VyraMark className={cn(mark, "drop-shadow-[0_0_10px_rgba(124,77,255,0.35)]")} />
      {showWord && (
        <span className={cn("font-display font-extrabold tracking-tight text-ink-high", word)}>
          Vyra
        </span>
      )}
    </span>
  );
}
