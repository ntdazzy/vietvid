"use client";

import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { LayoutTemplate, Sparkles, Trash2, Lock } from "lucide-react";
import { api } from "@/lib/api/endpoints";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ScreenHero } from "@/components/app/screen-hero";

// ảnh thumbnail theo category (dùng khung nội dung mẫu thật trong /samples).
const CAT_IMG: Record<string, string> = {
  review: "/samples/kol_review.png",
  lookbook: "/samples/lookbook.png",
  product_ad: "/samples/unboxing.png",
  text_to_video: "/samples/food_review.png",
};

export default function TemplatesPage() {
  const qc = useQueryClient();
  const templates = useQuery({ queryKey: ["templates"], queryFn: api.templates });

  async function remove(id: string) {
    await api.deleteTemplate(id);
    qc.invalidateQueries({ queryKey: ["templates"] });
  }

  return (
    <div className="flex flex-col gap-6">
      <ScreenHero
        icon={LayoutTemplate}
        accent="violet"
        title="Mẫu video"
        sub="Chọn một mẫu để bắt đầu thật nhanh, hoặc lưu mẫu của riêng bạn."
      />

      {templates.isLoading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-40 w-full rounded-xl" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {(templates.data ?? []).map((t) => (
            <GlassCard key={t.id} className="flex flex-col overflow-hidden p-0">
              {/* thumbnail mẫu — khung nội dung thật theo category */}
              <div className="relative aspect-[16/10] overflow-hidden bg-bg-surface">
                {CAT_IMG[t.category] ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={CAT_IMG[t.category]} alt={t.name} className="h-full w-full object-cover" />
                ) : (
                  <div className="grid h-full w-full place-items-center bg-grad-brand-soft">
                    <LayoutTemplate className="h-8 w-8 text-violet-300/60" />
                  </div>
                )}
                <div className="absolute inset-0 bg-gradient-to-t from-bg-base/80 to-transparent" />
                {t.is_system ? (
                  <Badge tone="neutral" className="absolute right-2 top-2 bg-black/40">
                    <Lock className="mr-1 h-3 w-3" /> Hệ thống
                  </Badge>
                ) : (
                  <button
                    onClick={() => remove(t.id)}
                    className="absolute right-2 top-2 grid h-8 w-8 place-items-center rounded-lg bg-black/40 text-ink-low hover:bg-danger/30 hover:text-danger"
                    aria-label="Xoá mẫu"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                )}
                <div className="absolute bottom-2 left-3 text-[11px] uppercase tracking-wider text-violet-200">{t.category}</div>
              </div>
              <div className="flex flex-1 flex-col p-5">
                <div className="font-display text-base font-semibold text-ink-high">{t.name}</div>
                <div className="mt-1 line-clamp-2 flex-1 text-sm text-ink-low">{t.description}</div>
                <Link href={`/app/create?template=${t.id}`} className="mt-4">
                  <Button className="w-full gap-2">
                    <Sparkles className="h-4 w-4" /> Dùng mẫu
                  </Button>
                </Link>
              </div>
            </GlassCard>
          ))}
        </div>
      )}
    </div>
  );
}
