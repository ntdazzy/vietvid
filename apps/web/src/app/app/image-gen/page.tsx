"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { Palette, Loader2, Download, AlertCircle, Sparkles, Lightbulb, RefreshCw, Wand2, ImageIcon } from "lucide-react";
import { api } from "@/lib/api/endpoints";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Field, ChipGroup, inputCls } from "@/components/ui/field";
import { Skeleton } from "@/components/ui/skeleton";
import { FilmLabel } from "@/components/ui/cinematic";
import { Reveal } from "@/components/marketing/reveal";
import { ACCENTS } from "@/lib/accents";
import { StudioShell } from "@/components/studio/studio-shell";
import { cn } from "@/lib/utils/cn";

const PRESET_KEYS = ["presetMilktea", "presetSerum", "presetHeadphones", "presetJacket"] as const;
const STYLE_KEYS = ["styleCinematic", "styleUgc", "styleMinimal", "styleBrandTone"] as const;
const TIP_KEYS = ["tipDescribe", "tipColorTone", "tipVertical"] as const;
// Reel ảnh mẫu cho empty-state — cảm hứng, ảnh có sẵn trong /showcase.
const REEL = [
  { src: "/showcase/food.jpg", tagKey: "reelFood" },
  { src: "/showcase/product.jpg", tagKey: "reelProduct" },
  { src: "/showcase/lookbook.jpg", tagKey: "reelFashion" },
  { src: "/showcase/affiliate.jpg", tagKey: "reelAd" },
  { src: "/showcase/explainer.jpg", tagKey: "reelScene" },
] as const;

const ASPECT_RATIO: Record<string, string> = { "9:16": "9 / 16", "1:1": "1 / 1", "16:9": "16 / 9" };

type Recent = { url: string; prompt: string; aspect: string };

export default function ImageGenPage() {
  const t = useTranslations("imagegen");
  const td = useTranslations("director");
  const a = ACCENTS.sky;
  const [prompt, setPrompt] = useState("");
  const [aspect, setAspect] = useState("9:16");
  const [url, setUrl] = useState<string>();
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  // "Gần đây" — ảnh đã tạo trong PHIÊN (blob: URL chỉ sống trong phiên nên không lưu đĩa).
  const [recents, setRecents] = useState<Recent[]>([]);

  function addStyle(s: string) {
    setPrompt((p) => (p.trim() ? `${p.replace(/[,\s]+$/, "")}, ${s}` : s));
  }

  async function generate() {
    if (prompt.trim().length < 3) return;
    setLoading(true);
    setErr(null);
    setUrl(undefined);
    try {
      const res = await api.generateImage(prompt.trim(), aspect);
      setUrl(res.url);
      setRecents((prev) => [{ url: res.url, prompt: prompt.trim(), aspect }, ...prev].slice(0, 8));
    } catch (e) {
      setErr(e instanceof Error ? e.message : t("errGenerate"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <StudioShell>
      <div className="flex flex-col gap-6">
      {/* ── Đầu màn: dải thông tin gọn, không dùng CineHero (bố cục riêng) ── */}
      <Reveal>
        <div className="relative overflow-hidden rounded-3xl glass-bordered p-6 sm:p-7">
          <div
            className="pointer-events-none absolute -right-16 -top-20 h-56 w-56 rounded-full blur-3xl"
            style={{ background: a.glow }}
          />
          <div className="relative flex flex-wrap items-end justify-between gap-4">
            <div>
              <FilmLabel>{t("filmLabel")}</FilmLabel>
              <h1 className="mt-3 font-display text-3xl font-extrabold leading-[1.05] text-ink-high lg:text-[40px]">
                {t.rich("heroTitle", { grad: (c) => <span className={a.text}>{c}</span> })}
              </h1>
              <p className="mt-2 max-w-xl text-ink-medium">
                {t("heroSubtitle")}
              </p>
            </div>
            <div className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 text-xs text-ink-low">
              <ImageIcon className={cn("h-3.5 w-3.5", a.icon)} /> {t("ratioBadge")}
            </div>
          </div>
        </div>
      </Reveal>

      {/* ── Sân khấu chính: canvas lớn (trái) + phiếu mô tả hẹp (phải) ── */}
      <div className="grid gap-6 lg:grid-cols-[1.45fr_1fr]">
        {/* CANVAS — chiếm sân khấu */}
        <Reveal delay={0.05}>
          <div className="relative flex min-h-[420px] flex-col overflow-hidden rounded-3xl glass-bordered">
            {/* dải nhãn trên canvas */}
            <div className="flex items-center justify-between gap-2 border-b border-white/[0.06] px-5 py-3">
              <span className="flex items-center gap-2.5 text-xs font-medium text-ink-medium">
                <span className="flex items-center gap-2">
                  <span className={cn("h-1.5 w-1.5 rounded-full", url ? "bg-emerald-400" : loading ? "bg-sky-400 animate-pulse" : a.bar)} />
                  {loading ? t("statusBuilding") : url ? t("statusResult") : t("statusEmpty")}
                </span>
                <span className="hidden items-center gap-1 rounded-md border border-sky-400/20 bg-sky-500/[0.08] px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-sky-200 sm:inline-flex">
                  <Sparkles className="h-2.5 w-2.5" /> Vyra AI
                </span>
              </span>
              {url && (
                <a href={url} download="vyra-image.png" aria-label={t("downloadAria")}>
                  <Button variant="glass" className="h-8 gap-1.5 px-3 text-xs">
                    <Download className="h-3.5 w-3.5" /> {t("downloadBtn")}
                  </Button>
                </a>
              )}
            </div>

            <div className="relative grid flex-1 place-items-center p-5 sm:p-7">
              {/* nền lưới mờ kiểu bàn dựng */}
              <div
                className="pointer-events-none absolute inset-0 opacity-[0.18]"
                style={{
                  backgroundImage:
                    "linear-gradient(to right, rgba(255,255,255,0.05) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.05) 1px, transparent 1px)",
                  backgroundSize: "32px 32px",
                }}
              />
              <div
                className="pointer-events-none absolute inset-x-10 -bottom-24 h-48 rounded-full blur-3xl"
                style={{ background: a.glow }}
              />

              {loading ? (
                <div className="relative flex flex-col items-center gap-3">
                  <div className="h-72" style={{ aspectRatio: ASPECT_RATIO[aspect] }}>
                    <Skeleton className="h-full w-full rounded-2xl" />
                  </div>
                  <span className="text-sm text-ink-low">{t("drawingFrame", { aspect })}</span>
                </div>
              ) : url ? (
                <div className="relative">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={url}
                    alt={t("resultAlt")}
                    className="max-h-[58vh] w-auto rounded-2xl border border-white/10 shadow-glow-sm"
                  />
                </div>
              ) : (
                // EMPTY-STATE — reel ảnh mẫu (signature)
                <div className="relative flex w-full flex-col items-center gap-5">
                  <div className="flex flex-col items-center gap-2 text-center">
                    <span className={cn("grid h-12 w-12 place-items-center rounded-2xl bg-gradient-to-br", a.tile)}>
                      <Wand2 className={cn("h-5 w-5", a.icon)} />
                    </span>
                    <p className="text-sm font-medium text-ink-medium">{t("emptyTitle")}</p>
                    <p className="max-w-xs text-xs text-ink-low">{t("emptyHint")}</p>
                  </div>
                  <div className="flex w-full max-w-md gap-2 overflow-x-auto pb-1">
                    {REEL.map((r) => (
                      <figure key={r.src} className="group relative aspect-[3/4] w-24 shrink-0 overflow-hidden rounded-xl border border-white/10">
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img src={r.src} alt="" loading="lazy" className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-[1.06]" />
                        <div className="absolute inset-0 bg-gradient-to-t from-bg-surface/90 to-transparent" />
                        <figcaption className="absolute bottom-1.5 left-2 text-[10px] font-semibold uppercase tracking-wide text-white/80">{t(r.tagKey)}</figcaption>
                      </figure>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </Reveal>

        {/* PHIẾU MÔ TẢ — cột điều khiển hẹp */}
        <Reveal delay={0.1}>
          <GlassCard className="flex h-fit flex-col gap-5 p-5">
            <Field label={t("descLabel")}>
              <textarea
                className={cn(inputCls, "min-h-[120px] resize-y")}
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                maxLength={500}
                placeholder={t("descPlaceholder")}
              />
            </Field>

            {/* gợi ý nhanh — bấm để điền cả câu */}
            <div>
              <div className="mb-2 flex items-center gap-1.5 text-xs font-medium text-ink-medium">
                <Sparkles className={cn("h-3.5 w-3.5", a.icon)} /> {t("quickIdeas")}
              </div>
              <div className="flex flex-col gap-1.5">
                {PRESET_KEYS.map((k) => (
                  <button
                    key={k}
                    onClick={() => setPrompt(t(k))}
                    className="rounded-lg border border-white/10 px-3 py-2 text-left text-[12px] text-ink-low transition-colors hover:border-sky-400/40 hover:bg-sky-500/[0.06] hover:text-ink-medium active:scale-[0.99]"
                  >
                    {t(`${k}Short`)}
                  </button>
                ))}
              </div>
            </div>

            {/* phong cách — append vào prompt */}
            <div>
              <div className="mb-2 text-xs font-medium text-ink-medium">{t("addStyle")}</div>
              <div className="flex flex-wrap gap-1.5">
                {STYLE_KEYS.map((k) => (
                  <button
                    key={k}
                    onClick={() => addStyle(t(k))}
                    className="rounded-full border border-sky-400/25 bg-sky-500/[0.06] px-2.5 py-1 text-[11px] text-sky-200 transition-colors hover:bg-sky-500/15 active:scale-[0.98]"
                  >
                    + {t(k)}
                  </button>
                ))}
              </div>
            </div>

            <Field label={t("ratioLabel")}>
              <ChipGroup
                value={aspect}
                onChange={(v) => setAspect(v as string)}
                options={[
                  { value: "9:16", label: t("ratioVertical") },
                  { value: "1:1", label: t("ratioSquare") },
                  { value: "16:9", label: t("ratioWide") },
                ]}
              />
            </Field>

            <div className="flex flex-col gap-2 border-t border-white/[0.06] pt-4">
              <Button onClick={generate} disabled={loading || prompt.trim().length < 3} className="w-full justify-center gap-2">
                {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : url ? <RefreshCw className="h-4 w-4" /> : <Palette className="h-4 w-4" />}
                {loading ? t("btnGenerating") : url ? t("btnRegenerate") : t("btnGenerate")}
              </Button>
              {err && (
                <span className="flex items-center gap-1.5 text-sm text-danger">
                  <AlertCircle className="h-4 w-4 shrink-0" /> {err}
                </span>
              )}
              {!err && (
                <p className="text-center text-[11px] text-ink-low">{t("minWordsHint")}</p>
              )}
            </div>
          </GlassCard>
        </Reveal>
      </div>

      {/* ── Gần đây — ảnh đã tạo trong phiên, bấm để xem lại (kho kết quả kiểu studio) ── */}
      {recents.length > 0 && (
        <Reveal delay={0.12}>
          <div>
            <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-ink-medium">
              <ImageIcon className={cn("h-4 w-4", a.icon)} /> {td("recent")}
              <span className="font-numeric text-xs text-ink-disabled">({recents.length})</span>
            </div>
            <div className="flex gap-3 overflow-x-auto pb-1">
              {recents.map((r, i) => (
                <button
                  key={r.url + i}
                  onClick={() => { setUrl(r.url); setPrompt(r.prompt); setAspect(r.aspect); }}
                  title={r.prompt}
                  className={cn(
                    "group relative aspect-[3/4] w-24 shrink-0 overflow-hidden rounded-xl border transition",
                    url === r.url ? "border-sky-400/60 ring-1 ring-sky-400/40" : "border-white/10 hover:border-sky-400/40",
                  )}
                >
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={r.url} alt="" className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-[1.06]" />
                  <span className="absolute bottom-1 right-1 rounded bg-bg-base/70 px-1 font-numeric text-[9px] text-ink-medium backdrop-blur-sm">{r.aspect}</span>
                </button>
              ))}
            </div>
          </div>
        </Reveal>
      )}

      {/* ── Mẹo viết mô tả — dải ngang dưới đáy ── */}
      <Reveal delay={0.15}>
        <GlassCard className="p-5">
          <div className="mb-3 flex items-center gap-1.5 text-sm font-semibold text-ink-high">
            <Lightbulb className={cn("h-4 w-4", a.icon)} /> {t("tipsTitle")}
          </div>
          <ul className="grid gap-2.5 sm:grid-cols-3">
            {TIP_KEYS.map((k, i) => (
              <li key={k} className="flex items-start gap-2.5 rounded-xl border border-white/[0.05] bg-white/[0.02] p-3 text-sm text-ink-low">
                <span className={cn("grid h-5 w-5 shrink-0 place-items-center rounded-md bg-gradient-to-br text-[11px] font-bold text-ink-high", a.tile)}>{i + 1}</span>
                {t(k)}
              </li>
            ))}
          </ul>
        </GlassCard>
      </Reveal>
      </div>
    </StudioShell>
  );
}
