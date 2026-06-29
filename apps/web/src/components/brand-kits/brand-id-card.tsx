"use client";

import { useTranslations } from "next-intl";
import { Palette, Trash2, Star, Type, ShieldCheck, Pencil } from "lucide-react";
import type { BrandKit } from "@/lib/api/types";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

/** Thẻ nhận diện lớn: gradient màu sống + logo + font + watermark + dòng công bố. */
export function BrandIdCard({ kit, onEdit, onDelete }: { kit: BrandKit; onEdit: () => void; onDelete: () => void }) {
  const t = useTranslations("brandkits");
  const p = kit.primary_color || "#7C3AED";
  const s = kit.secondary_color || "#2563EB";
  return (
    <div className="overflow-hidden rounded-2xl glass-bordered">
      {/* khung "video sống" mang nhận diện — chứng minh watermark/logo nằm ở đâu */}
      <div className="relative aspect-[4/3]" style={{ background: `linear-gradient(140deg, ${p}, ${s})` }}>
        <div className="absolute inset-0 bg-[radial-gradient(120%_80%_at_20%_-10%,rgba(255,255,255,0.22),transparent_60%)]" />
        {kit.is_default && (
          <Badge tone="brand" className="absolute left-3 top-3 border-white/30 bg-black/30 text-white">
            <Star className="mr-1 h-3 w-3" /> {t("default")}
          </Badge>
        )}
        {kit.logo_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={kit.logo_url} alt="" className="absolute right-3 top-3 h-12 w-12 rounded-xl object-cover ring-1 ring-white/50" />
        ) : (
          <span className="absolute right-3 top-3 grid h-12 w-12 place-items-center rounded-xl bg-black/25 text-white/80 ring-1 ring-white/30">
            <Palette className="h-5 w-5" />
          </span>
        )}
        {kit.watermark_text && (
          <span className="absolute bottom-3 right-3 rounded bg-black/40 px-2 py-0.5 text-[11px] font-medium text-white/95 backdrop-blur-sm">
            {kit.watermark_text}
          </span>
        )}
        <div className="absolute bottom-3 left-3">
          <div className="font-display text-xl font-bold text-white drop-shadow">{kit.name}</div>
          {kit.font && (
            <div className="mt-0.5 inline-flex items-center gap-1 text-[11px] text-white/85">
              <Type className="h-3 w-3" /> {kit.font}
            </div>
          )}
        </div>
      </div>

      <div className="flex flex-col gap-3 p-4">
        <div className="flex items-center gap-2 font-numeric text-[11px] text-ink-low">
          <span className="inline-flex items-center gap-1.5">
            <span className="h-3 w-3 rounded-sm ring-1 ring-white/20" style={{ background: p }} /> {p}
          </span>
          <span className="inline-flex items-center gap-1.5">
            <span className="h-3 w-3 rounded-sm ring-1 ring-white/20" style={{ background: s }} /> {s}
          </span>
        </div>
        {kit.disclosure_text && (
          <div className="flex items-start gap-1.5 text-xs text-ink-low">
            <ShieldCheck className="mt-0.5 h-3.5 w-3.5 shrink-0 text-rose-300" />
            <span className="line-clamp-2">{t("disclosurePrefix", { text: kit.disclosure_text })}</span>
          </div>
        )}
        <div className="mt-1 flex items-center gap-2">
          <Button onClick={onEdit} variant="outline" size="sm" className="flex-1 gap-1.5">
            <Pencil className="h-3.5 w-3.5" /> {t("editThis")}
          </Button>
          <button
            onClick={onDelete}
            className="grid h-9 w-9 shrink-0 place-items-center rounded-lg text-ink-low transition-colors hover:bg-danger/10 hover:text-danger focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-danger/40"
            aria-label={t("deleteAria", { name: kit.name })}
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
