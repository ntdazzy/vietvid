"use client";

import { useRef, useState } from "react";
import { AudioLines, Loader2, Download, AlertCircle } from "lucide-react";
import { api } from "@/lib/api/endpoints";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Field, ChipGroup, inputCls } from "@/components/ui/field";
import { cn } from "@/lib/utils/cn";

export default function AudioToolPage() {
  const [text, setText] = useState("");
  const [gender, setGender] = useState<"female" | "male">("female");
  const [url, setUrl] = useState<string>();
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  async function generate() {
    if (!text.trim()) return;
    setLoading(true);
    setErr(null);
    try {
      const u = await api.voicePreview(text.trim(), gender);
      setUrl(u);
      if (audioRef.current) {
        audioRef.current.src = u;
        await audioRef.current.play();
      }
    } catch {
      setErr("Không tạo được âm thanh, thử lại.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex max-w-2xl flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold text-ink-high lg:text-[34px]">Tạo âm thanh AI</h1>
        <p className="mt-1 text-ink-low">Chuyển văn bản thành giọng Việt thật, nghe và tải về.</p>
      </div>

      <GlassCard className="flex flex-col gap-4 p-5">
        <Field label="Nội dung">
          <textarea
            className={cn(inputCls, "min-h-[120px] resize-y")}
            value={text}
            onChange={(e) => setText(e.target.value)}
            maxLength={200}
            placeholder="Nhập câu/đoạn muốn chuyển thành giọng nói (tối đa 200 ký tự)…"
          />
        </Field>
        <Field label="Giọng">
          <ChipGroup
            value={gender}
            onChange={(v) => setGender(v as "female" | "male")}
            options={[
              { value: "female", label: "Nữ" },
              { value: "male", label: "Nam" },
            ]}
          />
        </Field>

        <div className="flex flex-wrap items-center gap-3">
          <Button onClick={generate} disabled={loading || !text.trim()} className="gap-2">
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <AudioLines className="h-4 w-4" />}
            {loading ? "Đang tạo…" : "Tạo giọng"}
          </Button>
          {url && (
            <a href={url} download="vietvid-audio.mp3">
              <Button variant="glass" className="gap-2">
                <Download className="h-4 w-4" /> Tải MP3
              </Button>
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
