import * as React from "react";
import { cn } from "@/lib/utils/cn";

/** Card kính mờ chuẩn toàn app (mục A pattern 6). `bordered` = viền-gradient sáng. */
export function GlassCard({
  className,
  bordered = false,
  ...props
}: React.HTMLAttributes<HTMLDivElement> & { bordered?: boolean }) {
  return (
    <div
      className={cn(
        bordered ? "glass-bordered" : "glass rounded-xl",
        "p-5",
        className,
      )}
      {...props}
    />
  );
}
