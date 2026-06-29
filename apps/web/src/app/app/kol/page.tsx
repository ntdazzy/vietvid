"use client";

import { useRef, useState } from "react";
import { useTranslations } from "next-intl";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  UserSquare2, Sparkles, Trash2, Lock, Loader2, ShieldCheck,
  Wand2, Images, Plus, Clapperboard,
} from "lucide-react";
import { api } from "@/lib/api/endpoints";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { HoverVideo } from "@/components/ui/hover-video";
import { CineHero, FilmLabel } from "@/components/ui/cinematic";
import { Reveal } from "@/components/marketing/reveal";
import { cn } from "@/lib/utils/cn";
import { SectionLabel } from "@/components/kol/section-label";
import { HeroStat } from "@/components/kol/hero-stat";
import { SceneCard } from "@/components/kol/scene-card";
import { CreateKol } from "@/components/kol/create-kol-form";

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

// Map giá trị category (dùng cho logic filter) → key dịch.
const CAT_KEYS: Record<string, string> = {
  "Tất cả": "catAll",
  "Thời trang": "catFashion",
  "Mỹ phẩm": "catCosmetics",
  "Skincare": "catSkincare",
  "F&B": "catFnb",
  "Gym": "catGym",
  "Văn phòng": "catOffice",
  "Gen Z": "catGenZ",
  "Cao cấp": "catLuxury",
  "Gia dụng": "catHome",
};

export default function KolPage() {
  const t = useTranslations("kol");
  const qc = useQueryClient();
  const router = useRouter();
  const kol = useQuery({ queryKey: ["kol"], queryFn: api.kolPersonas });
  const [open, setOpen] = useState(false);
  const [cat, setCat] = useState("Tất cả");
  const [usingId, setUsingId] = useState<string | null>(null);
  const libRef = useRef<HTMLDivElement>(null);
  const formRef = useRef<HTMLDivElement>(null);

  const personas = kol.data ?? [];
  const presets = cat === "Tất cả" ? PRESETS : PRESETS.filter((p) => p.cat === cat);

  function openForm() {
    setOpen(true);
    requestAnimationFrame(() => formRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }));
  }

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
    <div className="flex flex-col gap-8">
      {/* HERO ĐIỆN ẢNH — phòng casting */}
      <CineHero
        accent="rose"
        bg="/bg/ring.jpg"
        label={t("heroLabel")}
        status={t("heroStatus", { kol: personas.length, presets: PRESETS.length })}
        eyebrow={t("heroEyebrow")}
        title={t.rich("heroTitle", { grad: (c) => <span className="text-gradient">{c}</span> })}
        sub={t("heroSub")}
        actions={
          <>
            <Button onClick={openForm} size="lg" className="gap-2"><Plus className="h-4 w-4" /> {t("createKol")}</Button>
            <Button variant="outline" size="lg" onClick={() => libRef.current?.scrollIntoView({ behavior: "smooth", block: "start" })} className="gap-2">
              <Images className="h-4 w-4" /> {t("libraryNav")}
            </Button>
          </>
        }
      >
        <div className="flex flex-wrap items-center gap-x-8 gap-y-3">
          <HeroStat n={personas.length} l={t("statYourKol")} />
          <HeroStat n={PRESETS.length} l={t("statAiFaces")} />
          <span className="flex items-center gap-1.5 text-sm text-ink-medium">
            <ShieldCheck className="h-4 w-4 text-rose-300" /> {t("statConsistent")}
          </span>
        </div>
      </CineHero>

      {/* CHẾ ĐỘ TẠO — 2 "scene" */}
      <Reveal>
        <div className="grid gap-4 sm:grid-cols-2">
          <SceneCard
            label={t("sceneCustomLabel")}
            icon={Wand2}
            title={t("sceneCustomTitle")}
            desc={t("sceneCustomDesc")}
            cta={t("sceneCustomCta")}
            onClick={openForm}
          />
          <SceneCard
            label={t("sceneQuickLabel")}
            icon={Images}
            title={t("sceneQuickTitle")}
            desc={t("sceneQuickDesc")}
            cta={t("sceneQuickCta")}
            onClick={() => libRef.current?.scrollIntoView({ behavior: "smooth", block: "start" })}
          />
        </div>
      </Reveal>

      <div ref={formRef}>
        {open && <CreateKol onDone={() => { setOpen(false); qc.invalidateQueries({ queryKey: ["kol"] }); }} />}
      </div>

      {/* KOL CỦA BẠN */}
      <Reveal>
        <section className="flex flex-col gap-3">
          <SectionLabel>{t("yourKolLabel")}</SectionLabel>
          {kol.isLoading ? (
            <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
              {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="aspect-[3/4] w-full rounded-xl" />)}
            </div>
          ) : personas.length === 0 ? (
            <p className="rounded-xl border border-dashed border-white/10 px-4 py-8 text-center text-sm text-ink-low">
              {t("emptyKol")}
            </p>
          ) : (
            <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
              {personas.map((k) => {
                const face = k.avatar_url || SYSTEM_FACES[k.name] || "";
                const faceVideo = face.startsWith("/kol/") ? face.replace(/\.jpg$/, ".mp4") : undefined;
                const overlays = (
                  <>
                    <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-bg-base/85 to-transparent" />
                    <div className="absolute right-2 top-2 flex flex-col items-end gap-1">
                      {k.is_system && <Badge tone="neutral" className="bg-black/40"><Lock className="mr-1 h-3 w-3" />{t("badgeSystem")}</Badge>}
                      {k.moderation_status === "PENDING" && <Badge tone="hold" className="bg-black/40">{t("badgePending")}</Badge>}
                    </div>
                    <div className="absolute inset-x-3 bottom-2">
                      <div className="font-display text-sm font-semibold text-white">{k.name}</div>
                      <div className="line-clamp-1 text-[11px] text-white/70">{k.description}</div>
                    </div>
                  </>
                );
                return (
                  <GlassCard key={k.id} className="group flex flex-col overflow-hidden p-0 transition-all duration-200 hover:-translate-y-1 hover:shadow-glow-sm hover:ring-1 hover:ring-rose-400/30">
                    {face ? (
                      <HoverVideo poster={face} video={faceVideo} alt={k.name} className="aspect-[3/4] bg-bg-surface transition-transform duration-500 group-hover:scale-[1.04]">
                        {overlays}
                      </HoverVideo>
                    ) : (
                      <div className="relative grid aspect-[3/4] place-items-center overflow-hidden bg-bg-surface">
                        <UserSquare2 className="h-10 w-10 text-rose-300/50" />
                        {overlays}
                      </div>
                    )}
                    <div className="flex items-center gap-1.5 p-2.5">
                      <Link href={`/app/create?kol=${k.id}`} className="flex-1">
                        <Button className="w-full gap-1.5" size="sm" disabled={k.moderation_status === "PENDING"}>
                          <Sparkles className="h-3.5 w-3.5" /> {t("makeVideo")}
                        </Button>
                      </Link>
                      {!k.is_system && (
                        <button onClick={() => remove(k.id)} className="grid h-8 w-8 shrink-0 place-items-center rounded-lg text-ink-low transition-colors hover:bg-danger/10 hover:text-danger" aria-label={t("deleteKol")}>
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
      </Reveal>

      {/* THƯ VIỆN CASTING */}
      <section ref={libRef} className="flex scroll-mt-24 flex-col gap-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <SectionLabel>{t("libraryLabel")}</SectionLabel>
            <p className="mt-1 text-sm text-ink-low">{t("librarySub")}</p>
          </div>
          <FilmLabel dot={false} className="hidden sm:inline-flex">{t("presetCount", { count: presets.length })}</FilmLabel>
        </div>

        <div className="flex flex-wrap gap-2">
          {CATS.map((c) => (
            <button
              key={c}
              onClick={() => setCat(c)}
              aria-pressed={cat === c}
              className={cn(
                "rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors",
                cat === c ? "border-rose-400/40 bg-rose-500/20 text-ink-high" : "border-white/10 text-ink-low hover:text-ink-medium",
              )}
            >
              {t(CAT_KEYS[c])}
            </button>
          ))}
        </div>

        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          {presets.map((p) => (
            <GlassCard key={p.id} className="group flex flex-col overflow-hidden p-0 transition-all duration-200 hover:-translate-y-1 hover:shadow-glow-sm hover:ring-1 hover:ring-rose-400/30">
              <HoverVideo poster={p.img} video={p.img.replace(/\.jpg$/, ".mp4")} alt={p.name} className="aspect-[3/4] transition-transform duration-500 group-hover:scale-[1.04]">
                <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-bg-base/85 to-transparent" />
                <span className="absolute left-2 top-2 rounded-md bg-black/45 px-2 py-0.5 text-[10px] font-medium text-rose-200">{t(CAT_KEYS[p.cat])}</span>
                <div className="absolute inset-x-3 bottom-2">
                  <div className="font-display text-sm font-semibold text-white">{p.name}</div>
                  <div className="text-[11px] text-white/70">{p.gender === "male" ? t("genderMale") : t("genderFemale")}</div>
                </div>
              </HoverVideo>
              <div className="p-2.5">
                <Button onClick={() => usePreset(p)} disabled={usingId !== null} size="sm" className="w-full gap-1.5">
                  {usingId === p.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <Clapperboard className="h-4 w-4" />}
                  {t("usePreset")}
                </Button>
              </div>
            </GlassCard>
          ))}
        </div>
      </section>
    </div>
  );
}
