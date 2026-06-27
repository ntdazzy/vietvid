"use client";

import { Check } from "lucide-react";
import { cn } from "@/lib/utils/cn";
import type { WizardStep } from "@/store/wizard";

const STEPS = ["Nguồn", "Phong cách", "Giọng", "Xem trước", "Tạo"];

export function Stepper({ step }: { step: WizardStep }) {
  return (
    <ol className="flex items-center gap-2">
      {STEPS.map((label, i) => {
        const n = (i + 1) as WizardStep;
        const done = n < step;
        const active = n === step;
        return (
          <li key={label} className="flex flex-1 items-center gap-2">
            <div className="flex items-center gap-2">
              <span
                className={cn(
                  "grid h-8 w-8 shrink-0 place-items-center rounded-full text-sm font-medium transition-colors",
                  done && "bg-grad-brand text-white",
                  active && "border border-violet-500/60 bg-violet-500/15 text-violet-200 shadow-glow-sm",
                  !done && !active && "border border-white/10 text-ink-low",
                )}
              >
                {done ? <Check className="h-4 w-4" /> : n}
              </span>
              <span
                className={cn(
                  "hidden text-sm sm:block",
                  active ? "text-ink-high" : "text-ink-low",
                )}
              >
                {label}
              </span>
            </div>
            {i < STEPS.length - 1 && (
              <span className={cn("h-px flex-1", done ? "bg-violet-500/50" : "bg-white/10")} />
            )}
          </li>
        );
      })}
    </ol>
  );
}
