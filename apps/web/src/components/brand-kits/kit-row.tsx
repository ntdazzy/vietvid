"use client";

import { useTranslations } from "next-intl";
import { Trash2, Star } from "lucide-react";
import type { BrandKit } from "@/lib/api/types";
import { cn } from "@/lib/utils/cn";

/** Hàng trong bộ sưu tập: swatch nhỏ + tên + watermark. Bấm → xem ở thẻ lớn. */
export function KitRow({
  kit, selected, onSelect, onEdit, onDelete,
}: {
  kit: BrandKit; selected: boolean; onSelect: () => void; onEdit: () => void; onDelete: () => void;
}) {
  const t = useTranslations("brandkits");
  const p = kit.primary_color || "#7C3AED";
  const s = kit.secondary_color || "#2563EB";
  return (
    <div
      className={cn(
        "group relative flex items-center gap-3 rounded-2xl border p-3 transition-all duration-200 hover:-translate-y-0.5",
        selected
          ? "border-rose-400/40 bg-rose-500/[0.07] shadow-glow-sm"
          : "border-white/[0.06] bg-white/[0.02] hover:border-white/[0.14]",
      )}
    >
      {/* swatch bấm-được để chọn bộ xem ở thẻ lớn */}
      <button
        onClick={onSelect}
        aria-label={t("viewAria", { name: kit.name })}
        aria-pressed={selected}
        className="relative h-14 w-14 shrink-0 overflow-hidden rounded-xl ring-1 ring-white/15 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-400/60"
        style={{ background: `linear-gradient(135deg, ${p}, ${s})` }}
      >
        {kit.logo_url && (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={kit.logo_url} alt="" className="absolute inset-0 h-full w-full object-cover opacity-90" />
        )}
      </button>

      <button onClick={onSelect} className="min-w-0 flex-1 text-left focus-visible:outline-none">
        <div className="flex items-center gap-1.5">
          <span className="truncate font-display font-semibold text-ink-high">{kit.name}</span>
          {kit.is_default && <Star className="h-3.5 w-3.5 shrink-0 text-rose-300" aria-label={t("default")} />}
        </div>
        <div className="mt-0.5 truncate font-numeric text-[11px] text-ink-low">{p} · {s}</div>
        {kit.watermark_text && <div className="mt-0.5 truncate text-[11px] text-ink-low">{kit.watermark_text}</div>}
      </button>

      <div className="flex shrink-0 items-center gap-1">
        <button
          onClick={onEdit}
          className="rounded-lg px-2 py-1 text-xs text-rose-300 transition-colors hover:bg-white/[0.05] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-400/40"
        >
          {t("edit")}
        </button>
        <button
          onClick={onDelete}
          className="grid h-7 w-7 place-items-center rounded-lg text-ink-low transition-colors hover:bg-danger/10 hover:text-danger focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-danger/40"
          aria-label={t("deleteAria", { name: kit.name })}
        >
          <Trash2 className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  );
}
