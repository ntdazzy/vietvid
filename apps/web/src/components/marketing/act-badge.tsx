import { cn } from "@/lib/utils/cn";

export type Tone = "core" | "moat" | "hot" | "new";

// Badge cho act/capability — Badge UI thật không có các tone này nên tự dựng pill màu.
const TONE: Record<Tone, string> = {
  core: "bg-info/15 text-info ring-1 ring-info/30",
  moat: "bg-grad-brand text-white shadow-glow-sm",
  hot: "bg-danger/15 text-danger ring-1 ring-danger/30",
  new: "bg-violet-500/15 text-violet-300 ring-1 ring-violet-400/30",
};

export function ActBadge({ tone, label, className }: { tone: Tone; label: string; className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide",
        TONE[tone],
        className,
      )}
    >
      {label}
    </span>
  );
}
