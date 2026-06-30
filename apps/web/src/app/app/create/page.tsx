"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { ArrowLeft, ArrowRight, Sparkles, Loader2, AlertCircle, Layers } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { useWizard, freshKey, type WizardStep, type VideoType } from "@/store/wizard";
import { FEATURE_PRESETS } from "@/lib/features";
import { api } from "@/lib/api/endpoints";
import { useCreateJob } from "@/lib/query/mutations";
import { Stepper } from "@/components/create/stepper";
import { SourceStep } from "@/components/create/steps/source-step";
import { StyleStep } from "@/components/create/steps/style-step";
import { VoiceStep } from "@/components/create/steps/voice-step";
import { PreviewStep } from "@/components/create/steps/preview-step";
import { RenderTimeline } from "@/components/create/render-timeline";
import { PreviewRail } from "@/components/create/preview-rail";
import { MobileCostBar } from "@/components/create/mobile-cost-bar";
import { Launchpad, type Genre } from "@/components/create/launchpad";
import { GenreContextBar } from "@/components/create/genre-context-bar";
import { StudioShell } from "@/components/studio/studio-shell";
import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api/client";
import type { JobCreateRequest, Template } from "@/lib/api/types";

// có tín hiệu preset trên URL → vào thẳng configurator, bỏ qua launchpad.
function hasPresetSignal() {
  if (typeof window === "undefined") return false;
  const q = new URLSearchParams(window.location.search);
  return Boolean(q.get("feature") || q.get("template") || q.get("kol") || q.get("brand") || q.get("character"));
}

export default function CreatePage() {
  const t = useTranslations("create");
  const w = useWizard();
  const router = useRouter();
  const create = useCreateJob();
  const [error, setError] = useState<string | null>(null);
  const [insufficient, setInsufficient] = useState(false);
  const [seriesCount, setSeriesCount] = useState(1);
  const [seriesTarget, setSeriesTarget] = useState("");
  const [seriesBusy, setSeriesBusy] = useState(false);
  // Moment 0 (launchpad) vs Moment 1 (configurator). Bỏ qua launchpad nếu có preset URL
  // hoặc phiên dở đang có ảnh/mẫu (sessionStorage rehydrate) — không nháy về gallery.
  const [launched, setLaunched] = useState(
    () => hasPresetSignal() || Boolean(w.product.image_path || w.templateId),
  );
  const [picked, setPicked] = useState<Genre | null>(null); // thể loại đã chọn (accent + ngữ cảnh configurator)
  const genreAccent = picked?.accent ?? "violet";

  const templates = useQuery({ queryKey: ["templates"], queryFn: api.templates, staleTime: 300_000 });
  const templateName = templates.data?.find((t) => t.id === w.templateId)?.name ?? "";

  // áp một mẫu vào wizard (dùng chung cho click gallery + deep-link ?template=).
  function applyTemplate(t: Template) {
    const p = (t.preset ?? {}) as { videoType?: string; brief?: string; frameMode?: string };
    w.patch({
      templateId: t.id,
      videoType: (p.videoType as VideoType) ?? w.videoType,
      brief: typeof p.brief === "string" ? p.brief : w.brief,
      frameMode: (p.frameMode as "upload" | "ai") ?? "upload",
      step: 1,
    });
  }

  // chọn thể loại (Moment 0 genre-first) → set wizard + vào configurator.
  function pickGenre(g: Genre) {
    w.patch({ videoType: g.videoType, brief: g.brief, frameMode: g.frameMode, templateId: "", step: 1 });
    setPicked(g);
    setLaunched(true);
  }

  // đảm bảo có idempotency_key cho lần tạo này
  useEffect(() => {
    if (!w.idempotencyKey) w.patch({ idempotencyKey: freshKey() });
  }, [w]);

  // preset theo ?feature= (menu mega) hoặc ?template=/?kol=/?brand= (gallery Sóng 4).
  useEffect(() => {
    const q = new URLSearchParams(window.location.search);
    const f = q.get("feature");
    const preset = f ? FEATURE_PRESETS[f] : undefined;
    if (preset)
      w.patch({
        videoType: preset.videoType,
        brief: preset.brief,
        frameMode: preset.frameMode ?? "upload",
        step: 1,
      });

    const templateId = q.get("template");
    const kolId = q.get("kol");
    const brandId = q.get("brand");
    const charId = q.get("character");
    if (brandId) w.patch({ brandKitId: brandId });
    (async () => {
      if (templateId) {
        const t = (await api.templates().catch(() => [])).find((x) => x.id === templateId);
        if (t) applyTemplate(t);
      }
      if (kolId) {
        const k = (await api.kolPersonas().catch(() => [])).find((x) => x.id === kolId);
        if (k) {
          w.patch({
            kolPersonaId: k.id,
            videoType: "kol_full",
            kolName: k.name,
            voiceGender: (k.voice_gender as "female" | "male") || "female",
            step: 1,
          });
        }
      }
      // Nhân vật (Studio): prefill brief quanh nhân vật (tier brief-level, chưa khoá gương mặt render).
      if (charId) {
        const c = (await api.characters().catch(() => [])).find((x) => x.id === charId);
        if (c) {
          w.patch({
            videoType: "kol_full",
            kolName: c.name,
            voiceGender: (c.voice_gender as "female" | "male") || "female",
            brief: c.description ? `Video có nhân vật ${c.name}: ${c.description}` : `Video có nhân vật ${c.name}`,
            frameMode: "ai",
            step: 1,
          });
        }
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const needsConsent = w.videoType === "kol_full" && !w.consent;
  const canNext =
    w.step === 1
      ? Boolean(w.product.image_path)
      : w.step === 3
        ? !needsConsent
        : true;

  function next() {
    if (w.step < 5) w.setStep((w.step + 1) as WizardStep);
  }
  function back() {
    if (w.step > 1) w.setStep((w.step - 1) as WizardStep);
  }
  function handleReset() {
    w.reset();
    setError(null);
    setInsufficient(false);
    setLaunched(false);
    setPicked(null);
  }

  function handleCreate() {
    setError(null);
    setInsufficient(false);
    const body: JobCreateRequest = {
      idempotency_key: w.idempotencyKey,
      mode: w.videoType,
      purpose: w.purpose,
      seconds: w.seconds,
      resolution: w.resolution,
      product: {
        name: w.product.name,
        category: w.product.category,
        price: w.product.price,
        description: w.product.description,
        image_path: w.product.image_path,
      },
      kol:
        w.videoType === "kol_full"
          ? { name: w.kolName, gender: w.voiceGender || "female", style: w.kolStyle }
          : null,
      params: {
        brief: w.brief,
        voice_gender: w.voiceGender || "female",
        voice_persona: w.voicePersona,
        aspect: w.aspect,
        video_engine: w.videoEngine,
        clean_clip: false,
      },
      template_id: w.templateId || undefined,
      kol_persona_id: w.kolPersonaId || undefined,
      brand_kit_id: w.brandKitId || undefined,
    };
    create.mutate(body, {
      onSuccess: (res) => w.patch({ jobId: res.job_id, step: 5 }),
      onError: (e) => {
        if (e instanceof ApiError && e.status === 402) setInsufficient(true);
        else setError(e instanceof Error ? e.message : t("errCreateFailed"));
      },
    });
  }

  async function handleSeries() {
    setError(null);
    setInsufficient(false);
    setSeriesBusy(true);
    try {
      const res = await api.createSeries({
        idempotency_key: w.idempotencyKey,
        count: seriesCount,
        mode: w.videoType,
        purpose: w.purpose,
        seconds: w.seconds,
        resolution: w.resolution,
        brief: w.brief,
        voice_gender: w.voiceGender || "female",
        voice_persona: w.voicePersona,
        product: {
          name: w.product.name,
          category: w.product.category,
          price: w.product.price,
          description: w.product.description,
          image_path: w.product.image_path,
        },
        template_id: w.templateId || undefined,
        kol_persona_id: w.kolPersonaId || undefined,
        brand_kit_id: w.brandKitId || undefined,
        target_url: seriesTarget.trim() || undefined,
      });
      w.reset();
      router.push(`/app/series/${res.series_group}`);
    } catch (e) {
      if (e instanceof ApiError && e.status === 402) setInsufficient(true);
      else setError(e instanceof Error ? e.message : t("errSeriesFailed"));
    } finally {
      setSeriesBusy(false);
    }
  }

  // ── MOMENT 0 — Genre-first: chọn thể loại (bản sắc riêng màn Create) ────
  if (w.step === 1 && !launched) {
    return (
      <StudioShell>
        <Launchpad
          onPickGenre={pickGenre}
          onBuildFromScratch={() => { w.patch({ templateId: "", step: 1 }); setLaunched(true); }}
          onPickTemplate={(t) => {
            if (t) applyTemplate(t);
            else w.patch({ templateId: "", step: 1 });
            setLaunched(true);
          }}
        />
      </StudioShell>
    );
  }

  // ── Render surface (sau khi tạo) — full width ─────────────────────────
  if (w.step === 5 && w.jobId) {
    return <RenderTimeline jobId={w.jobId} onReset={handleReset} />;
  }

  // ── MOMENT 1 — Configurator: hai cột (controls + preview rail) ─────────
  return (
    <StudioShell>
      <div className="grid grid-cols-1 gap-8 pb-32 lg:grid-cols-12 lg:gap-8 lg:pb-0">
        {/* LEFT — điều khiển */}
        <div className="flex flex-col gap-6 lg:col-span-7">
          {picked && (
            <GenreContextBar
              image={picked.image}
              label={picked.label}
              title={t(`genre.${picked.key}.title`)}
              sub={t(`genre.${picked.key}.desc`)}
              accent={picked.accent}
              changeLabel={t("change")}
              onChange={() => { w.setStep(1); setLaunched(false); setPicked(null); }}
            />
          )}
          <Stepper
            step={w.step}
            templateName={templateName}
            accent={genreAccent}
            onChangeTemplate={() => {
              w.setStep(1);
              setLaunched(false);
              setPicked(null);
            }}
          />

          <div className="min-h-[320px]">
            {w.step === 1 && <SourceStep />}
            {w.step === 2 && <StyleStep />}
            {w.step === 3 && <VoiceStep />}
            {w.step === 4 && <PreviewStep />}
          </div>

          {insufficient && (
            <div className="flex items-center justify-between gap-3 rounded-xl border border-hold/30 bg-hold/[0.1] px-4 py-3 text-sm text-hold">
              <span className="flex items-center gap-2">
                <AlertCircle className="h-4 w-4" /> {t("insufficientCredit")}
              </span>
              <Link href="/app/billing" className="font-medium underline">
                {t("topUp")}
              </Link>
            </div>
          )}
          {error && (
            <p className="flex items-center gap-2 text-sm text-danger">
              <AlertCircle className="h-4 w-4" /> {error}
            </p>
          )}

          {/* auto-series: số biến thể (chỉ ở bước Tạo) */}
          {w.step === 4 && (
            <div className="flex items-center gap-3 rounded-xl border border-white/[0.06] bg-white/[0.02] p-4">
              <Layers className="h-5 w-5 shrink-0 text-violet-300" />
              <div className="flex-1">
                <div className="text-sm font-medium text-ink-high">{t("variantCountTitle")}</div>
                <div className="text-xs text-ink-low">
                  {t("variantCountDesc")}
                </div>
              </div>
              <div className="flex gap-1">
                {[1, 2, 3, 5].map((n) => (
                  <button
                    key={n}
                    onClick={() => setSeriesCount(n)}
                    aria-pressed={seriesCount === n}
                    aria-label={t("createNVariants", { n })}
                    className={`grid h-9 w-9 place-items-center rounded-lg text-sm font-medium transition-colors ${
                      seriesCount === n
                        ? "bg-violet-500/20 text-ink-high"
                        : "text-ink-low hover:bg-white/[0.05]"
                    }`}
                  >
                    {n}
                  </button>
                ))}
              </div>
            </div>
          )}
          {w.step === 4 && seriesCount > 1 && (
            <input
              value={seriesTarget}
              onChange={(e) => setSeriesTarget(e.target.value)}
              placeholder={t("seriesTargetPlaceholder")}
              className="w-full rounded-xl border border-white/10 bg-white/[0.02] px-4 py-2.5 text-sm text-ink-high placeholder:text-ink-low focus:border-violet-400/40 focus:outline-none"
            />
          )}

          {/* footer nav */}
          <div className="flex items-center justify-between border-t border-white/[0.06] pt-5">
            <Button variant="ghost" onClick={back} disabled={w.step === 1} className="gap-1.5">
              <ArrowLeft className="h-4 w-4" /> {t("back")}
            </Button>

            {w.step < 4 ? (
              <Button onClick={next} disabled={!canNext} className="gap-1.5">
                {t("continue")} <ArrowRight className="h-4 w-4" />
              </Button>
            ) : (
              <Button
                onClick={() => (seriesCount > 1 ? handleSeries() : handleCreate())}
                disabled={create.isPending || seriesBusy || needsConsent}
                className="gap-2"
              >
                {create.isPending || seriesBusy ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Sparkles className="h-4 w-4" />
                )}
                {create.isPending || seriesBusy
                  ? t("creating")
                  : seriesCount > 1
                    ? t("createNVideos", { n: seriesCount })
                    : t("createVideo")}
              </Button>
            )}
          </div>

          {w.step === 1 && !w.product.image_path && (
            <p className="text-center text-xs text-ink-low">{t("uploadToContinue")}</p>
          )}
          {w.step === 3 && needsConsent && (
            <p className="text-center text-xs text-hold">
              {t("consentToContinue")}
            </p>
          )}
        </div>

        {/* RIGHT — preview rail dính (desktop) */}
        <div className="hidden lg:col-span-5 lg:block">
          <div className="lg:sticky lg:top-28">
            <PreviewRail />
          </div>
        </div>
      </div>

      {/* mobile: thanh chi phí dính đáy */}
      <MobileCostBar />
    </StudioShell>
  );
}
