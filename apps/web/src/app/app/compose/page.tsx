"use client";

import { useRef, useState } from "react";
import { Layers, Loader2, Download, Plus, AlertCircle, Lightbulb } from "lucide-react";
import { api } from "@/lib/api/endpoints";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Field, ChipGroup } from "@/components/ui/field";
import { cn } from "@/lib/utils/cn";

interface Item {
  preview: string;
  path?: string;
  uploading: boolean;
}

export default function ComposePage() {
  const [items, setItems] = useState<Item[]>([]);
  const [secondsPer, setSecondsPer] = useState(3);
  const [videoUrl, setVideoUrl] = useState<string>();
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  function addFiles(files: FileList | null) {
    if (!files) return;
    Array.from(files).slice(0, 8 - items.length).forEach((file) => {
      const preview = URL.createObjectURL(file);
      const idx = items.length;
      setItems((cur) => [...cur, { preview, uploading: true }]);
      api
        .uploadImage(file)
        .then((res) =>
          setItems((cur) => cur.map((it, i) => (i === idx ? { ...it, path: res.image_path, uploading: false } : it))),
        )
        .catch(() => setItems((cur) => cur.map((it, i) => (i === idx ? { ...it, uploading: false } : it))));
    });
  }

  async function compose() {
    const paths = items.map((i) => i.path).filter(Boolean) as string[];
    if (paths.length < 2) return;
    setLoading(true);
    setErr(null);
    setVideoUrl(undefined);
    try {
      setVideoUrl(await api.compose(paths, secondsPer));
    } catch {
      setErr("Ghép video lỗi, thử lại.");
    } finally {
      setLoading(false);
    }
  }

  const ready = items.filter((i) => i.path).length;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <div className="flex items-center gap-2">
          <span className="grid h-10 w-10 place-items-center rounded-xl bg-grad-brand-soft">
            <Layers className="h-5 w-5 text-violet-300" />
          </span>
          <h1 className="font-display text-2xl font-bold text-ink-high lg:text-[32px]">Ghép Video & Hình ảnh</h1>
        </div>
        <p className="mt-2 text-ink-low">Chọn nhiều ảnh (2–8 tấm), Vyra ghép thành một video slideshow dọc có chuyển cảnh, xuất MP4 đăng được ngay.</p>
      </div>

      <GlassCard className="flex flex-col gap-4 p-5">
        {items.length === 0 && (
          <p className="text-sm text-ink-low">Bấm ô <span className="text-ink-medium">＋</span> để thêm ảnh — cần ít nhất 2 ảnh để ghép.</p>
        )}
        <div className="grid grid-cols-3 gap-3 sm:grid-cols-5">
          {items.map((it, i) => (
            <div key={i} className="relative aspect-[9/16] overflow-hidden rounded-lg border border-white/10">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={it.preview} alt="" className="h-full w-full object-cover" />
              {it.uploading && (
                <div className="absolute inset-0 grid place-items-center bg-bg-base/60">
                  <Loader2 className="h-4 w-4 animate-spin text-violet-300" />
                </div>
              )}
            </div>
          ))}
          {items.length < 8 && (
            <button
              type="button"
              onClick={() => inputRef.current?.click()}
              className="grid aspect-[9/16] place-items-center rounded-lg border border-dashed border-white/15 text-ink-low hover:border-violet-500/40"
            >
              <Plus className="h-6 w-6" />
            </button>
          )}
        </div>
        <input ref={inputRef} type="file" accept="image/jpeg,image/png,image/webp" multiple className="hidden" onChange={(e) => addFiles(e.target.files)} />

        <Field label="Thời lượng mỗi ảnh">
          <ChipGroup
            value={secondsPer}
            onChange={(v) => setSecondsPer(v as number)}
            options={[2, 3, 4].map((s) => ({ value: s, label: `${s}s` }))}
          />
        </Field>

        <div className="flex flex-wrap items-center gap-3">
          <Button onClick={compose} disabled={loading || ready < 2} className="gap-2">
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Layers className="h-4 w-4" />}
            {loading ? "Đang ghép…" : `Ghép ${ready} ảnh thành video`}
          </Button>
          {err && (
            <span className="flex items-center gap-1.5 text-sm text-danger">
              <AlertCircle className="h-4 w-4" /> {err}
            </span>
          )}
        </div>
      </GlassCard>

      {videoUrl && (
        <GlassCard bordered className={cn("flex flex-col items-center gap-4 p-6")}>
          <video src={videoUrl} controls autoPlay loop className="max-h-[60vh] w-auto rounded-xl border border-white/10" />
          <a href={videoUrl} download="vyra-compose.mp4">
            <Button className="gap-2">
              <Download className="h-4 w-4" /> Tải MP4
            </Button>
          </a>
        </GlassCard>
      )}

      {/* tips */}
      <GlassCard className="p-5">
        <div className="mb-3 flex items-center gap-1.5 text-sm font-semibold text-ink-high">
          <Lightbulb className="h-4 w-4 text-hold" /> Mẹo ghép đẹp
        </div>
        <ul className="grid gap-2.5 sm:grid-cols-3">
          {[
            "Dùng ảnh CÙNG tỉ lệ dọc 9:16 để video không bị viền đen.",
            "3–5 ảnh là vừa đẹp; mỗi ảnh 2–3 giây cho nhịp mượt.",
            "Muốn có giọng đọc + kịch bản? Dùng 'Tạo video' thay vì ghép.",
          ].map((t) => (
            <li key={t} className="flex items-start gap-2 text-sm text-ink-low">
              <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-violet-400" /> {t}
            </li>
          ))}
        </ul>
      </GlassCard>
    </div>
  );
}
