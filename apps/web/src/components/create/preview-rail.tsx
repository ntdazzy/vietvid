"use client";

import { useRef, useState, type ReactNode } from "react";
import { useTranslations } from "next-intl";
import { motion, AnimatePresence } from "framer-motion";
import { useQuery } from "@tanstack/react-query";
import { ImageIcon, Volume2, Loader2 } from "lucide-react";
import { useWizard } from "@/store/wizard";
import { useEstimate, useWallet } from "@/lib/query/hooks";
import { api } from "@/lib/api/endpoints";
import { CreditValue } from "@/components/ui/credit-value";
import { kolFace } from "@/lib/kol-faces";
import { HoldMeter } from "./hold-meter";
import { cn } from "@/lib/utils/cn";

const SAMPLE = "Da bạn sẽ căng mướt và rạng rỡ chỉ sau bảy ngày sử dụng.";

// kích thước khung theo tỷ lệ — framer-motion layout morph khi đổi.
const FRAME_SIZE: Record<string, { width: number; height: number }> = {
  "9:16": { width: 214, height: 380 },
  "1:1": { width: 300, height: 300 },
  "16:9": { width: 360, height: 203 },
};

/** Khung xem trước tỷ lệ thật — KHÔNG phải player giả: chỉ ảnh khung thật + caption thật. */
export function AspectFrame({ compact = false }: { compact?: boolean }) {
  const t = useTranslations("create");
  const w = useWizard();
  const size = FRAME_SIZE[w.aspect] ?? FRAME_SIZE["9:16"];
  const scale = compact ? 0.18 : 1;
  const briefLine = (w.brief || "").split("\n")[0].trim();

  const isKol = !compact && w.videoType === "kol_full";
  const kols = useQuery({ queryKey: ["kol-personas"], queryFn: api.kolPersonas, staleTime: 300_000, enabled: isKol });
  const kol = kols.data?.find((k) => k.id === w.kolPersonaId);
  const kolFaceUrl = kol ? kolFace(kol.name, kol.avatar_url) : "";

  return (
    <div className="grid w-full place-items-center" style={{ minHeight: compact ? 64 : 392 }}>
      <motion.div
        layout
        transition={{ type: "spring", stiffness: 220, damping: 26 }}
        style={{ width: size.width * scale, height: size.height * scale }}
        className="relative overflow-hidden rounded-[1.4rem] bg-grad-brand-soft ring-1 ring-white/10"
      >
        {w.imagePreviewUrl ? (
          // ảnh khung THẬT (tải lên / AI / bóc link) — không bịa
          // eslint-disable-next-line @next/next/no-img-element
          <img src={w.imagePreviewUrl} alt={t("frameAlt")} className="h-full w-full object-cover" />
        ) : (
          !compact && (
            <div className="flex h-full w-full flex-col items-center justify-center gap-2 px-4 text-center">
              <ImageIcon className="h-7 w-7 text-violet-300/70" />
              <span className="font-numeric text-xs text-ink-medium">
                {w.seconds}s · {w.resolution}
              </span>
              <span className="text-[11px] text-ink-low">{t("frameWillAppear")}</span>
            </div>
          )
        )}

        {isKol && kolFaceUrl && (
          <span className="absolute left-2 top-2 h-12 w-12 overflow-hidden rounded-full shadow-lg ring-2 ring-white/70">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={kolFaceUrl} alt={kol?.name ?? "KOL"} className="h-full w-full object-cover" />
          </span>
        )}

        {!compact && (
          <span className="absolute right-2 top-2 rounded-md bg-bg-base/70 px-1.5 py-0.5 font-numeric text-[10px] text-ink-medium backdrop-blur-sm">
            {w.aspect}
          </span>
        )}

        {!compact && briefLine && (
          <span className="absolute inset-x-2 bottom-2 line-clamp-2 rounded-md bg-bg-base/70 px-2 py-1 text-[11px] leading-snug text-ink-high backdrop-blur-sm">
            {briefLine}
          </span>
        )}
      </motion.div>
    </div>
  );
}

/** Tóm tắt cấu hình LIVE — đọc thẳng từ store, cập nhật theo từng thao tác. */
export function ConfigDigest() {
  const t = useTranslations("create");
  const w = useWizard();
  const personas = useQuery({ queryKey: ["voice-personas"], queryFn: api.voicePersonas, staleTime: 300_000 });
  const templates = useQuery({ queryKey: ["templates"], queryFn: api.templates, staleTime: 300_000 });
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [auditioning, setAuditioning] = useState(false);

  const personaName = personas.data?.find((p) => p.id === w.voicePersona)?.name;
  const templateName = templates.data?.find((t) => t.id === w.templateId)?.name;
  const voiceLabel = personaName || (w.voiceGender === "male" ? t("genderMale") : w.voiceGender === "female" ? t("genderFemale") : "");

  async function audition() {
    setAuditioning(true);
    try {
      const url = await api.voicePreview(SAMPLE, w.voiceGender || "female", w.voicePersona);
      if (audioRef.current) {
        audioRef.current.src = url;
        await audioRef.current.play();
      }
    } catch {
      /* nghe thử lỗi — bỏ qua, không chặn */
    } finally {
      setAuditioning(false);
    }
  }

  return (
    <dl className="divide-y divide-white/[0.06] rounded-xl bg-white/[0.02]">
      <Row k={t("digestVideoType")} v={w.videoType === "kol_full" ? t("videoTypeKol") : t("videoTypeProduct")} />
      <Row k={t("digestProduct")} v={w.product.name || undefined} />
      <Row k={t("digestSpecs")} v={<span className="font-numeric">{w.seconds}s · {w.resolution} · {w.aspect}</span>} />
      <Row k={t("digestEngine")} v="Vyra AI" />
      <Row
        k={t("digestVoice")}
        v={
          voiceLabel ? (
            <span className="flex items-center gap-2">
              {voiceLabel}
              <button
                type="button"
                onClick={audition}
                aria-label={t("auditionVoice")}
                className="grid h-6 w-6 place-items-center rounded-md text-ink-low transition-colors hover:bg-white/[0.06] hover:text-violet-300"
              >
                {auditioning ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Volume2 className="h-3.5 w-3.5" />}
              </button>
            </span>
          ) : undefined
        }
      />
      <Row k={t("digestEdition")} v={w.purpose === "draft" ? t("editionDraft") : t("editionFinal")} />
      {templateName && <Row k={t("digestTemplate")} v={templateName} />}
      <audio ref={audioRef} hidden />
    </dl>
  );
}

/** Pane phải dính — "bạn đang dựng gì": khung + tóm tắt + chi phí. */
export function PreviewRail() {
  const t = useTranslations("create");
  const w = useWizard();
  const est = useEstimate({ mode: w.videoType, purpose: w.purpose, seconds: w.seconds, resolution: w.resolution });
  const wallet = useWallet();

  return (
    <div className="glass-bordered flex flex-col gap-5 rounded-2xl p-5">
      {/* HUD "màn hình dựng" — chấm REC nhấp nháy + timecode → cảm giác monitor phòng dựng
          (KHÔNG dùng khung-ngắm 4 góc: đó là dấu hiệu autovis, đã cố ý bỏ). */}
      <div className="flex items-center justify-between text-[10px] font-medium uppercase tracking-[0.2em] text-ink-low">
        <span className="flex items-center gap-1.5">
          <span className="h-1.5 w-1.5 rounded-full bg-rose-500 shadow-[0_0_6px_rgba(244,63,94,0.8)] motion-safe:animate-pulse" />
          {t("previewMonitor")}
        </span>
        <span className="font-numeric tracking-normal">{w.aspect} · {w.seconds}s</span>
      </div>
      <AspectFrame />
      <ConfigDigest />

      {/* chi phí — bước 1-3: số ước tính lớn; bước 4: HoldMeter đầy đủ */}
      {w.step === 4 ? (
        <HoldMeter
          phase="estimate"
          balance={wallet.data?.balance_credits ?? 0}
          estCredits={est.data?.est_credits ?? 0}
          holdCredits={est.data?.hold_credits ?? 0}
        />
      ) : (
        <div className="relative overflow-hidden rounded-xl bg-white/[0.02] px-4 py-3">
          <div className="glow-radial pointer-events-none absolute inset-x-0 -top-8 h-16" />
          <div className="relative flex items-center justify-between">
            <span className="text-sm text-ink-low">{t("estimate")}</span>
            {est.isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin text-ink-low" />
            ) : (
              <AnimatePresence mode="wait">
                <motion.span
                  key={est.data?.est_credits ?? "?"}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.25 }}
                  className="font-numeric text-2xl font-bold text-ink-high"
                >
                  ~<CreditValue value={est.data?.est_credits ?? 0} className="text-2xl" />
                </motion.span>
              </AnimatePresence>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function Row({ k, v }: { k: string; v?: ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-3 px-3.5 py-2.5 text-sm">
      <dt className="shrink-0 text-ink-low">{k}</dt>
      <dd className={cn("truncate text-right", v ? "text-ink-high" : "text-ink-disabled")}>{v ?? "—"}</dd>
    </div>
  );
}

