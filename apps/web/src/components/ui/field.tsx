import { cn } from "@/lib/utils/cn";

export const inputCls =
  "w-full rounded-lg border border-white/10 bg-white/[0.03] px-3 py-2.5 text-sm text-ink-high placeholder:text-ink-disabled transition-colors focus:border-violet-500/50 focus:outline-none focus:ring-2 focus:ring-violet-500/25";

export function Field({
  label,
  hint,
  children,
  className,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <label className={cn("flex flex-col gap-2", className)}>
      <span className="text-sm font-medium text-ink-medium">{label}</span>
      {children}
      {hint && <span className="text-xs text-ink-low">{hint}</span>}
    </label>
  );
}

/** Hàng chip chọn-một (duration, resolution, gender...). */
export function ChipGroup<T extends string | number>({
  options,
  value,
  onChange,
}: {
  options: { value: T; label: string; sub?: string }[];
  value: T;
  onChange: (v: T) => void;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {options.map((o) => (
        <button
          key={String(o.value)}
          type="button"
          onClick={() => onChange(o.value)}
          className={cn(
            "rounded-lg border px-3.5 py-2 text-sm transition-colors active:scale-[0.98]",
            value === o.value
              ? "border-violet-500/60 bg-violet-500/15 text-ink-high shadow-glow-sm"
              : "border-white/10 text-ink-low hover:border-white/20 hover:text-ink-medium",
          )}
        >
          {o.label}
          {o.sub && <span className="ml-1.5 text-xs text-ink-low">{o.sub}</span>}
        </button>
      ))}
    </div>
  );
}
