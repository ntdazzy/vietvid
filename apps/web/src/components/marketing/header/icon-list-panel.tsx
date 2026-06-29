"use client";

import Link from "next/link";
import { type LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { PANEL } from "./mega-panel";

/** Panel danh sách có icon (Quản lý / Hỗ trợ) — gọn, nhưng vẫn có khí chất bảng điều khiển. */
export function IconListPanel({ title, items }: { title: string; items: { label: string; href: string; icon: LucideIcon }[] }) {
  return (
    <div className="absolute left-1/2 top-full z-50 w-64 -translate-x-1/2 pt-3">
      <div className={cn(PANEL, "overflow-hidden animate-in fade-in slide-in-from-top-1 duration-200")}>
        <div className="h-px w-full bg-gradient-to-r from-transparent via-violet-500/70 to-transparent" />
        <div className="flex items-center gap-2 px-3 pb-1 pt-3">
          <span className="h-[3px] w-4 rounded-full bg-grad-brand" />
          <span className="text-[10.5px] font-semibold uppercase tracking-[0.16em] text-violet-300/80">{title}</span>
        </div>
        <div className="p-2 pt-1">
          {items.map(({ label, href, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              className="group flex items-center gap-3 rounded-xl px-2.5 py-2 text-sm text-ink-medium outline-none transition-all hover:translate-x-0.5 hover:bg-violet-500/[0.07] hover:text-ink-high focus-visible:ring-2 focus-visible:ring-violet-400/60"
            >
              <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-violet-500/[0.1] text-violet-300 transition-colors group-hover:bg-violet-500/20">
                <Icon className="h-4 w-4" />
              </span>
              {label}
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
