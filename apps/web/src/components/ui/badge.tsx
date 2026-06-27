import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils/cn";

const badge = cva(
  "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-medium tracking-wide",
  {
    variants: {
      tone: {
        neutral: "bg-white/[0.06] text-ink-medium border border-white/[0.08]",
        brand: "bg-violet-500/14 text-violet-300 border border-violet-500/30",
        hold: "bg-hold/[0.12] text-hold border border-hold/30",
        success: "bg-success/[0.12] text-success border border-success/30",
        refund: "bg-refund/[0.12] text-refund border border-refund/30",
        danger: "bg-danger/[0.12] text-danger border border-danger/30",
      },
    },
    defaultVariants: { tone: "neutral" },
  },
);

export function Badge({
  className,
  tone,
  ...props
}: React.HTMLAttributes<HTMLSpanElement> & VariantProps<typeof badge>) {
  return <span className={cn(badge({ tone }), className)} {...props} />;
}
