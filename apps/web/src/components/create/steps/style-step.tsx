"use client";

import { useTranslations } from "next-intl";
import { Zap, Clapperboard, Gauge, Lock } from "lucide-react";
import { useWizard } from "@/store/wizard";
import { Field, ChipGroup, inputCls } from "@/components/ui/field";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils/cn";
import { ScriptStudio } from "./script-studio";
import { SceneBuilder } from "./scene-builder";

// name = tên thương hiệu (giữ nguyên); noteKey hiển thị lấy từ i18n.
const ENGINES = [
  { id: "seedance", name: "Seedance", noteKey: "engineNoteSeedance", icon: Zap, available: true },
  { id: "veo", name: "Veo 3.1", noteKey: "engineNoteVeo", icon: Clapperboard, available: false },
  { id: "kling", name: "Kling 3.0", noteKey: "engineNoteKling", icon: Clapperboard, available: false },
  { id: "hailuo", name: "Hailuo", noteKey: "engineNoteHailuo", icon: Gauge, available: false },
];

// Hộp xem trước tỷ lệ (px) — gợi hình dáng khung mà không cần ảnh.
const ASPECTS = [
  { value: "9:16", labelKey: "aspectVertical", box: { width: 18, height: 32 } },
  { value: "1:1", labelKey: "aspectSquare", box: { width: 28, height: 28 } },
  { value: "16:9", labelKey: "aspectHorizontal", box: { width: 32, height: 18 } },
];

// Thẻ trực quan (thay chip trần): mỗi lựa chọn kèm 1 gợi ý ngắn để bấm-chọn không cần đoán.
const DURATIONS = [
  { s: 5, hint: "Hook nhanh" },
  { s: 8, hint: "Chuẩn bán hàng" },
  { s: 10, hint: "Đủ ý" },
  { s: 15, hint: "Kể chuyện" },
];
const RESOLUTIONS = [
  { v: "480p", hint: "Nhẹ, rẻ" },
  { v: "720p", hint: "Khuyên dùng" },
  { v: "1080p", hint: "Nét nhất" },
];

export function StyleStep() {
  const t = useTranslations("create");
  const w = useWizard();

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-xl font-bold text-ink-high">{t("styleTitle")}</h2>
        <p className="mt-1 text-sm text-ink-low">{t("styleSubtitle")}</p>
      </div>

      <Field label={t("purpose")}>
        <ChipGroup
          value={w.purpose}
          onChange={(v) => w.patch({ purpose: v })}
          options={[
            { value: "final", label: t("purposeFinal") },
            { value: "draft", label: t("purposeDraft") },
          ]}
        />
      </Field>

      <div className="grid gap-5 sm:grid-cols-2">
        <Field label={t("duration")}>
          <div className="grid grid-cols-4 gap-2">
            {DURATIONS.map((d) => {
              const active = w.seconds === d.s;
              return (
                <button
                  key={d.s}
                  type="button"
                  onClick={() => w.patch({ seconds: d.s })}
                  className={cn(
                    "flex flex-col items-center gap-0.5 rounded-xl border py-2.5 transition-colors",
                    active ? "border-violet-500/60 bg-violet-500/10" : "border-white/10 hover:border-white/25",
                  )}
                >
                  <span className={cn("font-numeric text-base font-bold", active ? "text-ink-high" : "text-ink-medium")}>{d.s}s</span>
                  <span className="text-[10px] leading-tight text-ink-low">{d.hint}</span>
                </button>
              );
            })}
          </div>
        </Field>

        <Field label={t("resolution")}>
          <div className="grid grid-cols-3 gap-2">
            {RESOLUTIONS.map((r) => {
              const active = w.resolution === r.v;
              return (
                <button
                  key={r.v}
                  type="button"
                  onClick={() => w.patch({ resolution: r.v })}
                  className={cn(
                    "flex flex-col items-center gap-0.5 rounded-xl border py-2.5 transition-colors",
                    active ? "border-violet-500/60 bg-violet-500/10" : "border-white/10 hover:border-white/25",
                  )}
                >
                  <span className={cn("text-sm font-semibold", active ? "text-ink-high" : "text-ink-medium")}>{r.v}</span>
                  <span className="text-[10px] leading-tight text-ink-low">{r.hint}</span>
                </button>
              );
            })}
          </div>
        </Field>
      </div>

      <Field label={t("aspectRatio")} hint={t("aspectHint")}>
        <div className="grid grid-cols-3 gap-3">
          {ASPECTS.map((a) => {
            const active = w.aspect === a.value;
            return (
              <button
                key={a.value}
                type="button"
                onClick={() => w.patch({ aspect: a.value })}
                className={cn(
                  "flex flex-col items-center gap-2 rounded-xl border p-3 transition-colors",
                  active ? "border-violet-500/60 bg-violet-500/10" : "border-white/10 hover:border-white/25",
                )}
              >
                <span
                  className={cn("rounded-sm border", active ? "border-violet-300 bg-violet-500/20" : "border-ink-low/50")}
                  style={a.box}
                />
                <span className={cn("text-xs font-medium", active ? "text-ink-high" : "text-ink-low")}>{a.value}</span>
                <span className="text-[10px] text-ink-low">{t(a.labelKey)}</span>
              </button>
            );
          })}
        </div>
      </Field>

      <div className="border-t border-white/[0.06] pt-6 font-display text-base font-semibold text-ink-high">
        {t("engineAndScript")}
      </div>

      <Field label={t("videoEngine")} hint={t("engineHint")}>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {ENGINES.map((e) => {
            const active = w.videoEngine === e.id;
            return (
              <button
                key={e.id}
                type="button"
                disabled={!e.available}
                onClick={() => e.available && w.patch({ videoEngine: e.id })}
                className={cn(
                  "relative flex flex-col items-start gap-1.5 rounded-xl border p-3 text-left transition-colors",
                  active
                    ? "border-violet-500/60 bg-violet-500/10 shadow-glow-sm"
                    : "border-white/10",
                  e.available ? "hover:border-white/20" : "opacity-50",
                )}
              >
                <e.icon className={cn("h-5 w-5", active ? "text-violet-300" : "text-ink-low")} />
                <span className="text-sm font-medium text-ink-high">{e.name}</span>
                <span className="text-[11px] leading-tight text-ink-low">{t(e.noteKey)}</span>
                {!e.available && (
                  <Badge tone="neutral" className="absolute right-2 top-2 gap-1 px-2 py-0.5">
                    <Lock className="h-2.5 w-2.5" /> M2
                  </Badge>
                )}
              </button>
            );
          })}
        </div>
      </Field>

      <Field label={t("scriptAndIdeas")} hint={t("scriptHint")}>
        <SceneBuilder />
        <div className="mt-3">
          <ScriptStudio />
        </div>
        <textarea
          className={cn(inputCls, "mt-3 min-h-[72px] resize-y")}
          value={w.brief}
          onChange={(e) => w.patch({ brief: e.target.value })}
          placeholder={t("briefPlaceholder")}
        />
      </Field>
    </div>
  );
}
