"use client";

import type { ReactNode } from "react";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { ActBadge, type Tone } from "@/components/marketing/act-badge";

// Card năng lực kiểu autovis (số mờ + badge + link) NHƯNG ô demo là component SỐNG.
export function CapabilityCard({
  index,
  tone,
  badge,
  title,
  desc,
  href,
  children,
}: {
  index: number;
  tone: Tone;
  badge: string;
  title: string;
  desc: string;
  href: string;
  children: ReactNode;
}) {
  const num = String(index).padStart(2, "0");
  return (
    <div className="group relative flex min-h-[300px] sm:min-h-[380px] flex-col overflow-hidden rounded-[20px] glass-bordered p-5 transition-all duration-300 hover:-translate-y-1">
      {/* số mờ + viền tím khi hover */}
      <span className="pointer-events-none absolute right-4 top-1 font-display text-[5rem] font-bold leading-none text-white/[0.05]">
        {num}
      </span>
      <span className="pointer-events-none absolute inset-0 rounded-[20px] ring-1 ring-violet-400/0 transition duration-300 group-hover:ring-violet-400/30" />

      <ActBadge tone={tone} label={badge} className="relative w-fit" />

      {/* demo sống */}
      <div className="relative mt-4 max-h-[240px] flex-1 overflow-hidden sm:max-h-none">{children}</div>

      {/* đáy: tiêu đề + mô tả + link */}
      <div className="relative mt-4">
        <h3 className="font-display text-lg font-bold text-ink-high">{title}</h3>
        <p className="mt-1 text-sm text-ink-low">{desc}</p>
        <Link href={href} className="mt-2 inline-flex items-center gap-1 text-sm font-medium text-violet-300 transition hover:text-violet-200">
          Khám phá ngay <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-1" />
        </Link>
      </div>
    </div>
  );
}
