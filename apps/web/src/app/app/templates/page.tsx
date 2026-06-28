"use client";

import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { LayoutTemplate, Sparkles, Trash2, Lock } from "lucide-react";
import { api } from "@/lib/api/endpoints";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

export default function TemplatesPage() {
  const qc = useQueryClient();
  const templates = useQuery({ queryKey: ["templates"], queryFn: api.templates });

  async function remove(id: string) {
    await api.deleteTemplate(id);
    qc.invalidateQueries({ queryKey: ["templates"] });
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <div className="flex items-center gap-2">
          <span className="grid h-10 w-10 place-items-center rounded-xl bg-grad-brand-soft">
            <LayoutTemplate className="h-5 w-5 text-violet-300" />
          </span>
          <h1 className="font-display text-2xl font-bold text-ink-high lg:text-[32px]">Mẫu video</h1>
        </div>
        <p className="mt-1 text-ink-low">Chọn mẫu để bắt đầu nhanh, hoặc lưu mẫu của riêng bạn.</p>
      </div>

      {templates.isLoading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-40 w-full rounded-xl" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {(templates.data ?? []).map((t) => (
            <GlassCard key={t.id} className="flex flex-col p-5">
              <div className="mb-3 flex items-start justify-between gap-2">
                <span className="grid h-10 w-10 place-items-center rounded-xl bg-grad-brand-soft text-violet-300">
                  <LayoutTemplate className="h-5 w-5" />
                </span>
                {t.is_system ? (
                  <Badge tone="neutral">
                    <Lock className="mr-1 h-3 w-3" /> Hệ thống
                  </Badge>
                ) : (
                  <button
                    onClick={() => remove(t.id)}
                    className="grid h-8 w-8 place-items-center rounded-lg text-ink-low hover:bg-danger/10 hover:text-danger"
                    aria-label="Xoá mẫu"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                )}
              </div>
              <div className="text-base font-semibold text-ink-high">{t.name}</div>
              <div className="mt-1 line-clamp-2 flex-1 text-sm text-ink-low">{t.description}</div>
              <div className="mt-2 text-[11px] uppercase tracking-wider text-violet-300/70">
                {t.category}
              </div>
              <Link href={`/app/create?template=${t.id}`} className="mt-4">
                <Button className="w-full gap-2">
                  <Sparkles className="h-4 w-4" /> Dùng mẫu
                </Button>
              </Link>
            </GlassCard>
          ))}
        </div>
      )}
    </div>
  );
}
