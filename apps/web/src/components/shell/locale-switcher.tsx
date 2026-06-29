"use client";

import { useState, useTransition } from "react";
import { useLocale, useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { Globe, Check, ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils/cn";

const LOCALE_COOKIE = "NEXT_LOCALE";
const OPTIONS = ["vi", "en"] as const;

// Đổi ngôn ngữ qua cookie NEXT_LOCALE rồi router.refresh() — KHÔNG đổi URL.
export function LocaleSwitcher() {
  const router = useRouter();
  const current = useLocale();
  const t = useTranslations("locale");
  const tc = useTranslations("common");
  const [open, setOpen] = useState(false);
  const [, startTransition] = useTransition();

  const pick = (loc: (typeof OPTIONS)[number]) => {
    // 1 năm, path gốc — đồng nhất với cookie next-intl mặc định.
    document.cookie = `${LOCALE_COOKIE}=${loc}; path=/; max-age=31536000; samesite=lax`;
    setOpen(false);
    startTransition(() => router.refresh());
  };

  return (
    <div
      className="relative"
      onMouseLeave={() => setOpen(false)}
    >
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="true"
        aria-expanded={open}
        aria-label={tc("language")}
        className="flex h-9 items-center gap-1 rounded-lg px-2 text-ink-medium outline-none transition-colors hover:bg-white/[0.05] hover:text-ink-high focus-visible:ring-2 focus-visible:ring-violet-400/60"
      >
        <Globe className="h-[18px] w-[18px]" />
        <span className="hidden text-xs font-semibold uppercase sm:inline">{current}</span>
        <ChevronDown className={cn("h-3.5 w-3.5 transition-transform", open && "rotate-180")} />
      </button>

      {open && (
        <div className="absolute right-0 top-full z-50 w-40 pt-2">
          <div className="overflow-hidden rounded-xl border border-white/[0.1] bg-bg-elevated/95 backdrop-blur-2xl shadow-[0_24px_70px_-20px_rgba(0,0,0,0.8)] animate-in fade-in slide-in-from-top-1 duration-200">
            {OPTIONS.map((loc) => (
              <button
                key={loc}
                type="button"
                onClick={() => pick(loc)}
                className={cn(
                  "flex w-full items-center justify-between gap-2 px-3 py-2 text-left text-sm outline-none transition-colors hover:bg-violet-500/[0.07] focus-visible:bg-violet-500/[0.07]",
                  loc === current ? "text-ink-high" : "text-ink-medium",
                )}
              >
                {t(loc)}
                {loc === current && <Check className="h-4 w-4 text-violet-300" />}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
