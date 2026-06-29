"use client";

import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { CONTENT_GROUPS, type FeatureGroup } from "@/lib/features";
import { cn } from "@/lib/utils/cn";
import { FeatureRow } from "./feature-row";

export const TOOLS_GROUPS = CONTENT_GROUPS.slice(1); // "Xây kênh" + "Ảnh & Âm thanh"

// Mỗi mega-panel có 1 "spotlight" trái: ảnh candid + 1 dòng dẫn. Dữ liệu thật, không số bịa.
export const SPOTLIGHT: Record<"content" | "tools", { image: string; eyebrow: string; title: string; sub: string; href: string }> = {
  content: {
    image: "/showcase/kol.jpg",
    eyebrow: "bắt đầu nhanh",
    title: "Nhập ý tưởng, ra video AI",
    sub: "Chọn một loại nội dung bên cạnh, hoặc vào thẳng trình tạo video.",
    href: "/app/create",
  },
  tools: {
    image: "/showcase/product.jpg",
    eyebrow: "công cụ",
    title: "Ảnh, giọng nói và remix",
    sub: "Các công cụ rời để dựng kênh ẩn danh và xử lý ảnh, âm thanh.",
    href: "/app/create",
  },
};

// panel dropdown ĐỤC (không để nội dung phía sau lọt qua)
export const PANEL =
  "rounded-2xl border border-white/[0.1] bg-bg-elevated/95 backdrop-blur-2xl shadow-[0_24px_70px_-20px_rgba(0,0,0,0.8)]";

/**
 * Bố cục RIÊNG của header Vyra: KHÔNG phải 3 cột text đều nhau. Bên trái là một "spotlight"
 * có ảnh candid + glow accent + lối tắt vào trình tạo; bên phải là các nhóm feature dạng bento.
 * Chỉ màn header mới có layout này → phân biệt với mọi màn khác.
 */
export function MegaPanel({ kind, groups, cols }: { kind: "content" | "tools"; groups: FeatureGroup[]; cols: number }) {
  const spot = SPOTLIGHT[kind];
  return (
    <div className="absolute left-1/2 top-full z-50 -translate-x-1/2 pt-3">
      <div
        className={cn(
          "relative overflow-hidden rounded-3xl border border-white/[0.08] bg-bg-elevated/95 backdrop-blur-2xl",
          "shadow-[0_30px_90px_-24px_rgba(0,0,0,0.85)]",
          "animate-in fade-in slide-in-from-top-1 duration-200",
          cols === 3 ? "w-[940px]" : "w-[760px]",
        )}
      >
        {/* dải accent tím mảnh trên đỉnh — chữ ký riêng của panel Vyra */}
        <div className="h-px w-full bg-gradient-to-r from-transparent via-violet-500/70 to-transparent" />

        <div className="grid grid-cols-[260px_1fr]">
          {/* SPOTLIGHT trái — ảnh candid + glow + lối tắt (nét riêng, không có ở panel cũ) */}
          <Link
            href={spot.href}
            className="group relative flex flex-col justify-end overflow-hidden border-r border-white/[0.06] p-5"
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={spot.image}
              alt=""
              loading="lazy"
              className="absolute inset-0 h-full w-full object-cover opacity-30 transition-transform duration-500 group-hover:scale-[1.06]"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-bg-elevated via-bg-elevated/85 to-bg-elevated/40" />
            <div className="pointer-events-none absolute -left-10 top-1/3 h-40 w-40 rounded-full bg-violet-500/20 blur-3xl" />
            <div className="relative">
              <span className="inline-flex items-center gap-2.5 text-[11px] font-semibold uppercase tracking-[0.2em] text-violet-300/90">
                <span className="h-[3px] w-5 rounded-full bg-grad-brand" />
                {spot.eyebrow}
              </span>
              <div className="mt-2.5 font-display text-lg font-bold leading-tight text-ink-high">
                {spot.title}
              </div>
              <p className="mt-1.5 text-xs leading-snug text-ink-low">{spot.sub}</p>
              <span className="mt-3 inline-flex items-center gap-1 text-xs font-semibold text-violet-300 transition group-hover:text-violet-200">
                Mở trình tạo
                <ArrowUpRight className="h-3.5 w-3.5 transition group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
              </span>
            </div>
          </Link>

          {/* BENTO phải — các nhóm feature */}
          <div className={cn("grid gap-x-4 gap-y-1 p-4", cols === 3 ? "grid-cols-2" : "grid-cols-1")}>
            {groups.map((g) => (
              <div key={g.title} className="px-1">
                <div className="mb-0.5 flex items-center gap-2 px-2.5 py-1.5">
                  <span className="h-[3px] w-4 rounded-full bg-grad-brand" />
                  <span className="text-[10.5px] font-semibold uppercase tracking-[0.16em] text-violet-300/80">
                    {g.title}
                  </span>
                </div>
                <div className="flex flex-col">
                  {g.items.map((f) => (
                    <FeatureRow key={f.key} f={f} />
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
