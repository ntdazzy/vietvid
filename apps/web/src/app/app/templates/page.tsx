"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { LayoutTemplate, Sparkles, Trash2, Lock, ArrowRight, Layers } from "lucide-react";
import { api } from "@/lib/api/endpoints";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { FilmLabel } from "@/components/ui/cinematic";
import { Reveal } from "@/components/marketing/reveal";
import { HoverVideo } from "@/components/ui/hover-video";
import { cn } from "@/lib/utils/cn";
import type { Template } from "@/lib/api/types";

// ảnh thumbnail theo category (dùng khung nội dung mẫu thật trong /samples).
const CAT_IMG: Record<string, string> = {
  review: "/samples/kol_review.jpg",
  lookbook: "/samples/lookbook.jpg",
  product_ad: "/samples/unboxing.jpg",
  text_to_video: "/samples/food_review.jpg",
};

// clip preview chạy khi RÊ CHUỘT vào thẻ (di chuột → phát video). Trộn clip
// AI sinh mới (review = seedance 480p-5s) + clip mẫu sẵn có. Thiếu clip = chỉ ảnh.
const CAT_VID: Record<string, string> = {
  review: "/samples/gen/review.mp4",
  lookbook: "/samples/fashion.mp4",
  product_ad: "/samples/home.mp4",
  text_to_video: "/samples/food.mp4",
};

// khoá i18n cho category (không lộ enum thô review/product_ad…).
const CAT_KEY: Record<string, string> = {
  review: "catReview",
  lookbook: "catLookbook",
  product_ad: "catProductAd",
  text_to_video: "catTextToVideo",
};

type Translate = (key: string) => string;

function catLabel(t: Translate, c: string) {
  const key = CAT_KEY[c];
  return key ? t(key) : c;
}

function thumb(t: Template) {
  return CAT_IMG[t.category] ?? "";
}

function clip(t: Template) {
  return CAT_VID[t.category] ?? "";
}

export default function TemplatesPage() {
  const t = useTranslations("templates");
  const qc = useQueryClient();
  const templates = useQuery({ queryKey: ["templates"], queryFn: api.templates });
  const [cat, setCat] = useState<string>("all");

  const all = templates.data ?? [];

  // bộ lọc category — đếm theo dữ liệu THẬT (không số bịa).
  const cats = useMemo(() => {
    const m = new Map<string, number>();
    for (const t of all) m.set(t.category, (m.get(t.category) ?? 0) + 1);
    return [...m.entries()].map(([key, n]) => ({ key, n }));
  }, [all]);

  const shown = cat === "all" ? all : all.filter((t) => t.category === cat);
  const featured = shown[0];
  const rest = shown.slice(1);

  async function remove(id: string) {
    await api.deleteTemplate(id);
    qc.invalidateQueries({ queryKey: ["templates"] });
  }

  return (
    <div className="flex flex-col gap-8">
      {/* ── HERO 2-ZONE (signature Templates: kệ mẫu editorial, lệch trái) ── */}
      <section className="relative overflow-hidden rounded-3xl glass-bordered">
        <div
          className="pointer-events-none absolute -top-24 right-8 h-64 w-64 rounded-full blur-3xl"
          style={{ background: "rgba(124,77,255,0.20)" }}
        />
        <div className="relative grid gap-6 p-6 sm:p-9 lg:grid-cols-[1.15fr_0.85fr] lg:items-center lg:gap-10 lg:p-10">
          {/* zone trái — chữ */}
          <div>
            <FilmLabel>{t("heroEyebrow")}</FilmLabel>
            <h1 className="mt-3 font-display text-3xl font-extrabold leading-[1.05] text-ink-high sm:text-4xl lg:text-[48px]">
              {t.rich("heroTitle", {
                grad: (chunks) => <span className="text-gradient">{chunks}</span>,
              })}
            </h1>
            <p className="mt-3 max-w-md text-ink-medium sm:text-lg">
              {t("heroSubtitle")}
            </p>
            <div className="mt-6 flex flex-wrap items-center gap-x-7 gap-y-2">
              <span className="flex items-baseline gap-1.5">
                <span className="font-numeric text-2xl font-bold tabular text-ink-high">{all.length}</span>
                <span className="text-sm text-ink-low">{t("statTemplates")}</span>
              </span>
              <span className="flex items-center gap-1.5 text-sm text-ink-medium">
                <Layers className="h-4 w-4 text-violet-300" /> {t("statLocked")}
              </span>
            </div>
          </div>

          {/* zone phải — “bìa kệ”: 3 ảnh mẫu xếp chéo (asymmetric), trang trí, không bê CineHero */}
          <div className="relative hidden h-56 lg:block" aria-hidden>
            <ShelfTile className="absolute left-0 top-6 w-[46%] -rotate-3" img="/samples/lookbook.jpg" />
            <ShelfTile className="absolute left-1/4 top-0 z-10 w-[48%] rotate-1 ring-violet-400/30" img="/samples/kol_review.jpg" />
            <ShelfTile className="absolute right-0 top-10 w-[44%] rotate-3" img="/samples/unboxing.jpg" />
          </div>
        </div>
      </section>

      {/* ── BỘ LỌC CATEGORY (pill accent violet, đếm thật) ── */}
      {!templates.isLoading && all.length > 0 && (
        <div className="flex flex-wrap items-center gap-2">
          <FilterPill active={cat === "all"} onClick={() => setCat("all")} label={t("filterAll")} n={all.length} />
          {cats.map((c) => (
            <FilterPill key={c.key} active={cat === c.key} onClick={() => setCat(c.key)} label={catLabel(t, c.key)} n={c.n} />
          ))}
        </div>
      )}

      {/* ── GALLERY ── */}
      {templates.isLoading ? (
        <div className="flex flex-col gap-4">
          <Skeleton className="h-48 w-full rounded-2xl" />
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="aspect-[16/10] w-full rounded-2xl" />
            ))}
          </div>
        </div>
      ) : all.length === 0 ? (
        <EmptyState />
      ) : (
        <Reveal>
          {/* mẫu đầu = banner ngang full-width nổi bật; còn lại = lưới đều (luôn cân, không hở ô) */}
          <div className="flex flex-col gap-4">
            {featured && <FeaturedCard t={featured} onRemove={remove} />}
            {rest.length > 0 && (
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {rest.map((t) => (
                  <TemplateCard key={t.id} t={t} onRemove={remove} />
                ))}
              </div>
            )}
          </div>
        </Reveal>
      )}
    </div>
  );
}

/** Ảnh trang trí trong “bìa kệ” của hero (zone phải). */
function ShelfTile({ img, className }: { img: string; className?: string }) {
  return (
    <div className={cn("overflow-hidden rounded-xl glass-bordered shadow-glow-sm", className)}>
      <div className="aspect-[16/10]">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={img} alt="" loading="lazy" className="h-full w-full object-cover opacity-90" />
      </div>
    </div>
  );
}

function FilterPill({ active, onClick, label, n }: { active: boolean; onClick: () => void; label: string; n: number }) {
  return (
    <button
      onClick={onClick}
      aria-pressed={active}
      className={cn(
        "inline-flex items-center gap-2 rounded-lg border px-3 py-1.5 text-sm font-medium transition-colors",
        active
          ? "border-violet-400/40 bg-violet-500/20 text-ink-high"
          : "border-white/10 text-ink-low hover:text-ink-medium",
      )}
    >
      {label}
      <span className={cn("font-numeric text-xs tabular", active ? "text-violet-200" : "text-ink-low")}>{n}</span>
    </button>
  );
}

/** Mẫu nổi bật — banner NGANG full-width (ảnh trái + nội dung phải). Luôn cân, không hở ô. */
function FeaturedCard({ t, onRemove }: { t: Template; onRemove: (id: string) => void }) {
  const tr = useTranslations("templates");
  const img = thumb(t);
  return (
    <article className="group relative grid overflow-hidden rounded-2xl glass-bordered transition-all duration-200 hover:-translate-y-1 hover:shadow-glow-sm hover:ring-1 hover:ring-violet-400/30 sm:h-[300px] sm:grid-cols-[minmax(0,42%)_1fr]">
      {/* ảnh trái — rê chuột phát clip. Chiều cao banner cố định (sm:h-300) để ảnh không tự kéo cao. */}
      <div className="relative h-[200px] overflow-hidden bg-bg-surface sm:h-auto">
        {img ? (
          <HoverVideo poster={img} video={clip(t)} alt={t.name} badge={false} className="h-full w-full" />
        ) : (
          <div className="grid h-full w-full place-items-center bg-grad-brand-soft">
            <LayoutTemplate className="h-10 w-10 text-violet-300/60" />
          </div>
        )}
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-bg-base/60 to-transparent sm:bg-gradient-to-r sm:from-transparent sm:to-bg-surface/80" />
        <CardCorner t={t} onRemove={onRemove} />
      </div>
      {/* nội dung phải */}
      <div className="flex flex-col justify-center gap-2.5 p-5 sm:p-7">
        <FilmLabel dot={false} className="text-violet-200">{tr("featuredEyebrow", { category: catLabel(tr, t.category) })}</FilmLabel>
        <div className="font-display text-2xl font-bold text-ink-high">{t.name}</div>
        <p className="line-clamp-3 max-w-md text-sm text-ink-medium">{t.description}</p>
        <Link href={`/app/create?template=${t.id}`} className="mt-1.5">
          <Button className="gap-2">
            <Sparkles className="h-4 w-4" /> {tr("useThisTemplate")}
          </Button>
        </Link>
      </div>
    </article>
  );
}

/** Mẫu thường — thẻ ảnh ngang gọn. */
function TemplateCard({ t, onRemove }: { t: Template; onRemove: (id: string) => void }) {
  const tr = useTranslations("templates");
  const img = thumb(t);
  return (
    <article className="group relative flex flex-col overflow-hidden rounded-2xl glass-bordered transition-all duration-200 hover:-translate-y-1 hover:shadow-glow-sm hover:ring-1 hover:ring-violet-400/30">
      <div className="relative flex aspect-[16/10] overflow-hidden bg-bg-surface">
        {img ? (
          <HoverVideo poster={img} video={clip(t)} alt={t.name} badge={false} className="h-full w-full" />
        ) : (
          <div className="grid h-full w-full place-items-center bg-grad-brand-soft">
            <LayoutTemplate className="h-8 w-8 text-violet-300/60" />
          </div>
        )}
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-bg-base/85 to-transparent" />
        <CardCorner t={t} onRemove={onRemove} />
        <span className="pointer-events-none absolute bottom-2.5 left-3 text-[11px] font-semibold uppercase tracking-[0.16em] text-violet-200">
          {catLabel(tr, t.category)}
        </span>
      </div>
      <div className="flex flex-1 flex-col p-4">
        <div className="font-display font-semibold text-ink-high">{t.name}</div>
        <p className="mt-0.5 line-clamp-2 flex-1 text-sm leading-snug text-ink-low">{t.description}</p>
        <Link
          href={`/app/create?template=${t.id}`}
          className="mt-3 inline-flex items-center gap-1.5 text-sm font-medium text-violet-200 transition group-hover:gap-2.5"
        >
          {tr("useTemplate")} <ArrowRight className="h-4 w-4 transition group-hover:translate-x-0.5" />
        </Link>
      </div>
    </article>
  );
}

/** Góc trên-phải: huy hiệu hệ thống (khoá) hoặc nút xoá. */
function CardCorner({ t, onRemove }: { t: Template; onRemove: (id: string) => void }) {
  const tr = useTranslations("templates");
  if (t.is_system) {
    return (
      <span className="absolute right-2.5 top-2.5 inline-flex items-center gap-1 rounded-md border border-white/10 bg-black/40 px-2 py-0.5 text-[10px] font-medium text-ink-medium backdrop-blur-sm">
        <Lock className="h-3 w-3" /> {tr("systemBadge")}
      </span>
    );
  }
  return (
    <button
      onClick={() => onRemove(t.id)}
      className="absolute right-2.5 top-2.5 grid h-8 w-8 place-items-center rounded-lg bg-black/40 text-ink-low backdrop-blur-sm transition-colors hover:bg-danger/30 hover:text-danger active:scale-95"
      aria-label={tr("deleteAria", { name: t.name })}
    >
      <Trash2 className="h-4 w-4" />
    </button>
  );
}

function EmptyState() {
  const tr = useTranslations("templates");
  return (
    <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-white/10 py-16 text-center">
      <div className="grid h-14 w-14 place-items-center rounded-2xl bg-grad-brand-soft">
        <LayoutTemplate className="h-6 w-6 text-violet-300/70" />
      </div>
      <p className="text-ink-low">{tr("emptyText")}</p>
      <Link href="/app/create">
        <Button variant="glass" size="sm" className="gap-2">
          <Sparkles className="h-4 w-4" /> {tr("emptyCta")}
        </Button>
      </Link>
    </div>
  );
}
