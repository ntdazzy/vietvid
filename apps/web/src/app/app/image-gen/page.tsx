"use client";

import { useState } from "react";
import { Palette, Loader2, Download, AlertCircle, Sparkles, Lightbulb, RefreshCw } from "lucide-react";
import { api } from "@/lib/api/endpoints";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Field, ChipGroup, inputCls } from "@/components/ui/field";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils/cn";

const PRESETS = [
  "Ly trà sữa trân châu trên bàn gỗ, ánh sáng ấm, nền bokeh",
  "Chai serum dưỡng da trên nền hồng pastel, sang trọng, cận cảnh",
  "Tai nghe bluetooth trên bục đá, nền tối, ánh sáng viền xanh",
  "Áo khoác phối trên ma-nơ-canh, phong cách editorial, ánh sáng studio",
];
const STYLES = ["ánh sáng điện ảnh", "phong cách UGC điện thoại", "tối giản nền trơn", "tông tím xanh thương hiệu"];
const TIPS = [
  "Mô tả đủ CHỦ THỂ + BỐI CẢNH + ÁNH SÁNG để ảnh sắc nét, đúng ý.",
  "Thêm tông màu (vd 'tông tím xanh') để ảnh hợp nhận diện thương hiệu.",
  "Ảnh dọc 9:16 dùng làm khung đầu rồi dựng tiếp thành video.",
];

export default function ImageGenPage() {
  const [prompt, setPrompt] = useState("");
  const [aspect, setAspect] = useState("9:16");
  const [url, setUrl] = useState<string>();
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  function addStyle(s: string) {
    setPrompt((p) => (p.trim() ? `${p.replace(/[,\s]+$/, "")}, ${s}` : s));
  }

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
        <div className="flex items-center gap-2">
          <span className="grid h-10 w-10 place-items-center rounded-xl bg-grad-brand-soft">
            <Palette className="h-5 w-5 text-violet-300" />
          </span>
          <h1 className="font-display text-2xl font-bold text-ink-high lg:text-[32px]">Tạo ảnh nghệ thuật AI</h1>
        </div>
        <p className="mt-2 text-ink-low">Mô tả ý tưởng, AI dựng ảnh. Dùng làm khung video hoặc ảnh bài đăng — đủ 3 tỉ lệ.</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_1fr]">
        <GlassCard className="flex h-fit flex-col gap-4 p-5">
          {/* gợi ý nhanh */}
          <div>
            <div className="mb-2 flex items-center gap-1.5 text-xs font-medium text-ink-medium">
              <Sparkles className="h-3.5 w-3.5 text-violet-300" /> Gợi ý nhanh — bấm để điền
            </div>
            <div className="flex flex-wrap gap-1.5">
              {PRESETS.map((p) => (
                <button key={p} onClick={() => setPrompt(p)}
                  className="rounded-lg border border-white/10 px-2.5 py-1 text-left text-[11px] text-ink-low transition-colors hover:border-violet-400/40 hover:text-ink-medium">
                  {p.split(",")[0]}
                </button>
              ))}
            </div>
          </div>

          <Field label="Mô tả ảnh">
            <textarea
              className={cn(inputCls, "min-h-[110px] resize-y")}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              maxLength={500}
              placeholder="Ví dụ: ly cà phê trên bàn gỗ, ánh sáng điện ảnh, tông tím xanh, độ nét cao"
            />
          </Field>

          {/* phong cách — append vào prompt */}
          <div className="flex flex-wrap gap-1.5">
            {STYLES.map((s) => (
              <button key={s} onClick={() => addStyle(s)}
                className="rounded-full border border-violet-400/25 bg-violet-500/[0.06] px-2.5 py-1 text-[11px] text-violet-200 transition-colors hover:bg-violet-500/15">
                + {s}
              </button>
            ))}
          </div>

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
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : url ? <RefreshCw className="h-4 w-4" /> : <Palette className="h-4 w-4" />}
              {loading ? "Đang tạo ảnh…" : url ? "Tạo lại" : "Tạo ảnh"}
            </Button>
            {err && (
              <span className="flex items-center gap-1.5 text-sm text-danger">
                <AlertCircle className="h-4 w-4" /> {err}
              </span>
            )}
          </div>
        </GlassCard>

        <GlassCard bordered className="grid min-h-[360px] place-items-center p-4">
          {loading ? (
            <Skeleton className="aspect-[9/16] h-72 rounded-xl" />
          ) : url ? (
            <div className="flex flex-col items-center gap-3">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={url} alt="Ảnh AI" className="max-h-[60vh] w-auto rounded-xl border border-white/10" />
              <a href={url} download="vyra-image.png">
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

      {/* tips */}
      <GlassCard className="p-5">
        <div className="mb-3 flex items-center gap-1.5 text-sm font-semibold text-ink-high">
          <Lightbulb className="h-4 w-4 text-hold" /> Mẹo viết mô tả đẹp
        </div>
        <ul className="grid gap-2.5 sm:grid-cols-3">
          {TIPS.map((t) => (
            <li key={t} className="flex items-start gap-2 text-sm text-ink-low">
              <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-violet-400" /> {t}
            </li>
          ))}
        </ul>
      </GlassCard>
    </div>
  );
}
