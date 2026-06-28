"use client";

import { Check, LayoutTemplate, RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils/cn";
import type { WizardStep } from "@/store/wizard";

const STEPS = ["Nguồn", "Phong cách", "Giọng", "Xem trước", "Tạo"];

export function Stepper({
  step,
  templateName,
  onChangeTemplate,
}: {
  step: WizardStep;
  templateName?: string;
  onChangeTemplate?: () => void;
}) {
  return (
    <div>
      {templateName && (
        <button
          type="button"
          onClick={onChangeTemplate}
          className="mb-3 inline-flex items-center gap-1.5 rounded-full border border-violet-400/25 bg-violet-500/[0.08] px-3 py-1 text-xs text-violet-200 transition-colors hover:border-violet-400/50"
        >
          <LayoutTemplate className="h-3.5 w-3.5" /> Mẫu: <span className="font-medium text-ink-high">{templateName}</span>
          <span className="mx-0.5 text-violet-400/50">·</span>
          <RefreshCw className="h-3 w-3" /> Đổi
        </button>
      )}
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
      {/* mobile: tên bước hiện tại (label desktop bị ẩn) */}
      <p className="mt-2 text-center text-xs font-medium text-ink-medium sm:hidden">
        Bước {step}/{STEPS.length} · {STEPS[step - 1]}
      </p>
    </div>
  );
}
