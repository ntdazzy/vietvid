"use client";

import { useEffect, useRef, useState } from "react";
import { useTranslations } from "next-intl";
import { AudioLines, Loader2, Download, AlertCircle, Sparkles, Mic, Play, Quote } from "lucide-react";
import { api } from "@/lib/api/endpoints";
import type { VoicePersona } from "@/lib/api/types";
import { Button } from "@/components/ui/button";
import { FilmLabel } from "@/components/ui/cinematic";
import { Reveal } from "@/components/marketing/reveal";
import { ACCENTS } from "@/lib/accents";
import { cn } from "@/lib/utils/cn";

const ACCENT = ACCENTS.rose;

const EXAMPLE_KEYS = ["example1", "example2", "example3"] as const;

// Cao độ cột sóng âm — cố định để render ổn định (SSR/CSR khớp nhau), không random.
const WAVE = [
  18, 34, 52, 30, 46, 70, 88, 60, 40, 26, 44, 64, 82, 96, 72, 50, 34, 22, 38, 58,
  76, 90, 68, 48, 30, 42, 62, 80, 92, 70, 52, 36, 24, 40, 60, 78, 86, 64, 44, 28,
];

export default function AudioToolPage() {
  const t = useTranslations("audio");
  const [text, setText] = useState("");
  const [personas, setPersonas] = useState<VoicePersona[]>([]);
  const [persona, setPersona] = useState<VoicePersona | null>(null);
  const [url, setUrl] = useState<string>();
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    api.voicePersonas().then((p) => { setPersonas(p); setPersona(p[0] ?? null); }).catch(() => setPersonas([]));
  }, []);

  async function generate() {
    if (!text.trim() || !persona) return;
    setLoading(true);
    setErr(null);
    try {
      const u = await api.voicePreview(text.trim(), persona.gender, persona.id);
      setUrl(u);
      if (audioRef.current) { audioRef.current.src = u; await audioRef.current.play(); }
    } catch {
      setErr(t("error"));
    } finally {
      setLoading(false);
    }
  }

  const ready = Boolean(text.trim()) && Boolean(persona);
  const count = text.length;

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-6">
      {/* ── Eyebrow + tiêu đề (gọn, dồn trái) ─────────────────────────── */}
      <Reveal>
        <FilmLabel>{t("eyebrow")}</FilmLabel>
        <div className="mt-3 flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 className="font-display text-3xl font-extrabold leading-[1.05] text-ink-high lg:text-[40px]">
              {t.rich("title", { grad: (c) => <span className="text-gradient">{c}</span> })}
            </h1>
            <p className="mt-2 max-w-lg text-ink-medium">
              {t("subtitle")}
            </p>
          </div>
          <span className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-ink-low">
            <Mic className={cn("h-4 w-4", ACCENT.icon)} />
            {personas.length > 0 ? t("voicesReady", { count: personas.length }) : t("loadingVoices")}
          </span>
        </div>
      </Reveal>

      {/* ── BÀN TRỘN: 2 cột bất đối xứng — trái booth nhập, phải roster giọng ─ */}
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-12">
        {/* CỘT TRÁI — booth: lời thoại + sóng âm (signature) */}
        <Reveal className="lg:col-span-7" delay={0.05}>
          <section className="relative flex h-full flex-col overflow-hidden rounded-3xl glass-bordered">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/bg/ring.jpg" alt="" className="absolute inset-0 h-full w-full object-cover opacity-[0.12]" />
            <div className="absolute inset-0 bg-gradient-to-br from-bg-base/85 via-bg-base/92 to-bg-base" />
            <div
              className="pointer-events-none absolute -right-16 -top-16 h-56 w-56 rounded-full blur-3xl"
              style={{ background: ACCENT.glow }}
            />

            <div className="relative flex flex-1 flex-col gap-4 p-5 sm:p-6">
              <div className="flex items-center justify-between">
                <span className={cn("flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.18em]", ACCENT.text)}>
                  <Quote className="h-3.5 w-3.5" /> {t("scriptLabel")}
                </span>
                <span className={cn("text-[11px] tabular-nums", count >= 200 ? "text-danger" : "text-ink-low")}>
                  {count}/200
                </span>
              </div>

              {/* ô nhập lớn, không-viền-hộp — như màn hình tổng phổ */}
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                maxLength={200}
                placeholder={t("scriptPlaceholder")}
                aria-label={t("scriptAria")}
                className="min-h-[120px] flex-1 resize-none rounded-2xl border border-white/10 bg-white/[0.03] p-4 font-display text-lg leading-relaxed text-ink-high placeholder:text-ink-disabled focus:border-rose-400/50 focus:outline-none focus:ring-2 focus:ring-rose-500/20"
              />

              {/* ví dụ nhanh — chip dòng */}
              <div className="flex flex-wrap items-center gap-1.5">
                <span className="inline-flex items-center gap-1 text-xs text-ink-low">
                  <Sparkles className="h-3.5 w-3.5 text-rose-300" /> {t("examplesLabel")}
                </span>
                {EXAMPLE_KEYS.map((k) => {
                  const e = t(k);
                  return (
                    <button
                      key={k}
                      onClick={() => setText(e)}
                      className="rounded-lg border border-white/10 px-2.5 py-1 text-[11px] text-ink-low transition-colors hover:border-rose-400/40 hover:text-ink-medium active:scale-[0.98]"
                    >
                      {e.slice(0, 26)}…
                    </button>
                  );
                })}
              </div>

              {/* SÓNG ÂM — dải cột nhịp, sáng dần khi đang tạo (signature audio) */}
              <div
                className="relative mt-1 flex h-24 items-center gap-[3px] overflow-hidden rounded-2xl border border-white/10 bg-bg-surface/60 px-4"
                aria-hidden
              >
                {WAVE.map((h, i) => (
                  <span
                    key={i}
                    className={cn(
                      "w-[3px] flex-1 rounded-full transition-all duration-300",
                      loading ? "animate-pulse" : "",
                      ready || loading ? "bg-gradient-to-t from-rose-500/40 to-pink-400/90" : "bg-white/12",
                    )}
                    style={{
                      height: `${ready || loading ? h : Math.max(10, h * 0.35)}%`,
                      animationDelay: loading ? `${(i % 8) * 70}ms` : undefined,
                    }}
                  />
                ))}
                {!ready && !loading && (
                  <span className="pointer-events-none absolute inset-0 grid place-items-center text-xs text-ink-low">
                    {t("wavePlaceholder")}
                  </span>
                )}
              </div>
            </div>
          </section>
        </Reveal>

        {/* CỘT PHẢI — roster giọng (chọn ai sẽ đọc) */}
        <Reveal className="lg:col-span-5" delay={0.1}>
          <section className="flex h-full flex-col gap-3 rounded-3xl glass-bordered p-5 sm:p-6">
            <div className="flex items-center justify-between">
              <span className={cn("flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.18em]", ACCENT.text)}>
                <Mic className="h-3.5 w-3.5" /> {t("chooseVoice")}
              </span>
              <span className="text-[11px] text-ink-low">{t("eachVoice")}</span>
            </div>

            {personas.length === 0 ? (
              <div className="flex flex-col gap-2.5">
                {[0, 1, 2, 3].map((i) => (
                  <div key={i} className="h-[58px] animate-pulse rounded-2xl border border-white/[0.06] bg-white/[0.03]" />
                ))}
              </div>
            ) : (
              <div className="flex flex-col gap-2.5 overflow-y-auto pr-0.5">
                {personas.map((p) => {
                  const active = persona?.id === p.id;
                  const female = p.gender === "female";
                  return (
                    <button
                      key={p.id}
                      onClick={() => setPersona(p)}
                      aria-pressed={active}
                      aria-label={t("selectVoiceAria", { name: p.name })}
                      className={cn(
                        "group flex items-center gap-3 rounded-2xl border p-3 text-left transition-all duration-200 active:scale-[0.99]",
                        active
                          ? "border-rose-500/60 bg-rose-500/10 shadow-glow-sm"
                          : "border-white/10 hover:-translate-y-0.5 hover:border-white/25",
                      )}
                    >
                      <span
                        className={cn(
                          "grid h-11 w-11 shrink-0 place-items-center rounded-full text-base font-bold ring-1",
                          female
                            ? "bg-rose-500/15 text-rose-200 ring-rose-400/30"
                            : "bg-sky-500/15 text-sky-200 ring-sky-400/30",
                        )}
                      >
                        {p.name.charAt(0)}
                      </span>
                      <span className="min-w-0 flex-1">
                        <span className="flex items-center gap-2">
                          <span className="truncate text-sm font-semibold text-ink-high">{p.name}</span>
                          <span className={cn("text-[10px] uppercase tracking-wide", female ? "text-rose-300/80" : "text-sky-300/80")}>
                            {female ? t("female") : t("male")}
                          </span>
                        </span>
                        <span className="block truncate text-[11px] text-ink-low">{p.vibe}</span>
                      </span>
                      <span
                        className={cn(
                          "grid h-7 w-7 shrink-0 place-items-center rounded-full transition",
                          active ? "bg-rose-500/20 text-rose-200" : "text-ink-low group-hover:text-ink-medium",
                        )}
                      >
                        <Play className="h-3.5 w-3.5" />
                      </span>
                    </button>
                  );
                })}
              </div>
            )}
          </section>
        </Reveal>
      </div>

      {/* ── THANH ĐIỀU KHIỂN (transport bar) — dính đáy nội dung ───────── */}
      <Reveal delay={0.15}>
        <section className="relative overflow-hidden rounded-3xl glass-bordered p-4 sm:p-5">
          <div
            className="pointer-events-none absolute -left-10 bottom-0 h-32 w-32 rounded-full blur-3xl"
            style={{ background: ACCENT.glow }}
          />
          <div className="relative flex flex-wrap items-center gap-3">
            <div className="flex min-w-0 flex-1 items-center gap-3">
              <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-grad-brand-soft">
                <AudioLines className="h-5 w-5 text-rose-200" />
              </span>
              <div className="min-w-0">
                <div className="truncate text-sm font-medium text-ink-high">
                  {persona ? t("readBy", { name: persona.name }) : t("noVoice")}
                </div>
                <div className="text-[11px] text-ink-low">
                  {ready ? t("readyToCreate") : t("needInput")}
                </div>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              {err && (
                <span className="flex items-center gap-1.5 text-sm text-danger">
                  <AlertCircle className="h-4 w-4" /> {err}
                </span>
              )}
              {url && (
                <a href={url} download="vyra-audio.mp3" aria-label={t("downloadMp3Aria")}>
                  <Button variant="glass" className="gap-2"><Download className="h-4 w-4" /> {t("downloadMp3")}</Button>
                </a>
              )}
              <Button onClick={generate} disabled={loading || !ready} className="gap-2">
                {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <AudioLines className="h-4 w-4" />}
                {loading ? t("generating") : t("generate")}
              </Button>
            </div>
          </div>

          <audio ref={audioRef} controls hidden={!url} className="relative mt-4 w-full" />
        </section>
      </Reveal>
    </div>
  );
}
