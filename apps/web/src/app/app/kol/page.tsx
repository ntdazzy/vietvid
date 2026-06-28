"use client";

import { useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  UserSquare2, Sparkles, Trash2, Lock, Upload, Loader2, ShieldCheck,
  Wand2, Images, Plus, Clapperboard, type LucideIcon,
} from "lucide-react";
import { api } from "@/lib/api/endpoints";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Field, inputCls, ChipGroup } from "@/components/ui/field";
import { cn } from "@/lib/utils/cn";

// Gương mặt AI mẫu cho persona hệ thống (avatar_url rỗng).
const SYSTEM_FACES: Record<string, string> = { Linh: "/kol/linh.jpg", Minh: "/kol/an.jpg", Hà: "/kol/mai.jpg" };

// Thư viện casting — gương mặt AI có sẵn theo category. "Dùng mẫu" tạo persona thật (source=ai).
type Preset = { id: string; name: string; cat: string; gender: "female" | "male"; img: string };
const PRESETS: Preset[] = [
  { id: "tt-nu1", name: "Vy", cat: "Thời trang", gender: "female", img: "/kol/lib/tt-nu1.jpg" },
  { id: "tt-nam1", name: "Phong", cat: "Thời trang", gender: "male", img: "/kol/lib/tt-nam1.jpg" },
  { id: "my-nu1", name: "Châu", cat: "Mỹ phẩm", gender: "female", img: "/kol/lib/my-nu1.jpg" },
  { id: "my-nu2", name: "Ngọc", cat: "Skincare", gender: "female", img: "/kol/lib/my-nu2.jpg" },
  { id: "fb-nu1", name: "Hân", cat: "F&B", gender: "female", img: "/kol/lib/fb-nu1.jpg" },
  { id: "fb-nam1", name: "Đạt", cat: "F&B", gender: "male", img: "/kol/lib/fb-nam1.jpg" },
  { id: "gym-nam1", name: "Khải", cat: "Gym", gender: "male", img: "/kol/lib/gym-nam1.jpg" },
  { id: "gym-nu1", name: "Trâm", cat: "Gym", gender: "female", img: "/kol/lib/gym-nu1.jpg" },
  { id: "vp-nu1", name: "Lan", cat: "Văn phòng", gender: "female", img: "/kol/lib/vp-nu1.jpg" },
  { id: "genz-nu1", name: "Bống", cat: "Gen Z", gender: "female", img: "/kol/lib/genz-nu1.jpg" },
  { id: "cc-nu1", name: "Quỳnh", cat: "Cao cấp", gender: "female", img: "/kol/lib/cc-nu1.jpg" },
  { id: "gd-nu1", name: "Hoa", cat: "Gia dụng", gender: "female", img: "/kol/lib/gd-nu1.jpg" },
];
const CATS = ["Tất cả", "Thời trang", "Mỹ phẩm", "Skincare", "F&B", "Gym", "Văn phòng", "Gen Z", "Cao cấp", "Gia dụng"];

export default function KolPage() {
  const qc = useQueryClient();
  const router = useRouter();
  const kol = useQuery({ queryKey: ["kol"], queryFn: api.kolPersonas });
  const [open, setOpen] = useState(false);
  const [cat, setCat] = useState("Tất cả");
  const [usingId, setUsingId] = useState<string | null>(null);
  const libRef = useRef<HTMLDivElement>(null);

  const personas = kol.data ?? [];
  const presets = cat === "Tất cả" ? PRESETS : PRESETS.filter((p) => p.cat === cat);

  async function remove(id: string) {
    await api.deleteKol(id);
    qc.invalidateQueries({ queryKey: ["kol"] });
  }

  // Dùng một gương mặt mẫu → tạo persona thật (source ai) → vào thẳng tạo video với KOL đó.
  async function usePreset(p: Preset) {
    setUsingId(p.id);
    try {
      const k = await api.createKol({
        name: p.name, description: `KOL ${p.cat}`, gender: p.gender,
        voice_gender: p.gender, avatar_url: p.img, source: "ai", consent_confirmed: false,
      });
      qc.invalidateQueries({ queryKey: ["kol"] });
      router.push(`/app/create?kol=${k.id}`);
    } catch {
      setUsingId(null);
    }
  }

  return (
    <div className="flex flex-col gap-7">
      {/* HERO — phòng casting điện ảnh */}
      <div className="relative overflow-hidden rounded-3xl glass-bordered">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/bg/ring.jpg" alt="" className="absolute inset-0 h-full w-full object-cover opacity-25" />
        <div className="absolute inset-0 bg-gradient-to-r from-bg-base via-bg-base/85 to-bg-base/40" />
        <div className="relative flex flex-col gap-5 p-6 sm:p-9">
          <span className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-300">KOL AI · Phòng casting</span>
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div className="max-w-xl">
              <h1 className="font-display text-3xl font-bold leading-tight text-ink-high lg:text-[40px]">
                Tuyển chọn <span className="text-gradient">gương mặt KOL AI</span>
              </h1>
              <p className="mt-2 max-w-md text-ink-medium">
                Tạo nhân vật ảo, giữ gương mặt nhất quán qua mọi video — không cần người mẫu, không cần quay phim.
              </p>
            </div>
            <Button onClick={() => setOpen((v) => !v)} variant={open ? "glass" : "primary"} size="lg" className="gap-1.5">
              <Plus className="h-4 w-4" /> {open ? "Đóng" : "Tạo KOL"}
            </Button>
          </div>
          <div className="flex flex-wrap items-center gap-x-7 gap-y-2">
            <HeroStat n={personas.length} l="KOL của bạn" />
            <HeroStat n={PRESETS.length} l="mẫu gương mặt AI" />
            <span className="flex items-center gap-1.5 text-sm text-ink-low"><ShieldCheck className="h-4 w-4 text-violet-300" /> Giữ gương mặt nhất quán</span>
          </div>
        </div>
      </div>

      {open && <CreateKol onDone={() => { setOpen(false); qc.invalidateQueries({ queryKey: ["kol"] }); }} />}

      {/* CHẾ ĐỘ TẠO */}
      <div className="grid gap-4 sm:grid-cols-2">
        <ModeCard icon={Wand2} title="Thiết kế KOL độc bản" desc="Tự đặt tên, phong cách, giọng — hoặc tải ảnh thật của bạn." onClick={() => setOpen(true)} />
        <ModeCard icon={Images} title="Tạo nhanh từ mẫu" desc="Chọn một gương mặt AI có sẵn bên dưới, một chạm là dựng video." onClick={() => libRef.current?.scrollIntoView({ behavior: "smooth", block: "start" })} />
      </div>

      {/* KOL CỦA BẠN */}
      <section className="flex flex-col gap-3">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-ink-low">KOL của bạn</h2>
        {kol.isLoading ? (
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-64 w-full rounded-xl" />)}
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            {personas.map((k) => {
              const face = k.avatar_url || SYSTEM_FACES[k.name] || "";
              return (
                <GlassCard key={k.id} className="flex flex-col overflow-hidden p-0">
                  <div className="relative aspect-[3/4] overflow-hidden bg-bg-surface">
                    {face ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img src={face} alt={k.name} className="h-full w-full object-cover" />
                    ) : (
                      <div className="grid h-full w-full place-items-center"><UserSquare2 className="h-10 w-10 text-violet-300/60" /></div>
                    )}
                    <div className="absolute inset-0 bg-gradient-to-t from-bg-base/85 to-transparent" />
                    <div className="absolute right-2 top-2 flex flex-col items-end gap-1">
                      {k.is_system && <Badge tone="neutral" className="bg-black/40"><Lock className="mr-1 h-3 w-3" />Hệ thống</Badge>}
                      {k.moderation_status === "PENDING" && <Badge tone="hold" className="bg-black/40">Chờ duyệt</Badge>}
                    </div>
                    <div className="absolute inset-x-3 bottom-2">
                      <div className="font-display text-sm font-semibold text-white">{k.name}</div>
                      <div className="line-clamp-1 text-[11px] text-white/70">{k.description}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-1.5 p-2.5">
                    <Link href={`/app/create?kol=${k.id}`} className="flex-1">
                      <Button className="w-full gap-1.5" size="sm" disabled={k.moderation_status === "PENDING"}>
                        <Sparkles className="h-3.5 w-3.5" /> Tạo video
                      </Button>
                    </Link>
                    {!k.is_system && (
                      <button onClick={() => remove(k.id)} className="grid h-8 w-8 shrink-0 place-items-center rounded-lg text-ink-low hover:bg-danger/10 hover:text-danger" aria-label="Xoá KOL">
                        <Trash2 className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                </GlassCard>
              );
            })}
          </div>
        )}
      </section>

      {/* THƯ VIỆN CASTING */}
      <section ref={libRef} className="flex flex-col gap-4 scroll-mt-24">
        <div>
          <h2 className="text-sm font-semibold uppercase tracking-wider text-ink-low">Thư viện casting · gương mặt AI</h2>
          <p className="mt-1 text-sm text-ink-low">Chọn một mẫu, một chạm là có KOL để dựng video. Tất cả là gương mặt do AI tạo.</p>
        </div>

        <div className="flex flex-wrap gap-2">
          {CATS.map((c) => (
            <button
              key={c}
              onClick={() => setCat(c)}
              className={cn(
                "rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors",
                cat === c ? "border-violet-400/40 bg-violet-500/20 text-ink-high" : "border-white/10 text-ink-low hover:text-ink-medium",
              )}
            >
              {c}
            </button>
          ))}
        </div>

        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          {presets.map((p) => (
            <GlassCard key={p.id} className="flex flex-col overflow-hidden p-0">
              <div className="relative aspect-[3/4] overflow-hidden">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={p.img} alt={p.name} className="h-full w-full object-cover transition-transform duration-700 hover:scale-105" />
                <div className="absolute inset-0 bg-gradient-to-t from-bg-base/85 to-transparent" />
                <span className="absolute left-2 top-2 rounded-md bg-black/40 px-2 py-0.5 text-[10px] font-medium text-violet-200">{p.cat}</span>
                <div className="absolute inset-x-3 bottom-2">
                  <div className="font-display text-sm font-semibold text-white">{p.name}</div>
                  <div className="text-[11px] text-white/70">{p.gender === "male" ? "Nam" : "Nữ"}</div>
                </div>
              </div>
              <div className="p-2.5">
                <Button onClick={() => usePreset(p)} disabled={usingId !== null} size="sm" className="w-full gap-1.5">
                  {usingId === p.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <Clapperboard className="h-4 w-4" />}
                  Dùng mẫu này
                </Button>
              </div>
            </GlassCard>
          ))}
        </div>
      </section>
    </div>
  );
}

function HeroStat({ n, l }: { n: number; l: string }) {
  return (
    <span className="flex items-baseline gap-1.5">
      <span className="font-numeric text-xl font-bold text-ink-high">{n}</span>
      <span className="text-sm text-ink-low">{l}</span>
    </span>
  );
}

function ModeCard({ icon: Icon, title, desc, onClick }: { icon: LucideIcon; title: string; desc: string; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="group flex items-start gap-3 rounded-2xl glass-bordered p-5 text-left transition-all hover:-translate-y-0.5"
    >
      <span className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-grad-brand-soft text-violet-300 transition-colors group-hover:bg-violet-500/20">
        <Icon className="h-5 w-5" />
      </span>
      <div>
        <div className="font-display font-semibold text-ink-high">{title}</div>
        <p className="mt-0.5 text-sm leading-snug text-ink-low">{desc}</p>
      </div>
    </button>
  );
}

function CreateKol({ onDone }: { onDone: () => void }) {
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
      setErr("Tải ảnh lỗi");
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
      setErr(e instanceof Error ? e.message : "Tạo KOL lỗi");
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
              mode === m ? "bg-violet-500/20 text-ink-high" : "text-ink-low hover:text-ink-medium"
            }`}
          >
            {m === "ai" ? "Persona AI" : "Ảnh thật"}
          </button>
        ))}
      </div>

      <div className="flex flex-col gap-3">
        <Field label="Tên KOL">
          <input className={inputCls} value={name} onChange={(e) => setName(e.target.value)} placeholder="VD: Hương" />
        </Field>
        <Field label="Mô tả / phong cách">
          <input className={inputCls} value={desc} onChange={(e) => setDesc(e.target.value)} placeholder="Nữ, trẻ trung, giọng miền Nam..." />
        </Field>
        <Field label="Giọng">
          <ChipGroup
            value={voice}
            onChange={(v) => setVoice(v as "female" | "male")}
            options={[{ value: "female", label: "Nữ" }, { value: "male", label: "Nam" }]}
          />
        </Field>

        {mode === "upload" && (
          <>
            <Field label="Ảnh khuôn mặt">
              <label className="flex cursor-pointer items-center gap-2 rounded-lg border border-dashed border-white/15 px-3 py-3 text-sm text-ink-low hover:border-violet-400/40">
                {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
                {avatar ? "Đã tải ảnh ✓" : "Chọn ảnh khuôn mặt"}
                <input type="file" accept="image/*" className="hidden"
                  onChange={(e) => e.target.files?.[0] && upload(e.target.files[0])} />
              </label>
            </Field>
            <label className="flex items-start gap-2 text-xs text-ink-medium">
              <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} className="mt-0.5" />
              <span className="flex items-start gap-1">
                <ShieldCheck className="mt-0.5 h-3.5 w-3.5 shrink-0 text-violet-300" />
                Tôi xác nhận có quyền sử dụng hình ảnh này và đồng ý cho AI xử lý. Ảnh mặt thật sẽ qua kiểm duyệt trước khi dùng.
              </span>
            </label>
          </>
        )}

        {err && <p className="text-sm text-danger">{err}</p>}
        <Button onClick={submit} disabled={!ready || busy} className="self-start">
          {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : "Tạo KOL"}
        </Button>
      </div>
    </GlassCard>
  );
}
