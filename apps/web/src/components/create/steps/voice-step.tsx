"use client";

import { useEffect, useRef, useState } from "react";
import { useTranslations } from "next-intl";
import { Volume2, UserSquare2, ShieldCheck, Loader2, AlertCircle, Play } from "lucide-react";
import { useWizard } from "@/store/wizard";
import { api } from "@/lib/api/endpoints";
import type { VoicePersona } from "@/lib/api/types";
import { Field, inputCls } from "@/components/ui/field";
import { Button } from "@/components/ui/button";
import { KolPicker } from "@/components/create/kol-picker";
import { cn } from "@/lib/utils/cn";

const SAMPLE = "Da bạn sẽ căng mướt và rạng rỡ chỉ sau bảy ngày sử dụng.";

export function VoiceStep() {
  const t = useTranslations("create");
  const w = useWizard();
  const isKol = w.videoType === "kol_full";
  const [text, setText] = useState(SAMPLE);
  const [loading, setLoading] = useState(false);
  const [previewing, setPreviewing] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [personas, setPersonas] = useState<VoicePersona[]>([]);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    api.voicePersonas().then(setPersonas).catch(() => setPersonas([]));
  }, []);

  async function playUrl(url: string) {
    if (audioRef.current) {
      audioRef.current.src = url;
      await audioRef.current.play();
    }
  }

  async function play() {
    setLoading(true);
    setErr(null);
    try {
      await playUrl(await api.voicePreview(text.trim() || SAMPLE, w.voiceGender || "female", w.voicePersona));
    } catch {
      setErr(t("previewVoiceError"));
    } finally {
      setLoading(false);
    }
  }

  async function pickPersona(p: VoicePersona) {
    w.patch({ voicePersona: p.id, voiceGender: p.gender as "female" | "male" });
    setPreviewing(p.id);
    setErr(null);
    try {
      await playUrl(await api.voicePreview(text.trim() || SAMPLE, p.gender, p.id));
    } catch {
      setErr(t("previewVoiceError"));
    } finally {
      setPreviewing(null);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-xl font-bold text-ink-high">{isKol ? t("voiceKolTitle") : t("voiceTitle")}</h2>
        <p className="mt-1 text-sm text-ink-low">
          {t("voiceSubtitle")}
        </p>
      </div>

      <Field label={t("voiceLabel")} hint={t("voiceFieldHint")}>
        <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
          {personas.map((p) => {
            const active = w.voicePersona === p.id;
            return (
              <button
                key={p.id}
                type="button"
                onClick={() => pickPersona(p)}
                className={cn(
                  "group flex items-center gap-3 rounded-xl border p-3 text-left transition-colors",
                  active ? "border-violet-500/60 bg-violet-500/10" : "border-white/10 hover:border-white/25",
                )}
              >
                <span className={cn(
                  "grid h-9 w-9 shrink-0 place-items-center rounded-full text-sm font-bold",
                  p.gender === "female" ? "bg-rose-500/15 text-rose-200" : "bg-sky-500/15 text-sky-200",
                )}>
                  {previewing === p.id ? <Loader2 className="h-4 w-4 animate-spin" /> : p.name.charAt(0)}
                </span>
                <span className="min-w-0 flex-1">
                  <span className="flex items-center gap-1.5 text-sm font-medium text-ink-high">
                    {p.name}
                    <span className="text-[11px] font-normal text-ink-low">· {p.gender === "female" ? t("genderFemale") : t("genderMale")}</span>
                  </span>
                  <span className="block truncate text-xs text-ink-low">{p.vibe}</span>
                </span>
                <Play className={cn("h-4 w-4 shrink-0", active ? "text-violet-300" : "text-ink-low opacity-0 transition-opacity group-hover:opacity-100")} />
              </button>
            );
          })}
        </div>
        {w.voicePersona && (
          <p className="mt-2 text-xs text-ink-low">
            {personas.find((p) => p.id === w.voicePersona)?.blurb}
          </p>
        )}
      </Field>

      {/* nghe thử / đọc thử câu của tôi */}
      <div className="flex flex-col gap-3 rounded-xl border border-white/10 bg-white/[0.02] p-4">
        <div className="flex items-center gap-2 text-sm font-medium text-ink-medium">
          <Volume2 className="h-4 w-4 text-violet-300" /> {t("readYourSentence")}
        </div>
        <textarea
          className={cn(inputCls, "min-h-[64px] resize-y")}
          value={text}
          onChange={(e) => setText(e.target.value)}
          maxLength={200}
          placeholder={t("sentencePlaceholder")}
        />
        <div className="flex items-center gap-3">
          <Button variant="glass" size="sm" onClick={play} disabled={loading} className="gap-2">
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Volume2 className="h-4 w-4" />}
            {loading ? t("generatingVoice") : t("preview")}
          </Button>
          {err && (
            <span className="flex items-center gap-1.5 text-sm text-danger">
              <AlertCircle className="h-4 w-4" /> {err}
            </span>
          )}
        </div>
        <audio ref={audioRef} hidden />
      </div>

      {/* persona KOL — chỉ khi videoType=kol_full */}
      {isKol && (
        <div className="flex flex-col gap-4 rounded-xl border border-violet-500/25 bg-violet-500/[0.05] p-4">
          <div className="flex items-center gap-2 text-sm font-medium text-violet-200">
            <UserSquare2 className="h-4 w-4" /> {t("kolCharacter")}
          </div>

          {/* chọn gương mặt KOL — như autovis */}
          <div>
            <p className="mb-2 text-xs text-ink-low">{t("kolPickFace")}</p>
            <KolPicker />
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <Field label={t("kolName")}>
              <input
                className={inputCls}
                value={w.kolName}
                onChange={(e) => w.patch({ kolName: e.target.value })}
                placeholder="Mai Anh"
              />
            </Field>
            <Field label={t("kolStyle")}>
              <input
                className={inputCls}
                value={w.kolStyle}
                onChange={(e) => w.patch({ kolStyle: e.target.value })}
                placeholder={t("kolStylePlaceholder")}
              />
            </Field>
          </div>

          <label className="flex cursor-pointer items-start gap-3 rounded-lg border border-white/10 bg-white/[0.02] p-3">
            <input
              type="checkbox"
              checked={w.consent}
              onChange={(e) => w.patch({ consent: e.target.checked })}
              className="mt-0.5 h-4 w-4 accent-violet-500"
            />
            <span className="flex items-start gap-2 text-sm text-ink-medium">
              <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-violet-300" />
              {t("consentLabel")}
            </span>
          </label>
        </div>
      )}
    </div>
  );
}
