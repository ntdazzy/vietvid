"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Palette, Droplets, Plus } from "lucide-react";
import { api } from "@/lib/api/endpoints";
import type { BrandKit } from "@/lib/api/types";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { FilmLabel } from "@/components/ui/cinematic";
import { Reveal } from "@/components/marketing/reveal";
import { BrandIdCard } from "@/components/brand-kits/brand-id-card";
import { KitRow } from "@/components/brand-kits/kit-row";
import { BrandKitForm, EMPTY } from "@/components/brand-kits/brand-kit-form";

export default function BrandKitsPage() {
  const t = useTranslations("brandkits");
  const qc = useQueryClient();
  const kits = useQuery({ queryKey: ["brand-kits"], queryFn: api.brandKits });
  const [editing, setEditing] = useState<null | Partial<BrandKit>>(null);
  // Bộ đang xem ở khung preview lớn (mặc định: bộ mặc-định, không thì bộ đầu).
  const [activeId, setActiveId] = useState<string | null>(null);

  const refresh = () => qc.invalidateQueries({ queryKey: ["brand-kits"] });

  async function remove(id: string) {
    await api.deleteBrandKit(id);
    if (activeId === id) setActiveId(null);
    refresh();
  }

  const list = kits.data ?? [];
  const active =
    list.find((k) => k.id === activeId) ?? list.find((k) => k.is_default) ?? list[0] ?? null;

  return (
    <div className="flex flex-col gap-7">
      {/* ───── HERO: bàn nhận diện — eyebrow + tiêu đề + dải swatch sống ───── */}
      <section className="relative overflow-hidden rounded-3xl glass-bordered">
        <div
          className="pointer-events-none absolute -right-16 -top-24 h-72 w-72 rounded-full blur-3xl"
          style={{ background: "rgba(244,63,94,0.18)" }}
        />
        <div className="relative grid gap-6 p-6 sm:p-8 lg:grid-cols-[1.4fr_1fr] lg:items-end lg:p-10">
          <div>
            <FilmLabel>{t("heroEyebrow")}</FilmLabel>
            <h1 className="mt-4 max-w-xl font-display text-3xl font-extrabold leading-[1.07] text-ink-high sm:text-4xl lg:text-[46px]">
              {t.rich("heroTitle", { grad: (c) => <span className="text-gradient">{c}</span> })}
            </h1>
            <p className="mt-3 max-w-md text-ink-medium sm:text-lg">
              {t("heroSubtitle")}
            </p>
            <div className="mt-6 flex flex-wrap items-center gap-3">
              <Button
                onClick={() => setEditing(editing ? null : { ...EMPTY })}
                variant={editing ? "glass" : "primary"}
                size="lg"
                className="gap-2"
              >
                {editing ? t("closeForm") : <><Plus className="h-4 w-4" /> {t("createNew")}</>}
              </Button>
              <span className="inline-flex items-center gap-2 text-sm text-ink-low">
                <Palette className="h-4 w-4 text-rose-300" />
                {kits.isLoading ? t("loading") : t("kitCount", { count: list.length })}
                {active?.is_default && <span className="text-ink-low">{t("defaultLabel", { name: active.name })}</span>}
              </span>
            </div>
          </div>

          {/* dải swatch của bộ đang xem — bằng chứng "sống" ngay trong hero */}
          <div className="flex flex-col gap-2.5">
            {active ? (
              <>
                <span className="text-[11px] font-semibold uppercase tracking-[0.18em] text-ink-low">
                  {t("paletteOf", { name: active.name })}
                </span>
                <div className="flex h-16 overflow-hidden rounded-2xl ring-1 ring-white/10">
                  <div className="flex-1" style={{ background: active.primary_color || "#7C3AED" }} />
                  <div className="flex-1" style={{ background: active.secondary_color || "#2563EB" }} />
                  <div
                    className="w-20 shrink-0"
                    style={{ background: `linear-gradient(135deg, ${active.primary_color || "#7C3AED"}, ${active.secondary_color || "#2563EB"})` }}
                  />
                </div>
                <div className="flex items-center gap-1.5 font-numeric text-[11px] text-ink-low">
                  <Droplets className="h-3 w-3" /> {active.primary_color} · {active.secondary_color}
                </div>
              </>
            ) : (
              <div className="grid h-16 place-items-center rounded-2xl border border-dashed border-white/10 text-xs text-ink-low">
                {t("emptyPaletteHint")}
              </div>
            )}
          </div>
        </div>
      </section>

      {editing && (
        <Reveal>
          <BrandKitForm
            initial={editing}
            onDone={() => { setEditing(null); refresh(); }}
          />
        </Reveal>
      )}

      {/* ───── KHU LÀM VIỆC: trái = thẻ nhận diện sống, phải = bộ sưu tập ───── */}
      {kits.isLoading ? (
        <div className="grid gap-5 lg:grid-cols-[minmax(0,360px)_1fr]">
          <Skeleton className="h-[420px] w-full rounded-2xl" />
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-28 w-full rounded-2xl" />)}
          </div>
        </div>
      ) : list.length === 0 ? (
        <GlassCard className="grid place-items-center gap-3 p-12 text-center text-ink-low" bordered>
          <span className="grid h-14 w-14 place-items-center rounded-2xl bg-gradient-to-br from-rose-500/30 to-pink-500/10 text-rose-200 ring-1 ring-rose-400/25">
            <Palette className="h-7 w-7" />
          </span>
          <div className="font-display text-lg font-semibold text-ink-high">{t("emptyTitle")}</div>
          <p className="max-w-sm text-sm text-ink-low">
            {t("emptyBody")}
          </p>
          <Button onClick={() => setEditing({ ...EMPTY })} className="mt-1 gap-2"><Plus className="h-4 w-4" /> {t("createFirst")}</Button>
        </GlassCard>
      ) : (
        <div className="grid gap-5 lg:grid-cols-[minmax(0,360px)_1fr]">
          {/* THẺ NHẬN DIỆN SỐNG — preview lớn của bộ đang chọn */}
          {active && (
            <Reveal>
              <BrandIdCard
                kit={active}
                onEdit={() => setEditing(active)}
                onDelete={() => remove(active.id)}
              />
            </Reveal>
          )}

          {/* BỘ SƯU TẬP — bấm để xem bên trái */}
          <Reveal delay={0.05}>
            <section className="flex flex-col gap-3">
              <div className="flex items-baseline justify-between gap-3">
                <h2 className="text-sm font-semibold uppercase tracking-wider text-ink-low">{t("collection")}</h2>
                <FilmLabel dot={false} className="hidden sm:inline-flex">{t("kitCount", { count: list.length })}</FilmLabel>
              </div>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                {list.map((k) => (
                  <KitRow
                    key={k.id}
                    kit={k}
                    selected={active?.id === k.id}
                    onSelect={() => setActiveId(k.id)}
                    onEdit={() => setEditing(k)}
                    onDelete={() => remove(k.id)}
                  />
                ))}
              </div>
            </section>
          </Reveal>
        </div>
      )}
    </div>
  );
}
