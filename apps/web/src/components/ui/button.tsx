"use client";

import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils/cn";

const button = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-xl text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/60 focus-visible:ring-offset-2 focus-visible:ring-offset-bg-base disabled:pointer-events-none disabled:opacity-50 disabled:text-ink-disabled select-none",
  {
    variants: {
      variant: {
        // CTA chính — gradient brand + glow phát-từ-nội-dung (mục A pattern 3)
        primary:
          "bg-grad-brand text-white shadow-[0_0_0_1px_rgba(124,77,255,.5),0_8px_40px_-8px_rgba(99,102,241,.55)] hover:shadow-glow-md hover:brightness-110 active:scale-[.98]",
        // phụ — kính mờ
        glass:
          "glass text-ink-high hover:bg-white/[0.08] hover:border-white/[0.16] active:scale-[.98]",
        ghost: "text-ink-medium hover:text-ink-high hover:bg-white/[0.05]",
        outline:
          "border border-white/[0.12] text-ink-high hover:border-violet-500/50 hover:shadow-glow-sm active:scale-[.98]",
      },
      size: {
        sm: "h-9 px-4 text-[13px]",
        md: "h-11 px-5",
        lg: "h-13 px-7 text-base rounded-2xl h-[3.25rem]",
      },
    },
    defaultVariants: { variant: "primary", size: "md" },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof button> {}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => (
    <button ref={ref} className={cn(button({ variant, size }), className)} {...props} />
  ),
);
Button.displayName = "Button";
