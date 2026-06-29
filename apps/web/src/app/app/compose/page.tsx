"use client";

import { useRef, useState } from "react";
import { useTranslations } from "next-intl";
import { Layers, Loader2, Download, Plus, AlertCircle, X, Film, ImageIcon, Lightbulb } from "lucide-react";
import { api } from "@/lib/api/endpoints";
import { Button } from "@/components/ui/button";
import { Field, ChipGroup } from "@/components/ui/field";
import { FilmLabel } from "@/components/ui/cinematic";
import { Reveal } from "@/components/marketing/reveal";
import { ACCENTS } from "@/lib/accents";

interface Item {
  preview: string;
  path?: string;
  uploading: boolean;
}

const A = ACCENTS.emerald;

export default function ComposePage() {
  const t = useTranslations("compose");
  const [items, setItems] = useState<Item[]>([]);
  const [secondsPer, setSecondsPer] = useState(3);
  const [videoUrl, setVideoUrl] = useState<string>();
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  function addFiles(files: FileList | null) {
    if (!files) return;
    Array.from(files).slice(0, 8 - items.length).forEach((file) => {
      const preview = URL.createObjectURL(file);
      const idx = items.length;
      setItems((cur) => [...cur, { preview, uploading: true }]);
      api
        .uploadImage(file)
        .then((res) =>
          setItems((cur) => cur.map((it, i) => (i === idx ? { ...it, path: res.image_path, uploading: false } : it))),
        )
        .catch(() => setItems((cur) => cur.map((it, i) => (i === idx ? { ...it, uploading: false } : it))));
    });
  }

  function removeItem(idx: number) {
    setItems((cur) => cur.filter((_, i) => i !== idx));
  }

  async function compose() {
    const paths = items.map((i) => i.path).filter(Boolean) as string[];
    if (paths.length < 2) return;
    setLoading(true);
    setErr(null);
    setVideoUrl(undefined);
    try {
      setVideoUrl(await api.compose(paths, secondsPer));
    } catch {
      setErr(t("error"));
    } finally {
      setLoading(false);
    }
  }

  const ready = items.filter((i) => i.path).length;
  const totalSecs = ready * secondsPer;
  const canCompose = ready >= 2 && !loading;

  return (
    <div className="flex flex-col gap-8">
      {/* ── Hệ tiêu đề: bố cục bench, KHÔNG dùng CineHero ────────────────── */}
      <Reveal>
        <div className="relative overflow-hidden rounded-3xl glass-bordered p-6 sm:p-8">
          {/* nền: dải film mờ phía phải, glow emerald 1 vầng */}
          <div
            className="pointer-events-none absolute -top-24 right-1/4 h-56 w-56 rounded-full blur-3xl"
            style={{ background: A.glow }}
          />
          <div className="relative grid gap-6 lg:grid-cols-[1.4fr_1fr] lg:items-end">
            <div>
              <FilmLabel>{t("heroLabel")}</FilmLabel>
              <h1 className="mt-3 font-display text-3xl font-extrabold leading-[1.06] text-ink-high lg:text-[40px]">
                {t.rich("heroTitle", {
                  grad: (chunks) => (
                    <span className="bg-gradient-to-r from-emerald-300 to-teal-300 bg-clip-text text-transparent">
                      {chunks}
                    </span>
                  ),
                })}
              </h1>
              <p className="mt-3 max-w-lg text-ink-medium">
                {t("heroDescription")}
              </p>
            </div>

            {/* thẻ nhịp: hai chỉ số THẬT từ state hiện tại */}
            <div className="flex gap-3">
              <BenchStat label={t("statFramesLabel")} value={`${ready}`} sub={t("statFramesSub")} />
              <BenchStat
                label={t("statDurationLabel")}
                value={ready ? `${totalSecs}` : "—"}
                sub={ready ? t("statDurationSub") : t("statDurationSubEmpty")}
              />
            </div>
          </div>
        </div>
      </Reveal>

      {/* ── Bench: rail trình tự (trái) + bảng điều khiển 2 bước (phải) ─── */}
      <div className="grid gap-6 lg:grid-cols-[1fr_22rem] lg:items-start">
        {/* TRÁI — bàn ghép: film-strip có đánh số, KHÔNG phải lưới đối xứng */}
        <Reveal delay={0.05}>
          <section className="relative overflow-hidden rounded-3xl glass-bordered p-5 sm:p-6">
            <div className="mb-4 flex items-center justify-between">
              <FilmLabel>
                {t.rich("step1Label", {
                  step: (chunks) => <span className="text-emerald-300">{chunks}</span>,
                })}
              </FilmLabel>
              {ready > 0 && (
                <span className="text-xs text-ink-low">
                  {t("step1Hint")}
                </span>
              )}
            </div>

            {items.length === 0 ? (
              <EmptyBench onAdd={() => inputRef.current?.click()} />
            ) : (
              <ol className="flex flex-wrap items-stretch gap-3">
                {items.map((it, i) => (
                  <li key={i} className="flex items-center gap-3">
                    <FrameTile
                      it={it}
                      index={i + 1}
                      onRemove={() => removeItem(i)}
                    />
                    {/* nối khung → cảnh: dấu chuyển cảnh, không nhãn phim */}
                    {i < items.length - 1 && (
                      <span
                        aria-hidden
                        className="hidden h-px w-5 self-center bg-gradient-to-r from-emerald-400/60 to-transparent sm:block"
                      />
                    )}
                  </li>
                ))}
                {items.length < 8 && (
                  <li className="self-stretch">
                    <button
                      type="button"
                      onClick={() => inputRef.current?.click()}
                      aria-label={t("addImageAria")}
                      className="group grid aspect-[9/16] w-[88px] place-items-center rounded-xl border border-dashed border-white/15 text-ink-low transition-colors hover:border-emerald-400/50 hover:text-emerald-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400/40 sm:w-[104px]"
                    >
                      <span className="flex flex-col items-center gap-1.5">
                        <Plus className="h-6 w-6 transition-transform group-hover:scale-110" />
                        <span className="text-[11px]">{t("addImage")}</span>
                      </span>
                    </button>
                  </li>
                )}
              </ol>
            )}

            <input
              ref={inputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              multiple
              className="hidden"
              onChange={(e) => addFiles(e.target.files)}
            />
          </section>
        </Reveal>

        {/* PHẢI — bảng điều khiển dính: nhịp + render (Bước 2) ───────────── */}
        <Reveal delay={0.1}>
          <aside className="flex flex-col gap-4 lg:sticky lg:top-28">
            <div className="rounded-3xl glass-bordered p-5">
              <FilmLabel>
                {t.rich("step2Label", {
                  step: (chunks) => <span className="text-emerald-300">{chunks}</span>,
                })}
              </FilmLabel>

              <div className="mt-5">
                <Field label={t("durationField")}>
                  <ChipGroup
                    value={secondsPer}
                    onChange={(v) => setSecondsPer(v as number)}
                    options={[2, 3, 4].map((s) => ({ value: s, label: `${s}s` }))}
                  />
                </Field>
              </div>

              {/* tóm tắt clip — chỉ số thật */}
              <div className="mt-5 flex items-center justify-between rounded-xl border border-white/[0.06] bg-white/[0.02] px-4 py-3">
                <span className="flex items-center gap-2 text-sm text-ink-medium">
                  <Film className="h-4 w-4 text-emerald-300" /> {t("clipFormat")}
                </span>
                <span className="font-numeric text-sm font-semibold tabular-nums text-ink-high">
                  {ready ? `${totalSecs}s` : "—"}
                </span>
              </div>

              <Button
                onClick={compose}
                disabled={!canCompose}
                className="mt-4 w-full gap-2 bg-gradient-to-r from-emerald-500 to-teal-500 text-white shadow-[0_0_0_1px_rgba(16,185,129,.45),0_8px_36px_-10px_rgba(20,184,166,.6)] hover:brightness-110"
              >
                {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Layers className="h-4 w-4" />}
                {loading ? t("composing") : ready >= 2 ? t("composeCta", { count: ready }) : t("composeNeed")}
              </Button>

              {ready < 2 && !err && (
                <p className="mt-2.5 text-center text-xs text-ink-low">
                  {t("composeHint", { count: Math.max(0, 2 - ready) })}
                </p>
              )}
              {err && (
                <p className="mt-2.5 flex items-center justify-center gap-1.5 text-sm text-danger">
                  <AlertCircle className="h-4 w-4" /> {err}
                </p>
              )}
            </div>

            {/* mẹo gọn trong cùng cột */}
            <div className="rounded-3xl glass p-5">
              <div className="mb-3 flex items-center gap-1.5 text-sm font-semibold text-ink-high">
                <Lightbulb className="h-4 w-4 text-emerald-300" /> {t("tipsTitle")}
              </div>
              <ul className="grid gap-2.5">
                {[t("tip1"), t("tip2"), t("tip3")].map((tip) => (
                  <li key={tip} className="flex items-start gap-2 text-sm leading-snug text-ink-low">
                    <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-emerald-400" /> {tip}
                  </li>
                ))}
              </ul>
            </div>
          </aside>
        </Reveal>
      </div>

      {/* ── Output: bảng chiếu khi có clip ──────────────────────────────── */}
      {videoUrl && (
        <Reveal>
          <section className="relative overflow-hidden rounded-3xl glass-bordered">
            <div
              className="pointer-events-none absolute -bottom-20 left-1/4 h-52 w-52 rounded-full blur-3xl"
              style={{ background: A.glow }}
            />
            <div className="relative flex flex-col items-center gap-5 p-6 sm:p-8">
              <FilmLabel>{t("outputLabel")}</FilmLabel>
              <video
                src={videoUrl}
                controls
                autoPlay
                loop
                className="max-h-[60vh] w-auto rounded-2xl border border-white/10 shadow-[0_8px_60px_-12px_rgba(16,185,129,.4)]"
              />
              <a href={videoUrl} download="vyra-compose.mp4">
                <Button className="gap-2 bg-gradient-to-r from-emerald-500 to-teal-500 text-white hover:brightness-110">
                  <Download className="h-4 w-4" /> {t("downloadMp4")}
                </Button>
              </a>
            </div>
          </section>
        </Reveal>
      )}
    </div>
  );
}

/* ── Phụ trợ riêng màn này ─────────────────────────────────────────────── */

function BenchStat({ label, value, sub }: { label: string; value: string; sub: string }) {
  return (
    <div className="flex-1 rounded-2xl border border-white/[0.08] bg-white/[0.02] px-4 py-3">
      <div className="text-[11px] uppercase tracking-[0.16em] text-ink-low">{label}</div>
      <div className="mt-1 flex items-baseline gap-1.5">
        <span className="font-numeric text-2xl font-bold tabular-nums text-ink-high">{value}</span>
        <span className="text-xs text-ink-low">{sub}</span>
      </div>
    </div>
  );
}

function FrameTile({ it, index, onRemove }: { it: Item; index: number; onRemove: () => void }) {
  const t = useTranslations("compose");
  return (
    <div className="group relative aspect-[9/16] w-[88px] overflow-hidden rounded-xl border border-white/10 transition-all duration-200 hover:-translate-y-0.5 hover:border-emerald-400/40 hover:shadow-glow-sm sm:w-[104px]">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={it.preview} alt="" className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105" />

      {/* số thứ tự khung — bản sắc "trình tự" */}
      <span className="absolute left-1.5 top-1.5 grid h-6 w-6 place-items-center rounded-md bg-bg-base/70 font-numeric text-xs font-bold tabular-nums text-emerald-200 backdrop-blur-sm">
        {index}
      </span>

      {it.uploading ? (
        <div className="absolute inset-0 grid place-items-center bg-bg-base/60">
          <Loader2 className="h-4 w-4 animate-spin text-emerald-300" />
        </div>
      ) : (
        <button
          type="button"
          onClick={onRemove}
          aria-label={t("removeFrameAria", { index })}
          className="absolute right-1.5 top-1.5 grid h-6 w-6 place-items-center rounded-md bg-bg-base/70 text-ink-low opacity-0 backdrop-blur-sm transition hover:text-danger focus-visible:opacity-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400/40 group-hover:opacity-100"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      )}
    </div>
  );
}

function EmptyBench({ onAdd }: { onAdd: () => void }) {
  const t = useTranslations("compose");
  return (
    <button
      type="button"
      onClick={onAdd}
      className="group flex w-full flex-col items-center gap-3 rounded-2xl border border-dashed border-white/12 bg-white/[0.015] px-6 py-10 text-center transition-colors hover:border-emerald-400/40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400/40"
    >
      <span className="grid h-12 w-12 place-items-center rounded-2xl bg-gradient-to-br from-emerald-500/30 to-teal-500/10">
        <ImageIcon className="h-6 w-6 text-emerald-200" />
      </span>
      <div>
        <div className="font-display font-semibold text-ink-high">{t("emptyTitle")}</div>
        <p className="mt-1 text-sm text-ink-low">
          {t("emptyDesc")}
        </p>
      </div>
      <span className="mt-1 inline-flex items-center gap-1.5 rounded-lg border border-emerald-400/30 bg-emerald-500/10 px-3.5 py-2 text-sm text-emerald-200 transition group-hover:bg-emerald-500/15">
        <Plus className="h-4 w-4" /> {t("emptyCta")}
      </span>
    </button>
  );
}
