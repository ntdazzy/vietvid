"use client";

import { useEffect, useState } from "react";
import { ArrowLeft, ArrowRight, Sparkles, Loader2, AlertCircle, Layers } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useWizard, freshKey, type WizardStep } from "@/store/wizard";
import { FEATURE_PRESETS } from "@/lib/features";
import { api } from "@/lib/api/endpoints";
import { useCreateJob } from "@/lib/query/mutations";
import { Stepper } from "@/components/create/stepper";
import { SourceStep } from "@/components/create/steps/source-step";
import { StyleStep } from "@/components/create/steps/style-step";
import { VoiceStep } from "@/components/create/steps/voice-step";
import { PreviewStep } from "@/components/create/steps/preview-step";
import { RenderTimeline } from "@/components/create/render-timeline";
import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api/client";
import type { JobCreateRequest } from "@/lib/api/types";

export default function CreatePage() {
  const w = useWizard();
  const router = useRouter();
  const create = useCreateJob();
  const [error, setError] = useState<string | null>(null);
  const [insufficient, setInsufficient] = useState(false);
  const [seriesCount, setSeriesCount] = useState(1);
  const [seriesTarget, setSeriesTarget] = useState("");
  const [seriesBusy, setSeriesBusy] = useState(false);

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
    if (brandId) w.patch({ brandKitId: brandId });
    (async () => {
      if (templateId) {
        const t = (await api.templates().catch(() => [])).find((x) => x.id === templateId);
        if (t) {
          const p = (t.preset ?? {}) as { videoType?: string; brief?: string; frameMode?: string };
          w.patch({
            templateId: t.id,
            videoType: (p.videoType as "product_ad" | "kol_full") ?? w.videoType,
            brief: typeof p.brief === "string" ? p.brief : w.brief,
            frameMode: (p.frameMode as "upload" | "ai") ?? "upload",
            step: 1,
          });
        }
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
        else setError(e instanceof Error ? e.message : "Tạo video thất bại");
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
      else setError(e instanceof Error ? e.message : "Tạo loạt thất bại");
    } finally {
      setSeriesBusy(false);
    }
  }

  return (
    <div className="flex flex-col gap-8">
      <Stepper step={w.step} />

      <div className="min-h-[320px]">
        {w.step === 1 && <SourceStep />}
        {w.step === 2 && <StyleStep />}
        {w.step === 3 && <VoiceStep />}
        {w.step === 4 && <PreviewStep />}
        {w.step === 5 && w.jobId && <RenderTimeline jobId={w.jobId} onReset={handleReset} />}
      </div>

      {insufficient && (
        <div className="flex items-center justify-between gap-3 rounded-xl border border-hold/30 bg-hold/[0.1] px-4 py-3 text-sm text-hold">
          <span className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4" /> Không đủ credit cho video này.
          </span>
          <Link href="/app/billing" className="font-medium underline">
            Nạp thêm
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
            <div className="text-sm font-medium text-ink-high">Số biến thể (auto-series)</div>
            <div className="text-xs text-ink-low">
              Tạo nhiều video từ 1 sản phẩm, mỗi bản một góc nhìn khác (A/B).
            </div>
          </div>
          <div className="flex gap-1">
            {[1, 2, 3, 5].map((n) => (
              <button
                key={n}
                onClick={() => setSeriesCount(n)}
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
          placeholder="Link sản phẩm (Shopee/TikTok Shop...) — gắn để ĐO biến thể nào bán chạy"
          className="w-full rounded-xl border border-white/10 bg-white/[0.02] px-4 py-2.5 text-sm text-ink-high placeholder:text-ink-low focus:border-violet-400/40 focus:outline-none"
        />
      )}

      {/* footer nav (ẩn ở bước Tạo) */}
      {w.step !== 5 && (
        <div className="flex items-center justify-between border-t border-white/[0.06] pt-5">
          <Button variant="ghost" onClick={back} disabled={w.step === 1} className="gap-1.5">
            <ArrowLeft className="h-4 w-4" /> Quay lại
          </Button>

          {w.step < 4 ? (
            <Button onClick={next} disabled={!canNext} className="gap-1.5">
              Tiếp tục <ArrowRight className="h-4 w-4" />
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
                ? "Đang tạo…"
                : seriesCount > 1
                  ? `Tạo ${seriesCount} video`
                  : "Tạo video"}
            </Button>
          )}
        </div>
      )}

      {w.step === 1 && !w.product.image_path && (
        <p className="text-center text-xs text-ink-low">Tải ảnh sản phẩm để tiếp tục.</p>
      )}
      {w.step === 3 && needsConsent && (
        <p className="text-center text-xs text-hold">
          Tích ô đồng ý ở phần "Nhân vật KOL" để tiếp tục.
        </p>
      )}
    </div>
  );
}
