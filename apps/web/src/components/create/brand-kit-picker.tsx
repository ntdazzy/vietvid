"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Star, Check, Palette } from "lucide-react";
import { useWizard } from "@/store/wizard";
import { api } from "@/lib/api/endpoints";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils/cn";

/** Chọn bộ nhận diện thương hiệu (logo/màu/watermark) — tuỳ chọn, brand_kit_id nối thẳng job. */
export function BrandKitPicker() {
  const w = useWizard();
  const kits = useQuery({ queryKey: ["brand-kits"], queryFn: api.brandKits });

  if (kits.isLoading) {
    return (
      <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-16 w-full rounded-xl" />
        ))}
      </div>
    );
  }

  if (!kits.data?.length) {
    return (
      <div className="flex items-center justify-between gap-3 rounded-xl border border-dashed border-white/12 px-4 py-3 text-sm">
        <span className="flex items-center gap-2 text-ink-low">
          <Palette className="h-4 w-4" /> Chưa có bộ nhận diện nào.
        </span>
        <Link href="/app/brand-kits" className="font-medium text-violet-300 hover:text-violet-200">
          Tạo ở Cài đặt →
        </Link>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-3">
      {kits.data.map((k) => {
        const active = w.brandKitId === k.id;
        return (
          <button
            key={k.id}
            type="button"
            onClick={() => w.patch({ brandKitId: active ? "" : k.id })}
            aria-pressed={active}
            aria-label={`Bộ nhận diện ${k.name}${active ? " (đang chọn)" : ""}`}
            className={cn(
              "relative flex items-center gap-2.5 rounded-xl border p-2.5 text-left transition-colors",
              active ? "border-violet-500/60 bg-violet-500/10 shadow-glow-sm" : "border-white/10 hover:border-white/25",
            )}
          >
            <span
              className="h-8 w-8 shrink-0 rounded-lg ring-1 ring-white/15"
              style={{ background: k.primary_color || "#7C4DFF" }}
            />
            <span className="min-w-0 flex-1">
              <span className="flex items-center gap-1 truncate text-sm font-medium text-ink-high">
                {k.name}
                {k.is_default && <Star className="h-3 w-3 shrink-0 fill-hold text-hold" />}
              </span>
              <span className="block truncate text-[11px] text-ink-low">{k.watermark_text || "Không watermark"}</span>
            </span>
            {active && <Check className="absolute right-2 top-2 h-3.5 w-3.5 text-violet-300" />}
          </button>
        );
      })}
    </div>
  );
}
