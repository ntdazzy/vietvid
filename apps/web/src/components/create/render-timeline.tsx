"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { motion } from "framer-motion";
import {
  Clock,
  PenLine,
  Image as ImageIcon,
  Film,
  Mic,
  Layers,
  ShieldCheck,
  Sparkles,
  Check,
  Loader2,
  AlertTriangle,
  Download,
} from "lucide-react";
import { useJob } from "@/lib/query/hooks";
import { api } from "@/lib/api/endpoints";
import { getToken } from "@/lib/auth/session";
import { isTerminal } from "@/lib/job-status";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils/cn";

// label hiển thị lấy từ i18n theo `key` (stage.<KEY>); icon/key giữ nguyên (logic).
const STAGES = [
  { key: "QUEUED", icon: Clock },
  { key: "DIRECTING", icon: PenLine },
  { key: "IMAGING", icon: ImageIcon },
  { key: "RENDERING_VIDEO", icon: Film },
  { key: "VOICING", icon: Mic },
  { key: "COMPOSING", icon: Layers },
  { key: "QA", icon: ShieldCheck },
  { key: "READY", icon: Sparkles },
] as const;

type State = "done" | "active" | "pending" | "skip";

export function RenderTimeline({ jobId, onReset }: { jobId: string; onReset: () => void }) {
  const t = useTranslations("create");
  const { data: job } = useJob(jobId);
  const [videoUrl, setVideoUrl] = useState<string>();

  const status = job?.status;
  const terminal = status ? isTerminal(status) : false;
  const ok = status === "READY";
  const failedSystem = status === "FAILED" || status === "REFUNDED";

  // tải video (có Bearer) → blob để <video> phát được
  useEffect(() => {
    if (!ok || !job?.has_video) return;
    let url: string | undefined;
    let alive = true;
    (async () => {
      const token = await getToken();
      const res = await fetch(api.videoUrl(jobId), {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (res.ok && alive) {
        url = URL.createObjectURL(await res.blob());
        setVideoUrl(url);
      }
    })();
    return () => {
      alive = false;
      if (url) URL.revokeObjectURL(url);
    };
  }, [ok, job?.has_video, jobId]);

  function stateOf(stageKey: string): State {
    if (ok) return "done";
    if (stageKey === "QUEUED") return job ? "done" : "active";
    if (stageKey === "READY") return "pending";
    const evs = (job?.events ?? []).filter((e) => e.stage === stageKey);
    if (evs.some((e) => e.event_type === "SUCCEEDED")) return "done";
    if (evs.some((e) => e.event_type === "STARTED")) return terminal ? "skip" : "active";
    return terminal ? "skip" : "pending";
  }

  return (
    <div className="flex flex-col gap-6">
      {/* film strip */}
      <div className="glass-bordered overflow-x-auto p-5">
        <ol className="flex min-w-max items-center gap-1">
          {STAGES.map((s, i) => {
            const st = stateOf(s.key);
            const timing = job?.stage_timings?.[s.key];
            return (
              <li key={s.key} className="flex items-center">
                <div className="flex w-[88px] flex-col items-center gap-2 text-center">
                  <div
                    className={cn(
                      "grid h-11 w-11 place-items-center rounded-xl transition-colors",
                      st === "done" && "bg-grad-brand text-white",
                      st === "active" &&
                        "border border-violet-500/60 bg-violet-500/15 text-violet-200 shadow-glow-sm animate-glow-pulse",
                      st === "pending" && "border border-white/10 text-ink-low",
                      st === "skip" && "border border-white/5 text-ink-disabled",
                    )}
                  >
                    {st === "done" ? (
                      <Check className="h-5 w-5" />
                    ) : st === "active" ? (
                      <Loader2 className="h-5 w-5 animate-spin" />
                    ) : (
                      <s.icon className="h-5 w-5" />
                    )}
                  </div>
                  <span
                    className={cn(
                      "text-[11px] leading-tight",
                      st === "active" ? "text-ink-high" : "text-ink-low",
                    )}
                  >
                    {t(`stage.${s.key}`)}
                  </span>
                  {typeof timing === "number" && (
                    <span className="font-mono text-[10px] text-ink-disabled">
                      {timing.toFixed(1)}s
                    </span>
                  )}
                </div>
                {i < STAGES.length - 1 && (
                  <span
                    className={cn(
                      "h-px w-4 shrink-0",
                      st === "done" ? "bg-violet-500/50" : "bg-white/10",
                    )}
                  />
                )}
              </li>
            );
          })}
        </ol>
      </div>

      {/* result */}
      {ok && (
        <motion.div
          initial={{ opacity: 0, scale: 0.97 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
          className="glass-bordered flex flex-col items-center gap-4 p-6"
        >
          <div className="overflow-hidden rounded-xl border border-white/10 bg-black">
            {videoUrl ? (
              <video src={videoUrl} controls autoPlay loop muted className="max-h-[60vh] w-auto" />
            ) : (
              <div className="grid h-64 w-40 place-items-center text-ink-low">
                <Loader2 className="h-6 w-6 animate-spin" />
              </div>
            )}
          </div>
          <div className="flex gap-3">
            {videoUrl && (
              <a href={videoUrl} download={`vietvid-${jobId}.mp4`}>
                <Button className="gap-2">
                  <Download className="h-4 w-4" /> {t("downloadMp4")}
                </Button>
              </a>
            )}
            <Button variant="glass" onClick={onReset}>
              {t("createAnother")}
            </Button>
          </div>
        </motion.div>
      )}

      {terminal && !ok && (
        <div className="glass-bordered flex flex-col items-center gap-3 p-6 text-center">
          <div className="grid h-12 w-12 place-items-center rounded-xl bg-danger/[0.12]">
            <AlertTriangle className="h-6 w-6 text-danger" />
          </div>
          <p className="text-ink-high">
            {failedSystem ? t("failedSystem") : t("failedQa")}
          </p>
          {job?.error && <p className="max-w-md text-sm text-ink-low">{job.error}</p>}
          <Button variant="glass" onClick={onReset}>
            {t("retry")}
          </Button>
        </div>
      )}
    </div>
  );
}
