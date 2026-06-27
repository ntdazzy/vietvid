import { cn } from "@/lib/utils/cn";

/** Số credit/giá — mono tabular để số KHÔNG nhảy khi update (mục A pattern 11). */
export function CreditValue({
  value,
  className,
  prefix,
  suffix = "credit",
}: {
  value: number;
  className?: string;
  prefix?: string;
  suffix?: string | null;
}) {
  return (
    <span className={cn("font-numeric tabular tracking-tight", className)}>
      {prefix}
      {value.toLocaleString("vi-VN")}
      {suffix ? <span className="ml-1 text-[0.7em] font-sans text-ink-low">{suffix}</span> : null}
    </span>
  );
}
