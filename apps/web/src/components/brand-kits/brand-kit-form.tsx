"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { Palette, Loader2 } from "lucide-react";
import { api } from "@/lib/api/endpoints";
import type { BrandKit } from "@/lib/api/types";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Field, inputCls } from "@/components/ui/field";
import { FilmLabel } from "@/components/ui/cinematic";

export const EMPTY = {
  name: "", logo_url: "", primary_color: "#7C3AED", secondary_color: "#2563EB",
  font: "", watermark_text: "", disclosure_text: "", is_default: false,
};

export function BrandKitForm({ initial, onDone }: { initial: Partial<BrandKit>; onDone: () => void }) {
  const t = useTranslations("brandkits");
  const [f, setF] = useState({ ...EMPTY, ...initial });
  const [busy, setBusy] = useState(false);
  const set = (k: string, v: unknown) => setF((s) => ({ ...s, [k]: v }));

  async function save() {
    setBusy(true);
    try {
      const body = {
        name: f.name.trim(), logo_url: f.logo_url, primary_color: f.primary_color,
        secondary_color: f.secondary_color, font: f.font, watermark_text: f.watermark_text,
        disclosure_text: f.disclosure_text, is_default: f.is_default,
      };
      if (initial.id) await api.updateBrandKit(initial.id, body);
      else await api.createBrandKit(body);
      onDone();
    } finally {
      setBusy(false);
    }
  }

  return (
    <GlassCard className="grid gap-5 p-5 sm:p-6 lg:grid-cols-[1fr_minmax(0,240px)]" bordered>
      <div className="flex flex-col gap-4">
        <FilmLabel dot={false}>{initial.id ? t("formEditTitle") : t("formNewTitle")}</FilmLabel>
        <div className="grid gap-3 sm:grid-cols-2">
          <Field label={t("fieldName")}><input className={inputCls} value={f.name} onChange={(e) => set("name", e.target.value)} placeholder={t("placeholderName")} /></Field>
          <Field label={t("fieldLogoUrl")}><input className={inputCls} value={f.logo_url} onChange={(e) => set("logo_url", e.target.value)} placeholder="https://..." /></Field>
          <Field label={t("fieldPrimaryColor")}>
            <div className="flex items-center gap-2">
              <input type="color" value={f.primary_color} onChange={(e) => set("primary_color", e.target.value)} className="h-9 w-12 rounded border border-white/10 bg-transparent" aria-label={t("pickPrimaryColor")} />
              <input className={inputCls} value={f.primary_color} onChange={(e) => set("primary_color", e.target.value)} />
            </div>
          </Field>
          <Field label={t("fieldSecondaryColor")}>
            <div className="flex items-center gap-2">
              <input type="color" value={f.secondary_color} onChange={(e) => set("secondary_color", e.target.value)} className="h-9 w-12 rounded border border-white/10 bg-transparent" aria-label={t("pickSecondaryColor")} />
              <input className={inputCls} value={f.secondary_color} onChange={(e) => set("secondary_color", e.target.value)} />
            </div>
          </Field>
          <Field label={t("fieldFont")}><input className={inputCls} value={f.font} onChange={(e) => set("font", e.target.value)} placeholder={t("placeholderFont")} /></Field>
          <Field label={t("fieldWatermark")}><input className={inputCls} value={f.watermark_text} onChange={(e) => set("watermark_text", e.target.value)} placeholder="@shopabc" /></Field>
          <Field label={t("fieldDisclosure")} className="sm:col-span-2"><input className={inputCls} value={f.disclosure_text} onChange={(e) => set("disclosure_text", e.target.value)} placeholder={t("placeholderDisclosure")} /></Field>
        </div>
        <label className="flex items-center gap-2 text-sm text-ink-medium">
          <input type="checkbox" checked={f.is_default} onChange={(e) => set("is_default", e.target.checked)} />
          {t("setAsDefault")}
        </label>
        <Button onClick={save} disabled={!f.name.trim() || busy} className="self-start">
          {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : initial.id ? t("save") : t("createKit")}
        </Button>
      </div>

      {/* xem trước trực tiếp trong form — gõ tới đâu thấy tới đó */}
      <div className="flex flex-col gap-2 lg:border-l lg:border-white/[0.06] lg:pl-5">
        <span className="text-[11px] font-semibold uppercase tracking-[0.18em] text-ink-low">{t("preview")}</span>
        <div
          className="relative flex aspect-[4/3] flex-col justify-between overflow-hidden rounded-2xl p-3 ring-1 ring-white/10"
          style={{ background: `linear-gradient(140deg, ${f.primary_color || "#7C3AED"}, ${f.secondary_color || "#2563EB"})` }}
        >
          <div className="flex items-start justify-between">
            {f.logo_url ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={f.logo_url} alt="" className="h-9 w-9 rounded-lg object-cover ring-1 ring-white/50" />
            ) : (
              <span className="grid h-9 w-9 place-items-center rounded-lg bg-black/25 text-white/80 ring-1 ring-white/30"><Palette className="h-4 w-4" /></span>
            )}
            {f.watermark_text && <span className="rounded bg-black/40 px-2 py-0.5 text-[10px] font-medium text-white/95">{f.watermark_text}</span>}
          </div>
          <div>
            <div className="font-display text-base font-bold text-white drop-shadow">{f.name || t("previewNamePlaceholder")}</div>
            {f.font && <div className="text-[10px] text-white/85">{f.font}</div>}
          </div>
        </div>
        {f.disclosure_text && <p className="text-[11px] text-ink-low">{t("disclosurePrefix", { text: f.disclosure_text })}</p>}
      </div>
    </GlassCard>
  );
}
