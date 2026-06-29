"use client";

import { useTranslations } from "next-intl";
import { ArrowRight } from "lucide-react";
import { type VideoType } from "@/store/wizard";
import { TemplateGallery } from "@/components/create/template-gallery";
import { CornerFrame, FilmLabel } from "@/components/ui/cinematic";
import { ACCENTS, type Accent } from "@/lib/accents";
import { cn } from "@/lib/utils/cn";
import type { Template } from "@/lib/api/types";

// Thể loại (Moment 0 genre-first) — map về flow THẬT (videoType product_ad|kol_full + brief/frameMode).
// title/desc hiển thị lấy từ i18n theo `key`; brief gửi API giữ tiếng Việt (nội dung prompt, không phải UI).
export type Genre = {
  key: string; image: string; accent: Accent; label: string;
  videoType: VideoType; brief: string; frameMode: "upload" | "ai";
};
export const GENRES: Genre[] = [
  { key: "product_ad", image: "/showcase/affiliate.jpg", accent: "violet", label: "AFFILIATE", videoType: "product_ad", brief: "", frameMode: "upload" },
  { key: "review", image: "/showcase/kol.jpg", accent: "rose", label: "REVIEW", videoType: "kol_full", brief: "Làm video review sản phẩm theo kịch bản, KOL nói tự nhiên, nêu ưu điểm chính.", frameMode: "upload" },
  { key: "lookbook", image: "/showcase/lookbook.jpg", accent: "amber", label: "LOOKBOOK", videoType: "kol_full", brief: "Lookbook thời trang: KOL trình diễn sản phẩm trong bối cảnh editorial.", frameMode: "upload" },
  { key: "text_to_video", image: "/showcase/shortfilm.jpg", accent: "sky", label: "TEXT→VIDEO", videoType: "product_ad", brief: "", frameMode: "ai" },
  { key: "image_to_video", image: "/showcase/product.jpg", accent: "cyan", label: "IMG→VIDEO", videoType: "product_ad", brief: "", frameMode: "upload" },
  { key: "trend", image: "/showcase/trend.jpg", accent: "emerald", label: "TREND", videoType: "product_ad", brief: "Video ngắn bắt trend đang viral, nhịp nhanh, hook mạnh ở 2 giây đầu.", frameMode: "upload" },
];

// ── MOMENT 0 — Genre-first: chọn thể loại (bản sắc riêng màn Create) ────
export function Launchpad({
  onPickGenre,
  onPickTemplate,
  onBuildFromScratch,
}: {
  onPickGenre: (g: Genre) => void;
  onPickTemplate: (t: Template | null) => void;
  onBuildFromScratch: () => void;
}) {
  const t = useTranslations("create");
  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-8">
      <div className="relative overflow-hidden rounded-3xl glass-bordered p-6 sm:p-8">
        <div className="pointer-events-none absolute -top-20 right-4 h-48 w-48 rounded-full bg-violet-500/15 blur-3xl" />
        <CornerFrame color="border-white/15" />
        <div className="relative">
          <FilmLabel>{t("launchpadEyebrow")}</FilmLabel>
          <h1 className="mt-3 font-display text-3xl font-extrabold leading-tight text-ink-high lg:text-[40px]">
            {t.rich("launchpadTitle", { grad: (c) => <span className="text-gradient">{c}</span> })}
          </h1>
          <p className="mt-2 max-w-lg text-ink-medium">
            {t("launchpadSubtitle")}
          </p>
        </div>
      </div>

      <section className="flex flex-col gap-4">
        <h2 className="text-sm font-semibold uppercase tracking-[0.16em] text-ink-low">{t("genresHeading")}</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {GENRES.map((g) => (
            <GenreCard
              key={g.key}
              g={g}
              title={t(`genre.${g.key}.title`)}
              desc={t(`genre.${g.key}.desc`)}
              onClick={() => onPickGenre(g)}
            />
          ))}
        </div>
      </section>

      <section className="flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold uppercase tracking-[0.16em] text-ink-low">{t("orStartFromTemplate")}</h2>
          <button
            onClick={onBuildFromScratch}
            className="text-sm text-violet-300 transition hover:text-violet-200"
          >
            {t("buildFromScratchArrow")}
          </button>
        </div>
        <TemplateGallery onPick={onPickTemplate} />
      </section>
    </div>
  );
}

function GenreCard({ g, title, desc, onClick }: { g: Genre; title: string; desc: string; onClick: () => void }) {
  const a = ACCENTS[g.accent];
  return (
    <button
      onClick={onClick}
      className="group relative flex flex-col overflow-hidden rounded-2xl glass-bordered text-left transition-all duration-200 hover:-translate-y-1 hover:shadow-glow-sm"
    >
      <div className="relative aspect-[16/10] overflow-hidden">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={g.image} alt="" loading="lazy" className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-[1.05]" />
        <div className="absolute inset-0 bg-gradient-to-t from-bg-surface via-bg-surface/30 to-transparent" />
        <CornerFrame color="border-white/0 group-hover:border-white/35" inset="inset-2" />
        <FilmLabel dot={false} className="absolute bottom-2.5 left-3 text-white/80">{g.label}</FilmLabel>
      </div>
      <div className="flex items-start gap-2 p-4">
        <div className="min-w-0">
          <div className="font-display font-semibold text-ink-high">{title}</div>
          <p className="mt-0.5 text-sm leading-snug text-ink-low">{desc}</p>
        </div>
        <ArrowRight className={cn("ml-auto mt-0.5 h-4 w-4 shrink-0 transition group-hover:translate-x-0.5", a.icon)} />
      </div>
    </button>
  );
}
