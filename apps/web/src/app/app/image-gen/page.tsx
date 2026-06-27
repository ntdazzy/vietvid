"use client";

import { useState } from "react";
import { Palette, Loader2, Download, AlertCircle } from "lucide-react";
import { api } from "@/lib/api/endpoints";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Field, ChipGroup, inputCls } from "@/components/ui/field";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils/cn";

export default function ImageGenPage() {
  const [prompt, setPrompt] = useState("");
  const [aspect, setAspect] = useState("9:16");
  const [url, setUrl] = useState<string>();
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function generate() {
    if (prompt.trim().length < 3) return;
    setLoading(true);
    setErr(null);
    setUrl(undefined);
    try {
      setUrl((await api.generateImage(prompt.trim(), aspect)).url);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Tạo ảnh lỗi");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold text-ink-high lg:text-[34px]">Tạo ảnh nghệ thuật AI</h1>
        <p className="mt-1 text-ink-low">Mô tả ý tưởng, AI tạo ảnh. Dùng làm khung video hoặc ảnh bài đăng.</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_1fr]">
        <GlassCard className="flex h-fit flex-col gap-4 p-5">
          <Field label="Mô tả ảnh">
            <textarea
              className={cn(inputCls, "min-h-[120px] resize-y")}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              maxLength={500}
              placeholder="Ví dụ: ly cà phê trên bàn gỗ, ánh sáng điện ảnh, tông tím xanh, độ nét cao"
            />
          </Field>
          <Field label="Tỉ lệ">
            <ChipGroup
              value={aspect}
              onChange={(v) => setAspect(v as string)}
              options={[
                { value: "9:16", label: "Dọc 9:16" },
                { value: "1:1", label: "Vuông 1:1" },
                { value: "16:9", label: "Ngang 16:9" },
              ]}
            />
          </Field>
          <div className="flex flex-wrap items-center gap-3">
            <Button onClick={generate} disabled={loading || prompt.trim().length < 3} className="gap-2">
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Palette className="h-4 w-4" />}
              {loading ? "Đang tạo ảnh…" : "Tạo ảnh"}
            </Button>
            {err && (
              <span className="flex items-center gap-1.5 text-sm text-danger">
                <AlertCircle className="h-4 w-4" /> {err}
              </span>
            )}
          </div>
        </GlassCard>

        <GlassCard bordered className="grid min-h-[320px] place-items-center p-4">
          {loading ? (
            <Skeleton className="aspect-[9/16] h-72 rounded-xl" />
          ) : url ? (
            <div className="flex flex-col items-center gap-3">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={url} alt="Ảnh AI" className="max-h-[60vh] w-auto rounded-xl border border-white/10" />
              <a href={url} download="vietvid-image.png">
                <Button variant="glass" className="gap-2">
                  <Download className="h-4 w-4" /> Tải ảnh
                </Button>
              </a>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-2 text-ink-low">
              <Palette className="h-8 w-8" />
              <span className="text-sm">Ảnh sẽ hiện ở đây</span>
            </div>
          )}
        </GlassCard>
      </div>
    </div>
  );
}
