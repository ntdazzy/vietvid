"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { UserSquare2, Sparkles, Trash2, Lock, Upload, Loader2, ShieldCheck } from "lucide-react";
import { api } from "@/lib/api/endpoints";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Field, inputCls, ChipGroup } from "@/components/ui/field";

// Gương mặt AI mẫu cho persona hệ thống (avatar_url rỗng). User tự tải sẽ đè lên.
const SYSTEM_FACES: Record<string, string> = {
  Linh: "/kol/linh.jpg",
  Minh: "/kol/an.jpg",
  Hà: "/kol/mai.jpg",
};

export default function KolPage() {
  const qc = useQueryClient();
  const kol = useQuery({ queryKey: ["kol"], queryFn: api.kolPersonas });
  const [open, setOpen] = useState(false);

  async function remove(id: string) {
    await api.deleteKol(id);
    qc.invalidateQueries({ queryKey: ["kol"] });
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-end justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="grid h-10 w-10 place-items-center rounded-xl bg-grad-brand-soft">
              <UserSquare2 className="h-5 w-5 text-violet-300" />
            </span>
            <h1 className="font-display text-2xl font-bold text-ink-high lg:text-[32px]">KOL AI</h1>
          </div>
          <p className="mt-1 text-ink-low">Chọn người mẫu AI sẵn có hoặc tạo KOL của riêng bạn.</p>
        </div>
        <Button onClick={() => setOpen((v) => !v)} variant={open ? "glass" : "primary"}>
          {open ? "Đóng" : "+ Tạo KOL"}
        </Button>
      </div>

      {open && <CreateKol onDone={() => { setOpen(false); qc.invalidateQueries({ queryKey: ["kol"] }); }} />}

      {kol.isLoading ? (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-56 w-full rounded-xl" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {(kol.data ?? []).map((k) => {
            const face = k.avatar_url || SYSTEM_FACES[k.name] || "";
            return (
            <GlassCard key={k.id} className="flex flex-col p-4">
              <div className="relative mb-3 grid aspect-square place-items-center overflow-hidden rounded-xl bg-bg-surface">
                {face ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={face} alt={k.name} className="h-full w-full object-cover" />
                ) : (
                  <UserSquare2 className="h-10 w-10 text-violet-300/60" />
                )}
                <div className="absolute right-2 top-2 flex flex-col gap-1">
                  {k.is_system && <Badge tone="neutral"><Lock className="mr-1 h-3 w-3" />Hệ thống</Badge>}
                  {k.moderation_status === "PENDING" && <Badge tone="hold">Chờ duyệt</Badge>}
                </div>
              </div>
              <div className="text-sm font-semibold text-ink-high">{k.name}</div>
              <div className="line-clamp-2 flex-1 text-xs text-ink-low">{k.description}</div>
              <div className="mt-3 flex items-center gap-1.5">
                <Link href={`/app/create?kol=${k.id}`} className="flex-1">
                  <Button
                    className="w-full gap-1.5"
                    size="sm"
                    disabled={k.moderation_status === "PENDING"}
                  >
                    <Sparkles className="h-3.5 w-3.5" /> Tạo video
                  </Button>
                </Link>
                {!k.is_system && (
                  <button
                    onClick={() => remove(k.id)}
                    className="grid h-8 w-8 shrink-0 place-items-center rounded-lg text-ink-low hover:bg-danger/10 hover:text-danger"
                    aria-label="Xoá KOL"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                )}
              </div>
            </GlassCard>
            );
          })}
        </div>
      )}
    </div>
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
