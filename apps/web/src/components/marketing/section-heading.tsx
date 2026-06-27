import type { ReactNode } from "react";
import { cn } from "@/lib/utils/cn";
import { Reveal } from "./reveal";

/** Heading section tái dùng: eyebrow (uppercase) + H2 + sub. Mặc định canh trái. */
export function SectionHeading({
  eyebrow,
  title,
  sub,
  align = "left",
  className,
}: {
  eyebrow?: string;
  title: ReactNode;
  sub?: ReactNode;
  align?: "left" | "center";
  className?: string;
}) {
  return (
    <Reveal
      className={cn(
        align === "center" ? "mx-auto max-w-3xl text-center" : "max-w-2xl",
        className,
      )}
    >
      {eyebrow && (
        <span className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-300">
          {eyebrow}
        </span>
      )}
      <h2 className="mt-2 font-display text-[clamp(1.75rem,4vw,2.75rem)] font-bold leading-[1.08] tracking-tight text-ink-high">
        {title}
      </h2>
      {sub && <p className="mt-4 text-ink-medium">{sub}</p>}
    </Reveal>
  );
}
