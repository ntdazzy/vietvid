import { cn } from "@/lib/utils/cn";

/** Skeleton shimmer (violet sweep) — loading khắp app (mục C). */
export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-lg bg-white/[0.05]",
        "after:absolute after:inset-0 after:-translate-x-full after:animate-shimmer",
        "after:bg-gradient-to-r after:from-transparent after:via-violet-500/10 after:to-transparent",
        className,
      )}
    />
  );
}
