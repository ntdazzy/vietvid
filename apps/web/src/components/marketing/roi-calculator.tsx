"use client";

import { useState } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { TrendingDown, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { FilmLabel } from "@/components/ui/cinematic";
import { Reveal } from "@/components/marketing/reveal";
import { cn } from "@/lib/utils/cn";

// Số THẬT, không bịa: gói Cơ bản 300.000đ ≈ 12 video 30s → ~25.000đ/video.
// Thuê KOC/quay dựng ~300.000đ/video là giá thị trường tham khảo (ghi rõ ở dòng giả định).
const VYRA_PER_VIDEO = 25_000;
const KOC_PER_VIDEO = 300_000;

const fmt = (n: number) => n.toLocaleString("vi-VN") + "đ";

export function RoiCalculator() {
  const t = useTranslations("pricing");
  const [videos, setVideos] = useState(20);

  const vyra = videos * VYRA_PER_VIDEO;
  const koc = videos * KOC_PER_VIDEO;
  const save = koc - vyra;
  const savePct = Math.round((save / koc) * 100);

  return (
    <section className="mx-auto max-w-6xl px-4 pb-16">
      <Reveal>
        <div className="relative overflow-hidden rounded-3xl glass-bordered p-7 sm:p-9">
          <div className="pointer-events-none absolute -top-16 left-1/4 h-56 w-56 rounded-full bg-emerald-500/15 blur-3xl" />
          <div className="relative">
            <FilmLabel>{t("roiEyebrow")}</FilmLabel>
            <h2 className="mt-3 max-w-2xl font-display text-[clamp(1.6rem,3.4vw,2.4rem)] font-bold leading-tight text-ink-high">
              {t("roiHeading")}
            </h2>

            <div className="mt-8 grid gap-8 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)] lg:items-center">
              {/* nhập: số video / tháng */}
              <div>
                <label htmlFor="roi-videos" className="text-sm font-medium text-ink-medium">
                  {t("roiInputLabel")}
                </label>
                <div className="mt-3 flex items-baseline gap-2">
                  <span className="font-numeric text-5xl font-bold tabular-nums text-emerald-300">{videos}</span>
                  <span className="text-ink-low">{t("roiPerMonthUnit")}</span>
                </div>
                <input
                  id="roi-videos"
                  type="range"
                  min={1}
                  max={100}
                  value={videos}
                  onChange={(e) => setVideos(Number(e.target.value))}
                  className="mt-4 w-full accent-emerald-400"
                />
                <div className="mt-1 flex justify-between text-[11px] text-ink-disabled">
                  <span>1</span>
                  <span>100</span>
                </div>
              </div>

              {/* kết quả: Vyra vs thuê người + tiết kiệm */}
              <div className="grid gap-4 sm:grid-cols-2">
                <CostCard label={t("roiVyraLabel")} amount={fmt(vyra)} tone="accent" />
                <CostCard label={t("roiKocLabel")} amount={fmt(koc)} tone="strike" />
                <div className="rounded-2xl border border-emerald-400/30 bg-emerald-500/[0.08] p-5 sm:col-span-2">
                  <div className="flex items-center gap-2 text-sm text-ink-medium">
                    <TrendingDown className="h-4 w-4 text-emerald-400" /> {t("roiSaveLabel")}
                  </div>
                  <div className="mt-1 flex flex-wrap items-baseline gap-x-3 gap-y-1">
                    <span className="font-numeric text-3xl font-bold tabular-nums text-emerald-300">{fmt(save)}</span>
                    <span className="rounded-full bg-emerald-500/15 px-2.5 py-0.5 text-sm font-semibold text-emerald-200">
                      −{savePct}%
                    </span>
                    <span className="text-sm text-ink-low">{t("roiPerMonth")}</span>
                  </div>
                </div>
              </div>
            </div>

            <p className="mt-6 max-w-3xl text-xs leading-relaxed text-ink-disabled">{t("roiAssumption")}</p>
            <Link href="/login" className="mt-5 inline-block">
              <Button className="gap-1.5">
                {t("roiCta")} <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
          </div>
        </div>
      </Reveal>
    </section>
  );
}

function CostCard({ label, amount, tone }: { label: string; amount: string; tone: "accent" | "strike" }) {
  return (
    <div
      className={cn(
        "rounded-2xl border p-5",
        tone === "accent" ? "border-emerald-400/25 bg-emerald-500/[0.05]" : "border-white/[0.08] bg-white/[0.02]",
      )}
    >
      <div className="text-sm text-ink-medium">{label}</div>
      <div
        className={cn(
          "mt-1 font-numeric text-2xl font-bold tabular-nums",
          tone === "accent" ? "text-emerald-300" : "text-ink-low line-through decoration-red-400/50",
        )}
      >
        {amount}
      </div>
    </div>
  );
}
