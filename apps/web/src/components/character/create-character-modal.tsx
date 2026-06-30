"use client";

// Modal "Tạo nhân vật" — clone openart /suite/character "Create a character".
// 3 lối tạo: 'image' (upload ảnh), 'describe' (prompt text), 'build' (thuộc tính).
// describe/build → api.generateImage sinh ảnh nhân vật; image → upload + thumbnail data-URL.

import { useEffect, useRef, useState } from "react";
import {
  X, ImagePlus, Wand2, SlidersHorizontal, Loader2, AlertCircle, ArrowLeft, UploadCloud, Sparkles,
} from "lucide-react";
import { api } from "@/lib/api/endpoints";
import { Button } from "@/components/ui/button";
import { Field, ChipGroup, inputCls } from "@/components/ui/field";
import { cn } from "@/lib/utils/cn";
import type { CharacterCreate } from "@/lib/api/types";

type Mode = null | "image" | "describe" | "build";

// Downscale ảnh upload → thumbnail JPEG data-URL (≤640px) để lưu avatar hiển thị được
// (uploads chỉ trả image_path local không serve; data-URL nhỏ ~50-90KB là đủ cho lưới).
async function fileToThumbDataUrl(file: File, max = 640): Promise<string> {
  const bitmap = await createImageBitmap(file);
  const scale = Math.min(1, max / Math.max(bitmap.width, bitmap.height));
  const w = Math.round(bitmap.width * scale);
  const h = Math.round(bitmap.height * scale);
  const canvas = document.createElement("canvas");
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("Trình duyệt không hỗ trợ canvas");
  ctx.drawImage(bitmap, 0, 0, w, h);
  bitmap.close?.();
  return canvas.toDataURL("image/jpeg", 0.82);
}

const VIBES = ["Đời thường", "Điện ảnh", "Sang trọng", "Năng động", "Dịu dàng"];
const GENDERS = [
  { value: "female", label: "Nữ" },
  { value: "male", label: "Nam" },
  { value: "neutral", label: "Trung tính" },
];
const ETHNICITIES = ["Việt Nam", "Châu Á", "Châu Âu", "Đa sắc tộc"];
const AGES = ["18-25", "26-35", "36-45", "46+"];

export function CreateCharacterModal({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: () => void;
}) {
  const [mode, setMode] = useState<Mode>(null);
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  // image flow
  const fileRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string>("");

  // describe flow
  const [prompt, setPrompt] = useState("");

  // build flow
  const [vibe, setVibe] = useState(VIBES[0]);
  const [gender, setGender] = useState("female");
  const [ethnicity, setEthnicity] = useState(ETHNICITIES[0]);
  const [age, setAge] = useState(AGES[0]);

  // Esc để đóng
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  function pickFile(f: File | undefined) {
    if (!f) return;
    setErr(null);
    setFile(f);
    setPreview(URL.createObjectURL(f));
  }

  function buildPrompt() {
    const g = GENDERS.find((x) => x.value === gender)?.label ?? "";
    return `Chân dung nhân vật ${g}, ${ethnicity}, độ tuổi ${age}, phong cách ${vibe}, toàn thân, nền studio sạch, ánh sáng điện ảnh, chi tiết cao`;
  }

  async function submit() {
    if (!name.trim()) {
      setErr("Cần đặt tên nhân vật");
      return;
    }
    setBusy(true);
    setErr(null);
    try {
      let body: CharacterCreate;
      if (mode === "image") {
        if (!file) throw new Error("Chọn một ảnh để bắt đầu");
        const thumb = await fileToThumbDataUrl(file);
        const up = await api.uploadImage(file).catch(() => null); // image_path để tham chiếu render sau
        body = {
          name: name.trim(),
          source: "image",
          avatar_url: thumb,
          images: up ? [up.image_path] : [],
          voice_gender: "female",
        };
      } else if (mode === "describe") {
        if (prompt.trim().length < 3) throw new Error("Mô tả nhân vật ít nhất vài từ");
        const { url } = await api.generateImage(prompt.trim(), "9:16");
        body = {
          name: name.trim(),
          source: "describe",
          description: prompt.trim(),
          avatar_url: url,
          images: [url],
          voice_gender: "female",
        };
      } else {
        const p = buildPrompt();
        const { url } = await api.generateImage(p, "9:16");
        body = {
          name: name.trim(),
          source: "build",
          description: p,
          avatar_url: url,
          images: [url],
          gender,
          ethnicity,
          age_range: age,
          vibe,
          voice_gender: gender === "male" ? "male" : "female",
        };
      }
      await api.createCharacter(body);
      onCreated();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Tạo nhân vật lỗi");
    } finally {
      setBusy(false);
    }
  }

  const genLabel = busy ? "Đang tạo…" : "Tạo nhân vật";

  return (
    <div
      className="fixed inset-0 z-50 grid place-items-center bg-bg-base/80 p-4 backdrop-blur-sm"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label="Tạo nhân vật"
    >
      <div
        className="relative w-full max-w-3xl rounded-3xl glass-bordered bg-bg-surface/95 p-6 sm:p-8"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          aria-label="Đóng"
          className="absolute right-4 top-4 grid h-8 w-8 place-items-center rounded-lg text-ink-low transition-colors hover:bg-white/[0.06] hover:text-ink-high"
        >
          <X className="h-4 w-4" />
        </button>

        {/* tiêu đề (giống openart: "Create a character") */}
        <div className="text-center">
          <h2 className="font-display text-2xl font-bold text-ink-high sm:text-3xl">
            Tạo <span className="text-gradient">nhân vật</span>
          </h2>
          <p className="mx-auto mt-1.5 max-w-md text-sm text-ink-low">
            Tạo một nhân vật tái dùng để đưa vào ảnh và video sau này.
          </p>
        </div>

        {/* ── Bước 1: chọn 1 trong 3 lối ───────────────────────────────── */}
        {mode === null && (
          <div className="mt-7 grid gap-4 sm:grid-cols-3">
            <OptionCard
              icon={UploadCloud}
              title="Bắt đầu từ ảnh"
              desc="Tải ảnh có sẵn làm nhân vật"
              img="/kol/lib/tt-nu1.jpg"
              onClick={() => setMode("image")}
            />
            <OptionCard
              icon={Wand2}
              title="Mô tả nhân vật"
              desc="Gõ một câu, AI dựng nhân vật"
              img="/kol/lib/my-nu2.jpg"
              onClick={() => setMode("describe")}
            />
            <OptionCard
              icon={SlidersHorizontal}
              title="Tự dựng nhân vật"
              desc="Chọn phong cách · giới · tuổi"
              img="/kol/lib/genz-nu1.jpg"
              badge="Mới"
              onClick={() => setMode("build")}
            />
          </div>
        )}

        {/* ── Bước 2: form theo lối đã chọn ────────────────────────────── */}
        {mode !== null && (
          <div className="mt-6 flex flex-col gap-5">
            <button
              onClick={() => { setMode(null); setErr(null); }}
              className="flex w-fit items-center gap-1.5 text-xs text-ink-low transition-colors hover:text-ink-medium"
            >
              <ArrowLeft className="h-3.5 w-3.5" /> Chọn lối khác
            </button>

            <div className="grid gap-5 sm:grid-cols-[1fr_1.1fr]">
              {/* trái — preview */}
              <div className="grid aspect-[3/4] place-items-center overflow-hidden rounded-2xl border border-white/10 bg-bg-base/60">
                {preview && mode === "image" ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={preview} alt="Xem trước nhân vật" className="h-full w-full object-cover" />
                ) : (
                  <div className="flex flex-col items-center gap-2 px-6 text-center text-ink-low">
                    <Sparkles className="h-7 w-7 text-violet-300" />
                    <span className="text-xs">
                      {mode === "image" ? "Ảnh nhân vật sẽ hiện ở đây" : "AI sẽ dựng nhân vật theo mô tả của bạn"}
                    </span>
                  </div>
                )}
              </div>

              {/* phải — điều khiển */}
              <div className="flex flex-col gap-4">
                <Field label="Tên nhân vật">
                  <input
                    className={inputCls}
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    maxLength={60}
                    placeholder="VD: Linh, Khôi, Bo…"
                  />
                </Field>

                {mode === "image" && (
                  <>
                    <input
                      ref={fileRef}
                      type="file"
                      accept="image/jpeg,image/png,image/webp"
                      className="hidden"
                      onChange={(e) => pickFile(e.target.files?.[0])}
                    />
                    <Button variant="glass" onClick={() => fileRef.current?.click()} className="gap-2">
                      <ImagePlus className="h-4 w-4 text-violet-300" />
                      {file ? "Đổi ảnh" : "Chọn ảnh nhân vật"}
                    </Button>
                    <p className="text-xs text-ink-low">JPEG/PNG/WebP, tối đa 12MB.</p>
                  </>
                )}

                {mode === "describe" && (
                  <Field label="Mô tả nhân vật">
                    <textarea
                      className={cn(inputCls, "min-h-[120px] resize-y")}
                      value={prompt}
                      onChange={(e) => setPrompt(e.target.value)}
                      maxLength={500}
                      placeholder="VD: cô gái tóc ngắn, áo blazer be, phong cách công sở hiện đại, gương mặt thân thiện"
                    />
                  </Field>
                )}

                {mode === "build" && (
                  <div className="flex flex-col gap-3.5">
                    <Field label="Phong cách">
                      <ChipGroup value={vibe} onChange={(v) => setVibe(v as string)}
                        options={VIBES.map((x) => ({ value: x, label: x }))} />
                    </Field>
                    <Field label="Giới tính">
                      <ChipGroup value={gender} onChange={(v) => setGender(v as string)} options={GENDERS} />
                    </Field>
                    <Field label="Sắc tộc">
                      <ChipGroup value={ethnicity} onChange={(v) => setEthnicity(v as string)}
                        options={ETHNICITIES.map((x) => ({ value: x, label: x }))} />
                    </Field>
                    <Field label="Độ tuổi">
                      <ChipGroup value={age} onChange={(v) => setAge(v as string)}
                        options={AGES.map((x) => ({ value: x, label: x }))} />
                    </Field>
                  </div>
                )}

                {err && (
                  <p className="flex items-center gap-1.5 text-sm text-danger">
                    <AlertCircle className="h-4 w-4 shrink-0" /> {err}
                  </p>
                )}

                <Button onClick={submit} disabled={busy} className="mt-1 gap-2">
                  {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
                  {genLabel}
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function OptionCard({
  icon: Icon,
  title,
  desc,
  img,
  badge,
  onClick,
}: {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  desc: string;
  img: string;
  badge?: string;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="group relative flex flex-col overflow-hidden rounded-2xl border border-white/10 bg-bg-base/40 p-2.5 text-left transition-all duration-200 hover:-translate-y-0.5 hover:border-violet-400/40 hover:shadow-glow-sm"
    >
      {badge && (
        <span className="absolute left-3.5 top-3.5 z-10 rounded-md bg-amber-300 px-1.5 py-0.5 text-[10px] font-bold text-bg-base">
          {badge}
        </span>
      )}
      <div className="relative aspect-[4/5] overflow-hidden rounded-xl">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={img} alt="" className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-[1.05]" />
        <div className="absolute inset-0 bg-gradient-to-t from-bg-base/85 to-transparent" />
        <span className="absolute bottom-2.5 left-1/2 grid h-9 w-9 -translate-x-1/2 place-items-center rounded-full bg-violet-500/30 text-violet-100 ring-1 ring-violet-300/40 backdrop-blur-sm">
          <Icon className="h-4 w-4" />
        </span>
      </div>
      <div className="px-1 pb-1 pt-2.5">
        <div className="text-sm font-semibold text-ink-high">{title}</div>
        <div className="mt-0.5 text-[11px] text-ink-low">{desc}</div>
      </div>
    </button>
  );
}
