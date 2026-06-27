import { cn } from "@/lib/utils/cn";

/** Logo VietVid — dấu play hình tam-giác-trong-khung-phim + wordmark gradient. */
export function Logo({ className, showWord = true }: { className?: string; showWord?: boolean }) {
  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <span className="relative grid h-8 w-8 place-items-center rounded-lg bg-grad-brand shadow-glow-sm">
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden>
          <path d="M3 2.5L11 7L3 11.5V2.5Z" fill="white" />
        </svg>
      </span>
      {showWord && (
        <span className="font-display text-[17px] font-extrabold tracking-tight text-ink-high">
          Viet<span className="text-gradient">Vid</span>
        </span>
      )}
    </span>
  );
}
