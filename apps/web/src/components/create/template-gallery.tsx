"use client";

import { useQuery } from "@tanstack/react-query";
import { MessageSquareQuote, Shirt, Megaphone, Type, Plus, Sparkles, type LucideIcon } from "lucide-react";
import { api } from "@/lib/api/endpoints";
import type { Template } from "@/lib/api/types";
import { Skeleton } from "@/components/ui/skeleton";
import { Reveal } from "@/components/marketing/reveal";
import { cn } from "@/lib/utils/cn";

// nhãn category → icon. KHÔNG có thumbnail thật (thumbnail_url="") → dùng iconography, không ảnh giả.
const CAT_ICON: Record<string, LucideIcon> = {
  review: MessageSquareQuote,
  lookbook: Shirt,
  product_ad: Megaphone,
  text_to_video: Type,
};

/** Moment 0 — cửa trước: chọn mẫu có sẵn để bắt đầu nhanh, hoặc dựng từ đầu. */
export function TemplateGallery({ onPick }: { onPick: (t: Template | null) => void }) {
  const templates = useQuery({ queryKey: ["templates"], queryFn: api.templates });

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
      {/* dựng từ đầu — sức nặng khác: viền gradient + nền brand đậm hơn */}
      <Reveal>
        <button
          type="button"
          onClick={() => onPick(null)}
          aria-label="Dựng video từ đầu"
          className="group relative flex aspect-[3/4] w-full flex-col justify-between overflow-hidden rounded-xl glass-bordered p-4 text-left transition-transform hover:-translate-y-0.5"
        >
          <div className="pointer-events-none absolute inset-0 bg-grad-brand opacity-[0.12] transition-opacity group-hover:opacity-20" />
          <span className="relative grid h-11 w-11 place-items-center rounded-xl bg-grad-brand text-white shadow-glow-sm">
            <Plus className="h-5 w-5" />
          </span>
          <div className="relative">
            <div className="font-display text-sm font-semibold text-ink-high">Dựng từ đầu</div>
            <div className="mt-1 text-xs text-ink-low">Tự chọn mọi thứ từ trắng.</div>
          </div>
        </button>
      </Reveal>

      {templates.isLoading
        ? Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="aspect-[3/4] w-full rounded-xl" />
          ))
        : (templates.data ?? []).map((t, i) => {
            const Icon = CAT_ICON[t.category] ?? Sparkles;
            return (
              <Reveal key={t.id} delay={0.05 * (i + 1)}>
                <button
                  type="button"
                  onClick={() => onPick(t)}
                  aria-label={`Dùng mẫu ${t.name}`}
                  className={cn(
                    "group relative flex aspect-[3/4] w-full flex-col justify-between overflow-hidden rounded-xl border border-white/[0.08] glass p-4 text-left transition-transform hover:-translate-y-0.5 hover:border-violet-500/40",
                  )}
                >
                  <div className="pointer-events-none absolute inset-0 bg-grad-brand-soft opacity-0 transition-opacity group-hover:opacity-100" />
                  {/* motif khung video nghiêng — gợi "video-ness" mà không cần ảnh */}
                  <span className="pointer-events-none absolute -right-2 top-4 h-16 w-10 rotate-12 rounded-md border border-violet-400/15" />
                  <span className="relative grid h-11 w-11 place-items-center rounded-xl bg-grad-brand-soft text-violet-300">
                    <Icon className="h-5 w-5" />
                  </span>
                  <div className="relative">
                    <div className="font-display text-sm font-semibold text-ink-high">{t.name}</div>
                    <div className="mt-1 line-clamp-2 text-xs text-ink-low">{t.description}</div>
                  </div>
                </button>
              </Reveal>
            );
          })}
    </div>
  );
}
