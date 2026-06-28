"use client";

import { useEffect, useRef, useState } from "react";
import { AudioLines, Loader2, Download, AlertCircle, Sparkles } from "lucide-react";
import { api } from "@/lib/api/endpoints";
import type { VoicePersona } from "@/lib/api/types";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Field, inputCls } from "@/components/ui/field";
import { cn } from "@/lib/utils/cn";

const EXAMPLES = [
  "Da bạn sẽ căng mướt và rạng rỡ chỉ sau bảy ngày sử dụng.",
  "Sản phẩm này đỉnh thật sự nha mọi người, mình mê tít luôn!",
  "Deal hôm nay cực hời, để link giỏ hàng rồi, bấm vô lẹ nha.",
];

export default function AudioToolPage() {
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
      setErr("Không tạo được âm thanh, thử lại.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex max-w-3xl flex-col gap-6">
      <div>
        <div className="flex items-center gap-2">
          <span className="grid h-10 w-10 place-items-center rounded-xl bg-grad-brand-soft">
            <AudioLines className="h-5 w-5 text-violet-300" />
          </span>
          <h1 className="font-display text-2xl font-bold text-ink-high lg:text-[32px]">Tạo âm thanh AI</h1>
        </div>
        <p className="mt-2 text-ink-low">Chuyển văn bản thành giọng Việt thật — chọn 1 trong 7 giọng có cá tính, nghe và tải về.</p>
      </div>

      <GlassCard className="flex flex-col gap-5 p-5">
        {/* ví dụ nhanh */}
        <div className="flex flex-wrap gap-1.5">
          <span className="inline-flex items-center gap-1 text-xs text-ink-low"><Sparkles className="h-3.5 w-3.5 text-violet-300" /> Ví dụ:</span>
          {EXAMPLES.map((e) => (
            <button key={e} onClick={() => setText(e)}
              className="rounded-lg border border-white/10 px-2.5 py-1 text-[11px] text-ink-low transition-colors hover:border-violet-400/40 hover:text-ink-medium">
              {e.slice(0, 26)}…
            </button>
          ))}
        </div>

        <Field label="Nội dung">
          <textarea
            className={cn(inputCls, "min-h-[100px] resize-y")}
            value={text}
            onChange={(e) => setText(e.target.value)}
            maxLength={200}
            placeholder="Nhập câu/đoạn muốn chuyển thành giọng nói (tối đa 200 ký tự)…"
          />
        </Field>

        <Field label="Chọn giọng" hint="7 giọng Việt thật, mỗi giọng một cá tính.">
          <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-3 lg:grid-cols-4">
            {personas.map((p) => {
              const active = persona?.id === p.id;
              return (
                <button key={p.id} onClick={() => setPersona(p)}
                  className={cn("flex items-center gap-2 rounded-xl border p-2.5 text-left transition-colors",
                    active ? "border-violet-500/60 bg-violet-500/10" : "border-white/10 hover:border-white/25")}>
                  <span className={cn("grid h-8 w-8 shrink-0 place-items-center rounded-full text-xs font-bold",
                    p.gender === "female" ? "bg-rose-500/15 text-rose-200" : "bg-sky-500/15 text-sky-200")}>
                    {p.name.charAt(0)}
                  </span>
                  <span className="min-w-0">
                    <span className="block text-sm font-medium text-ink-high">{p.name}</span>
                    <span className="block truncate text-[11px] text-ink-low">{p.vibe}</span>
                  </span>
                </button>
              );
            })}
          </div>
        </Field>

        <div className="flex flex-wrap items-center gap-3">
          <Button onClick={generate} disabled={loading || !text.trim() || !persona} className="gap-2">
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <AudioLines className="h-4 w-4" />}
            {loading ? "Đang tạo…" : "Tạo giọng"}
          </Button>
          {url && (
            <a href={url} download="vyra-audio.mp3">
              <Button variant="glass" className="gap-2"><Download className="h-4 w-4" /> Tải MP3</Button>
            </a>
          )}
          {err && (
            <span className="flex items-center gap-1.5 text-sm text-danger">
              <AlertCircle className="h-4 w-4" /> {err}
            </span>
          )}
        </div>
        <audio ref={audioRef} controls hidden={!url} className="mt-1 w-full" />
      </GlassCard>
    </div>
  );
}
