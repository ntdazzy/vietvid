"use client";

import { useQuery } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { Check, UserSquare2 } from "lucide-react";
import { useWizard } from "@/store/wizard";
import { api } from "@/lib/api/endpoints";
import { kolFace } from "@/lib/kol-faces";
import { Skeleton } from "@/components/ui/skeleton";
import { HoverVideo } from "@/components/ui/hover-video";
import { cn } from "@/lib/utils/cn";

/** Chọn KOL bằng GƯƠNG MẶT (gallery ảnh) — như autovis, thay vì chỉ gõ tên. */
export function KolPicker() {
  const t = useTranslations("create");
  const w = useWizard();
  const kols = useQuery({ queryKey: ["kol-personas"], queryFn: api.kolPersonas });

  return (
    <div className="grid grid-cols-3 gap-2.5 sm:grid-cols-4">
      {kols.isLoading
        ? Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="aspect-[3/4] w-full rounded-xl" />)
        : (kols.data ?? []).map((k) => {
            const active = w.kolPersonaId === k.id;
            const face = kolFace(k.name, k.avatar_url);
            const faceVideo = face.startsWith("/kol/") ? face.replace(/\.jpg$/, ".mp4") : undefined;
            const overlays = (
              <>
                <div className="pointer-events-none absolute inset-x-0 bottom-0 bg-gradient-to-t from-bg-base/90 to-transparent p-1.5 pt-5">
                  <div className="truncate text-[11px] font-medium text-white">{k.name}</div>
                  <div className="text-[9px] uppercase tracking-wide text-violet-200">
                    {k.gender === "male" || k.voice_gender === "male" ? t("genderMale") : t("genderFemale")}
                  </div>
                </div>
                {active && (
                  <span className="absolute right-1.5 top-1.5 grid h-5 w-5 place-items-center rounded-full bg-violet-500">
                    <Check className="h-3 w-3 text-white" />
                  </span>
                )}
              </>
            );
            return (
              <button
                key={k.id}
                type="button"
                onClick={() =>
                  w.patch({
                    kolPersonaId: k.id,
                    kolName: k.name,
                    voiceGender: (k.voice_gender as "female" | "male") || "female",
                  })
                }
                aria-pressed={active}
                aria-label={t("selectKolAria", { name: k.name })}
                className={cn(
                  "relative aspect-[3/4] overflow-hidden rounded-xl border-2 transition-all",
                  active ? "border-violet-400 shadow-glow-sm" : "border-white/10 hover:border-white/30",
                )}
              >
                {face ? (
                  <HoverVideo poster={face} video={faceVideo} alt={k.name} className="h-full w-full">
                    {overlays}
                  </HoverVideo>
                ) : (
                  <div className="relative grid h-full w-full place-items-center bg-bg-surface">
                    <UserSquare2 className="h-6 w-6 text-violet-300/60" />
                    {overlays}
                  </div>
                )}
              </button>
            );
          })}
    </div>
  );
}
