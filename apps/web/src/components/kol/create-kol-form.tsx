"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { Loader2, Upload, ShieldCheck } from "lucide-react";
import { api } from "@/lib/api/endpoints";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Field, inputCls, ChipGroup } from "@/components/ui/field";

export function CreateKol({ onDone }: { onDone: () => void }) {
  const t = useTranslations("kol");
  const [mode, setMode] = useState<"ai" | "upload">("ai");
  const [name, setName] = useState("");
  const [desc, setDesc] = useState("");
  const [voice, setVoice] = useState<"female" | "male">("female");
  const [avatar, setAvatar] = useState("");
  const [consent, setConsent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function upload(file: File) {
    setBusy(true);
    try {
      const r = await api.uploadImage(file);
      setAvatar(r.image_path);
    } catch {
      setErr(t("errUpload"));
    } finally {
      setBusy(false);
    }
  }

  async function submit() {
    setErr(null);
    setBusy(true);
    try {
      await api.createKol({
        name: name.trim(),
        description: desc.trim(),
        gender: voice,
        voice_gender: voice,
        source: mode,
        avatar_url: mode === "upload" ? avatar : "",
        consent_confirmed: mode === "upload" ? consent : false,
      });
      onDone();
    } catch (e) {
      setErr(e instanceof Error ? e.message : t("errCreate"));
    } finally {
      setBusy(false);
    }
  }

  const ready = name.trim() && (mode === "ai" || (avatar && consent));

  return (
    <GlassCard className="p-5">
      <div className="mb-4 grid grid-cols-2 gap-1 rounded-lg border border-white/10 bg-white/[0.02] p-1">
        {(["ai", "upload"] as const).map((m) => (
          <button
            key={m}
            onClick={() => setMode(m)}
            className={`rounded-md py-2 text-sm font-medium transition-colors ${
              mode === m ? "bg-rose-500/20 text-ink-high" : "text-ink-low hover:text-ink-medium"
            }`}
          >
            {m === "ai" ? t("modeAi") : t("modeUpload")}
          </button>
        ))}
      </div>

      <div className="flex flex-col gap-3">
        <Field label={t("fieldName")}>
          <input className={inputCls} value={name} onChange={(e) => setName(e.target.value)} placeholder={t("fieldNamePlaceholder")} />
        </Field>
        <Field label={t("fieldDesc")}>
          <input className={inputCls} value={desc} onChange={(e) => setDesc(e.target.value)} placeholder={t("fieldDescPlaceholder")} />
        </Field>
        <Field label={t("fieldVoice")}>
          <ChipGroup
            value={voice}
            onChange={(v) => setVoice(v as "female" | "male")}
            options={[{ value: "female", label: t("genderFemale") }, { value: "male", label: t("genderMale") }]}
          />
        </Field>

        {mode === "upload" && (
          <>
            <Field label={t("fieldFace")}>
              <label className="flex cursor-pointer items-center gap-2 rounded-lg border border-dashed border-white/15 px-3 py-3 text-sm text-ink-low hover:border-rose-400/40">
                {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
                {avatar ? t("faceUploaded") : t("faceChoose")}
                <input type="file" accept="image/*" className="hidden"
                  onChange={(e) => e.target.files?.[0] && upload(e.target.files[0])} />
              </label>
            </Field>
            <label className="flex items-start gap-2 text-xs text-ink-medium">
              <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} className="mt-0.5" />
              <span className="flex items-start gap-1">
                <ShieldCheck className="mt-0.5 h-3.5 w-3.5 shrink-0 text-rose-300" />
                {t("consent")}
              </span>
            </label>
          </>
        )}

        {err && <p className="text-sm text-danger">{err}</p>}
        <Button onClick={submit} disabled={!ready || busy} className="self-start">
          {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : t("createKol")}
        </Button>
      </div>
    </GlassCard>
  );
}
