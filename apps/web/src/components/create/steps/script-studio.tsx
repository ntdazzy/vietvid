"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { Wand2, Loader2, Sparkles, RefreshCw, Download, ShieldAlert } from "lucide-react";
import { useWizard } from "@/store/wizard";
import { api } from "@/lib/api/endpoints";
import type { Script } from "@/lib/api/types";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils/cn";

const BEAT_KEYS = ["hook", "pain", "desire", "benefit", "cta"] as const;

// Bộ máy kịch bản: chọn góc → sinh hook + beat theo timecode → sửa từng câu → ghi vào brief.
export function ScriptStudio() {
  const t = useTranslations("create");
  // nhãn beat hiển thị từ i18n (key beatLabel.<type>); fallback về b.label thô nếu type lạ.
  const LABEL: Record<string, string> = Object.fromEntries(BEAT_KEYS.map((k) => [k, t(`beatLabel.${k}`)]));
  const w = useWizard();
  const [angles, setAngles] = useState<{ value: string; label: string }[]>([]);
  const [angle, setAngle] = useState("problem_solution");
  const [script, setScript] = useState<Script | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  // Load 6 GÓC CHỐT ĐƠN ngay khi mở (không chờ bấm Tạo) — làm nổi điểm khác biệt vs đối thủ.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { ensureAngles(); }, []);

  async function ensureAngles() {
    if (angles.length) return;
    try {
      setAngles(await api.scriptAngles());
    } catch {
      /* giữ mặc định nếu lỗi */
    }
  }

  async function gen(a = angle) {
    setBusy(true);
    setErr(null);
    try {
      const s = await api.generateScript({
        product: {
          name: w.product.name,
          category: w.product.category,
          price: w.product.price,
          description: w.product.description,
        },
        angle: a,
        seconds: w.seconds,
        voice_gender: w.voiceGender || "female",
      });
      setScript(s);
      w.patch({ brief: s.narration_full });
    } catch (e) {
      setErr(e instanceof Error ? e.message : t("scriptGenError"));
    } finally {
      setBusy(false);
    }
  }

  async function downloadSrt() {
    if (!script) return;
    try {
      const { content } = await api.scriptCaptions(script.beats, "srt");
      const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `vietvid-${script.angle}.srt`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      setErr(t("captionsError"));
    }
  }

  function editBeat(i: number, value: string) {
    if (!script) return;
    const beats = script.beats.map((b, idx) => (idx === i ? { ...b, narration: value } : b));
    const narration_full = beats.map((b) => b.narration).join(" ");
    const next = { ...script, beats, narration_full, word_count: narration_full.split(/\s+/).filter(Boolean).length };
    setScript(next);
    w.patch({ brief: narration_full });
  }

  return (
    <div className="rounded-xl border border-violet-500/20 bg-violet-500/[0.04] p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-1.5 text-sm font-semibold text-ink-high">
          <Sparkles className="h-4 w-4 text-violet-300" /> {t("scriptAi")}
        </div>
        <Button variant="glass" size="sm" className="gap-1.5" disabled={busy} onClick={async () => { await ensureAngles(); gen(); }}>
          {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : script ? <RefreshCw className="h-4 w-4 text-violet-300" /> : <Wand2 className="h-4 w-4 text-violet-300" />}
          {script ? t("regenerate") : t("generateScript")}
        </Button>
      </div>

      {/* chọn GÓC CHỐT ĐƠN — hiện ngay từ đầu (không chờ bấm Tạo). Fallback về góc của script nếu load lỗi. */}
      {(() => {
        const shown = angles.length ? angles : (script ? [{ value: angle, label: script.angle_label ?? angle }] : []);
        if (!shown.length) return null;
        return (
          <div className="mt-3">
            <div className="mb-1.5 text-[11px] font-medium text-violet-200">
              Góc chốt đơn — chọn cách thuyết phục, AI viết kịch bản theo góc đó
            </div>
            <div className="flex flex-wrap gap-1.5">
              {shown.map((a) => (
                <button
                  key={a.value}
                  type="button"
                  // Trước khi có script: bấm = chọn góc. Sau khi có: bấm = viết lại theo góc mới.
                  onClick={() => { setAngle(a.value); if (script) gen(a.value); }}
                  className={cn(
                    "rounded-lg border px-2.5 py-1 text-xs transition-colors",
                    angle === a.value ? "border-violet-500/60 bg-violet-500/15 text-violet-100" : "border-white/10 text-ink-low hover:border-white/25",
                  )}
                >
                  {a.label}
                </button>
              ))}
            </div>
          </div>
        );
      })()}

      {err && <p className="mt-2 text-xs text-danger">{err}</p>}

      {script && (
        <div className="mt-4 flex flex-col gap-2.5">
          {(script.claim_warnings?.length ?? 0) > 0 && (
            <div className="rounded-lg border border-hold/30 bg-hold/[0.07] p-2.5">
              <div className="mb-1 flex items-center gap-1.5 text-xs font-semibold text-hold">
                <ShieldAlert className="h-3.5 w-3.5" /> {t("adClaimWarning")}
              </div>
              <ul className="flex flex-col gap-0.5">
                {script.claim_warnings!.map((w, i) => (
                  <li key={i} className="text-[11px] text-ink-low">
                    <span className={cn("font-medium", w.severity === "block" ? "text-danger" : "text-hold")}>“{w.match}”</span> — {w.label}
                  </li>
                ))}
              </ul>
            </div>
          )}
          <div className="flex items-center gap-2 text-xs text-ink-low">
            <span className="rounded bg-white/[0.06] px-1.5 py-0.5 font-medium text-ink-high">“{script.hook_line}”</span>
            <span className={cn("font-numeric", script.word_count > script.target_words * 1.25 ? "text-hold" : "text-ink-low")}>
              {t("wordCount", { count: script.word_count, target: script.target_words, seconds: script.duration_seconds })}
            </span>
          </div>
          {script.beats.map((b, i) => (
            <div key={i} className="flex gap-2.5">
              <div className="flex w-14 shrink-0 flex-col items-center pt-1.5">
                <span className="text-[10px] font-semibold uppercase tracking-wide text-violet-300">{LABEL[b.label] ?? b.label}</span>
                <span className="font-numeric text-[10px] text-ink-low">{b.t_start}-{b.t_end}s</span>
              </div>
              <div className="flex-1">
                <textarea
                  className="w-full resize-none rounded-lg border border-white/10 bg-bg-base/40 px-2.5 py-1.5 text-sm text-ink-high outline-none focus:border-violet-500/40"
                  rows={2}
                  value={b.narration}
                  onChange={(e) => editBeat(i, e.target.value)}
                />
                {b.scene && <p className="mt-0.5 line-clamp-1 text-[11px] text-ink-low">🎬 {b.scene}</p>}
              </div>
            </div>
          ))}
          <div className="flex items-center justify-between gap-2 pt-1">
            {script.source === "template" ? (
              <p className="text-[11px] text-ink-low">{t("scriptTip")}</p>
            ) : <span />}
            <button
              type="button"
              onClick={downloadSrt}
              className="flex shrink-0 items-center gap-1.5 rounded-lg border border-white/10 px-2.5 py-1 text-xs text-ink-medium hover:border-white/25 hover:text-ink-high"
            >
              <Download className="h-3.5 w-3.5" /> {t("downloadSrt")}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
