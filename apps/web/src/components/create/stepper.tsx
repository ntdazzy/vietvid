"use client";

import { useTranslations } from "next-intl";
import { Check, LayoutTemplate, RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { ACCENTS, type Accent } from "@/lib/accents";
import type { WizardStep } from "@/store/wizard";

const STEP_KEYS = ["stepSource", "stepStyle", "stepVoice", "stepPreview", "stepCreate"] as const;

export function Stepper({
  step,
  templateName,
  onChangeTemplate,
  accent = "violet",
}: {
  step: WizardStep;
  templateName?: string;
  onChangeTemplate?: () => void;
  accent?: Accent;
}) {
  const t = useTranslations("create");
  const a = ACCENTS[accent];
  const labels = STEP_KEYS.map((k) => t(k));
  return (
    <div>
      {templateName && (
        <button
          type="button"
          onClick={onChangeTemplate}
          className="mb-3 inline-flex items-center gap-1.5 rounded-full border border-violet-400/25 bg-violet-500/[0.08] px-3 py-1 text-xs text-violet-200 transition-colors hover:border-violet-400/50"
        >
          <LayoutTemplate className="h-3.5 w-3.5" /> {t("templatePrefix")} <span className="font-medium text-ink-high">{templateName}</span>
          <span className="mx-0.5 text-violet-400/50">·</span>
          <RefreshCw className="h-3 w-3" /> {t("change")}
        </button>
      )}
      <ol className="flex items-center gap-2">
      {labels.map((label, i) => {
        const n = (i + 1) as WizardStep;
        const done = n < step;
        const active = n === step;
        return (
          <li key={label} className="flex flex-1 items-center gap-2">
            <div className="flex items-center gap-2">
              <span
                className={cn(
                  "grid h-8 w-8 shrink-0 place-items-center rounded-full text-sm font-medium transition-colors",
                  done && cn("bg-gradient-to-br text-white", a.grad),
                  active && cn("border shadow-glow-sm", a.chip),
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
            {i < labels.length - 1 && (
              <span className={cn("h-px flex-1", done ? a.bar : "bg-white/10")} />
            )}
          </li>
        );
      })}
      </ol>
      {/* mobile: tên bước hiện tại (label desktop bị ẩn) */}
      <p className="mt-2 text-center text-xs font-medium text-ink-medium sm:hidden">
        {t("stepProgress", { step, total: labels.length, label: labels[step - 1] })}
      </p>
    </div>
  );
}
