"use client";

import { useRef, useState } from "react";
import { useTranslations } from "next-intl";
import { UploadCloud, Loader2, ImageOff, Sparkles, Wand2, Link2, Check } from "lucide-react";
import { useWizard } from "@/store/wizard";
import { useUploadImage } from "@/lib/query/mutations";
import { api } from "@/lib/api/endpoints";
import { Field, ChipGroup, inputCls } from "@/components/ui/field";
import { Button } from "@/components/ui/button";
import { AdvancedDisclosure } from "@/components/create/advanced-disclosure";
import { BrandKitPicker } from "@/components/create/brand-kit-picker";
import { cn } from "@/lib/utils/cn";

export function SourceStep() {
  const t = useTranslations("create");
  const w = useWizard();
  const upload = useUploadImage();
  const inputRef = useRef<HTMLInputElement>(null);
  const [genPrompt, setGenPrompt] = useState("");
  const [genLoading, setGenLoading] = useState(false);
  const [genErr, setGenErr] = useState<string | null>(null);
  const [impUrl, setImpUrl] = useState("");
  const [impBusy, setImpBusy] = useState(false);
  const [impMsg, setImpMsg] = useState<{ kind: "ok" | "err"; text: string } | null>(null);

  async function importProduct() {
    if (!impUrl.trim()) return;
    setImpBusy(true);
    setImpMsg(null);
    try {
      const d = await api.importProduct(impUrl.trim());
      w.patchProduct({
        name: d.name || w.product.name,
        description: d.description || w.product.description,
        price: d.price ? `${Number(d.price).toLocaleString("vi-VN")}đ` : w.product.price,
      });
      if (d.image_url) w.patch({ imagePreviewUrl: d.image_url });
      setImpMsg({ kind: "ok", text: d.name ? t("importGot", { name: d.name }) : t("importPartial") });
    } catch (e) {
      setImpMsg({ kind: "err", text: e instanceof Error ? e.message : t("importFailed") });
    } finally {
      setImpBusy(false);
    }
  }

  function onFile(file: File | undefined) {
    if (!file) return;
    w.patch({ imagePreviewUrl: URL.createObjectURL(file) });
    upload.mutate(file, { onSuccess: (res) => w.patchProduct({ image_path: res.image_path }) });
  }

  async function genFrame() {
    if (genPrompt.trim().length < 3) return;
    setGenLoading(true);
    setGenErr(null);
    try {
      const { url, path } = await api.generateImage(genPrompt.trim(), "9:16");
      w.patch({ imagePreviewUrl: url });
      w.patchProduct({ image_path: path });
    } catch (e) {
      setGenErr(e instanceof Error ? e.message : t("genImageError"));
    } finally {
      setGenLoading(false);
    }
  }

  const ai = w.frameMode === "ai";

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-xl font-bold text-ink-high">{t("sourceTitle")}</h2>
        <p className="mt-1 text-sm text-ink-low">
          {t("sourceSubtitle")}
        </p>
      </div>

      {/* Auto-ad: dán link sản phẩm → tự điền */}
      <div className="rounded-xl border border-violet-500/20 bg-violet-500/[0.04] p-3">
        <div className="mb-2 flex items-center gap-1.5 text-xs font-medium text-violet-200">
          <Link2 className="h-3.5 w-3.5" /> {t("quickPasteLink")}
        </div>
        <div className="flex gap-2">
          <input
            className={cn(inputCls, "flex-1")}
            value={impUrl}
            onChange={(e) => setImpUrl(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && importProduct()}
            placeholder="https://shopee.vn/..."
          />
          <Button variant="glass" onClick={importProduct} disabled={impBusy || !impUrl.trim()} className="gap-1.5">
            {impBusy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4 text-violet-300" />}
            {t("fetch")}
          </Button>
        </div>
        {impMsg && (
          <p className={cn("mt-2 flex items-center gap-1.5 text-xs", impMsg.kind === "ok" ? "text-success" : "text-danger")}>
            {impMsg.kind === "ok" && <Check className="h-3.5 w-3.5" />} {impMsg.text}
          </p>
        )}
      </div>

      {/* "Vyra đã hiểu SP" — định vị CHỐT ĐƠN: hiện khi có tên SP (từ link hoặc gõ tay).
          Cho người bán thấy AI đã nắm được gì trước khi dựng → tin tưởng luồng. */}
      {w.product.name.trim() && (
        <div className="rounded-xl border border-success/25 bg-success/[0.05] p-3.5">
          <div className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-success">
            <Check className="h-3.5 w-3.5" /> Vyra đã hiểu sản phẩm của bạn
          </div>
          <div className="flex flex-wrap gap-1.5">
            <span className="rounded-md bg-white/[0.06] px-2 py-0.5 text-[11px] text-ink-medium">
              Tên: <span className="text-ink-high">{w.product.name}</span>
            </span>
            {w.product.price.trim() && (
              <span className="rounded-md bg-white/[0.06] px-2 py-0.5 text-[11px] text-ink-medium">
                Giá: <span className="text-ink-high">{w.product.price}</span>
              </span>
            )}
            {w.product.category.trim() && (
              <span className="rounded-md bg-white/[0.06] px-2 py-0.5 text-[11px] text-ink-medium">
                Ngành: <span className="text-ink-high">{w.product.category}</span>
              </span>
            )}
          </div>
          <p className="mt-2 text-[11px] text-ink-low">
            Bước sau, AI tự viết <span className="text-ink-medium">kịch bản chốt đơn</span> tiếng Việt (có hook + kêu gọi mua) từ thông tin này.
          </p>
        </div>
      )}

      <Field label={t("videoTypeLabel")}>
        <ChipGroup
          value={w.videoType}
          onChange={(v) => w.patch({ videoType: v as "product_ad" | "kol_full" })}
          options={[
            { value: "product_ad", label: t("videoTypeProduct") },
            { value: "kol_full", label: t("videoTypeKol") },
          ]}
        />
      </Field>

      <Field label={t("frameLabel")}>
        <ChipGroup
          value={w.frameMode}
          onChange={(v) => w.patch({ frameMode: v as "upload" | "ai" })}
          options={[
            { value: "upload", label: t("frameUpload") },
            { value: "ai", label: t("frameAi") },
          ]}
        />
      </Field>

      {ai ? (
        <div className="flex flex-col gap-3">
          <textarea
            className={cn(inputCls, "min-h-[80px] resize-y")}
            value={genPrompt}
            onChange={(e) => setGenPrompt(e.target.value)}
            maxLength={500}
            placeholder={t("genPromptPlaceholder")}
          />
          <div className="flex flex-wrap items-center gap-3">
            <Button variant="glass" onClick={genFrame} disabled={genLoading || genPrompt.trim().length < 3} className="gap-2">
              {genLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Wand2 className="h-4 w-4 text-violet-300" />}
              {genLoading ? t("genFrameLoading") : t("genFrameBtn")}
            </Button>
            {genErr && <span className="text-sm text-danger">{genErr}</span>}
          </div>
          {w.imagePreviewUrl && (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={w.imagePreviewUrl} alt={t("frameAltShort")} className="max-h-72 w-auto self-start rounded-xl border border-white/10" />
          )}
          <p className="flex items-center gap-1.5 text-xs text-ink-low">
            <Sparkles className="h-3.5 w-3.5 text-violet-300" /> {t("aiFrameHint")}
          </p>
        </div>
      ) : (
        <>
          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            aria-label={t("uploadOrChangeAria")}
            className={cn(
              "relative grid aspect-video w-full place-items-center overflow-hidden rounded-xl border border-dashed transition-colors",
              w.imagePreviewUrl ? "border-violet-500/40" : "border-white/15 hover:border-violet-500/40 hover:bg-white/[0.02]",
            )}
          >
            {w.imagePreviewUrl ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={w.imagePreviewUrl} alt={t("productImageAlt")} className="h-full w-full object-contain" />
            ) : (
              <div className="flex flex-col items-center gap-2 text-ink-low">
                <UploadCloud className="h-7 w-7" />
                <span className="text-sm">{t("uploadHint")}</span>
              </div>
            )}
            {upload.isPending && (
              <div className="absolute inset-0 grid place-items-center bg-bg-base/60 backdrop-blur-sm">
                <Loader2 className="h-6 w-6 animate-spin text-violet-300" />
              </div>
            )}
            <input
              ref={inputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              className="hidden"
              onChange={(e) => onFile(e.target.files?.[0])}
            />
          </button>
          {upload.isError && (
            <p className="flex items-center gap-2 text-sm text-danger">
              <ImageOff className="h-4 w-4" /> {(upload.error as Error)?.message ?? t("uploadError")}
            </p>
          )}
        </>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        <Field label={t("productName")}>
          <input className={inputCls} value={w.product.name} onChange={(e) => w.patchProduct({ name: e.target.value })} placeholder={t("productNamePlaceholder")} />
        </Field>
        <Field label={t("price")}>
          <input className={inputCls} value={w.product.price} onChange={(e) => w.patchProduct({ price: e.target.value })} placeholder="199.000đ" />
        </Field>
        <Field label={t("category")}>
          <input className={inputCls} value={w.product.category} onChange={(e) => w.patchProduct({ category: e.target.value })} placeholder={t("categoryPlaceholder")} />
        </Field>
        <Field label={t("shortDescription")} className="sm:col-span-2">
          <textarea className={cn(inputCls, "min-h-[80px] resize-y")} value={w.product.description} onChange={(e) => w.patchProduct({ description: e.target.value })} placeholder={t("descriptionPlaceholder")} />
        </Field>
      </div>

      <AdvancedDisclosure label={t("advancedOptions")}>
        <Field label={t("brandKitField")} hint={t("brandKitHint")}>
          <BrandKitPicker />
        </Field>
      </AdvancedDisclosure>
    </div>
  );
}
