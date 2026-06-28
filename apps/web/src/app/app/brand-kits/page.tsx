"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Palette, Trash2, Star, Loader2, Layers, Droplets } from "lucide-react";
import { api } from "@/lib/api/endpoints";
import type { BrandKit } from "@/lib/api/types";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Field, inputCls } from "@/components/ui/field";
import { ScreenHero, StatTile } from "@/components/app/screen-hero";

const EMPTY = {
  name: "", logo_url: "", primary_color: "#7C3AED", secondary_color: "#2563EB",
  font: "", watermark_text: "", disclosure_text: "", is_default: false,
};

export default function BrandKitsPage() {
  const qc = useQueryClient();
  const kits = useQuery({ queryKey: ["brand-kits"], queryFn: api.brandKits });
  const [editing, setEditing] = useState<null | Partial<BrandKit>>(null);

  const refresh = () => qc.invalidateQueries({ queryKey: ["brand-kits"] });

  async function remove(id: string) {
    await api.deleteBrandKit(id);
    refresh();
  }

  const list = kits.data ?? [];

  return (
    <div className="flex flex-col gap-6">
      <ScreenHero
        icon={Palette}
        accent="rose"
        title="Bộ thương hiệu"
        sub="Logo, màu, watermark & dòng công bố — gắn nhận diện vào mọi video."
        action={
          <Button onClick={() => setEditing(editing ? null : { ...EMPTY })} variant={editing ? "glass" : "primary"}>
            {editing ? "Đóng" : "+ Tạo bộ"}
          </Button>
        }
      >
        <div className="grid grid-cols-2 gap-3 sm:max-w-sm">
          <StatTile icon={Layers} label="Số bộ" value={kits.isLoading ? "" : list.length} loading={kits.isLoading} accent="rose" />
          <StatTile icon={Star} label="Mặc định" value={list.find((k) => k.is_default)?.name ?? "Chưa đặt"} accent="amber" />
        </div>
      </ScreenHero>

      {editing && (
        <BrandKitForm
          initial={editing}
          onDone={() => { setEditing(null); refresh(); }}
        />
      )}

      {kits.isLoading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-36 w-full rounded-xl" />)}
        </div>
      ) : (kits.data ?? []).length === 0 ? (
        <GlassCard className="grid place-items-center gap-2 p-10 text-center text-ink-low">
          <Palette className="h-8 w-8 text-violet-300/60" />
          Chưa có bộ thương hiệu nào. Tạo bộ đầu tiên để gắn logo & watermark vào video.
        </GlassCard>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {(kits.data ?? []).map((k) => (
            <GlassCard key={k.id} className="overflow-hidden p-0">
              {/* preview thương hiệu — gradient màu chính→phụ + logo + watermark */}
              <div
                className="relative flex h-24 items-end p-3"
                style={{ background: `linear-gradient(135deg, ${k.primary_color || "#7C3AED"}, ${k.secondary_color || "#2563EB"})` }}
              >
                {k.logo_url && (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={k.logo_url} alt="" className="absolute left-3 top-3 h-9 w-9 rounded-lg object-cover ring-1 ring-white/40" />
                )}
                {k.is_default && (
                  <Badge tone="brand" className="absolute right-2 top-2 border-white/30 bg-black/30 text-white">
                    <Star className="mr-1 h-3 w-3" /> Mặc định
                  </Badge>
                )}
                {k.watermark_text && (
                  <span className="ml-auto rounded bg-black/35 px-2 py-0.5 text-[11px] font-medium text-white/95 backdrop-blur-sm">
                    {k.watermark_text}
                  </span>
                )}
              </div>
              <div className="p-4">
                <div className="flex items-center justify-between gap-2">
                  <div className="min-w-0 font-display font-semibold text-ink-high">{k.name}</div>
                  <div className="flex shrink-0 items-center gap-1">
                    <button onClick={() => setEditing(k)} className="rounded-lg px-2 py-1 text-xs text-rose-300 hover:bg-white/[0.05]">Sửa</button>
                    <button onClick={() => remove(k.id)} className="grid h-7 w-7 place-items-center rounded-lg text-ink-low hover:bg-danger/10 hover:text-danger" aria-label="Xoá">
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>
                <div className="mt-2 flex items-center gap-1.5 font-numeric text-[11px] text-ink-low">
                  <Droplets className="h-3 w-3" /> {k.primary_color} · {k.secondary_color}
                </div>
                {k.disclosure_text && <div className="mt-1 line-clamp-1 text-xs text-ink-low">Công bố: {k.disclosure_text}</div>}
              </div>
            </GlassCard>
          ))}
        </div>
      )}
    </div>
  );
}

function BrandKitForm({ initial, onDone }: { initial: Partial<BrandKit>; onDone: () => void }) {
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
    <GlassCard className="p-5">
      <div className="grid gap-3 sm:grid-cols-2">
        <Field label="Tên bộ"><input className={inputCls} value={f.name} onChange={(e) => set("name", e.target.value)} placeholder="Shop ABC" /></Field>
        <Field label="Logo URL"><input className={inputCls} value={f.logo_url} onChange={(e) => set("logo_url", e.target.value)} placeholder="https://..." /></Field>
        <Field label="Màu chính">
          <div className="flex items-center gap-2">
            <input type="color" value={f.primary_color} onChange={(e) => set("primary_color", e.target.value)} className="h-9 w-12 rounded border border-white/10 bg-transparent" />
            <input className={inputCls} value={f.primary_color} onChange={(e) => set("primary_color", e.target.value)} />
          </div>
        </Field>
        <Field label="Màu phụ">
          <div className="flex items-center gap-2">
            <input type="color" value={f.secondary_color} onChange={(e) => set("secondary_color", e.target.value)} className="h-9 w-12 rounded border border-white/10 bg-transparent" />
            <input className={inputCls} value={f.secondary_color} onChange={(e) => set("secondary_color", e.target.value)} />
          </div>
        </Field>
        <Field label="Watermark"><input className={inputCls} value={f.watermark_text} onChange={(e) => set("watermark_text", e.target.value)} placeholder="@shopabc" /></Field>
        <Field label="Dòng công bố (affiliate)"><input className={inputCls} value={f.disclosure_text} onChange={(e) => set("disclosure_text", e.target.value)} placeholder="Tiếp thị liên kết" /></Field>
      </div>
      <label className="mt-3 flex items-center gap-2 text-sm text-ink-medium">
        <input type="checkbox" checked={f.is_default} onChange={(e) => set("is_default", e.target.checked)} />
        Đặt làm bộ mặc định
      </label>
      <Button onClick={save} disabled={!f.name.trim() || busy} className="mt-4 self-start">
        {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : initial.id ? "Lưu" : "Tạo bộ"}
      </Button>
    </GlassCard>
  );
}
