"use client";

// /app/character — clone openart.ai/suite/character.
// Bố cục 3-pane: [rail StudioShell] · [panel Nhân vật: tạo + thư viện + bắt đầu nhanh] ·
// [main: filter bar + promo "Tạo nhân vật" + lưới nhân vật]. Modal 3 lối tạo.

import { useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  UserRound, UserPlus, Images, Info, Trash2, Sparkles, Clapperboard, ImageIcon,
  AudioLines, Layers, Plus,
} from "lucide-react";
import { api } from "@/lib/api/endpoints";
import { StudioShell } from "@/components/studio/studio-shell";
import { CreateCharacterModal } from "@/components/character/create-character-modal";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils/cn";
import type { Character } from "@/lib/api/types";

type Filter = "all" | "mine" | "system";

// Bắt đầu nhanh — shortcut sang công cụ (mô phỏng Quick Starts của openart).
type Quick = { key: string; label: string; img: string; action?: "modal"; href?: string };
const QUICK: Quick[] = [
  { key: "create", label: "Tạo nhân vật", img: "/kol/lib/tt-nu1.jpg", action: "modal" },
  { key: "image", label: "Nhân vật → Ảnh", img: "/showcase/lookbook.jpg", href: "/app/image-gen" },
  { key: "video", label: "Nhân vật → Video", img: "/showcase/kol.jpg", href: "/app/create" },
  { key: "talk", label: "Video nói", img: "/showcase/explainer.jpg", href: "/app/kol" },
];

export default function CharacterPage() {
  const qc = useQueryClient();
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [filter, setFilter] = useState<Filter>("all");
  const gridRef = useRef<HTMLDivElement>(null);

  const chars = useQuery({ queryKey: ["characters"], queryFn: api.characters });
  const all = chars.data ?? [];
  const shown = useMemo(
    () => all.filter((c) => filter === "all" || (filter === "mine" ? !c.is_system : c.is_system)),
    [all, filter],
  );

  function onCreated() {
    setOpen(false);
    qc.invalidateQueries({ queryKey: ["characters"] });
  }

  async function remove(id: string) {
    await api.deleteCharacter(id);
    qc.invalidateQueries({ queryKey: ["characters"] });
  }

  function scrollToGrid() {
    gridRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  const FILTERS: { key: Filter; label: string }[] = [
    { key: "all", label: "Tất cả" },
    { key: "mine", label: "Của tôi" },
    { key: "system", label: "Mẫu" },
  ];

  return (
    <StudioShell>
      <div className="flex gap-5">
        {/* ── ZONE 2 — panel Nhân vật ──────────────────────────────────── */}
        <aside className="sticky top-28 hidden h-[calc(100dvh-9rem)] w-[300px] shrink-0 flex-col gap-4 overflow-y-auto rounded-2xl glass-bordered p-4 lg:flex">
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-2 text-sm font-semibold text-ink-high">
              <UserRound className="h-4 w-4 text-violet-300" /> Nhân vật
            </span>
            <Info className="h-4 w-4 text-ink-low" />
          </div>

          <div className="grid grid-cols-2 gap-2.5">
            <button
              onClick={() => setOpen(true)}
              className="flex aspect-[4/3] flex-col items-center justify-center gap-2 rounded-xl border border-white/10 bg-white/[0.02] text-center transition-all hover:-translate-y-0.5 hover:border-violet-400/40 hover:bg-violet-500/[0.06]"
            >
              <span className="grid h-9 w-9 place-items-center rounded-full bg-violet-500/15 text-violet-200 ring-1 ring-violet-400/25">
                <UserPlus className="h-4 w-4" />
              </span>
              <span className="text-xs font-medium text-ink-medium">Tạo nhân vật</span>
            </button>
            <button
              onClick={scrollToGrid}
              className="flex aspect-[4/3] flex-col items-center justify-center gap-2 rounded-xl border border-white/10 bg-white/[0.02] text-center transition-all hover:-translate-y-0.5 hover:border-violet-400/40 hover:bg-violet-500/[0.06]"
            >
              <span className="grid h-9 w-9 place-items-center rounded-full bg-white/[0.06] text-ink-medium">
                <Images className="h-4 w-4" />
              </span>
              <span className="text-xs font-medium text-ink-medium">Thư viện</span>
            </button>
          </div>

          <div className="flex flex-col gap-2">
            <span className="text-[10px] font-semibold uppercase tracking-[0.16em] text-ink-disabled">
              Bắt đầu nhanh
            </span>
            <div className="grid grid-cols-2 gap-2.5">
              {QUICK.map((q) =>
                q.action === "modal" ? (
                  <button key={q.key} onClick={() => setOpen(true)} className="group text-left">
                    <QuickThumb img={q.img} label={q.label} badge="Mới" />
                  </button>
                ) : (
                  <Link key={q.key} href={q.href!} className="group">
                    <QuickThumb img={q.img} label={q.label} />
                  </Link>
                ),
              )}
            </div>
          </div>

          {/* tool tabs đáy (mô phỏng thanh tab openart) */}
          <div className="mt-auto flex items-center justify-around rounded-xl border border-white/[0.06] bg-white/[0.02] p-1.5">
            {([
              { href: "/app/create", icon: Clapperboard },
              { href: "/app/image-gen", icon: ImageIcon },
              { href: "/app/character", icon: UserRound, active: true },
              { href: "/app/kol", icon: Layers },
              { href: "/app/audio", icon: AudioLines },
            ] as { href: string; icon: React.ComponentType<{ className?: string }>; active?: boolean }[]).map((t, i) => {
              const Icon = t.icon;
              return (
                <Link
                  key={i}
                  href={t.href}
                  className={cn(
                    "grid h-8 w-8 place-items-center rounded-lg transition-colors",
                    t.active ? "bg-violet-500/20 text-violet-200" : "text-ink-low hover:text-ink-medium",
                  )}
                >
                  <Icon className="h-4 w-4" />
                </Link>
              );
            })}
          </div>
        </aside>

        {/* ── ZONE 3 — main ────────────────────────────────────────────── */}
        <div className="flex min-w-0 flex-1 flex-col gap-5">
          {/* filter bar */}
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-1.5 rounded-xl border border-white/[0.06] bg-white/[0.02] p-1">
              {FILTERS.map((f) => (
                <button
                  key={f.key}
                  onClick={() => setFilter(f.key)}
                  aria-pressed={filter === f.key}
                  className={cn(
                    "rounded-lg px-3 py-1.5 text-xs font-medium transition-colors",
                    filter === f.key ? "bg-violet-500/20 text-ink-high" : "text-ink-low hover:text-ink-medium",
                  )}
                >
                  {f.label}
                </button>
              ))}
            </div>
            <Button onClick={() => setOpen(true)} size="sm" className="gap-1.5 lg:hidden">
              <Plus className="h-4 w-4" /> Tạo nhân vật
            </Button>
          </div>

          {/* promo banner — "Create Character" */}
          <div className="relative overflow-hidden rounded-3xl glass-bordered p-6 sm:p-7">
            <div className="pointer-events-none absolute -right-10 -top-16 h-56 w-56 rounded-full bg-violet-500/20 blur-3xl" />
            <div className="relative flex flex-wrap items-center justify-between gap-5">
              <div className="max-w-md">
                <h1 className="font-display text-2xl font-extrabold text-ink-high sm:text-[28px]">
                  Tạo <span className="text-gradient">nhân vật</span>
                </h1>
                <p className="mt-1.5 text-sm text-ink-medium">
                  Thiết kế nhân vật gốc từ bất kỳ ý tưởng hay hình ảnh nào — dùng lại xuyên ảnh & video.
                </p>
                <Button onClick={() => setOpen(true)} className="mt-4 gap-2">
                  <UserPlus className="h-4 w-4" /> Tạo nhân vật
                </Button>
              </div>
              <button
                onClick={() => setOpen(true)}
                aria-label="Tạo nhân vật từ ảnh"
                className="relative hidden h-32 w-48 place-items-center overflow-hidden rounded-2xl border border-dashed border-violet-400/30 bg-violet-500/[0.05] sm:grid"
              >
                <div
                  className="pointer-events-none absolute inset-0 opacity-30"
                  style={{
                    backgroundImage:
                      "linear-gradient(to right, rgba(255,255,255,0.06) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.06) 1px, transparent 1px)",
                    backgroundSize: "22px 22px",
                  }}
                />
                <span className="relative flex flex-col items-center gap-1.5 text-violet-200">
                  <Plus className="h-6 w-6" />
                  <span className="text-[11px] font-medium">Thêm ảnh mặt</span>
                </span>
              </button>
            </div>
          </div>

          {/* lưới nhân vật */}
          <div ref={gridRef} className="scroll-mt-24">
            {chars.isLoading ? (
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 xl:grid-cols-4">
                {Array.from({ length: 8 }).map((_, i) => (
                  <Skeleton key={i} className="aspect-[3/4] w-full rounded-2xl" />
                ))}
              </div>
            ) : shown.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-white/10 px-4 py-16 text-center">
                <p className="text-sm text-ink-low">Chưa có nhân vật nào. Bấm "Tạo nhân vật" để bắt đầu.</p>
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 xl:grid-cols-4">
                {shown.map((c) => (
                  <CharacterCard key={c.id} c={c} onUse={() => router.push(`/app/create?character=${c.id}`)} onDelete={() => remove(c.id)} />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {open && <CreateCharacterModal onClose={() => setOpen(false)} onCreated={onCreated} />}
    </StudioShell>
  );
}

function QuickThumb({ img, label, badge }: { img: string; label: string; badge?: string }) {
  return (
    <div className="flex flex-col gap-1.5">
      <div className="relative aspect-square overflow-hidden rounded-xl border border-white/10">
        {badge && (
          <span className="absolute left-1.5 top-1.5 z-10 rounded bg-amber-300 px-1 py-0.5 text-[8px] font-bold text-bg-base">
            {badge}
          </span>
        )}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={img} alt="" className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-[1.06]" />
        <div className="absolute inset-0 bg-gradient-to-t from-bg-base/70 to-transparent" />
      </div>
      <span className="truncate text-[11px] font-medium text-ink-medium">{label}</span>
    </div>
  );
}

function CharacterCard({ c, onUse, onDelete }: { c: Character; onUse: () => void; onDelete: () => void }) {
  return (
    <GlassCard className="group relative flex flex-col overflow-hidden p-0 transition-all duration-200 hover:-translate-y-1 hover:shadow-glow-sm hover:ring-1 hover:ring-violet-400/30">
      <div className="relative aspect-[3/4] overflow-hidden bg-bg-surface">
        {c.avatar_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={c.avatar_url} alt={c.name} className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-[1.04]" />
        ) : (
          <div className="grid h-full place-items-center">
            <UserRound className="h-10 w-10 text-violet-300/40" />
          </div>
        )}
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-bg-base/85 to-transparent" />
        {c.vibe && (
          <span className="absolute left-2 top-2 rounded-md bg-black/45 px-2 py-0.5 text-[10px] font-medium text-violet-100">
            {c.vibe}
          </span>
        )}
        <div className="absolute inset-x-3 bottom-2">
          <div className="font-display text-sm font-semibold text-white">{c.name}</div>
          {c.description && <div className="line-clamp-1 text-[11px] text-white/70">{c.description}</div>}
        </div>
      </div>
      <div className="flex items-center gap-1.5 p-2.5">
        <Button onClick={onUse} className="w-full gap-1.5" size="sm">
          <Sparkles className="h-3.5 w-3.5" /> Dùng nhân vật
        </Button>
        {!c.is_system && (
          <button
            onClick={onDelete}
            aria-label="Xoá nhân vật"
            className="grid h-8 w-8 shrink-0 place-items-center rounded-lg text-ink-low transition-colors hover:bg-danger/10 hover:text-danger"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        )}
      </div>
    </GlassCard>
  );
}
